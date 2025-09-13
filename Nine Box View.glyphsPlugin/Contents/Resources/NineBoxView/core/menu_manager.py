# encoding: utf-8

"""
右鍵選單統一管理模組
移植自舊版本，移除左鍵功能，保留右鍵和控制面板選單功能
適配平面座標系統 (0-8) 和新的模組化架構
"""

from __future__ import division, print_function, unicode_literals
import traceback
from AppKit import NSMenu, NSMenuItem, NSPasteboard
from GlyphsApp import Glyphs

# 匯入新的模組（適配當前架構）
from ..data.cache import get_glyph_with_fallback
from .utils import FontManager

# 匯入本地化模組（僅用於選單文字）
from ..localization import localize


class MenuManager:
    """統一的選單管理器（右鍵和控制面板選單功能）"""
    
    # ==========================================================================
    # 統一字型上下文方法（官方模式）
    # ==========================================================================
    
    
    # ==========================================================================
    # 業務邏輯方法
    # ==========================================================================
    
    @staticmethod
    def insert_glyph_to_current_tab(glyph):
        """插入字符到目前編輯分頁的游標位置（支援多字符）"""
        try:
            # 🆕 多字符模式：SearchTextView 實例
            if hasattr(glyph, 'selectedRange'):
                # 從搜尋框上下文提取並尋找所有 glyph
                glyphs_to_insert = MenuManager._extract_and_find_glyphs_from_search_context(glyph)
                if not glyphs_to_insert:
                    return False
                
                # 內聯多字符插入邏輯（採用官方模式統一上下文）
                font, current_master = FontManager.getCurrentFontContext()
                if not font:
                    return False
                
                current_tab = font.currentTab
                if not current_tab:
                    return False
                if not current_master:
                    return False
                
                # 獲取游標位置並逐個插入（使用官方 textCursor API）
                cursor_position = current_tab.textCursor
                inserted_count = 0
                
                for glyph_obj in glyphs_to_insert:
                    try:
                        layer = glyph_obj.layers[current_master.id]
                        if not layer:
                            continue
                        
                        # 插入圖層
                        layers = list(current_tab.layers) if current_tab.layers else []
                        insert_pos = cursor_position + inserted_count
                        layers.insert(insert_pos, layer)
                        current_tab.layers = layers
                        inserted_count += 1
                        
                    except Exception:
                        print(traceback.format_exc())
                        continue
                
                # 返回結果
                if inserted_count > 0:
                    return True
                else:
                    return False
            
            # 🆕 九宮格模式：char_info 字典
            elif isinstance(glyph, dict) and glyph.get('is_valid'):
                char_info = glyph  # 重新命名以符合原邏輯
            else:
                return False
            
            # 獲取目前字型和編輯分頁（採用官方模式統一上下文）
            font, current_master = FontManager.getCurrentFontContext()
            if not font or not current_master:
                return False
            
            current_tab = font.currentTab
            if not current_tab:
                return False
            
            # 獲取要插入的字符
            glyph = char_info.get('glyph')
            char_or_name = char_info.get('char_or_name')
            
            if not glyph or not char_or_name:
                return False
            
            # 確認字符在當前主板中存在且有效
            layer_to_insert = glyph.layers[current_master.id]
            if not layer_to_insert:
                return False
            
            # 備份目前狀態
            original_layers = list(current_tab.layers) if current_tab.layers else []
            original_cursor = current_tab.textCursor
            
            # 安全插入邏輯
            if not layer_to_insert:
                return False
            
            # 獲取當前圖層列表
            current_layers = list(current_tab.layers) if current_tab.layers else []
            
            # 確保游標位置合理
            insert_pos = original_cursor
            if insert_pos < 0:
                insert_pos = 0
            elif insert_pos > len(current_layers):
                insert_pos = len(current_layers)
            
            # 建立新的圖層列表
            new_layers = current_layers[:insert_pos] + [layer_to_insert] + current_layers[insert_pos:]
            
            # 執行插入
            current_tab.layers = new_layers
            
            # 驗證插入是否成功
            updated_layers = current_tab.layers if current_tab.layers else []
            
            if len(updated_layers) == 0 and len(new_layers) > 0:
                try:
                    current_tab.layers = original_layers
                    current_tab.textCursor = original_cursor
                except:
                    pass
                return False
            
            if len(updated_layers) != len(new_layers):
                try:
                    current_tab.layers = original_layers
                    current_tab.textCursor = original_cursor
                except:
                    pass
                return False
            
            # 更新文字游標位置
            new_cursor_pos = insert_pos + 1
            current_tab.textCursor = new_cursor_pos
            
            return True
            
        except Exception:
            print(traceback.format_exc())
            # 嘗試恢復原始狀態
            try:
                if 'current_tab' in locals() and 'original_layers' in locals() and 'original_cursor' in locals():
                    current_tab.layers = original_layers
                    current_tab.textCursor = original_cursor
            except:
                pass
            
            return False
    
    @staticmethod
    def open_glyph_in_new_tab(glyph):
        """在新分頁開啟字符（支援多字符）"""
        try:
            # 🆕 多字符模式：SearchTextView 實例
            if hasattr(glyph, 'selectedRange'):
                # 從搜尋框上下文提取並尋找所有 glyph
                glyphs_to_open = MenuManager._extract_and_find_glyphs_from_search_context(glyph)
                if not glyphs_to_open:
                    return False
                
                # 內聯多字符開啟邏輯（採用官方模式統一上下文）
                font, current_master = FontManager.getCurrentFontContext()
                if not font:
                    return False
                
                if not current_master:
                    return False
                
                # 收集有效的圖層
                valid_layers = []
                for glyph_obj in glyphs_to_open:
                    try:
                        layer = glyph_obj.layers[current_master.id]
                        if layer:
                            valid_layers.append(layer)
                    except Exception:
                        print(traceback.format_exc())
                        continue
                
                if not valid_layers:
                    return False
                
                # 建立新分頁並新增圖層
                new_tab = font.newTab()
                if new_tab:
                    new_tab.layers = valid_layers
                    return True
                else:
                    return False
            
            # 採用官方模式統一上下文
            font, _ = FontManager.getCurrentFontContext()
            if glyph and font:
                # 使用 Glyphs API 開啟新分頁
                new_tab = font.newTab(f"/{glyph.name}")
                if new_tab:
                    return True
                else:
                    pass
        except Exception:
            print(traceback.format_exc())
        return False
    
    @staticmethod
    def copy_glyph_name(glyph_name):
        """複製字符名稱到剪貼簿"""
        try:
            if glyph_name:
                # 取得系統剪貼簿
                pasteboard = NSPasteboard.generalPasteboard()
                pasteboard.clearContents()
                pasteboard.setString_forType_(glyph_name, "public.utf8-plain-text")
                
                return True
        except Exception:
            print(traceback.format_exc())
        return False
    
    @staticmethod
    def _extract_and_find_glyphs_from_search_context(text_view):
        """從搜尋框上下文提取字符並尋找對應的 glyph 列表
        
        Args:
            text_view: SearchTextView 實例
            
        Returns:
            list: glyph 物件列表，如果無效則返回空列表
        """
        try:
            if not text_view or not hasattr(text_view, 'selectedRange'):
                return []
            
            font, _ = FontManager.getCurrentFontContext()
            if not font:
                return []
            
            # 1. 提取字符邏輯（來自原 _extract_chars_from_search_context）
            selected_range = text_view.selectedRange()
            text_content = text_view.string() or ""
            
            selected_chars = ""
            if selected_range.length > 0:
                # 有選中文字：返回完整選中文字
                selected_text = text_content[selected_range.location:selected_range.location + selected_range.length]
                selected_chars = selected_text if selected_text else ""
            else:
                # 無選中文字：獲取游標位置的字符
                cursor_pos = selected_range.location
                if cursor_pos > 0 and cursor_pos <= len(text_content):
                    # 獲取游標前的字符
                    selected_chars = text_content[cursor_pos - 1]
                elif cursor_pos < len(text_content):
                    # 獲取游標後的字符
                    selected_chars = text_content[cursor_pos]
            
            if not selected_chars:
                return []
            
            # 2. 尋找 glyph 邏輯（來自原多字符方法的字符尋找機制）
            glyphs = []
            for char in selected_chars:
                # 過濾空白字符（空格、換行、Tab等）
                if char.isspace():
                    continue
                    
                try:
                    # 方法1：通過 Unicode 尋找
                    glyph = None
                    try:
                        unicode_val = ord(char)
                        for font_glyph in font.glyphs:
                            if font_glyph.unicode and int(font_glyph.unicode, 16) == unicode_val:
                                glyph = font_glyph
                                break
                    except:
                        pass
                    
                    # 方法2：通過字符名稱尋找
                    if not glyph:
                        try:
                            glyph = font.glyphs[char]
                        except:
                            continue
                    
                    if glyph:
                        glyphs.append(glyph)
                        
                except Exception:
                    print(traceback.format_exc())
                    continue
            
            return glyphs
                
        except Exception:
            print(traceback.format_exc())
            return []
    
    
    # ==========================================================================
    # 滑鼠事件處理（統一管理）- 移除左鍵功能，只保留右鍵
    # ==========================================================================
    
    @staticmethod
    def handle_right_mouse_click(preview_view, event):
        """處理右鍵點擊事件，顯示字符資訊選單
        
        支援所有 9 個格子（包括中心格）的右鍵選單功能：
        - 顯示字符資訊（GlyphsName 和 Unicode）
        - 複製 GlyphsName 到剪貼簿
        - 在新分頁開啟字符
        
        Args:
            preview_view: NineBoxPreviewView 實例
            event: 滑鼠事件
        """
        try:
            # 取得點擊位置
            click_point = event.locationInWindow()
            view_point = preview_view.convertPoint_fromView_(click_point, None)
            
            # 檢查視窗標題列高度
            titlebar_height = 22
            if view_point.y >= preview_view.frame().size.height - titlebar_height:
                return  # 在標題列區域，不處理右鍵
            
            # 計算點擊位置對應的字符格索引
            grid_index = MenuManager.get_grid_index_at_point(preview_view, view_point)
            
            # 檢查是否為有效的格子位置
            if grid_index is None:
                return
            
            # 取得該位置的字符資訊
            char_info = MenuManager.get_glyph_info_at_index(preview_view, grid_index)
            if not char_info:
                return  # 空白格子不顯示選單
            
            # 建立並顯示右鍵選單
            MenuManager.create_grid_character_menu(char_info, preview_view, view_point)
            
        except Exception:
            print(traceback.format_exc())
    
    
    # ==========================================================================
    # 滑鼠事件輔助方法
    # ==========================================================================
    
    @staticmethod
    def get_grid_index_at_point(preview_view, point):
        """根據點擊位置計算對應的字符格索引
        
        Args:
            preview_view: NineBoxPreviewView 實例
            point: 點擊位置 (NSPoint)
            
        Returns:
            字符格索引 (0-8) 或 None（如果不在有效範圍內）
        """
        try:
            # 使用預覽視圖的佈局計算
            layout = preview_view._calculate_layout()
            if not layout:
                return None
            
            positions = layout['positions']
            
            # 檢查每個格子的邊界
            for i, position_info in enumerate(positions):
                # 從字典取得位置資訊
                centerX = position_info['centerX']
                centerY = position_info['centerY']
                cellWidth = position_info['cellWidth']
                cellHeight = position_info['cellHeight']
                
                # 格子的邊界（從中心點計算邊界）
                left = centerX - cellWidth / 2
                right = centerX + cellWidth / 2
                bottom = centerY - cellHeight / 2
                top = centerY + cellHeight / 2
                
                # 檢查點擊位置是否在此格子內
                if left <= point.x <= right and bottom <= point.y <= top:
                    return i
            
            return None
            
        except Exception:
            print(traceback.format_exc())
            return None
    
    @staticmethod
    def get_glyph_info_at_index(preview_view, grid_index):
        """取得指定索引位置的字符資訊
        
        Args:
            preview_view: NineBoxPreviewView 實例
            grid_index: 字符格索引 (0-8)
            
        Returns:
            字符資訊字典或 None
        """
        try:
            font, _ = FontManager.getCurrentFontContext()
            if not font:
                return None
            
            arrangement = preview_view._currentArrangement or []
            if grid_index >= len(arrangement):
                return None
            
            char_or_name = arrangement[grid_index]
            if char_or_name is None:
                return None  # 空白格子
            
            # 取得字符物件
            glyph = get_glyph_with_fallback(font, char_or_name)
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
            
        except Exception:
            print(traceback.format_exc())
            return None
    
    
    # ==========================================================================
    # 字符選擇器功能（官方 PickGlyphs API）
    # ==========================================================================
    
    @staticmethod
    def get_selected_glyphs():
        """顯示字符選擇器對話框並返回選中的字符列表
        
        使用官方 PickGlyphs API 實作字符選擇功能
        
        Returns:
            tuple: (success: bool, glyphs: list) - 成功狀態和選中的字符列表
        """
        try:
            # 檢查目前字型（採用官方模式統一上下文）
            font, _ = FontManager.getCurrentFontContext()
            if not font:
                return False, []
            
            # 使用官方 PickGlyphs API
            from GlyphsApp import PickGlyphs
            
            # PickGlyphs() 返回 tuple(list, str)：(選中的字符列表, 搜尋字串)
            result = PickGlyphs()
            
            if result and len(result) >= 2:
                selected_glyphs, _ = result  # 忽略 search_string
                
                if selected_glyphs:
                    # 返回成功和字符列表
                    return True, selected_glyphs
                else:
                    # 使用者取消選擇
                    return False, []
            else:
                # 對話框被取消或出現問題
                return False, []
                
        except ImportError:
            # PickGlyphs 不可用
            print(traceback.format_exc())
            return False, []
        except Exception:
            # 處理其他錯誤
            print(traceback.format_exc())
            return False, []
    
    
    # ==========================================================================
    # 選單組合器（純粹的功能組合邏輯）
    # ==========================================================================
    
    @staticmethod
    def create_text_field_menu(target_object, include_glyph_picker=True, include_tab_actions=False):
        """
        建立文字欄位右鍵選單（組合器）
        
        Args:
            target_object: 選單項目的目標物件
            include_glyph_picker: 是否包含字符選擇器
            include_tab_actions: 是否包含分頁相關操作
        """
        
        try:
            contextMenu = NSMenu.alloc().init()
            
            # 直接建立字符選擇器項目
            if include_glyph_picker:
                glyph_picker_title = localize('menu_glyph_picker')
                
                pickGlyphItem = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
                    glyph_picker_title,
                    "pickGlyphAction:",
                    ""
                )
                
                pickGlyphItem.setTarget_(target_object)
                
                contextMenu.addItem_(pickGlyphItem)
            
            # 直接組合分頁操作項目
            if include_tab_actions:
                if include_glyph_picker:
                    contextMenu.addItem_(NSMenuItem.separatorItem())
                
                # 直接建立「插入字符到目前分頁」項目
                insertToCurrentTabItem = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
                    localize('menu_insert_to_current_tab'),
                    "insertGlyphToCurrentTab:",
                    ""
                )
                insertToCurrentTabItem.setTarget_(target_object)
                contextMenu.addItem_(insertToCurrentTabItem)
                
                # 直接建立「在新分頁開啟字符」項目
                openInNewTabItem = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
                    localize('menu_open_in_new_tab'),
                    "openGlyphInNewTab:",
                    ""
                )
                openInNewTabItem.setTarget_(target_object)
                contextMenu.addItem_(openInNewTabItem)
            return contextMenu
            
        except Exception:
            print(traceback.format_exc())
            # 返回空白選單作為後備
            fallback_menu = NSMenu.alloc().init()
            return fallback_menu
    
    @staticmethod
    def create_field_editor_menu(base_menu, target_object):
        """
        建立 field editor 右鍵選單（組合器）
        
        Args:
            base_menu: 基礎選單（可能為 None）
            target_object: 選單項目的目標物件
        
        Returns:
            NSMenu: 包含字符選擇器的選單
        """
        try:
            contextMenu = base_menu if base_menu else NSMenu.alloc().init()
            
            # 檢查是否已經有字符選擇器
            has_glyph_picker = False
            for i in range(contextMenu.numberOfItems()):
                if contextMenu.itemAtIndex_(i).action() == "pickGlyphAction:":
                    has_glyph_picker = True
                    break
            
            if not has_glyph_picker:
                if contextMenu.numberOfItems() > 0:
                    contextMenu.addItem_(NSMenuItem.separatorItem())
                
                # 直接建立字符選擇器項目
                pickGlyphItem = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
                    localize('menu_glyph_picker'),
                    "pickGlyphAction:",
                    ""
                )
                pickGlyphItem.setTarget_(target_object)
                contextMenu.addItem_(pickGlyphItem)
            
            return contextMenu
            
        except Exception:
            print(traceback.format_exc())
            # 返回原始選單或建立基本選單
            return base_menu if base_menu else NSMenu.alloc().init()
    
    @staticmethod
    def create_grid_character_menu(char_info, target_object, point):
        """
        建立九宮格字符右鍵選單（組合器）

        Args:
            char_info: 字符資訊字典
            target_object: 選單項目的目標物件
            point: 選單顯示位置
        """
        try:
            # 建立選單
            menu = NSMenu.alloc().init()
            
            # 直接建立字符資訊顯示項目
            # 格式化字符資訊標題
            if char_info['is_valid'] and char_info['unicode']:
                # 有效字符且有 Unicode
                info_title = f"{char_info['glyph_name']} (U+{char_info['unicode']})"
            elif char_info['is_valid']:
                # 有效字符但無 Unicode
                info_title = f"{char_info['glyph_name']}"
            else:
                # 無效字符
                info_title = f"{char_info['char_or_name']}"
            
            info_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
                info_title, None, ""
            )
            info_item.setEnabled_(False)  # 設為不可點擊
            menu.addItem_(info_item)
            
            # 新增分隔線
            menu.addItem_(NSMenuItem.separatorItem())
            
            # 直接組合字符操作項目（無效字符處理）
            if not char_info['is_valid']:
                # 無效字符的提示
                invalid_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
                    localize('error_glyph_not_exist'),
                    None, ""
                )
                invalid_item.setEnabled_(False)
                menu.addItem_(invalid_item)
            else:
                # 直接建立「複製字符名稱」選項
                copy_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
                    localize('menu_copy_glyph_name'),
                    "copyGlyphName:", ""
                )
                copy_item.setTarget_(target_object)
                copy_item.setRepresentedObject_(char_info['glyph_name'])
                menu.addItem_(copy_item)
                
                # 直接建立「插入字符到目前分頁」選項
                insert_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
                    localize('menu_insert_to_current_tab'),
                    "insertGlyphToCurrentTab:", ""
                )
                insert_item.setTarget_(target_object)
                insert_item.setRepresentedObject_(char_info)
                menu.addItem_(insert_item)
                
                # 直接建立「在新分頁開啟字符」選項
                new_tab_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
                    localize('menu_open_in_new_tab'),
                    "openGlyphInNewTab:", ""
                )
                new_tab_item.setTarget_(target_object)
                new_tab_item.setRepresentedObject_(char_info['glyph'])
                menu.addItem_(new_tab_item)
            
            # 顯示選單
            menu.popUpMenuPositioningItem_atLocation_inView_(
                None, point, target_object
            )
            
            return menu
            
        except Exception:
            print(traceback.format_exc())
            return None


# 右鍵選單功能統一管理完成：移除左鍵邏輯，保留右鍵和控制面板選單功能