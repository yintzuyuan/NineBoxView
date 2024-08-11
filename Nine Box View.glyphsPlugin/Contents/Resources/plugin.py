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

# 導入必要的模組
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

            # 檢查是否有選中的字體和圖層
            if not Glyphs.font or not Glyphs.font.selectedLayers:
                return

            # 獲取當前選中的圖層和字符
            self.currentLayer = Glyphs.font.selectedLayers[0]
            currentChar = self.currentLayer.parent.unicode

            # 處理搜索欄邏輯
            if self.wrapper.plugin.w.searchField.get().strip() == "":
                self.searchChar = currentChar
            else:
                self.searchChar = self.wrapper.plugin.lastChar or currentChar

            # 獲取中心字形和搜索字形
            centerGlyph = self.currentLayer.parent
            searchGlyph = Glyphs.font.glyphs[self.searchChar] if self.searchChar else centerGlyph

            # 獲取當前選中的主板
            currentMaster = Glyphs.font.selectedFontMaster

            # 設定可調整參數
            MARGIN_RATIO = 0.07  # 邊距佔視窗高度的比例
            SPACING_RATIO = 0.03  # 間距佔字寬的比例

            # 計算字形高度和邊距
            self.cachedHeight = currentMaster.ascender - currentMaster.descender
            MARGIN = min(rect.size.width, rect.size.height) * MARGIN_RATIO

            # 計算字寬和間距
            centerWidth = self.currentLayer.width
            searchWidth = searchGlyph.layers[currentMaster.id].width
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

            # 繪製九宮格中的每個字形
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

                # 選擇要繪製的圖層
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
        # 設定插件名稱（支援多語言）
        self.name = Glyphs.localize({
            'en': u'Nine Box View', 
            'zh-Hant': u'九宮格預覽'
        })
        self.loadPreferences()  # 在設定中載入偏好設定

    @objc.python_method
    def start(self):
        try:
            # 在 Glyphs 的視窗選單中添加新的選項
            newMenuItem = NSMenuItem(self.name, self.toggleWindow_)
            Glyphs.menu[WINDOW_MENU].append(newMenuItem)
            
            # 添加回調函數
            Glyphs.addCallback(self.updateInterface, UPDATEINTERFACE)
            Glyphs.addCallback(self.updateInterface, FONTMASTER_CHANGED)

            # 添加應用程式啟動和停用的觀察者
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
            
            # 確保在啟動時載入偏好設定
            self.loadPreferences()
        except:
            self.logToMacroWindow(traceback.format_exc())

    @objc.python_method
    def toggleWindow_(self, sender):
        try:
            # 切換視窗的顯示狀態
            if not hasattr(self, 'w') or self.w is None:
                # 創建新視窗
                self.w = FloatingWindow((300, 340), self.name, minSize=(200, 240),
                                        autosaveName="com.YinTzuYuan.NineBoxView.mainwindow")
                self.w.preview = NineBoxPreview((0, 0, -0, -40), self)
                self.w.searchField = EditText((10, -30, -100, -10), 
                                            placeholder="輸入一個字符", 
                                            callback=self.searchFieldCallback)
                # 設置搜索欄的初始值
                self.w.searchField.set(self.lastChar)
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
        # 視窗關閉時的處理
        self.w = None

    @objc.python_method
    def getDarkModeIcon(self):
        # 獲取深色模式圖標
        return "🌙" if self.darkMode else "☀️"

    @objc.python_method
    def loadPreferences(self):
        # 載入使用者偏好設定
        self.darkMode = Glyphs.defaults.get("com.YinTzuYuan.NineBoxView.darkMode", False)
        self.lastChar = Glyphs.defaults.get("com.YinTzuYuan.NineBoxView.lastChar", "")
        self.testMode = Glyphs.defaults.get("com.YinTzuYuan.NineBoxView.testMode", False)

    @objc.python_method
    def savePreferences(self):
        # 儲存使用者偏好設定
        Glyphs.defaults["com.YinTzuYuan.NineBoxView.darkMode"] = self.darkMode
        Glyphs.defaults["com.YinTzuYuan.NineBoxView.lastChar"] = self.lastChar
        Glyphs.defaults["com.YinTzuYuan.NineBoxView.testMode"] = self.testMode

    @objc.python_method
    def logToMacroWindow(self, message):
        # 將訊息記錄到巨集視窗
        Glyphs.clearLog()
        print(message)

    @objc.python_method
    def updateInterface(self, sender):
        # 更新介面
        if hasattr(self, 'w') and self.w is not None and hasattr(self.w, 'preview'):
            self.w.preview.redraw()

    @objc.python_method
    def searchFieldCallback(self, sender):
        # 搜索欄回調函數
        char = sender.get()
        if len(char) > 0:
            self.lastChar = char[0]
        else:
            self.lastChar = ""
        self.savePreferences()  # 保存設定
        self.updateInterface(None)

    @objc.python_method
    def darkModeCallback(self, sender):
        # 深色模式切換回調函數
        self.darkMode = not self.darkMode
        sender.setTitle(self.getDarkModeIcon())
        self.savePreferences()  # 保存設定
        self.updateInterface(None)

    @objc.python_method
    def showWindow(self):
        # 顯示視窗
        if hasattr(self, 'w') and self.w is not None:
            self.w.show()

    @objc.python_method
    def hideWindow(self):
        # 隱藏視窗
        if hasattr(self, 'w') and self.w is not None:
            self.w.hide()

    @objc.python_method
    def __del__(self):
        # 清理工作
        self.savePreferences()  # 確保在插件被刪除時保存設定
        Glyphs.removeCallback(self.updateInterface, UPDATEINTERFACE)
        Glyphs.removeCallback(self.updateInterface, FONTMASTER_CHANGED)
        NSWorkspace.sharedWorkspace().notificationCenter().removeObserver_(self)

    def __file__(self):
        return __file__