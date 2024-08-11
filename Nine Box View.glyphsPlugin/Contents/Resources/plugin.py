# encoding: utf-8

###########################################################################################################
#
#
#    General Plugin
#
#    Read the docs:
#    https://github.com/schriftgestalt/GlyphsSDK/tree/master/Python%20Templates/General%20Plugin
#
#
###########################################################################################################


#https://developer.apple.com/library/content/documentation/Cocoa/Conceptual/CocoaViewsGuide/SubclassingNSView/SubclassingNSView.html

import objc
from GlyphsApp import *
from GlyphsApp.plugins import *
from AppKit import NSColor, NSFont, NSAffineTransform, NSRectFill, NSView, NSBezierPath, NSWorkspace
from vanilla import FloatingWindow, Group, Button, EditText
import traceback


class NineBoxPreviewView(NSView):
    def drawRect_(self, rect):
        try:
            # 設定背景顏色
            if self.wrapper.plugin.darkMode:
                NSColor.blackColor().set()
            else:
                NSColor.whiteColor().set()
            NSRectFill(rect)

            if not Glyphs.font or not Glyphs.font.selectedLayers:
                return

            # 獲取當前選中的圖層
            self.currentLayer = Glyphs.font.selectedLayers[0]
            currentChar = self.currentLayer.parent.unicode

            # 檢查搜索欄是否為空
            if self.wrapper.plugin.w.searchField.get().strip() == "":
                # 如果搜索欄為空,使用當前選中的字符
                self.searchChar = currentChar
            else:
                # 否則使用上次搜索的字符或當前字符
                self.searchChar = self.wrapper.plugin.lastChar or currentChar

            # 獲取搜索字符的字形
            centerGlyph = self.currentLayer.parent
            searchGlyph = Glyphs.font.glyphs[self.searchChar] if self.searchChar else centerGlyph

            # 獲取當前選中的主板
            currentMaster = Glyphs.font.selectedFontMaster

            # 可調整參數
            MARGIN_RATIO = 0.07  # 邊距佔視窗高度的比例
            SPACING_RATIO = 0.03  # 間距佔字寬的比例

            # 計算固定的字形高度
            self.cachedHeight = currentMaster.ascender - currentMaster.descender

            # 計算邊距
            MARGIN = min(rect.size.width, rect.size.height) * MARGIN_RATIO

            # 獲取中間字符和搜尋字符的寬度
            centerGlyph = self.currentLayer.parent
            centerWidth = self.currentLayer.width
            searchGlyph = Glyphs.font.glyphs[self.searchChar] if self.searchChar else centerGlyph
            searchWidth = searchGlyph.layers[currentMaster.id].width

            # 計算間距
            SPACING = max(centerWidth, searchWidth) * SPACING_RATIO

            # 計算格子寬度
            searchCellWidth = searchWidth + SPACING
            centerCellWidth = max(centerWidth, searchWidth) + SPACING

            # 計算九宮格的實際大小
            gridWidth = centerCellWidth + 2 * searchCellWidth + 2 * SPACING
            gridHeight = 3 * self.cachedHeight + 2 * SPACING

            # 確保九宮格不超出可用空間
            availableWidth = rect.size.width - 2 * MARGIN
            availableHeight = rect.size.height - 2 * MARGIN
            scale = min(availableWidth / gridWidth, availableHeight / gridHeight, 1)

            # 應用縮放
            centerCellWidth *= scale
            searchCellWidth *= scale
            gridWidth *= scale
            gridHeight *= scale
            SPACING *= scale

            # 計算九宮格的起始位置和列寬度
            startX = rect.size.width / 2 - gridWidth / 2
            offsetY = rect.size.height * 0.05
            startY = (rect.size.height + gridHeight) / 2 + offsetY
            leftColumnCenterX = startX + searchCellWidth / 2
            middleColumnCenterX = startX + searchCellWidth + SPACING + centerCellWidth / 2
            rightColumnCenterX = startX + gridWidth - searchCellWidth / 2

            for i in range(9):
                row = i // 3
                col = i % 3
                
                # 計算每個格子的中心位置和大小
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

                if i == 4:  # 中間格子
                    layer = self.currentLayer
                else:
                    layer = searchGlyph.layers[currentMaster.id]

                if layer:
                    # 計算縮放比例
                    glyphWidth = layer.width
                    glyphHeight = self.cachedHeight
                    scaleX = cellWidth / glyphWidth if glyphWidth > 0 else 1
                    scaleY = cellHeight / glyphHeight if glyphHeight > 0 else 1
                    glyphScale = min(scaleX, scaleY)

                    # 計算字符的左上角位置
                    scaledWidth = glyphWidth * glyphScale
                    scaledHeight = glyphHeight * glyphScale
                    x = centerX - scaledWidth / 2
                    y = centerY - scaledHeight / 2

                    # 創建變換矩陣
                    transform = NSAffineTransform.transform()
                    transform.translateXBy_yBy_(x, y)
                    transform.scaleBy_(glyphScale)

                    # 繪製字符
                    bezierPath = layer.completeBezierPath.copy()
                    bezierPath.transformUsingAffineTransform_(transform)

                    # 設定繪製顏色
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

    @objc.python_method
    def start(self):
        try:
            newMenuItem = NSMenuItem(self.name, self.toggleWindow_)
            Glyphs.menu[WINDOW_MENU].append(newMenuItem)
            
            self.loadPreferences()
            
            Glyphs.addCallback(self.updateInterface, UPDATEINTERFACE)
            Glyphs.addCallback(self.updateInterface, FONTMASTER_CHANGED)

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
        except:
            self.logToMacroWindow(traceback.format_exc())

    @objc.python_method
    def toggleWindow_(self, sender):
        try:
            if not hasattr(self, 'w') or self.w is None:
                self.w = FloatingWindow((300, 340), self.name, minSize=(200, 240),
                                        autosaveName="com.YinTzuYuan.NineBoxView.mainwindow")
                self.w.preview = NineBoxPreview((0, 0, -0, -40), self)
                self.w.searchField = EditText((10, -30, -100, -10), 
                                            placeholder="輸入一個字符", 
                                            callback=self.searchFieldCallback)
                self.w.darkModeButton = Button((-90, -30, -10, -10), self.getDarkModeIcon(),
                                            callback=self.darkModeCallback)
                self.w.bind("close", self.windowClosed_)
                self.w.open()
            elif self.w.isVisible():
                self.w.close()
            else:
                self.w.show()

            self.updateInterface(None)
        except:
            self.logToMacroWindow(traceback.format_exc())

    @objc.python_method
    def windowClosed_(self, sender):
        self.w = None

    @objc.python_method
    def getDarkModeIcon(self):
        return "🌙" if self.darkMode else "☀️"

    @objc.python_method
    def loadPreferences(self):
        self.darkMode = Glyphs.defaults.get("com.YinTzuYuan.NineBoxView.darkMode", False)
        self.lastChar = Glyphs.defaults.get("com.YinTzuYuan.NineBoxView.lastChar", "")

    @objc.python_method
    def savePreferences(self):
        Glyphs.defaults["com.YinTzuYuan.NineBoxView.darkMode"] = self.darkMode
        Glyphs.defaults["com.YinTzuYuan.NineBoxView.lastChar"] = self.lastChar

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
        else:
            self.lastChar = ""
        self.updateInterface(None)

    @objc.python_method
    def darkModeCallback(self, sender):
        self.darkMode = not self.darkMode
        sender.setTitle(self.getDarkModeIcon())
        self.updateInterface(None)

    @objc.python_method
    def applicationActivated_(self, notification):
        activatedApp = notification.userInfo()["NSWorkspaceApplicationKey"]
        if activatedApp.bundleIdentifier() == "com.GeorgSeifert.Glyphs3":
            self.showWindow()

    @objc.python_method
    def applicationDeactivated_(self, notification):
        deactivatedApp = notification.userInfo()["NSWorkspaceApplicationKey"]
        if deactivatedApp.bundleIdentifier() == "com.GeorgSeifert.Glyphs3":
            self.hideWindow()

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
        Glyphs.removeCallback(self.updateInterface, FONTMASTER_CHANGED)
        NSWorkspace.sharedWorkspace().notificationCenter().removeObserver_(self)

    def __file__(self):
        return __file__