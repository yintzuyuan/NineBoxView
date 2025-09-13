# encoding: utf-8

"""
GlyphsService - 統一的 Glyphs API 服務介面
所有與 Glyphs.app 相關的 API 呼叫都應透過此服務進行
這是唯一允許直接匯入 GlyphsApp 的 core 層模組
"""

from __future__ import division, print_function, unicode_literals
import time
import traceback

# 唯一允許直接匯入 GlyphsApp 的模組
try:
    from GlyphsApp import Glyphs
    GLYPHS_AVAILABLE = True
except ImportError:
    Glyphs = None
    GLYPHS_AVAILABLE = False

from .utils import FontManager


class GlyphsService(object):
    """統一的 Glyphs API 服務類
    
    提供所有與 Glyphs.app 互動的統一介面
    UI 層不得直接呼叫 GlyphsApp 模組，必須透過此服務
    """
    
    @staticmethod
    def is_available():
        """檢查 Glyphs API 是否可用
        
        Returns:
            bool: Glyphs API 是否可用
        """
        return GLYPHS_AVAILABLE and Glyphs is not None
    
    @staticmethod
    def get_current_font():
        """獲取當前字體
        
        Returns:
            GSFont or None: 當前字體
        """
        if not GlyphsService.is_available():
            return None
        return Glyphs.font
    
    @staticmethod
    def get_current_font_context():
        """獲取當前字體上下文（字體和主版）
        
        Returns:
            tuple: (font, master) 或 (None, None)
        """
        try:
            return FontManager.getCurrentFontContext()
        except:
            return (None, None)
    
    @staticmethod
    def get_glyph_from_font(font, char_or_name):
        """從字體中獲取字符（減法重構：統一使用官方方法）
        
        Args:
            font: GSFont 字體物件
            char_or_name (str): 字符或字符名稱
            
        Returns:
            GSGlyph or None: 字符物件
        """
        if not font or not char_or_name:
            return None
        
        try:
            # 使用官方 tempData 快取
            cache_key = f"glyph_lookup_{char_or_name}"
            if hasattr(font, 'tempData') and cache_key in font.tempData:
                return font.tempData[cache_key]
            
            # 統一使用官方 font.glyphs 字典存取
            # 官方原生支援：字符名稱、直接字符、Unicode十六進制
            glyph = None
            if hasattr(font, 'glyphs'):
                try:
                    glyph = font.glyphs[char_or_name]
                except (KeyError, IndexError):
                    # 單字符嘗試 Unicode 十六進制格式
                    if len(char_or_name) == 1:
                        try:
                            unicode_hex = f"{ord(char_or_name):04X}"
                            glyph = font.glyphs[unicode_hex]
                        except (KeyError, ValueError, OverflowError):
                            pass
            
            # 使用官方快取
            if hasattr(font, 'tempData'):
                font.tempData[cache_key] = glyph
            
            return glyph
            
        except Exception:
            print(traceback.format_exc())
            return None
    
    @staticmethod
    def get_layer_from_glyph(glyph, master_id):
        """從字符獲取指定主版的圖層
        
        Args:
            glyph: GSGlyph 字符物件
            master_id (str): 主版 ID
            
        Returns:
            GSLayer or None: 圖層物件
        """
        if not glyph or not master_id:
            return None
        
        try:
            if hasattr(glyph, 'layers') and master_id in glyph.layers:
                return glyph.layers[master_id]
            return None
        except Exception:
            print(traceback.format_exc())
            return None
    
    @staticmethod
    def get_layer_for_char(font, char_or_name, master_id):
        """為字符獲取圖層（完整流程）
        
        Args:
            font: GSFont 字體物件
            char_or_name (str): 字符或字符名稱
            master_id (str): 主版 ID
            
        Returns:
            GSLayer or None: 圖層物件
        """
        glyph = GlyphsService.get_glyph_from_font(font, char_or_name)
        if not glyph:
            return None
        
        return GlyphsService.get_layer_from_glyph(glyph, master_id)
    
    @staticmethod
    def get_selected_glyph():
        """獲取當前選中的字符
        
        Returns:
            str or None: 選中的字符名稱或字符
        """
        if not GlyphsService.is_available():
            return None
        
        try:
            font = GlyphsService.get_current_font()
            if not font:
                return None
            
            # 檢查是否有選中的圖層
            if font.selectedLayers:
                layer = font.selectedLayers[0]
                if layer and layer.parent:
                    glyph = layer.parent
                    # 優先返回單字符
                    if glyph.unicode:
                        try:
                            return chr(int(glyph.unicode, 16))
                        except (ValueError, TypeError):
                            pass
                    # 復原到字符名稱
                    return glyph.name
            
            return None
        except Exception:
            print(traceback.format_exc())
            return None
    
    @staticmethod
    def is_in_font_view():
        """偵測當前是否在 Font View 模式
        
        Returns:
            bool: 是否在 Font View
        """
        try:
            font, _ = GlyphsService.get_current_font_context()
            if not font:
                return True
            
            # 檢查是否有活動的編輯分頁
            if not font.currentTab:
                return True
            
            # 檢查是否有選中的圖層（Edit View 特徵）
            if not font.selectedLayers:
                return True
                
            return False  # 在 Edit View
        except:
            return True  # 例外時假設在 Font View
    
    @staticmethod
    def get_visible_tab_layers():
        """取得當前分頁中可見的圖層列表（Edit View 專用）
        
        Returns:
            list: 可見圖層列表
        """
        try:
            font, _ = GlyphsService.get_current_font_context()
            if not font or not font.currentTab:
                return []
            
            current_tab = font.currentTab
            if not hasattr(current_tab, 'layers') or not current_tab.layers:
                return []
            
            return list(current_tab.layers)
            
        except Exception:
            print(traceback.format_exc())
            return []
    
    @staticmethod
    def show_notification(title, message):
        """顯示 Glyphs 通知
        
        Args:
            title (str): 通知標題
            message (str): 通知訊息
        """
        if not GlyphsService.is_available():
            return
        
        try:
            if hasattr(Glyphs, 'showNotification'):
                Glyphs.showNotification(title, message)
        except Exception:
            print(traceback.format_exc())

    @staticmethod
    def get_current_font_id():
        """獲取當前字型的唯一標識
        
        Returns:
            str or None: 字型唯一標識（檔案路徑 + 修改時間）
        """
        try:
            font = GlyphsService.get_current_font()
            if not font:
                return None
                
            # 使用檔案路徑作為主要識別
            font_path = getattr(font, 'filepath', None)
            if font_path:
                try:
                    import os
                    # 結合檔案路徑和修改時間作為唯一標識
                    mtime = os.path.getmtime(font_path)
                    return f"{font_path}#{mtime}"
                except (OSError, AttributeError):
                    # 檔案不存在或無法存取時，僅使用路徑
                    return font_path
            
            # 使用字型核心屬性生成穩定的雜湊值（Gemini 建議）
            try:
                master_ids = "".join(sorted([m.id for m in font.masters]) if hasattr(font, 'masters') else [])
                glyph_count = len(font.glyphs) if hasattr(font, 'glyphs') else 0
                family_name = getattr(font, 'familyName', 'unknown')
                font_hash_key = f"{family_name}-{glyph_count}-{master_ids}"
                return str(hash(font_hash_key))
            except Exception:
                print(traceback.format_exc())
                # 最終復原：使用時間戳
                return f"font_{int(time.time() * 1000)}"
            
        except Exception:
            print(traceback.format_exc())
            return None
    
    @staticmethod
    def has_font_changed(previous_font_id):
        """檢查字型是否已變更
        
        Args:
            previous_font_id (str): 先前記錄的字型 ID
            
        Returns:
            bool: 字型是否已變更
        """
        if previous_font_id is None:
            return True  # 首次檢查視為變更
            
        current_font_id = GlyphsService.get_current_font_id()
        return current_font_id != previous_font_id
    
    @staticmethod
    def clear_font_cache():
        """清除字型相關快取
        
        清除 tempData 中的字符尋找快取，確保使用最新字型進行驗證
        """
        try:
            font = GlyphsService.get_current_font()
            if font and hasattr(font, 'tempData'):
                # 清除所有以 "glyph_lookup_" 開頭的快取項目
                temp_data = font.tempData
                if temp_data:
                    keys_to_remove = [key for key in temp_data.keys() 
                                    if isinstance(key, str) and key.startswith('glyph_lookup_')]
                    for key in keys_to_remove:
                        try:
                            del temp_data[key]
                        except KeyError:
                            pass
                            
        except Exception:
            print(traceback.format_exc())
    
    @staticmethod
    def register_font_change_callback(callback_handler):
        """註冊字型變更回呼（使用官方 Glyphs API）
        
        Args:
            callback_handler: 回呼處理器物件（需具備相關方法）
            
        Returns:
            bool: 註冊成功與否
        """
        if not GlyphsService.is_available() or not hasattr(Glyphs, 'addCallback'):
            return False
            
        try:
            # 註冊文件開啟事件
            Glyphs.addCallback(callback_handler.handle_document_opened, 'GSDocumentOpenNotification')
            
            # 註冊文件啟動事件  
            Glyphs.addCallback(callback_handler.handle_document_activated, 'GSDocumentActivatedNotification')
            
            # 註冊文件保存事件（字型更新時）
            Glyphs.addCallback(callback_handler.handle_document_saved, 'GSDocumentSaveNotification')
            
            return True
        except Exception:
            print(traceback.format_exc())
            return False
    
    @staticmethod  
    def unregister_font_change_callback(callback_handler):
        """移除字型變更回呼
        
        Args:
            callback_handler: 回呼處理器物件
            
        Returns:
            bool: 移除成功與否
        """
        if not GlyphsService.is_available() or not hasattr(Glyphs, 'removeCallback'):
            return False
            
        try:
            # 移除所有已註冊的回呼
            Glyphs.removeCallback(callback_handler.handle_document_opened)
            Glyphs.removeCallback(callback_handler.handle_document_activated) 
            Glyphs.removeCallback(callback_handler.handle_document_saved)
            
            return True
        except Exception:
            print(traceback.format_exc())
            return False
    
    @staticmethod
    def are_all_fonts_closed():
        """偵測是否所有字型檔案都已關閉
        
        Returns:
            bool: True 如果所有字型檔案都已關閉
        """
        if not GlyphsService.is_available():
            return True  # Glyphs 不可用時視為已關閉
        
        try:
            # 檢查是否還有開啟的字型
            if hasattr(Glyphs, 'fonts'):
                # 檢查字型列表是否為空
                return len(Glyphs.fonts) == 0
            elif hasattr(Glyphs, 'font') and Glyphs.font:
                # 有當前字型
                return False
            else:
                # 沒有字型可用
                return True
        except Exception:
            print(traceback.format_exc())
            return True  # 例外時視為已關閉
    
    @staticmethod
    def is_last_font_closing():
        """偵測是否即將關閉最後一個字型檔案（用於 DOCUMENTWILLCLOSE 事件）
        
        在 DOCUMENTWILLCLOSE 事件中，目的檔尚未實際關閉，
        所以需要檢查關閉後是否只會剩下一個或零個文件
        
        Returns:
            bool: True 如果這是最後一個字型檔案即將關閉
        """
        if not GlyphsService.is_available():
            return True  # Glyphs 不可用時視為關閉最後一個
        
        try:
            # 檢查開啟的字型數量
            if hasattr(Glyphs, 'fonts') and Glyphs.fonts:
                font_count = len(Glyphs.fonts)
                # 如果只有一個字型，關閉後就沒有字型了
                return font_count <= 1
            else:
                # 沒有字型列表或為空
                return True
        except Exception:
            print(traceback.format_exc())
            return True  # 例外時視為關閉最後一個


# 模組級別的服務實例（單例模式）
_service_instance = GlyphsService()

def get_glyphs_service():
    """獲取 Glyphs 服務實例
    
    Returns:
        GlyphsService: 服務實例
    """
    return _service_instance