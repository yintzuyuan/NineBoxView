# encoding: utf-8

###########################################################################################################
#
#
#    一般插件
#
#    閱讀文檔：
#    https://github.com/schriftgestalt/GlyphsSDK/tree/master/Python%20Templates/General%20Plugin
#
#
###########################################################################################################


# https://developer.apple.com/library/content/documentation/Cocoa/Conceptual/CocoaViewsGuide/SubclassingNSView/SubclassingNSView.html

import objc
from GlyphsApp import *
from GlyphsApp.plugins import *
from AppKit import NSColor, NSFont, NSAffineTransform, NSRectFill, NSView, NSBezierPath, NSWorkspace, NSClickGestureRecognizer
from vanilla import FloatingWindow, Group, Button, EditText, Slider
import traceback  # Added this line

class NineBoxPreviewView(NSView):
    def init(self):
        self = super(NineBoxPreviewView, self).init()
        if self:
            doubleClickRecognizer = NSClickGestureRecognizer.alloc().initWithTarget_action_(self, self.handleDoubleClick_)
            doubleClickRecognizer.setNumberOfClicksRequired_(2)
            self.addGestureRecognizer_(doubleClickRecognizer)
        return self
    
    def handleDoubleClick_(self, sender):
        self.wrapper.plugin.resetZoom()

    def drawRect_(self, rect):
        try:
            # Set background color
            if self.wrapper.plugin.darkMode:
                NSColor.colorWithCalibratedRed_green_blue_alpha_(0, 0, 0, 1.0).set()
            else:
                NSColor.colorWithCalibratedRed_green_blue_alpha_(1.0, 1.0, 1.0, 1.0).set()
            NSRectFill(rect)

            if not Glyphs.font or not Glyphs.font.selectedLayers:
                return

            self.currentLayer = Glyphs.font.selectedLayers[0]
            currentChar = self.currentLayer.parent.unicode

            if self.wrapper.plugin.w.searchField.get().strip() == "":
                self.searchChar = currentChar
            else:
                self.searchChar = self.wrapper.plugin.lastChar or currentChar

            centerGlyph = self.currentLayer.parent
            searchGlyph = Glyphs.font.glyphs[self.searchChar] if self.searchChar else centerGlyph
            currentMaster = Glyphs.font.selectedFontMaster

            MARGIN_RATIO = 0.07
            SPACING_RATIO = 0.03

            self.cachedHeight = currentMaster.ascender - currentMaster.descender
            MARGIN = min(rect.size.width, rect.size.height) * MARGIN_RATIO

            centerWidth = self.currentLayer.width
            searchWidth = searchGlyph.layers[currentMaster.id].width
            SPACING = max(centerWidth, searchWidth) * SPACING_RATIO

            searchCellWidth = searchWidth + SPACING
            centerCellWidth = max(centerWidth, searchWidth) + SPACING

            gridWidth = centerCellWidth + 2 * searchCellWidth + 2 * SPACING
            gridHeight = 3 * self.cachedHeight + 2 * SPACING

            availableWidth = rect.size.width - 2 * MARGIN
            availableHeight = rect.size.height - 2 * MARGIN
            scale = min(availableWidth / gridWidth, availableHeight / gridHeight, 1)

            # 應用自定義縮放
            customScale = self.wrapper.plugin.zoomFactor
            scale *= customScale

            centerCellWidth *= scale
            searchCellWidth *= scale
            gridWidth *= scale
            gridHeight *= scale
            SPACING *= scale

            startX = rect.size.width / 2 - gridWidth / 2
            offsetY = rect.size.height * 0.05
            startY = (rect.size.height + gridHeight) / 2 + offsetY
            leftColumnCenterX = startX + searchCellWidth / 2
            middleColumnCenterX = startX + searchCellWidth + SPACING + centerCellWidth / 2
            rightColumnCenterX = startX + gridWidth - searchCellWidth / 2

            for i in range(9):
                row = i // 3
                col = i % 3
                
                if col == 0:
                    centerX = leftColumnCenterX
                    cellWidth = searchCellWidth
                elif col == 1:
                    centerX = middleColumnCenterX
                    cellWidth = centerCellWidth if i == 4 else searchCellWidth
                else:
                    centerX = rightColumnCenterX
                    cellWidth = searchCellWidth
                
                centerY = startY - (row + 0.5) * (gridHeight / 3)
                cellHeight = gridHeight / 3 - SPACING

                if i == 4:
                    layer = self.currentLayer
                else:
                    layer = searchGlyph.layers[currentMaster.id]

                if layer:
                    glyphWidth = layer.width
                    glyphHeight = self.cachedHeight
                    scaleX = cellWidth / glyphWidth if glyphWidth > 0 else 1
                    scaleY = cellHeight / glyphHeight if glyphHeight > 0 else 1
                    glyphScale = min(scaleX, scaleY)

                    scaledWidth = glyphWidth * glyphScale
                    scaledHeight = glyphHeight * glyphScale
                    x = centerX - scaledWidth / 2
                    y = centerY - scaledHeight / 2

                    transform = NSAffineTransform.transform()
                    transform.translateXBy_yBy_(x, y)
                    transform.scaleBy_(glyphScale)

                    bezierPath = layer.completeBezierPath.copy()
                    bezierPath.transformUsingAffineTransform_(transform)

                    if self.wrapper.plugin.darkMode:
                        NSColor.whiteColor().set()
                    else:
                        NSColor.blackColor().set()
                    bezierPath.fill()

        except Exception as e:
            print(traceback.format_exc())

class NineBoxPreview(Group):
    nsViewClass = NineBoxPreviewView

    def __init__(self, posSize, plugin):
        super(NineBoxPreview, self).__init__(posSize)
        self._nsObject.wrapper = self
        self.plugin = plugin

    def redraw(self):
        self._nsObject.setNeedsDisplay_(True)

class NineBoxView(GeneralPlugin):

    @objc.python_method
    def settings(self):
        self.name = Glyphs.localize({
            'en': u'Nine Box View', 
            'zh-Hant': u'九宮格預覽'
        })
        self.loadPreferences()

    @objc.python_method
    def start(self):
        try:
            newMenuItem = NSMenuItem(self.name, self.toggleWindow_)
            Glyphs.menu[WINDOW_MENU].append(newMenuItem)
            
            Glyphs.addCallback(self.updateInterface, UPDATEINTERFACE)
            # Changed FONTMASTER_CHANGED to DOCUMENTACTIVATED
            Glyphs.addCallback(self.updateInterface, DOCUMENTACTIVATED)

            NSWorkspace.sharedWorkspace().notificationCenter().addObserver_selector_name_object_(
                self,
                self.applicationActivated_,
                "NSWorkspaceDidActivateApplicationNotification",
                None
            )
            NSWorkspace.sharedWorkspace().notificationCenter().addObserver_selector_name_object_(
                self,
                self.applicationDeactivated_,
                "NSWorkspaceDidDeactivateApplicationNotification",
                None
            )
            
            self.loadPreferences()
        except:
            self.logToMacroWindow(traceback.format_exc())

    @objc.python_method
    def pickGlyph(self, sender):
        font = Glyphs.font
        if not font:
            return
        
        choice = PickGlyphs(
            list(font.glyphs),
            font.selectedFontMaster.id,
            self.lastChar,
            "com.YinTzuYuan.NineBoxView.search"
        )
        
        if choice and choice[0]:
            self.lastChar = choice[0][0].unicode
            self.w.searchField.set(self.lastChar)
            self.savePreferences()
            self.updateInterface(None)

    @objc.python_method
    def toggleWindow_(self, sender):
        try:
            if not hasattr(self, 'w') or self.w is None:
                self.w = FloatingWindow((300, 340), self.name, minSize=(200, 240),
                                        autosaveName="com.YinTzuYuan.NineBoxView.mainwindow")
                self.w.preview = NineBoxPreview((0, 0, -0, -60), self)
                
                self.w.zoomSlider = Slider((10, -55, -10, 22), 
                                           minValue=0.5, 
                                           maxValue=2.0, 
                                           value=self.zoomFactor, 
                                           callback=self.zoomCallback)
                
                placeholder = Glyphs.localize({
                    'en': u'Enter a character',
                    'zh-Hant': u'輸入一個字符'
                })
                
                self.w.searchField = EditText((10, -30, -140, 22), 
                                            placeholder=placeholder, 
                                            callback=self.searchFieldCallback)
                self.w.searchField.set(self.lastChar)
                
                searchButtonTitle = Glyphs.localize({
                    'en': u'Search',
                    'zh-Hant': u'搜尋'
                })
                self.w.searchButton = Button((-130, -30, -70, 22), searchButtonTitle,
                                            callback=self.pickGlyph)
                
                self.w.darkModeButton = Button((-60, -30, -10, 22), self.getDarkModeIcon(),
                                            callback=self.darkModeCallback)
                
                self.w.bind("close", self.windowClosed_)
                self.w.open()
                self.w.makeKeyAndOrderFront_(None)  # 修改為 makeKeyAndOrderFront 以聚焦視窗
            elif self.w.isVisible():
                self.w.close()
            else:
                self.w.show()
                self.w.makeKeyAndOrderFront_(None)  # 修改為 makeKeyAndOrderFront 以聚焦視窗

            self.updateInterface(None)
        except:
            self.logToMacroWindow(traceback.format_exc())

    @objc.python_method
    def windowClosed_(self, sender):
        self.w = None

    @objc.python_method
    def getDarkModeIcon(self):
        return "◐" if self.darkMode else "◑"

    @objc.python_method
    def loadPreferences(self):
        self.darkMode = Glyphs.defaults.get("com.YinTzuYuan.NineBoxView.darkMode", False)
        self.lastChar = Glyphs.defaults.get("com.YinTzuYuan.NineBoxView.lastChar", "")
        self.testMode = Glyphs.defaults.get("com.YinTzuYuan.NineBoxView.testMode", False)
        self.searchHistory = Glyphs.defaults.get("com.YinTzuYuan.NineBoxView.search", "")
        self.zoomFactor = Glyphs.defaults.get("com.YinTzuYuan.NineBoxView.zoomFactor", 1.0)

    @objc.python_method
    def savePreferences(self):
        Glyphs.defaults["com.YinTzuYuan.NineBoxView.darkMode"] = self.darkMode
        Glyphs.defaults["com.YinTzuYuan.NineBoxView.lastChar"] = self.lastChar
        Glyphs.defaults["com.YinTzuYuan.NineBoxView.testMode"] = self.testMode
        Glyphs.defaults["com.YinTzuYuan.NineBoxView.search"] = self.searchHistory
        Glyphs.defaults["com.YinTzuYuan.NineBoxView.zoomFactor"] = self.zoomFactor

    @objc.python_method
    def logToMacroWindow(self, message):
        Glyphs.clearLog()
        print(message)

    @objc.python_method
    def updateInterface(self, sender):
        if hasattr(self, 'w') and self.w is not None and hasattr(self.w, 'preview'):
            self.w.preview.redraw()

    @objc.python_method
    def searchFieldCallback(self, sender):
        char = sender.get()
        if len(char) > 0:
            self.lastChar = char[0]
            sender.set(self.lastChar)  # 將輸入欄位限制只能輸入一個字符
        else:
            self.lastChar = ""
        self.savePreferences()
        self.updateInterface(None)

    @objc.python_method
    def darkModeCallback(self, sender):
        self.darkMode = not self.darkMode
        sender.setTitle(self.getDarkModeIcon())
        self.savePreferences()
        self.updateInterface(None)

    @objc.python_method
    def zoomCallback(self, sender):
        self.zoomFactor = sender.get()
        self.savePreferences()
        self.updateInterface(None)

    @objc.python_method
    def resetZoom(self):
        self.zoomFactor = 1.0
        self.w.zoomSlider.set(self.zoomFactor)
        self.savePreferences()
        self.updateInterface(None)

    @objc.python_method
    def showWindow(self):
        if hasattr(self, 'w') and self.w is not None:
            self.w.show()

    @objc.python_method
    def hideWindow(self):
        if hasattr(self, 'w') and self.w is not None:
            self.w.hide()

    @objc.python_method
    def __del__(self):
        self.savePreferences()
        Glyphs.removeCallback(self.updateInterface, UPDATEINTERFACE)
        Glyphs.removeCallback(self.updateInterface, DOCUMENTACTIVATED)
        NSWorkspace.sharedWorkspace().notificationCenter().removeObserver_(self)

    def __file__(self):
        return __file__