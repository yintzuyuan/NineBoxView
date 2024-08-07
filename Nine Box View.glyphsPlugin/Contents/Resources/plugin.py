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
from AppKit import NSColor, NSFont, NSAffineTransform, NSRectFill, NSView, NSBezierPath, NSFloatingWindowLevel
from vanilla import Window, Group, Button, EditText
import traceback

class NineBoxPreviewView(NSView):
    def init(self):
        self = super(NineBoxPreviewView, self).init()
        if self:
            self.cachedWidth = 0
            self.cachedHeight = 0
            self.cachedSearchChar = None
            self.currentLayer = None
            self.searchChar = None
        return self

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

            self.currentLayer = Glyphs.font.selectedLayers[0]
            currentChar = self.currentLayer.parent.unicode
            self.searchChar = self.wrapper.plugin.lastChar or currentChar

            # 可調整參數
            MARGIN_RATIO = 0.10  # 邊距佔視窗高度的比例
            SPACING_RATIO = 0.03  # 間距佔字寬的比例

            # 計算固定的字形高度和寬度
            self.cachedWidth = self.currentLayer.width
            self.cachedHeight = Glyphs.font.masters[0].ascender - Glyphs.font.masters[0].descender

            # 計算邊距
            MARGIN = min(rect.size.width, rect.size.height) * MARGIN_RATIO

            # 計算九宮格的可用空間
            availableWidth = rect.size.width - 2 * MARGIN
            availableHeight = rect.size.height - 2 * MARGIN

            # 計算單個字形的理想大小和間距
            idealCellWidth = self.cachedWidth
            idealCellHeight = self.cachedHeight
            idealSpacing = idealCellWidth * SPACING_RATIO
            idealGridWidth = idealCellWidth * 3 + idealSpacing * 2
            idealGridHeight = idealCellHeight * 3 + idealSpacing * 2

            # 計算縮放比例
            scale = min(availableWidth / idealGridWidth, availableHeight / idealGridHeight)

            # 計算實際的字形大小和間距
            cellWidth = idealCellWidth * scale
            cellHeight = idealCellHeight * scale
            SPACING = idealSpacing * scale

            # 計算九宮格的實際大小
            gridWidth = cellWidth * 3 + SPACING * 2
            gridHeight = cellHeight * 3 + SPACING * 2

            # 計算九宮格的起始位置（左上角），確保居中
            startX = (rect.size.width - gridWidth) / 2
            startY = (rect.size.height + gridHeight) / 2

            for i in range(9):
                row = i // 3
                col = i % 3
                
                # 計算每個格子的左上角位置
                x = startX + col * (cellWidth + SPACING)
                y = startY - (row + 1) * (cellHeight + SPACING)

                if i == 4:  # 中間格子
                    glyph = self.currentLayer.parent
                else:
                    glyph = Glyphs.font.glyphs[self.searchChar] if self.searchChar else None

                if glyph:
                    layer = glyph.layers[Glyphs.font.selectedFontMaster.id]
                    
                    # 計算縮放比例
                    glyphWidth = layer.width
                    glyphHeight = self.cachedHeight
                    scaleX = cellWidth / glyphWidth if glyphWidth > 0 else 1
                    scaleY = cellHeight / glyphHeight if glyphHeight > 0 else 1
                    glyphScale = min(scaleX, scaleY)

                    transform = NSAffineTransform.transform()
                    transform.translateXBy_yBy_(x, y)
                    transform.scaleBy_(glyphScale)

                    # 移動字形，使其在格子中居中
                    scaledWidth = glyphWidth * glyphScale
                    scaledHeight = glyphHeight * glyphScale
                    offsetX = (cellWidth - scaledWidth) / 2
                    offsetY = (cellHeight - scaledHeight) / 2
                    transform.translateXBy_yBy_(offsetX, offsetY)

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
        self.name = Glyphs.localize({'en': u'Nine Box View', 'zh-Hant': u'九宮格預覽'})

    @objc.python_method
    def start(self):
        try:
            newMenuItem = NSMenuItem(self.name, self.showWindow_)
            Glyphs.menu[WINDOW_MENU].append(newMenuItem)
            
            self.loadPreferences()
            
            Glyphs.addCallback(self.updateInterface, UPDATEINTERFACE)
        except:
            self.logToMacroWindow(traceback.format_exc())

    @objc.python_method
    def showWindow_(self, sender):
        try:
            self.w = Window((300, 340), self.name, minSize=(200, 240))
            self.w.preview = NineBoxPreview((0, 0, -0, -40), self)
            self.w.searchField = EditText((10, -30, -100, -10), 
                                          placeholder="輸入一個字符", 
                                          callback=self.searchFieldCallback)
            self.w.darkModeButton = Button((-90, -30, -10, -10), "深色模式",
                                           callback=self.darkModeCallback)
            self.w.open()
            
            # 設定視窗永遠浮動於上方
            self.w.getNSWindow().setLevel_(NSFloatingWindowLevel)
            
            self.updateInterface(None)
        except:
            self.logToMacroWindow(traceback.format_exc())

    @objc.python_method
    def loadPreferences(self):
        self.darkMode = Glyphs.defaults.get("com.YinTzuYuan.NineBoxView.darkMode", False)
        self.lastChar = Glyphs.defaults.get("com.YinTzuYuan.NineBoxView.lastChar", "")

    @objc.python_method
    def savePreferences(self):
        Glyphs.defaults["com.YinTzuYuan.NineBoxView.darkMode"] = self.darkMode
        Glyphs.defaults["com.YinTzuYuan.NineBoxView.lastChar"] = self.lastChar

    @objc.python_method
    def __del__(self):
        self.savePreferences()
        Glyphs.removeCallback(self.updateInterface, UPDATEINTERFACE)

    @objc.python_method
    def logToMacroWindow(self, message):
        Glyphs.clearLog()
        print(message)

    @objc.python_method
    def updateInterface(self, sender):
        if hasattr(self, 'w') and hasattr(self.w, 'preview'):
            self.w.preview.redraw()

    @objc.python_method
    def searchFieldCallback(self, sender):
        char = sender.get()
        if len(char) > 0:
            self.lastChar = char[0]
        self.updateInterface(None)

    @objc.python_method
    def darkModeCallback(self, sender):
        self.darkMode = not self.darkMode
        self.updateInterface(None)

    ## 以下程式碼務必保留置底
    #------------------------------
    @objc.python_method # 關閉外掛行為方法
    def __del__(self):
        Glyphs.removeCallback(self.changeInstance_, UPDATEINTERFACE)
        Glyphs.removeCallback(self.changeDocument_, DOCUMENTACTIVATED)

    def __file__(self):
        """Please leave this method unchanged"""
        return __file__

