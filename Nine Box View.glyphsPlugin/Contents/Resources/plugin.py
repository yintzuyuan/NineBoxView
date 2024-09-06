# encoding: utf-8

import objc
from GlyphsApp import *
from GlyphsApp.plugins import *
from AppKit import NSColor, NSFont, NSAffineTransform, NSRectFill, NSView, NSBezierPath
from vanilla import Window, Group, Button, EditText
import traceback

class NineBoxPreviewView(NSView):
    
    def drawRect_(self, rect):
        try:
            NSColor.whiteColor().set()
            NSRectFill(rect)

            if not Glyphs.font or not Glyphs.font.selectedLayers:
                return

            currentLayer = Glyphs.font.selectedLayers[0]
            currentChar = currentLayer.parent.unicode
            searchChar = self.wrapper.plugin.lastChar or currentChar

            cellSize = min(rect.size.width, rect.size.height) / 3
            spacing = cellSize / 10

            for i in range(9):
                x = (i % 3) * (cellSize + spacing)
                y = (2 - i // 3) * (cellSize + spacing)

                if i == 4:  # 中間格子
                    glyph = currentLayer.parent
                else:
                    glyph = Glyphs.font.glyphs[searchChar] if searchChar else None

                if glyph:
                    layer = glyph.layers[Glyphs.font.selectedFontMaster.id]
                    
                    transform = NSAffineTransform.transform()
                    transform.translateXBy_yBy_(x + cellSize/2, y + cellSize/2)
                    scale = cellSize / (Glyphs.font.upm * 1.2)
                    transform.scaleBy_(scale)

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
            self.updateInterface(None)
        except:
            self.logToMacroWindow(traceback.format_exc())

    @objc.python_method
    def loadPreferences(self):
        self.darkMode = Glyphs.defaults.get("com.yourname.NineBoxView.darkMode", False)
        self.lastChar = Glyphs.defaults.get("com.yourname.NineBoxView.lastChar", "")

    @objc.python_method
    def savePreferences(self):
        Glyphs.defaults["com.yourname.NineBoxView.darkMode"] = self.darkMode
        Glyphs.defaults["com.yourname.NineBoxView.lastChar"] = self.lastChar

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

    @objc.python_method
    def __file__(self):
        """Please leave this method unchanged"""
        return __file__