# encoding: utf-8
"""
九宮格預覽外掛 - 預覽畫面
Nine Box Preview Plugin - Preview View
"""

from __future__ import division, print_function, unicode_literals
import traceback
import objc
from GlyphsApp import Glyphs
from AppKit import (
    NSView, NSColor, NSBezierPath, NSAffineTransform, NSRectFill,
    NSFont, NSFontAttributeName, NSForegroundColorAttributeName,
    NSString, NSMakePoint
)

# 匯入常數定義，在類別內部使用
# Import constants definition, use it inside the class

class NineBoxPreviewView(NSView):
    """
    九宮格預覽畫面類別，負責實際的繪製工作。
    Nine Box Preview View Class, responsible for actual drawing work.
    """

    def initWithFrame_plugin_(self, frame, plugin):
        """
        初始化畫面
        Initialize the view
        
        Args:
            frame: 畫面尺寸和位置
            plugin: 外掛主類別實例
        
        Returns:
            self: 初始化後的畫面實例
        """
        self = objc.super(NineBoxPreviewView, self).initWithFrame_(frame)
        if self:
            self.plugin = plugin
            self.cachedHeight = 0
            
            # 從常數模組中導入繪圖相關的常數
            from constants import MARGIN_RATIO, SPACING_RATIO
            self.MARGIN_RATIO = MARGIN_RATIO
            self.SPACING_RATIO = SPACING_RATIO
        return self
    
    def mouseDown_(self, event):
        """
        處理滑鼠點擊事件
        Handle mouse click event
        
        當滑鼠在畫面中點擊時，觸發隨機排列功能。
        When mouse clicked in view, trigger randomize function.
        
        Args:
            event: 滑鼠事件
        """
        # 如果是雙擊，執行縮放重置
        if event.clickCount() == 2:
            self.plugin.zoomFactor = 1.0
            self.plugin.savePreferences()
            self.setNeedsDisplay_(True)
        else:
            # 單擊時進行隨機排列
            self.window().makeKeyWindow()
            self.window().makeFirstResponder_(self)
            self.plugin.randomizeCallback(self)

    def drawRect_(self, rect):
        """
        繪製畫面內容
        Draw the content of the view
        
        Args:
            rect: 要繪製的矩形區域
        """
        try:
            # === 設定背景顏色 / Set the background color ===
            if self.plugin.darkMode:
                NSColor.colorWithCalibratedRed_green_blue_alpha_(0.1, 0.1, 0.1, 1.0).set()
            else:
                NSColor.colorWithCalibratedRed_green_blue_alpha_(1.0, 1.0, 1.0, 1.0).set()
            NSRectFill(rect)

            # === 取得基本參數 / Get basic parameters ===
            # 取得目前字型和主板 / Get the current font and master
            if not Glyphs.font:
                return

            currentMaster = Glyphs.font.selectedFontMaster

            # 使用目前的排列 / Use the current arrangement
            display_chars = self.plugin.currentArrangement if self.plugin.selectedChars else []

            # === 設定基本尺寸 / Set basic sizes ===
            # 計算字符高度和邊距 / Calculate the character height and margin
            self.cachedHeight = currentMaster.ascender - currentMaster.descender
            MARGIN = min(rect.size.width, rect.size.height) * self.MARGIN_RATIO

            # === 計算網格尺寸 / Calculate the grid size ===
            # 使用 getBaseWidth 方法取得基準寬度
            baseWidth = self.plugin.getBaseWidth()

            # 計算最大寬度
            maxWidth = baseWidth
            if display_chars:
                for char in display_chars:
                    glyph = Glyphs.font.glyphs[char]
                    if glyph and glyph.layers[currentMaster.id]:
                        maxWidth = max(maxWidth, glyph.layers[currentMaster.id].width)

            SPACING = maxWidth * self.SPACING_RATIO

            # 計算單元格寬度 / Calculate the cell width
            cellWidth = maxWidth + SPACING

            # 計算網格總寬度和高度 / Calculate the total width and height of the grid
            gridWidth = 3 * cellWidth + 2 * SPACING
            gridHeight = 3 * self.cachedHeight + 2 * SPACING

            # === 計算縮放比例 / Calculate the scale ===
            availableWidth = rect.size.width - 2 * MARGIN
            availableHeight = rect.size.height - 2 * MARGIN
            scale = min(availableWidth / gridWidth, availableHeight / gridHeight, 1)

            # 應用自定義縮放 / Apply custom scale
            customScale = min(max(self.plugin.zoomFactor, 0.5), 2.0)  # 確保縮放值在有效範圍內
            scale *= customScale

            # 更新網格尺寸 / Update the grid size
            cellWidth *= scale
            gridWidth *= scale
            gridHeight *= scale
            SPACING *= scale

            # 計算繪製起始位置 / Calculate the starting position for drawing
            startX = rect.size.width / 2 - gridWidth / 2
            offsetY = rect.size.height * 0.05
            startY = (rect.size.height + gridHeight) / 2 + offsetY

            # === 繪製九宮格字符 / Draw the characters in the nine-box grid ===
            for i in range(9):
                row = i // 3
                col = i % 3

                # 計算目前單元格的中心位置 / Calculate the center position of the current cell
                centerX = startX + (col + 0.5) * cellWidth + col * SPACING
                centerY = startY - (row + 0.5) * (gridHeight / 3)

                # 選擇要繪製的字符層 / Select the character layer to draw
                layer = None
                if i == 4 and Glyphs.font.selectedLayers:  # 中心位置 / Center position
                    layer = Glyphs.font.selectedLayers[0]
                else:
                    # 當沒有其他字符時，使用目前編輯的字符填充 / When there are no other characters, fill with the currently edited character
                    if not display_chars:
                        if Glyphs.font.selectedLayers:
                            layer = Glyphs.font.selectedLayers[0]
                    else:
                        char_index = i if i < 4 else i - 1
                        if char_index < len(display_chars):
                            glyph = Glyphs.font.glyphs[display_chars[char_index]]
                            layer = glyph.layers[currentMaster.id] if glyph else None

                if layer:
                    # 計算字符縮放比例 / Calculate the character scale
                    glyphWidth = layer.width
                    glyphHeight = self.cachedHeight
                    scaleX = cellWidth / glyphWidth if glyphWidth > 0 else 1
                    scaleY = (gridHeight / 3 - SPACING) / glyphHeight if glyphHeight > 0 else 1
                    glyphScale = min(scaleX, scaleY)

                    # 計算縮放後的字符尺寸和位置 / Calculate the scaled character size and position
                    scaledWidth = glyphWidth * glyphScale
                    scaledHeight = glyphHeight * glyphScale
                    x = centerX - scaledWidth / 2
                    y = centerY - scaledHeight / 2

                    # 建立變換矩陣 / Create a transformation matrix
                    transform = NSAffineTransform.transform()
                    transform.translateXBy_yBy_(x, y)
                    transform.scaleBy_(glyphScale)

                    # === 繪製開放和封閉路徑 / Draw open and closed paths ===
                    # 取得完整路徑的副本 / Get a copy of complete path
                    bezierPath = layer.completeBezierPath.copy()
                    bezierPath.transformUsingAffineTransform_(transform)

                    # 取得開放路徑的副本 / Get a copy of open path
                    openBezierPath = layer.completeOpenBezierPath.copy()
                    openBezierPath.transformUsingAffineTransform_(transform)

                    # 設定繪製顏色 / Set drawing color
                    if self.plugin.darkMode:
                        fillColor = NSColor.whiteColor()
                        strokeColor = NSColor.whiteColor()
                    else:
                        fillColor = NSColor.blackColor()
                        strokeColor = NSColor.blackColor()

                    # 繪製封閉路徑（使用填充）/ Draw closed paths (using fill)
                    fillColor.set()
                    bezierPath.fill()

                    # 繪製開放路徑（使用描邊）/ Draw open paths (using stroke)
                    strokeColor.set()
                    openBezierPath.setLineWidth_(1.0)  # 設定線寬 / Set line width
                    openBezierPath.stroke()

                    # 繪製格子編號 / Draw grid number
                    if self.plugin.showNumbers:
                        # 直接在這裡繪製數字 / Draw number directly here
                        numberText = NSString.stringWithString_(str(i))
                        numberAttributes = {
                            NSFontAttributeName: NSFont.boldSystemFontOfSize_(9.0),
                            NSForegroundColorAttributeName: fillColor.colorWithAlphaComponent_(0.5)
                        }
                        numberSize = numberText.sizeWithAttributes_(numberAttributes)
                        numberPosition = NSMakePoint(
                            centerX - numberSize.width/2, 
                            centerY - scaledHeight/2 - 15 - numberSize.height/2
                        )
                        numberText.drawAtPoint_withAttributes_(numberPosition, numberAttributes)

        except Exception as e:
            print(traceback.format_exc()) 