# encoding: utf-8
"""
九宮格預覽外掛 - 預覽畫面
Nine Box Preview Plugin - Preview View
基於字身寬度的穩定佈局設計，採用官方 Glyphs UI 重繪模式
"""

from __future__ import division, print_function, unicode_literals
import traceback
import objc
import random
import time
from GlyphsApp import Glyphs
from AppKit import (
    NSView, NSColor, NSBezierPath, NSAffineTransform, NSRectFill,
    NSFont, NSFontAttributeName, NSForegroundColorAttributeName,
    NSString, NSMakePoint, NSGradient, NSMakeRect, 
    NSFontManager, NSFontWeightThin, NSFontWeightBold,
    NSGraphicsContext, NSCompositingOperationSourceOver, NSInsetRect,
    NSUserDefaults, NSNotificationCenter, NSUserDefaultsDidChangeNotification,
    NSMenu, NSMenuItem, NSPasteboard
)

# 匯入常數和工具函數
from core.constants import (
    MARGIN_RATIO, SPACING_RATIO, MIN_ZOOM, MAX_ZOOM, DEBUG_MODE,
    GRID_SIZE, GRID_TOTAL, CENTER_POSITION
)
from core.utils import debug_log, error_log, get_cached_glyph, get_cached_width

class NineBoxPreviewView(NSView):
    """
    九宮格預覽畫面類別
    Nine Box Preview View Class

    設計原則：
    - 佈局計算完全基於 layer.width（字身寬度）
    - 不使用 LSB、RSB 或路徑邊界等動態資訊
    - 提供穩定的預覽框架，不受路徑編輯影響
    - 採用官方 Glyphs UI 重繪模式，使用屬性設定器自動觸發重繪
    """

    def initWithFrame_plugin_(self, frame, plugin):
        """
        初始化畫面
        Initialize the view
        """
        self = objc.super(NineBoxPreviewView, self).initWithFrame_(frame)
        if self:
            self.plugin = plugin
            self.cachedHeight = 0
            self.panOffset = (0, 0)
            
            # 效能最佳化：快取常用值
            self._cached_theme_is_black = None
            self._cached_master = None
            self._cached_grid_metrics = None
            
            # 初始化屬性設定器的內部值
            self._currentArrangement = []
            self._zoomFactor = 1.0
            
            # 狀態追蹤：用於檢測真正的字符變更
            self._last_active_char = None
            
            # 監聽主題變更
            NSNotificationCenter.defaultCenter().addObserver_selector_name_object_(
                self,
                "glyphsPreviewThemeChanged:",
                NSUserDefaultsDidChangeNotification,
                None
            )
            
        return self
    
    def glyphsPreviewThemeChanged_(self, notification):
        """處理主題變更（官方模式）"""
        try:
            # 清除主題快取
            self._cached_theme_is_black = None
            self.setNeedsDisplay_(True)
            debug_log("主題變更，已觸發重繪")
        except Exception as e:
            error_log("處理主題變更時發生錯誤", e)
    
    def _get_grid_index_at_point(self, point):
        """根據點擊位置計算對應的字符格索引
        
        Args:
            point: 點擊位置 (NSPoint)
            
        Returns:
            字符格索引 (0-8) 或 None（如果不在有效範圍內）
        """
        try:
            rect = self.bounds()
            if not Glyphs.font or not Glyphs.font.selectedFontMaster:
                return None
            
            currentMaster = Glyphs.font.selectedFontMaster
            
            # 使用現有的網格度量計算方法
            arrangement = self.currentArrangement or []
            if len(arrangement) < 9:
                return None
            
            display_chars = arrangement[:8]
            metrics = self._calculate_grid_metrics(rect, display_chars, currentMaster)
            if not metrics:
                return None
            
            # 計算每個格子的邊界
            for i in range(9):
                row = i // 3
                col = i % 3
                
                # 計算格子的中心位置
                centerX = metrics['startX'] + (col + 0.5) * metrics['cellWidth'] + col * metrics['SPACING']
                centerY = metrics['startY'] - (row + 0.5) * (metrics['gridHeight'] / 3)
                
                # 計算格子的邊界
                halfWidth = metrics['cellWidth'] / 2
                halfHeight = (metrics['gridHeight'] / 3) / 2
                
                left = centerX - halfWidth
                right = centerX + halfWidth
                bottom = centerY - halfHeight
                top = centerY + halfHeight
                
                # 檢查點擊位置是否在此格子內
                if left <= point.x <= right and bottom <= point.y <= top:
                    debug_log(f"點擊位置 ({point.x:.1f}, {point.y:.1f}) 對應格子 {i}")
                    return i
            
            debug_log(f"點擊位置 ({point.x:.1f}, {point.y:.1f}) 不在任何格子內")
            return None
            
        except Exception as e:
            error_log("計算網格索引時發生錯誤", e)
            return None
    
    def _get_character_info_at_index(self, grid_index):
        """取得指定索引位置的字符資訊
        
        Args:
            grid_index: 字符格索引 (0-8)
            
        Returns:
            字符資訊字典或 None
        """
        try:
            if not Glyphs.font:
                return None
            
            arrangement = self.currentArrangement or []
            if grid_index >= len(arrangement):
                return None
            
            char_or_name = arrangement[grid_index]
            if char_or_name is None:
                return None  # 空白格子
            
            # 取得字符物件
            glyph = get_cached_glyph(Glyphs.font, char_or_name)
            if not glyph:
                return {
                    'char_or_name': char_or_name,
                    'glyph_name': char_or_name,
                    'unicode': None,
                    'is_valid': False,
                    'grid_index': grid_index
                }
            
            return {
                'char_or_name': char_or_name,
                'glyph_name': glyph.name,
                'unicode': glyph.unicode,
                'is_valid': True,
                'glyph': glyph,
                'grid_index': grid_index
            }
            
        except Exception as e:
            error_log("取得字符資訊時發生錯誤", e)
            return None
    
    def _show_context_menu_for_character(self, char_info, point):
        """為指定字符顯示右鍵選單
        
        Args:
            char_info: 字符資訊字典
            point: 選單顯示位置
        """
        try:
            # 創建選單
            menu = NSMenu.alloc().init()
            
            # 格式化字符資訊標題
            # 檢查是否為中心格
            position_info = "中心格" if char_info.get('grid_index') == CENTER_POSITION else "周圍格"
            
            if char_info['is_valid'] and char_info['unicode']:
                # 有效字符且有 Unicode
                info_title = f"{char_info['glyph_name']} (U+{char_info['unicode']})"
            elif char_info['is_valid']:
                # 有效字符但無 Unicode
                info_title = f"{char_info['glyph_name']}"
            else:
                # 無效字符
                info_title = f"{char_info['char_or_name']}"
            
            # 新增資訊顯示項目（不可點擊）
            info_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
                info_title, None, ""
            )
            info_item.setEnabled_(False)  # 設為不可點擊
            menu.addItem_(info_item)
            
            # 新增分隔線
            menu.addItem_(NSMenuItem.separatorItem())
            
            # 只有有效字符才顯示操作選項
            if char_info['is_valid']:
                # 新增「複製字符名稱」選項
                copy_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
                    Glyphs.localize({
                        'en': 'Copy Glyph Name',
                        'zh-Hant': '複製字符名稱',
                        'zh-Hans': '复制字符名称',
                        'ja': 'グリフ名をコピー',
                        'ko': '글리프 이름 복사'
                    }),
                    "copyGlyphName:", ""
                )
                copy_item.setTarget_(self)
                copy_item.setRepresentedObject_(char_info['glyph_name'])
                menu.addItem_(copy_item)
                
                # 新增「插入字符到目前分頁」選項
                insert_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
                    Glyphs.localize({
                        'en': 'Insert Character to Current Tab',
                        'zh-Hant': '插入字符到目前分頁',
                        'zh-Hans': '插入字符到当前标签页',
                        'ja': '現在のタブに文字を挿入',
                        'ko': '현재 탭에 글리프 삽입'
                    }),
                    "insertCharacterToCurrentTab:", ""
                )
                insert_item.setTarget_(self)
                insert_item.setRepresentedObject_(char_info)
                menu.addItem_(insert_item)
                
                # 新增「在新分頁開啟字符」選項
                new_tab_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
                    Glyphs.localize({
                        'en': 'Open Glyph in New Tab',
                        'zh-Hant': '在新分頁開啟字符',
                        'zh-Hans': '在新标签页打开字符',
                        'ja': '新しいタブでグリフを開く',
                        'ko': '새 탭에서 글리프 열기'
                    }),
                    "openGlyphInNewTab:", ""
                )
                new_tab_item.setTarget_(self)
                new_tab_item.setRepresentedObject_(char_info['glyph'])
                menu.addItem_(new_tab_item)
            else:
                # 無效字符的提示
                invalid_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
                    Glyphs.localize({
                        'en': 'This character does not exist in the font',
                        'zh-Hant': '此字符在字型中不存在',
                        'zh-Hans': '此字符在字体中不存在',
                        'ja': 'この文字はフォントに存在しません',
                        'ko': '이 글리프는 글꼴에 존재하지 않습니다'
                    }),
                    None, ""
                )
                invalid_item.setEnabled_(False)
                menu.addItem_(invalid_item)
            
            # 顯示選單
            menu.popUpMenuPositioningItem_atLocation_inView_(
                None, point, self
            )
            
            debug_log(f"顯示字符右鍵選單：{char_info['glyph_name'] if char_info['is_valid'] else char_info['char_or_name']}")
            
        except Exception as e:
            error_log("顯示右鍵選單時發生錯誤", e)
    
    def copyGlyphName_(self, sender):
        """複製字符名稱到剪貼簿"""
        try:
            glyph_name = sender.representedObject()
            if glyph_name:
                # 取得系統剪貼簿
                pasteboard = NSPasteboard.generalPasteboard()
                pasteboard.clearContents()
                pasteboard.setString_forType_(glyph_name, "public.utf8-plain-text")
                
                debug_log(f"已複製字符名稱到剪貼簿：{glyph_name}")
                
                # 顯示通知（可選）
                if hasattr(Glyphs, 'showNotification'):
                    Glyphs.showNotification(
                        "九宮格預覽",
                        f"已複製字符名稱：{glyph_name}"
                    )
            
        except Exception as e:
            error_log("複製字符名稱時發生錯誤", e)
    
    def openGlyphInNewTab_(self, sender):
        """在新分頁開啟字符"""
        try:
            glyph = sender.representedObject()
            if glyph and Glyphs.font:
                # 使用 Glyphs API 開啟新分頁
                new_tab = Glyphs.font.newTab(f"/{glyph.name}")
                if new_tab:
                    debug_log(f"已在新分頁開啟字符：{glyph.name}")
                    
                    # 顯示通知（可選）
                    if hasattr(Glyphs, 'showNotification'):
                        Glyphs.showNotification(
                            "九宮格預覽",
                            f"已在新分頁開啟字符：{glyph.name}"
                        )
                else:
                    error_log("無法開啟新分頁", None)
            
        except Exception as e:
            error_log("開啟新分頁時發生錯誤", e)
    
    def insertCharacterToCurrentTab_(self, sender):
        """插入字符到目前編輯分頁的遊標位置（統一使用官方 layers 方法）"""
        try:
            char_info = sender.representedObject()
            if not char_info or not char_info.get('is_valid'):
                debug_log("無效的字符資訊，不能插入")
                return
            
            # 獲取目前字型和編輯分頁
            if not Glyphs.font:
                debug_log("無開啟的字型檔案")
                return
            
            current_tab = Glyphs.font.currentTab
            if not current_tab:
                debug_log("無目前編輯分頁")
                return
            
            # 獲取要插入的字符
            glyph = char_info.get('glyph')
            char_or_name = char_info.get('char_or_name')
            
            if not glyph or not char_or_name:
                debug_log("無法獲取字符資訊")
                return
            
            # 驗證字符是否真的存在於當前字型和主板中
            current_master = Glyphs.font.selectedFontMaster
            if not current_master:
                debug_log("無選擇的主板")
                return
            
            # 確認字符在當前主板中存在且有效
            layer_to_insert = glyph.layers[current_master.id]
            if not layer_to_insert:
                debug_log(f"字符 '{char_or_name}' 在主板 '{current_master.name}' 中不存在")
                if hasattr(Glyphs, 'showNotification'):
                    Glyphs.showNotification(
                        "九宮格預覽",
                        Glyphs.localize({
                            'en': f'Character "{char_or_name}" does not exist in current master',
                            'zh-Hant': f'字符 "{char_or_name}" 在目前主板中不存在',
                            'zh-Hans': f'字符 "{char_or_name}" 在当前主板中不存在',
                            'ja': f'文字 "{char_or_name}" は現在のマスターに存在しません',
                            'ko': f'글리프 "{char_or_name}" 은(는) 현재 마스터에 존재하지 않습니다'
                        })
                    )
                return
            
            # === 統一使用官方 layers 方法（避免特殊字符名稱解析問題）===
            debug_log(f"使用官方 layers 方法插入字符: '{glyph.name}' (原始輸入: '{char_or_name}')")
            
            # 備份目前狀態
            original_layers = list(current_tab.layers) if current_tab.layers else []
            original_cursor = current_tab.textCursor
            
            # 執行插入（使用 layers 方法）
            insertion_success = self._insert_layer_safely(
                current_tab, layer_to_insert, original_cursor, original_layers
            )
            
            # 檢查插入結果
            if insertion_success:
                debug_log(f"成功插入字符 '{glyph.name}' 使用 layers 方法")
                
                # 顯示成功通知
                if hasattr(Glyphs, 'showNotification'):
                    Glyphs.showNotification(
                        "九宮格預覽",
                        Glyphs.localize({
                            'en': f'Inserted "{glyph.name}" to current tab',
                            'zh-Hant': f'已插入 "{glyph.name}" 到目前分頁',
                            'zh-Hans': f'已插入 "{glyph.name}" 到当前标签页',
                            'ja': f'現在のタブに "{glyph.name}" を挿入しました',
                            'ko': f'현재 탭에 "{glyph.name}" 삽입되었습니다'
                        })
                    )
            else:
                debug_log(f"layers 方法插入失敗，字符: '{glyph.name}'")
                
                # 顯示失敗通知
                if hasattr(Glyphs, 'showNotification'):
                    Glyphs.showNotification(
                        "九宮格預覽",
                        Glyphs.localize({
                            'en': f'Cannot insert "{glyph.name}" - insertion failed',
                            'zh-Hant': f'無法插入 "{glyph.name}" - 插入失敗',
                            'zh-Hans': f'无法插入 "{glyph.name}" - 插入失败',
                            'ja': f'"{glyph.name}" を挿入できません - 挿入失敗',
                            'ko': f'"{glyph.name}" 삽입할 수 없음 - 삽입 실패'
                        })
                    )
            
        except Exception as e:
            error_log("插入字符到編輯分頁時發生錯誤", e)
            
            # 顯示錯誤通知
            if hasattr(Glyphs, 'showNotification'):
                Glyphs.showNotification(
                    "九宮格預覽",
                    Glyphs.localize({
                        'en': 'Failed to insert character due to system error',
                        'zh-Hant': '因系統錯誤插入字符失敗',
                        'zh-Hans': '因系统错误插入字符失败',
                        'ja': 'システムエラーにより文字の挿入に失敗しました',
                        'ko': '시스템 오류로 인한 글리프 삽입 실패'
                    })
                )
    
    def _insert_text_safely(self, current_tab, text_to_insert, original_cursor, original_text):
        """
        安全地使用文字插入方法
        
        Args:
            current_tab: 當前編輯分頁
            text_to_insert: 要插入的文字
            original_cursor: 原始游標位置
            original_text: 原始文字內容
            
        Returns:
            bool: 插入是否成功
        """
        try:
            # 安全檢查：確保游標位置合理
            cursor_pos = original_cursor
            if cursor_pos < 0:
                cursor_pos = 0
            elif cursor_pos > len(original_text):
                cursor_pos = len(original_text)
            
            # 在游標位置插入字符
            new_text = original_text[:cursor_pos] + text_to_insert + original_text[cursor_pos:]
            debug_log(f"文字插入 - 原長度: {len(original_text)}, 新長度: {len(new_text)}, 插入: '{text_to_insert}'")
            
            # 執行插入
            current_tab.text = new_text
            
            # 驗證插入是否成功（檢查內容是否被意外清空）
            updated_text = current_tab.text or ""
            if len(updated_text) == 0 and len(new_text) > 0:
                # 內容被清空，恢復原始內容
                debug_log("偵測到內容被清空，恢復原始內容")
                current_tab.text = original_text
                current_tab.textCursor = original_cursor
                return False
            
            # 更新游標位置到插入文字之後
            new_cursor_pos = cursor_pos + len(text_to_insert)
            current_tab.textCursor = new_cursor_pos
            
            debug_log(f"文字插入成功 - 新游標位置: {new_cursor_pos}")
            return True
            
        except Exception as e:
            debug_log(f"文字插入失敗: {e}")
            # 嘗試恢復原始狀態
            try:
                current_tab.text = original_text
                current_tab.textCursor = original_cursor
            except:
                pass
            return False
    
    def _insert_layer_safely(self, current_tab, layer_to_insert, original_cursor, original_layers):
        """
        安全地使用圖層插入方法（適用於特殊字符名稱，避免文字解析問題）
        
        Args:
            current_tab: 當前編輯分頁
            layer_to_insert: 要插入的圖層
            original_cursor: 原始游標位置
            original_layers: 原始圖層列表
            
        Returns:
            bool: 插入是否成功
        """
        try:
            if not layer_to_insert:
                debug_log("無效的圖層，無法插入")
                return False
            
            # 獲取當前圖層列表（確保複製以避免引用問題）
            current_layers = list(current_tab.layers) if current_tab.layers else []
            
            # 確保游標位置合理
            insert_pos = original_cursor
            if insert_pos < 0:
                insert_pos = 0
            elif insert_pos > len(current_layers):
                insert_pos = len(current_layers)
            
            debug_log(f"圖層插入準備 - 原數量: {len(current_layers)}, 插入位置: {insert_pos}, 字符: '{layer_to_insert.parent.name}'")
            
            # 創建新的圖層列表
            new_layers = current_layers[:insert_pos] + [layer_to_insert] + current_layers[insert_pos:]
            
            # 驗證新圖層列表的合理性
            if len(new_layers) != len(current_layers) + 1:
                debug_log("新圖層列表長度不符合預期")
                return False
            
            # 執行插入（使用 layers 屬性，避免文字解析問題）
            current_tab.layers = new_layers
            
            # 立即驗證插入是否成功（檢查內容是否被意外清空）
            updated_layers = current_tab.layers if current_tab.layers else []
            
            # 檢查是否成功插入且沒有被清空
            if len(updated_layers) == 0 and len(new_layers) > 0:
                debug_log("偵測到圖層列表被清空，恢復原始狀態")
                try:
                    current_tab.layers = original_layers
                    current_tab.textCursor = original_cursor
                except:
                    pass
                return False
            
            if len(updated_layers) != len(new_layers):
                debug_log(f"圖層插入數量驗證失敗 - 期望: {len(new_layers)}, 實際: {len(updated_layers)}")
                try:
                    current_tab.layers = original_layers
                    current_tab.textCursor = original_cursor
                except:
                    pass
                return False
            
            # 更新文字游標位置到插入字符之後
            new_cursor_pos = insert_pos + 1
            current_tab.textCursor = new_cursor_pos
            
            debug_log(f"圖層插入成功 - 字符: '{layer_to_insert.parent.name}', 新游標位置: {new_cursor_pos}")
            return True
            
        except Exception as e:
            debug_log(f"圖層插入失敗: {e}")
            # 嘗試恢復原始狀態
            try:
                current_tab.layers = original_layers
                current_tab.textCursor = original_cursor
                debug_log("已恢復到原始狀態")
            except Exception as restore_error:
                debug_log(f"恢復原始狀態時也發生錯誤: {restore_error}")
            return False
    
    def mouseDown_(self, event):
        """處理滑鼠左鍵點擊事件，觸發隨機排列
        
        左鍵點擊任何格子（包括中心格）都會觸發隨機排列功能
        """
        # 取得點擊位置
        click_point = event.locationInWindow()
        view_point = self.convertPoint_fromView_(click_point, None)
        
        # 取得視窗標題列高度（約 22 點）
        titlebar_height = 22
        
        # 如果點擊位置在標題列區域內，不觸發隨機排列
        if view_point.y >= self.frame().size.height - titlebar_height:
            return
        
        # 動態防抖機制
        current_time = time.time()
        
        # 初始化或取得上次點擊時間
        if not hasattr(self, '_last_click_time'):
            self._last_click_time = 0
            self._is_first_click_after_focus = True
        
        # 計算時間差
        time_diff = current_time - self._last_click_time
        
        # 根據是否為聚焦後第一次點擊決定防抖時間
        debounce_time = 0.3 if self._is_first_click_after_focus else 0.1  # 300ms vs 100ms
        
        if time_diff < debounce_time:
            return
        
        # 更新點擊時間和狀態
        self._last_click_time = current_time
        self._is_first_click_after_focus = False
        
        
        # 在非標題列區域點擊時，觸發隨機排列
        self.window().makeKeyWindow()
        self.window().makeFirstResponder_(self)
        self.plugin.randomizeCallback(self)
    
    def rightMouseDown_(self, event):
        """處理右鍵點擊事件，顯示字符資訊選單
        
        支援所有 9 個格子（包括中心格）的右鍵選單功能：
        - 顯示字符資訊（GlyphsName 和 Unicode）
        - 複製 GlyphsName 到剪貼簿
        - 在新分頁開啟字符
        
        注意：左鍵點擊仍然會觸發隨機排列（包括中心格）
        """
        try:
            # 取得點擊位置
            click_point = event.locationInWindow()
            view_point = self.convertPoint_fromView_(click_point, None)
            
            # 檢查視窗標題列高度
            titlebar_height = 22
            if view_point.y >= self.frame().size.height - titlebar_height:
                return  # 在標題列區域，不處理右鍵
            
            # 計算點擊位置對應的字符格索引
            grid_index = self._get_grid_index_at_point(view_point)
            
            # 檢查是否為有效的格子位置
            if grid_index is None:
                return
            
            # 取得該位置的字符資訊
            char_info = self._get_character_info_at_index(grid_index)
            if not char_info:
                return  # 空白格子不顯示選單
            
            # 創建並顯示右鍵選單
            self._show_context_menu_for_character(char_info, view_point)
            
        except Exception as e:
            error_log("處理右鍵點擊時發生錯誤", e)

    # === 官方模式：屬性設定器（參照 GlyphView 模式）===
    
    def _get_currentArrangement(self):
        """取得目前排列"""
        return getattr(self, '_currentArrangement', [])
    
    def _set_currentArrangement(self, arrangement):
        """設定目前排列（自動觸發重繪）"""
        if arrangement == getattr(self, '_currentArrangement', []):
            return  # 如果排列沒有改變，不觸發重繪
    
        self._currentArrangement = arrangement if arrangement else []
        self.setNeedsDisplay_(True)  # 官方模式：屬性變更時立即重繪
        debug_log(f"currentArrangement 已更新，觸發重繪: {arrangement}")
    
    currentArrangement = property(_get_currentArrangement, _set_currentArrangement)
    
    def _get_zoomFactor(self):
        """取得縮放係數"""
        return getattr(self, '_zoomFactor', 1.0)
    
    def _set_zoomFactor(self, factor):
        """設定縮放係數（自動觸發重繪）"""
        self._zoomFactor = factor if factor else 1.0
        self.setNeedsDisplay_(True)  # 縮放變更時立即重繪
        debug_log(f"zoomFactor 已更新，觸發重繪: {factor}")
    
    zoomFactor = property(_get_zoomFactor, _set_zoomFactor)
    
    def update(self):
        """標準更新方法（遵循官方 CanvasView 模式）"""
        self.setNeedsDisplay_(True)
        debug_log("呼叫 update() 方法，觸發重繪")
    
    def setFrame_(self, frame):
        """覆寫 setFrame_ 方法（官方模式）"""
        # 記錄舊框架
        oldFrame = self.frame()
        
        # 呼叫父類別方法
        objc.super(NineBoxPreviewView, self).setFrame_(frame)
        
        # 如果框架大小改變，觸發重繪
        if (oldFrame.size.width != frame.size.width or 
            oldFrame.size.height != frame.size.height):
            debug_log(f"預覽畫面框架變更：{oldFrame.size.width}x{oldFrame.size.height} -> {frame.size.width}x{frame.size.height}")
            
            # 清除網格度量快取
            self._cached_grid_metrics = None
            
            # 官方模式：直接觸發重繪
            self.setNeedsDisplay_(True)

    def _get_theme_is_black(self):
        """檢查目前主題是否為深色模式"""
        return NSUserDefaults.standardUserDefaults().boolForKey_("GSPreview_Black")
    
    def _calculate_grid_metrics(self, rect, display_chars, currentMaster):
        """計算網格度量（完全基於字身寬度的穩定佈局）"""
        try:
            # 檢查區域是否合法
            if rect.size.width <= 0 or rect.size.height <= 0:
                debug_log(f"警告：無效的繪製區域：{rect.size.width}x{rect.size.height}")
                return None
            
            # 計算字符高度和邊距
            self.cachedHeight = currentMaster.ascender - currentMaster.descender
            MARGIN = min(rect.size.width, rect.size.height) * MARGIN_RATIO
            
            # === 使用 getBaseWidth 方法取得基準寬度 ===
            try:
                baseWidth = self.plugin.getBaseWidth()
                if not isinstance(baseWidth, (int, float)) or baseWidth <= 0:
                    debug_log(f"警告：基準寬度值無效 ({baseWidth})，使用預設值 1000")
                    baseWidth = 1000
                else:
                    debug_log(f"基準寬度 baseWidth: {baseWidth}")
            except Exception as e:
                error_log("取得基準寬度時發生錯誤", e)
                baseWidth = 1000
            
            # === 計算最大字身寬度（僅使用 layer.width）===
            # 這是佈局計算的唯一依據，確保穩定性
            maxWidth = 0  # 初始設為 0，不預設為 baseWidth
            
            # 考慮周圍字符的寬度（過濾掉 None 值）
            if display_chars:
                for char in display_chars:
                    if char is not None:  # 只處理非 None 的字符
                        glyph = get_cached_glyph(Glyphs.font, char)
                        if glyph and glyph.layers[currentMaster.id]:
                            # 僅使用 layer.width（字身寬度）
                            layer_width = glyph.layers[currentMaster.id].width
                            maxWidth = max(maxWidth, layer_width)
                            debug_log(f"字符 '{char}' 的字身寬度: {layer_width}")
                    else:
                        debug_log("跳過 None 字符的寬度計算")
            
            # 考慮中央字符的寬度
            if Glyphs.font.selectedLayers:
                center_layer = Glyphs.font.selectedLayers[0]
                if center_layer:
                    center_width = center_layer.width
                    maxWidth = max(maxWidth, center_width)
                    debug_log(f"中央字符 '{center_layer.parent.name}' 的字身寬度: {center_width}")
            
            # 如果沒有有效字符或所有字符寬度為0，則使用 baseWidth
            if maxWidth == 0:
                maxWidth = baseWidth
                debug_log(f"無有效字符寬度（可能全為空白），使用基準寬度: {baseWidth}")
            
            debug_log(f"計算後的最大寬度 maxWidth: {maxWidth}")
            
            # 基於字身寬度計算間距
            SPACING = maxWidth * SPACING_RATIO
            
            # 計算單元格寬度（基於字身寬度）
            cellWidth = maxWidth + SPACING
            debug_log(f"單元格寬度 cellWidth: {cellWidth}")
            
            # 計算網格總寬度和高度
            gridWidth = 3 * cellWidth + 2 * SPACING
            gridHeight = 3 * self.cachedHeight + 2 * SPACING
            debug_log(f"網格總寬度 gridWidth: {gridWidth}, 網格總高度 gridHeight: {gridHeight}")
            
            # 計算縮放比例
            availableWidth = rect.size.width - 2 * MARGIN
            availableHeight = rect.size.height - 2 * MARGIN
            scale = min(availableWidth / gridWidth, availableHeight / gridHeight, 1)
            debug_log(f"可用寬度 availableWidth: {availableWidth}, 可用高度 availableHeight: {availableHeight}")
            debug_log(f"計算的縮放比例 scale: {scale}")
            
            # 套用自訂縮放（使用屬性設定器）
            customScale = self.zoomFactor
            scale *= customScale
            debug_log(f"套用自訂縮放後的比例 scale: {scale}")
            
            # 更新網格尺寸
            cellWidth *= scale
            gridWidth *= scale
            gridHeight *= scale
            SPACING *= scale
            debug_log(f"縮放後的單元格寬度 cellWidth: {cellWidth}")
            debug_log(f"縮放後的網格總寬度 gridWidth: {gridWidth}")
            
            # === 計算繪製起始位置（固定的佈局）===
            startX = rect.size.width / 2 - gridWidth / 2
            offsetY = rect.size.height * 0.02  # 向上偏移 2%
            startY = (rect.size.height + gridHeight) / 2 + offsetY
            
            # 回傳穩定的網格度量
            metrics = {
                'cellWidth': cellWidth,
                'gridWidth': gridWidth,
                'gridHeight': gridHeight,
                'SPACING': SPACING,
                'startX': startX,
                'startY': startY,
                'scale': scale
            }
            
            debug_log(f"網格度量（基於字身寬度）：{metrics}")
            return metrics
        
        except Exception as e:
            error_log("計算網格度量時發生錯誤", e)
            return None

    def _draw_character_at_position(self, layer, centerX, centerY, cellWidth, cellHeight, scale, is_black):
        """繪製單個字符（完全基於字身寬度的穩定佈局）"""
        if not layer:
            return
        
        try:
            # === 佈局計算：僅使用字身寬度（layer.width）===
            glyphWidth = layer.width  # 字身寬度（advance width）- 佈局的唯一依據
            glyphHeight = self.cachedHeight
            
            debug_log(f"繪製字符 '{layer.parent.name}' - 字身寬度: {glyphWidth}")
            
            # 計算字符縮放比例（基於字身寬度）
            scaleX = cellWidth / glyphWidth if glyphWidth > 0 else 1
            scaleY = cellHeight / glyphHeight if glyphHeight > 0 else 1
            glyphScale = min(scaleX, scaleY)
            
            # === 位置計算：完全基於字身寬度，確保穩定置中 ===
            scaledWidth = glyphWidth * glyphScale
            scaledHeight = glyphHeight * glyphScale
            
            # 計算繪製起始位置（穩定的置中，不受路徑變化影響）
            x = centerX - scaledWidth / 2
            y = centerY - scaledHeight / 2
            
            # 建立變換矩陣
            transform = NSAffineTransform.transform()
            transform.translateXBy_yBy_(x, y)
            transform.scaleBy_(glyphScale)
            
            # === 內容繪製：使用 completeBezierPath 顯示實際字形 ===
            # 注意：這裡只是繪製內容，不影響佈局
            completeBezierPath = layer.completeBezierPath
            if completeBezierPath:
                completeBezierPath = completeBezierPath.copy()
                completeBezierPath.transformUsingAffineTransform_(transform)
            
            completeOpenBezierPath = layer.completeOpenBezierPath
            if completeOpenBezierPath:
                completeOpenBezierPath = completeOpenBezierPath.copy()
                completeOpenBezierPath.transformUsingAffineTransform_(transform)
            
            # 設定繪製顏色（根據主題）
            if is_black:
                fillColor = NSColor.whiteColor()
                strokeColor = NSColor.whiteColor()
            else:
                fillColor = NSColor.blackColor()
                strokeColor = NSColor.blackColor()
            
            # 繪製路徑
            if completeBezierPath:
                fillColor.set()
                completeBezierPath.fill()
            
            if completeOpenBezierPath:
                strokeColor.set()
                completeOpenBezierPath.setLineWidth_(1.0)
                completeOpenBezierPath.stroke()
            
            debug_log(f"完成繪製 - 縮放: {glyphScale:.3f}, 位置: ({x:.1f}, {y:.1f})")
                
        except Exception as e:
            error_log("繪製字符時發生錯誤", e)

    def drawRect_(self, rect):
        """繪製畫面內容"""
        try:
            debug_log(f"預覽重繪：{rect.size.width}x{rect.size.height}")
            
            # === 確保在任何情況下都先繪製背景 ===
            # 設定背景顏色（根據 Glyphs 主題設定）
            is_black = self._get_theme_is_black()
            if is_black:
                NSColor.colorWithCalibratedRed_green_blue_alpha_(0, 0, 0, 1.0).set()
            else:
                NSColor.colorWithCalibratedRed_green_blue_alpha_(1.0, 1.0, 1.0, 1.0).set()
            NSRectFill(rect)
            
            # 檢查字型
            if not Glyphs.font:
                debug_log("沒有開啟字型，中止繪製")
                return
            
            currentMaster = Glyphs.font.selectedFontMaster
            if not currentMaster:
                debug_log("沒有選擇主板，中止繪製")
                return
                
            # 檢查切換字符 - 如果 plugin 存在且視窗顯示中，嘗試獲取最新數據
            try:
                if hasattr(self, 'plugin') and self.plugin:
                    if hasattr(self.plugin, 'event_handlers') and self.plugin.event_handlers:
                        # === 安全檢查：如果正在進行細粒度更新，跳過字符變更檢測 ===
                        if hasattr(self.plugin.event_handlers, '_performing_granular_update') and self.plugin.event_handlers._performing_granular_update:
                            debug_log("正在進行細粒度更新，跳過字符變更檢測")
                        else:
                            current_char = self.plugin.event_handlers._get_current_editing_char()
                            
                            # === 使用狀態追蹤機制檢測真正的字符變更 ===
                            previous_char = getattr(self, '_last_active_char', None)
                            
                            # 更新追蹤狀態
                            self._last_active_char = current_char
                            
                            # 修正：更精確的字符變更檢測，避免視窗操作時誤觸發
                            if (hasattr(self.plugin, 'currentArrangement') and 
                                len(self.plugin.currentArrangement) >= 9):
                                current_center = self.plugin.currentArrangement[4]
                                
                                # === 關鍵修正：只檢測真正的狀態變更 ===
                                should_update = (
                                    # 情況1：有意義的字符變更（字符 → 字符）
                                    (current_char is not None and 
                                     current_center is not None and 
                                     current_center != current_char and
                                     hasattr(self.plugin, 'selectedChars') and 
                                     self.plugin.selectedChars) or
                                    
                                    # 情況2：真正從有字符切換到無字符（狀態變更檢測）
                                    (previous_char is not None and 
                                     current_char is None and
                                     current_center is not None and
                                     hasattr(self.plugin, 'selectedChars') and 
                                     self.plugin.selectedChars)
                                )
                                
                                if should_update:
                                    debug_log(f"檢測到真正的字符變更: {previous_char} -> {current_char} (center: {current_center})")
                                    # 主動觸發重新生成排列
                                    if hasattr(self.plugin.event_handlers, 'selection_changed'):
                                        self.plugin.event_handlers.selection_changed(None)
                                else:
                                    debug_log(f"字符狀態檢測: prev='{previous_char}', current='{current_char}', center='{current_center}' - 不觸發更新")
            except Exception as e:
                debug_log(f"檢查字符變更時出錯: {e}")
                # 繼續繪製，不中斷流程
            
            # === 使用屬性設定器的值優先，然後是 plugin 的值 ===
            arrangement = self.currentArrangement
            
            # 如果 view 的排列為空，嘗試從 plugin 取得
            if not arrangement and hasattr(self.plugin, 'currentArrangement'):
                arrangement = self.plugin.currentArrangement
                # 同時更新 view 的屬性（但不觸發重繪，避免遞迴）
                self._currentArrangement = arrangement
            
            # 檢查排列是否有效（長度為9）
            if not arrangement or len(arrangement) != 9:
                debug_log("沒有有效的9格排列，生成後備排列")
                if hasattr(self.plugin, 'event_handlers'):
                    self.plugin.event_handlers.generate_new_arrangement()
                    if (hasattr(self.plugin, 'currentArrangement') and 
                        len(self.plugin.currentArrangement) == 9):
                        arrangement = self.plugin.currentArrangement
                        # 更新 view 的屬性
                        self._currentArrangement = arrangement
                
                # 如果仍然沒有有效排列，才使用後備邏輯
                if not arrangement or len(arrangement) != 9:
                    current_char = None
                    if Glyphs.font and Glyphs.font.selectedLayers:
                        current_layer = Glyphs.font.selectedLayers[0]
                        if current_layer and current_layer.parent:
                            current_glyph = current_layer.parent
                            if current_glyph.unicode:
                                try:
                                    current_char = chr(int(current_glyph.unicode, 16))
                                except:
                                    current_char = current_glyph.name
                            elif current_glyph.name:
                                current_char = current_glyph.name
                    
                    if not current_char:
                        current_char = "A"  # 最終後備
                    
                    arrangement = [current_char] * 9
                    debug_log(f"使用最終後備排列：{arrangement}")
                    # 更新 view 的屬性
                    self._currentArrangement = arrangement
            
            # 檢查是否為有效的空白排列（根據 flow.md 規則 R8, R10, R12）
            elif arrangement and len(arrangement) == 9:
                # 檢查是否所有元素都是 None（空白排列）
                all_none = all(item is None for item in arrangement)
                if all_none:
                    debug_log("檢測到有效的空白排列（所有元素為 None），這是符合 flow.md 的正確行為")
                else:
                    debug_log(f"檢測到有效的混合排列，包含 {sum(1 for item in arrangement if item is not None)} 個非空元素")
            
            debug_log(f"最終使用排列: {arrangement}")
            
            # 計算網格度量（使用前8個字符作為參考）
            display_chars = arrangement[:8] if len(arrangement) >= 8 else arrangement
            metrics = self._calculate_grid_metrics(rect, display_chars, currentMaster)
            if not metrics:
                debug_log("無法計算網格度量")
                return
            
            # === 繪製九宮格字符 ===
            for i in range(9):
                row = i // 3
                col = i % 3
                
                # 計算目前單元格的中心位置
                centerX = metrics['startX'] + (col + 0.5) * metrics['cellWidth'] + col * metrics['SPACING']
                centerY = metrics['startY'] - (row + 0.5) * (metrics['gridHeight'] / 3)
                
                # 從排列中取得字符
                char_or_name = arrangement[i] if i < len(arrangement) else None
                
                layer = None
                if char_or_name is not None:  # 不是空白
                    # 嘗試取得字符的圖層
                    glyph = get_cached_glyph(Glyphs.font, char_or_name)
                    if glyph and glyph.layers[currentMaster.id]:
                        layer = glyph.layers[currentMaster.id]
                        debug_log(f"位置 {i}: 繪製字符 '{char_or_name}'")
                    else:
                        debug_log(f"位置 {i}: 字符 '{char_or_name}' 在字型中不存在，跳過繪製")
                        # 字符不存在時，確保不繪製任何內容
                        layer = None
                else:
                    debug_log(f"位置 {i}: 空白格（None），完全不繪製")
                
                # 繪製字符（如果有有效的layer）
                if layer:
                    # 計算單元格高度
                    cellHeight = metrics['gridHeight'] / 3 - metrics['SPACING']
                    
                    # 繪製字符
                    self._draw_character_at_position(
                        layer, centerX, centerY, 
                        metrics['cellWidth'], cellHeight, 
                        metrics['scale'], is_black
                    )
                else:
                    # None 值或無效字符：完全不繪製任何內容，保持背景色
                    debug_log(f"位置 {i}: 保持空白（無任何繪製）")
                    
        except Exception as e:
            error_log("繪製預覽畫面時發生錯誤", e)
    
    def dealloc(self):
        """解構式"""
        try:
            NSNotificationCenter.defaultCenter().removeObserver_(self)
        except:
            pass
        objc.super(NineBoxPreviewView, self).dealloc()
