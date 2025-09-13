# encoding: utf-8
"""
九宮格預覽外掛 - 統一字符輸入辨識系統
Nine Box Preview Plugin - Unified Glyph Input Recognition System

減法重構：統一處理搜尋輸入框和鎖定輸入框的字符辨識邏輯
"""

from __future__ import division, print_function, unicode_literals
import traceback

# 僅匯入保留的前台本地化功能（錯誤訊息已移除）

# 有條件匯入 GlyphsApp（支援測試環境）
try:
    from GlyphsApp import Glyphs
except ImportError:
    # 測試環境：使用 Mock 或設為 None
    try:
        # 嘗試匯入測試用的 Mock Glyphs
        import os
        
        # 尋找測試目錄
        current_dir = os.path.dirname(__file__)
        tests_dir = os.path.join(os.path.dirname(current_dir), 'tests')
        
        # 避免未使用變數警告
        _ = current_dir
        _ = tests_dir
        
    except ImportError:
        Glyphs = None


# 統一匯入快取管理系統
# 移除舊的快取匯入，統一使用 glyphs_service



class InputGuardService:
    """輸入防護機制服務（集中管理所有輸入防護邏輯）
    
    負責以下防護：
    1. 重複輸入防護 - 避免相同輸入重複處理
    2. 狀態同步防護 - 避免無意義的狀態更新
    3. 程式化更新防護 - 避免循環觸發
    4. 輸入有效性防護 - 統一輸入驗證邏輯
    """
    
    @staticmethod
    def should_process_input(search_text, plugin_state):
        """檢查是否應該處理輸入變更
        
        Args:
            search_text (str): 當前輸入文字
            plugin_state: Plugin 狀態物件
            
        Returns:
            bool: True 如果應該處理此輸入
        """
        # 重複輸入防護
        if hasattr(plugin_state, 'lastInput') and plugin_state.lastInput == search_text:
            return False  # 相同輸入，跳過處理
        
        return True
    
    @staticmethod
    def should_update_state(chars, plugin_state):
        """檢查是否應該更新字符狀態
        
        Args:
            chars (list): 解析出的字符列表
            plugin_state: Plugin 狀態物件
            
        Returns:
            bool: True 如果需要更新狀態
        """
        # 狀態同步防護
        current_chars = getattr(plugin_state, 'selectedChars', [])
        return chars != current_chars
    
    @staticmethod
    def process_search_input(search_text, plugin_state, update_callback, randomize_callback):
        """統一的搜尋輸入處理（包含完整防護機制）
        
        Args:
            search_text (str): 搜尋文字
            plugin_state: Plugin 狀態物件
            update_callback: 更新回呼函數
            randomize_callback: 隨機化回呼函數
            
        Returns:
            dict: 處理結果
        """
        try:
            # 防護機制1: 重複輸入檢查
            if not InputGuardService.should_process_input(search_text, plugin_state):
                return {'processed': False, 'reason': 'duplicate_input'}
            
            # 更新輸入狀態
            plugin_state.lastInput = search_text
            
            if not search_text:
                # 空輸入：完全重置狀態確保下次任何輸入都被視為新狀態
                plugin_state.lastInput = ""  # 設為空字串，確保狀態轉換被正確辨認
                plugin_state.selectedChars = []  # 同時重置字符狀態，避免第二層防護攔截
                randomize_callback()
                return {'processed': True, 'action': 'randomize'}
            else:
                # 有輸入：解析並處理
                chars = parse_glyph_input(search_text)
                
                # 防護機制2: 狀態同步檢查
                if InputGuardService.should_update_state(chars, plugin_state):
                    plugin_state.selectedChars = chars
                    
                    if chars:
                        # 有效字符：更新排列
                        update_callback(chars)
                        return {'processed': True, 'action': 'update', 'chars': chars}
                    else:
                        # 無效字符：隨機排列
                        randomize_callback()
                        return {'processed': True, 'action': 'randomize_invalid'}
                else:
                    # 字符狀態沒變化，跳過更新
                    return {'processed': False, 'reason': 'no_state_change'}
            
        except Exception as e:
            print(traceback.format_exc())
            return {'processed': False, 'reason': 'error', 'error': str(e)}


class InputRecognitionService:
    """統一的字符輸入辨識服務
    
    減法重構原則：
    - 單字符 = 多字符的特殊情況（max_glyphs=1）
    - 統一術語：character → glyph
    - 一個方法處理所有輸入辨識需求
    """
    
    @staticmethod
    def parse_glyph_input(text, max_glyphs=None, allow_fallback=True, font=None, master=None):
        """統一的字符輸入解析（使用 font.tempData 快取機制）
        
        Args:
            text: 輸入文字
            max_glyphs: 最大字符數限制（保留向後相容性，但內部統一處理）
            allow_fallback: 保留向後相容性參數
            font: GSFont 物件（用於 tempData 快取）
            master: GSFontMaster 物件（用於生成快取鍵）
            
        Returns:
            list: 有效字符列表
            
        Examples:
            # 多字符搜尋：parse_glyph_input("天天") → ['天', '天']
            # 鎖定輸入框：parse_glyph_input("天天")[0] → '天' （呼叫方取第一個）
            # Nice Names：parse_glyph_input("u-bopomofo abc") → ['u-bopomofo', 'a', 'b', 'c']
            # 無效輸入：parse_glyph_input("xyz") → []
            # 空白字符：parse_glyph_input("   ") → []
        """
        # 避免未使用參數警告（保持向後相容性）
        _ = allow_fallback
        
        # 空白字符正規化：先檢查是否僅包含空白字符
        if not text or not text.strip() or not Glyphs or not Glyphs.font:
            return []
        
        # 使用 font.tempData 快取解析結果
        current_font = font or Glyphs.font
        if current_font and hasattr(current_font, 'tempData') and master:
            # 生成快取鍵
            text_hash = hash(text.strip())
            max_glyphs_key = f"_{max_glyphs}" if max_glyphs else ""
            cache_key = f"parse_input_{master.id}_{text_hash}{max_glyphs_key}"
            
            # 檢查快取
            if cache_key in current_font.tempData:
                cached_result = current_font.tempData[cache_key]
                if isinstance(cached_result, list):
                    return cached_result
                else:
                    # 快取無效，移除
                    del current_font.tempData[cache_key]
        
        # 統一使用多字符解析邏輯（減法重構：消除複雜分支）
        result = InputRecognitionService._parse_multi_glyph_input(text, max_glyphs, current_font, master)
        
        # 快取結果
        if current_font and hasattr(current_font, 'tempData') and master:
            current_font.tempData[cache_key] = result[:]
        
        return result
    
    @staticmethod
    def _parse_multi_glyph_input(text, max_glyphs=None, font=None, master=None):
        """多字符輸入解析（整合 font.tempData 快取支援）"""
        glyphs = []
        segments = InputRecognitionService._smart_split_text(text)
        
        # 避免未使用參數警告（master 保留供未來快取功能使用）
        _ = master
        
        for segment in segments:
            if not segment:
                continue
            
            # 使用統一服務進行字符尋找（享受 tempData 快取優化）
            current_font = font or Glyphs.font
            try:
                from .glyphs_service import get_glyphs_service
                glyphs_service = get_glyphs_service()
                glyph = glyphs_service.get_glyph_from_font(current_font, segment)
                
                if glyph:
                    glyphs.append(segment)
                    
                    # 檢查是否達到最大限制
                    if max_glyphs and len(glyphs) >= max_glyphs:
                        break
                # 如果不是有效字符或 Nice Name，直接跳過（不進行任何分解）
                # 用戶期望：只有完全匹配有效字符名稱時才有效，絕不分解
                
            except ImportError:
                # 復原到原始方法（測試環境或匯入失敗時）
                pass
        
        return glyphs
    
    
    @staticmethod
    def _smart_split_text(text):
        """智慧分割文字，區分CJK字符和非CJK群組"""
        if not text:
            return []
        
        # 空白字符前置檢查：如果輸入僅包含空白字符，直接返回空列表
        if not text.strip():
            return []
        
        segments = []
        i = 0
        
        while i < len(text):
            char = text[i]
            
            # 跳過所有類型的空白字符（包括空格、tab、換行等）
            if char.isspace():
                i += 1
                continue
            
            # 判斷是否為CJK字符
            if InputRecognitionService._is_cjk_char(char):
                # CJK字符：每個字符單獨處理
                segments.append(char)
                i += 1
            else:
                # 非CJK字符：收集連續的非空白字符
                start = i
                while i < len(text) and not text[i].isspace() and not InputRecognitionService._is_cjk_char(text[i]):
                    i += 1
                segments.append(text[start:i])
        
        return segments
    
    @staticmethod
    def _is_cjk_char(char):
        """檢查是否為CJK字符（完整 Unicode 15.1 支援）
        
        涵蓋所有 CJK 相關 Unicode 區塊：
        - CJK 統一表意文字及所有擴充區 (A-I)
        - CJK 相容表意文字及補充
        - 假名（平假名、片假名及擴充）
        - 韓文（音節、字母及擴充）
        - 注音符號及擴充
        - CJK 符號、部首、描述字符
        
        Args:
            char: 單一字符
            
        Returns:
            bool: 是否為 CJK 字符
        """
        if not char:
            return False
        
        code_point = ord(char)
        
        # === 按 Unicode 碼位順序檢查（優化效能） ===
        
        # 1. 韓文字母 (U+1100-U+11FF) - 초성, 중성, 종성
        if 0x1100 <= code_point <= 0x11FF:
            return True
        
        # 2. 康熙部首 (U+2F00-U+2FDF) - ⼀⼆⼈儿入
        if 0x2F00 <= code_point <= 0x2FDF:
            return True
        
        # 3. 表意文字描述字符 (U+2FF0-U+2FFF) - ⿰⿱⿲⿳⿴⿵⿶⿷⿸⿹⿺⿻
        if 0x2FF0 <= code_point <= 0x2FFF:
            return True
        
        # 4. CJK 符號和標點符號 (U+3000-U+303F) - 　、。〃〈〉《》「」『』【】〔〕
        if 0x3000 <= code_point <= 0x303F:
            return True
        
        # 5. 平假名 (U+3040-U+309F) - あいうえお
        if 0x3040 <= code_point <= 0x309F:
            return True
        
        # 6. 片假名 (U+30A0-U+30FF) - アイウエオ
        if 0x30A0 <= code_point <= 0x30FF:
            return True
        
        # 7. 注音符號 (U+3105-U+312F) - ㄅㄆㄇㄈ
        if 0x3105 <= code_point <= 0x312F:
            return True
        
        # 8. 韓文相容字母 (U+3130-U+318F) - ㄱㄲㄳㄴㄵㄶㄷㄸㄹㄺㄻㄼㄽㄾㄿ
        if 0x3130 <= code_point <= 0x318F:
            return True
        
        # 9. 注音符號擴充 (U+31A0-U+31BF) - 方言注音符號
        if 0x31A0 <= code_point <= 0x31BF:
            return True
        
        # 10. 片假名語音擴充 (U+31F0-U+31FF) - ㇰㇱㇲㇳㇴㇵㇶㇷㇸㇹㇺㇻㇼㇽㇾㇿ
        if 0x31F0 <= code_point <= 0x31FF:
            return True
        
        # 11. CJK 統一表意文字擴充A (U+3400-U+4DBF) - 㐀㐁㐂㐃
        if 0x3400 <= code_point <= 0x4DBF:
            return True
        
        # 12. CJK 統一表意文字 (U+4E00-U+9FFF) - 一乙二十丁七
        if 0x4E00 <= code_point <= 0x9FFF:
            return True
        
        # 13. 韓文字母擴充A (U+A960-U+A97F) - 古韓文字母
        if 0xA960 <= code_point <= 0xA97F:
            return True
        
        # 14. 韓文音節 (U+AC00-U+D7AF) - 가각갂갃간갅갆갇갈갉갊갋갌갍갎갏
        if 0xAC00 <= code_point <= 0xD7AF:
            return True
        
        # 15. 韓文字母擴充B (U+D7B0-U+D7FF) - 擴充韓文字母
        if 0xD7B0 <= code_point <= 0xD7FF:
            return True
        
        # 16. CJK 相容表意文字 (U+F900-U+FAFF) - 豈更車賈滑串句龜龜契金喇奈懶癩羅
        if 0xF900 <= code_point <= 0xFAFF:
            return True
        
        # 17. 半寬韓文 (U+FFA0-U+FFDC) - ᄀᄁᄂᄃᄄᄅᄆᄇᄈᄉᄊᄋᄌᄍᄎᄏᄐᄑ하ᅢᅣᅤᅥᅦᅧᅨᅩᅪᅫᅬᅭᅮᅯᅰᅱᅲᅳᅴᅵ
        if 0xFFA0 <= code_point <= 0xFFDC:
            return True
        
        # 18. 假名補充 (U+1B000-U+1B0FF) - 變體假名
        if 0x1B000 <= code_point <= 0x1B0FF:
            return True
        
        # 19. 假名擴充A (U+1B100-U+1B12F) - 歷史假名變體
        if 0x1B100 <= code_point <= 0x1B12F:
            return True
        
        # 20. 小假名擴充 (U+1B130-U+1B16F) - 組合用小假名
        if 0x1B130 <= code_point <= 0x1B16F:
            return True
        
        # 21. CJK 統一表意文字擴充B (U+20000-U+2A6DF) - 𠀀𠀁𠀂
        if 0x20000 <= code_point <= 0x2A6DF:
            return True
        
        # 22. CJK 統一表意文字擴充C (U+2A700-U+2B73F)
        if 0x2A700 <= code_point <= 0x2B73F:
            return True
        
        # 23. CJK 統一表意文字擴充D (U+2B740-U+2B81F)
        if 0x2B740 <= code_point <= 0x2B81F:
            return True
        
        # 24. CJK 統一表意文字擴充E (U+2B820-U+2CEAF)
        if 0x2B820 <= code_point <= 0x2CEAF:
            return True
        
        # 25. CJK 統一表意文字擴充F (U+2CEB0-U+2EBEF)
        if 0x2CEB0 <= code_point <= 0x2EBEF:
            return True
        
        # 26. CJK 統一表意文字擴充I (U+2EBF0-U+2EE5F) - 最新 Unicode 15.1
        if 0x2EBF0 <= code_point <= 0x2EE5F:
            return True
        
        # 27. CJK 相容表意文字補充 (U+2F800-U+2FA1F) - 衣𧙧裗
        if 0x2F800 <= code_point <= 0x2FA1F:
            return True
        
        # 28. CJK 統一表意文字擴充G (U+30000-U+3134F)
        if 0x30000 <= code_point <= 0x3134F:
            return True
        
        # 29. CJK 統一表意文字擴充H (U+31350-U+323AF) - 最新 Unicode 15.0
        if 0x31350 <= code_point <= 0x323AF:
            return True
        
        return False

    @staticmethod
    def validate_glyph_input(text):
        """驗證字符輸入是否有效（新增功能：即時驗證用）
        
        Args:
            text: 輸入文字
            
        Returns:
            dict: 驗證結果
                {
                    'valid': bool,           # 是否有效
                    'valid_glyphs': list,    # 有效的字符列表
                    'invalid_chars': list    # 無效的字符列表
                }
        """
        # 空白字符檢查：包含純空白字符的情況
        if not text or not text.strip() or not Glyphs or not Glyphs.font:
            return {
                'valid': False,
                'valid_glyphs': [],
                'invalid_chars': []
            }
        
        segments = InputRecognitionService._smart_split_text(text)
        valid_glyphs = []
        invalid_chars = []
        
        for segment in segments:
            try:
                from .glyphs_service import get_glyphs_service
                glyphs_service = get_glyphs_service()
                glyph = glyphs_service.get_glyph_from_font(Glyphs.font, segment)
                
                if glyph:
                    valid_glyphs.append(segment)
                else:
                    # 嚴格匹配策略：整個 segment 無效就視為無效，不分解
                    invalid_chars.append(segment)
                    
            except ImportError:
                # 復原到原始方法
                pass
        
        # 驗證結果
        all_valid = len(invalid_chars) == 0
        
        return {
            'valid': all_valid,
            'valid_glyphs': valid_glyphs,
            'invalid_chars': invalid_chars
        }


# 向後相容性函數：保持原有 API 並支援 tempData 快取
def parse_glyph_input(text, max_glyphs=None, allow_fallback=True, font=None, master=None):
    """統一字符輸入解析的便捷函數（支援 font.tempData 快取）
    
    這是 InputRecognitionService.parse_glyph_input() 的便捷包裝器
    
    Args:
        text: 輸入文字
        max_glyphs: 最大字符數限制
        allow_fallback: 向後相容性參數
        font: GSFont 物件（用於 tempData 快取）
        master: GSFontMaster 物件（用於生成快取鍵）
    
    Returns:
        list: 有效字符列表
    """
    return InputRecognitionService.parse_glyph_input(text, max_glyphs, allow_fallback, font, master)


def validate_glyph_input(text):
    """字符輸入驗證的便捷函數
    
    這是 InputRecognitionService.validate_glyph_input() 的便捷包裝器
    """
    return InputRecognitionService.validate_glyph_input(text)


class VisualFeedbackService:
    """統一的視覺標注服務 - 為無效字符新增紅色標記"""
    
    # 字型狀態追蹤 
    _current_font_id = None
    
    @staticmethod
    def on_font_changed():
        """字型變更時的處理邏輯
        
        偵測字型變更並更新所有相關的視覺標注
        
        Returns:
            bool: 是否偵測到字型變更
        """
        try:
            from .glyphs_service import get_glyphs_service
            glyphs_service = get_glyphs_service()
            
            # 檢查字型是否變更
            if glyphs_service.has_font_changed(VisualFeedbackService._current_font_id):
                # 更新當前字型 ID
                VisualFeedbackService._current_font_id = glyphs_service.get_current_font_id()
                
                # 清除字型相關快取
                glyphs_service.clear_font_cache()
                
                return True
            
            return False
            
        except Exception:
            print(traceback.format_exc())
            return False
    
    @staticmethod
    def refresh_all_annotations_on_font_change(plugin):
        """字型變更時更新所有視覺標注（模擬初次開啟流程）
        
        Args:
            plugin: 外掛實例
        """
        try:
            # 偵測字型變更
            if VisualFeedbackService.on_font_changed():
                
                # 模擬初次開啟的完整流程：先更新內容再套用視覺標注
                VisualFeedbackService._simulate_initial_content_update(plugin)
                
                # 額外的安全措施：再次直接套用視覺標注
                VisualFeedbackService.apply_feedback_to_all_inputs(plugin)
                
        except Exception:
            print(traceback.format_exc())
    
    @staticmethod
    def _simulate_initial_content_update(plugin):
        """模擬初次開啟時的內容更新流程（觸發視覺標注重新套用）
        
        此方法模擬 makeKeyAndOrderFront() → update_ui() → update_content() → setStringValue_() 
        的完整流程，確保視覺標注在字型變更時能正確重新套用
        
        Args:
            plugin: 外掛實例
        """
        try:
            
            # 取得視窗控制器（修正架構層次存取路徑）
            # plugin 是 NineBoxViewController，需要透過 _parent_plugin 存取 plugin.py 中的 window_controller
            parent_plugin = getattr(plugin, '_parent_plugin', None)
            if not parent_plugin:
                return
                
            window_controller = getattr(parent_plugin, 'window_controller', None)
            if not window_controller:
                return
            
            controls_view = getattr(window_controller, 'controlsPanelView', None)
            if not controls_view:
                return
            
            # 1. 模擬搜尋框的內容更新流程
            VisualFeedbackService._simulate_search_field_update(controls_view, plugin)
            
            # 2. 模擬鎖定輸入框的內容更新流程
            VisualFeedbackService._simulate_lock_fields_update(controls_view, plugin)
            
        except Exception:
            print(traceback.format_exc())
    
    @staticmethod
    def _simulate_search_field_update(controls_view, plugin):
        """模擬搜尋框的內容更新流程"""
        try:
            search_panel = getattr(controls_view, 'searchPanel', None)
            if not search_panel:
                return
                
            search_field = getattr(search_panel, 'searchField', None)
            if not search_field:
                return
            
            # 取得當前內容
            current_value = search_field.stringValue()
            
            # 重新設定相同內容（觸發 setStringValue_ 流程）
            search_field.setStringValue_(current_value)
            
            # 避免未使用參數警告
            _ = plugin
            
        except Exception:
            print(traceback.format_exc())
    
    @staticmethod
    def _simulate_lock_fields_update(controls_view, plugin):
        """模擬鎖定輸入框的內容更新流程"""
        try:
            lock_panel = getattr(controls_view, 'lockFieldsPanel', None)
            if not lock_panel:
                return
                
            # 遍歷所有鎖定輸入框（修正字典遍歷邏輯）
            lock_fields = getattr(lock_panel, 'lockFields', {})
            if not lock_fields:
                return
            
            
            # lockFields 是字典 {position: field_object}，需要正確遍歷
            for position, field in lock_fields.items():
                if field and hasattr(field, 'stringValue'):
                    try:
                        current_value = field.stringValue()
                        
                        # 重新設定相同內容（觸發 setStringValue_ 流程）
                        if hasattr(field, 'setStringValue_'):
                            field.setStringValue_(current_value)
                            
                    except Exception:
                        print(traceback.format_exc())
                
                # 避免未使用參數警告
                _ = position
            
            # 避免未使用參數警告
            _ = plugin
            
        except Exception:
            print(traceback.format_exc())
    
    
    @staticmethod
    def apply_visual_feedback(text_control, validation_result):
        """為無效字符套用紅色標注
        
        Args:
            text_control: NSTextView 或 NSTextField 控件
            validation_result: 驗證結果，包含 'invalid_chars' 列表
        """
        try:
            if not text_control or not validation_result:
                return
                
            # 取得當前文字
            if hasattr(text_control, 'string'):
                # NSTextView
                current_text = text_control.string()
            elif hasattr(text_control, 'stringValue'):
                # NSTextField  
                current_text = text_control.stringValue()
            else:
                return
                
            if not current_text:
                return
                
            # 如果沒有無效字符，清除任何現有標注
            invalid_chars = validation_result.get('invalid_chars', [])
            if not invalid_chars:
                VisualFeedbackService.clear_visual_feedback(text_control)
                return
                
            # 匯入必要的 AppKit 類別
            from AppKit import (NSMutableAttributedString, NSUnderlineStyleAttributeName, 
                               NSUnderlineColorAttributeName, NSColor, NSFont, NSFontAttributeName, 
                               NSForegroundColorAttributeName, NSParagraphStyleAttributeName, 
                               NSMutableParagraphStyle, NSCenterTextAlignment, NSBackgroundColorAttributeName)
            
            # 建立屬性字符串
            attributed_string = NSMutableAttributedString.alloc().initWithString_(current_text)
            
            # 設定基礎屬性 - 修復：使用等寬字體而非當前字體
            from ..core.utils import FontManager
            
            # 智慧字體選擇：根據控件類型選擇對應的等寬字體
            if hasattr(text_control, 'textStorage'):
                # NSTextView (搜尋框)
                font_to_use = FontManager.get_monospace_font_for_search()
            else:
                # NSTextField (鎖定輸入框)
                font_to_use = FontManager.get_monospace_font_for_lock_field()
            
            # 如果無法取得等寬字體，才使用系統字體作為備案
            if not font_to_use:
                font_to_use = NSFont.systemFontOfSize_(14.0)
                
            if font_to_use:
                attributed_string.addAttribute_value_range_(NSFontAttributeName, font_to_use, (0, len(current_text)))
            
            # 使用系統文字顏色
            attributed_string.addAttribute_value_range_(NSForegroundColorAttributeName, NSColor.controlTextColor(), (0, len(current_text)))
            
            # 為 NSTextField 設定段落樣式以保持置中對齊
            if hasattr(text_control, 'setAttributedStringValue_'):
                paragraph_style = NSMutableParagraphStyle.alloc().init()
                paragraph_style.setAlignment_(NSCenterTextAlignment)
                attributed_string.addAttribute_value_range_(NSParagraphStyleAttributeName, paragraph_style, (0, len(current_text)))
            
            # 標注無效字符
            text_lower = current_text.lower()
            for invalid_char in invalid_chars:
                if not invalid_char:
                    continue
                    
                # 搜尋所有該字符出現的位置（不區分大小寫）
                invalid_lower = invalid_char.lower()
                start = 0
                while True:
                    pos = text_lower.find(invalid_lower, start)
                    if pos == -1:
                        break
                        
                    char_range = (pos, len(invalid_char))
                    
                    # 使用系統紅色搭配透明度（錯誤標注語義，自動適應明暗模式）
                    error_background_color = NSColor.systemRedColor().colorWithAlphaComponent_(0.2)
                    attributed_string.addAttribute_value_range_(NSBackgroundColorAttributeName, error_background_color, char_range)
                    
                    # 可選：加上系統紅色底線樣式（用於測試對比）
                    attributed_string.addAttribute_value_range_(NSUnderlineStyleAttributeName, 1, char_range)  
                    attributed_string.addAttribute_value_range_(NSUnderlineColorAttributeName, NSColor.systemRedColor(), char_range)
                    
                    start = pos + len(invalid_char)
            
            # 套用屬性字符串
            if hasattr(text_control, 'textStorage'):
                # NSTextView
                text_control.textStorage().setAttributedString_(attributed_string)
                text_control.setNeedsDisplay_(True)
            elif hasattr(text_control, 'setAttributedStringValue_'):
                # NSTextField
                text_control.setAttributedStringValue_(attributed_string)
                text_control.setNeedsDisplay_(True)
                
        except Exception:
            print(traceback.format_exc())
    
    @staticmethod
    def clear_visual_feedback(text_control):
        """清除視覺標注，恢復原始格式"""
        try:
            if not text_control:
                return
                
            # 取得當前文字
            if hasattr(text_control, 'string'):
                # NSTextView
                current_text = text_control.string()
            elif hasattr(text_control, 'stringValue'):
                # NSTextField
                current_text = text_control.stringValue()
            else:
                return
                
            if not current_text:
                return
                
            from AppKit import (NSMutableAttributedString, NSFont, NSFontAttributeName, NSForegroundColorAttributeName, 
                               NSColor, NSParagraphStyleAttributeName, NSMutableParagraphStyle, NSCenterTextAlignment)
            
            # 建立清潔的屬性字符串
            clean_attributed_string = NSMutableAttributedString.alloc().initWithString_(current_text)
            
            # 設定基礎屬性 - 修復：使用等寬字體而非當前字體
            from ..core.utils import FontManager
            
            # 智慧字體選擇：根據控件類型選擇對應的等寬字體
            if hasattr(text_control, 'textStorage'):
                # NSTextView (搜尋框)
                font_to_use = FontManager.get_monospace_font_for_search()
            else:
                # NSTextField (鎖定輸入框)
                font_to_use = FontManager.get_monospace_font_for_lock_field()
            
            # 如果無法取得等寬字體，才使用系統字體作為備案
            if not font_to_use:
                font_to_use = NSFont.systemFontOfSize_(14.0)
                
            if font_to_use:
                clean_attributed_string.addAttribute_value_range_(NSFontAttributeName, font_to_use, (0, len(current_text)))
            clean_attributed_string.addAttribute_value_range_(NSForegroundColorAttributeName, NSColor.controlTextColor(), (0, len(current_text)))
            
            # 為 NSTextField 設定段落樣式以保持置中對齊
            if hasattr(text_control, 'setAttributedStringValue_'):
                paragraph_style = NSMutableParagraphStyle.alloc().init()
                paragraph_style.setAlignment_(NSCenterTextAlignment)
                clean_attributed_string.addAttribute_value_range_(NSParagraphStyleAttributeName, paragraph_style, (0, len(current_text)))
            
            # 套用清潔屬性字符串
            if hasattr(text_control, 'textStorage'):
                text_control.textStorage().setAttributedString_(clean_attributed_string)
                text_control.setNeedsDisplay_(True)
            elif hasattr(text_control, 'setAttributedStringValue_'):
                text_control.setAttributedStringValue_(clean_attributed_string)
                text_control.setNeedsDisplay_(True)
                
        except Exception:
            print(traceback.format_exc())
    
    @staticmethod
    def apply_visual_feedback_to_text(text_control):
        """便捷方法：驗證並標注當前文字"""
        try:
            current_text = text_control.string() if hasattr(text_control, 'string') else text_control.stringValue()
            validation_result = InputRecognitionService.validate_glyph_input(current_text)
            VisualFeedbackService.apply_visual_feedback(text_control, validation_result)
        except Exception:
            print(traceback.format_exc())
    
    @staticmethod
    def apply_feedback_to_all_inputs(plugin):
        """對所有輸入框執行視覺標注（工具開啟時主動執行）"""
        try:
            # 透過視窗控制器取得UI元件（修正架構層次存取路徑）
            # plugin 是 NineBoxViewController，需要透過 _parent_plugin 存取 plugin.py 中的 window_controller
            parent_plugin = getattr(plugin, '_parent_plugin', None)
            if not parent_plugin:
                return
                
            window_controller = getattr(parent_plugin, 'window_controller', None)
            if not window_controller:
                return
            
            # 標注搜尋框
            VisualFeedbackService.apply_feedback_to_search_field(window_controller)
            
            # 標注鎖定輸入框
            VisualFeedbackService.apply_feedback_to_lock_fields(window_controller)
            
        except Exception:
            print(traceback.format_exc())
    
    @staticmethod
    def apply_feedback_to_search_field(window_controller):
        """搜尋框專用視覺標注"""
        try:
            controls_view = getattr(window_controller, 'controlsPanelView', None)
            if not controls_view:
                return
                
            search_panel = getattr(controls_view, 'searchPanel', None)
            if not search_panel:
                return
                
            search_field = getattr(search_panel, 'searchField', None)
            if search_field:
                VisualFeedbackService.apply_visual_feedback_to_text(search_field)
                
        except Exception:
            print(traceback.format_exc())
    
    @staticmethod
    def apply_feedback_to_lock_fields(window_controller):
        """鎖定輸入框專用視覺標注"""
        try:
            controls_view = getattr(window_controller, 'controlsPanelView', None)
            if not controls_view:
                return
                
            lock_panel = getattr(controls_view, 'lockFieldsPanel', None)
            if not lock_panel:
                return
                
            # 遍歷所有鎖定輸入框（平面座標系統 0-8）
            lock_fields = getattr(lock_panel, 'lockFields', {})
            for position, field in lock_fields.items():
                if field:
                    VisualFeedbackService.apply_visual_feedback_to_text(field)
                
                # 避免未使用參數警告
                _ = position
                    
        except Exception:
            print(traceback.format_exc())
    
    @staticmethod
    def clear_all_annotations_on_font_close(plugin):
        """字型完全關閉時清空所有視覺標注
        
        這個方法專門處理字型檔案完全關閉的情況，
        確保所有輸入框的視覺標注都被清空，避免顯示無效的標注
        
        Args:
            plugin: 外掛實例（NineBoxViewController）
        """
        try:
            # 重置字型狀態追蹤
            VisualFeedbackService._current_font_id = None
            
            # 取得視窗控制器
            parent_plugin = getattr(plugin, '_parent_plugin', None)
            if not parent_plugin:
                return
                
            window_controller = getattr(parent_plugin, 'window_controller', None)
            if not window_controller:
                return
            
            controls_view = getattr(window_controller, 'controlsPanelView', None)
            if not controls_view:
                return
            
            # 清空搜尋框視覺標注
            try:
                search_panel = getattr(controls_view, 'searchPanel', None)
                if search_panel:
                    search_field = getattr(search_panel, 'searchField', None)
                    if search_field:
                        VisualFeedbackService.clear_visual_feedback(search_field)
            except Exception:
                print(traceback.format_exc())
            
            # 清空所有鎖定輸入框視覺標注
            try:
                lock_panel = getattr(controls_view, 'lockFieldsPanel', None)
                if lock_panel:
                    lock_fields = getattr(lock_panel, 'lockFields', {})
                    for field in lock_fields.values():
                        if field:
                            VisualFeedbackService.clear_visual_feedback(field)
            except Exception:
                print(traceback.format_exc())
                    
        except Exception:
            print(traceback.format_exc())