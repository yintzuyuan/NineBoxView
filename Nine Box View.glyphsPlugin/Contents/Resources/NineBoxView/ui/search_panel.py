# encoding: utf-8

"""
九宮格預覽外掛 - 搜尋面板元件
基於原版 SearchPanel 的完整復刻，使用 NSTextView 多行輸入
"""

from __future__ import division, print_function, unicode_literals
import traceback
import objc
from AppKit import (
    NSView, NSTextView, NSFont, NSColor, 
    NSViewWidthSizable, NSViewHeightSizable, NSFocusRingTypeDefault,
    NSNotificationCenter, NSMakeRect, NSScrollView
)
from Foundation import NSSize

# 本地化支援
from ..localization import localize

class SearchTextView(NSTextView):
    """多行文字檢視，基於原版 SearchTextView 的完整復刻"""
    
    def initWithFrame_plugin_(self, frame, plugin):
        """初始化多行文字檢視"""
        self = objc.super(SearchTextView, self).initWithFrame_(frame)
        if self:
            self.plugin = plugin
            self._programmatic_update = False  # 標記是否為程式化更新
            self._setup_basic_properties()
            self._register_notifications()
            
        return self
    
    def _setup_basic_properties(self):
        """設定基本屬性 - 使用 DrawBot 風格的字體和搜尋功能"""
        try:
            # 基本編輯屬性
            self.setEditable_(True)
            self.setSelectable_(True)
            self.setRichText_(False)  # 純文字模式
            self.setImportsGraphics_(False)
            self.setAllowsUndo_(True)
            
            # 使用 DrawBot 風格的等寬字體工具設定字體和搜尋功能
            from ..core.utils import setup_text_view_for_monospace_search
            setup_text_view_for_monospace_search(self)
            
            # 文字容器設定
            textContainer = self.textContainer()
            if textContainer:
                # 允許文字換行，寬度跟隨檢視
                textContainer.setWidthTracksTextView_(True)
                textContainer.setHeightTracksTextView_(False)
                # 保持適度邊距以提高可讀性
                textContainer.setLineFragmentPadding_(3.0)
            
            # 文字容器內距設定 - 設為零實作頂部貼齊
            self.setTextContainerInset_(NSSize(3, 8))
            
            # 佈局管理器設定 - 關閉字體 leading 減少頂部間距
            if self.layoutManager():
                self.layoutManager().setUsesFontLeading_(False)
            
            self.setBackgroundColor_(NSColor.textBackgroundColor())
            self.setToolTip_(localize('tooltip_search_input'))
            
        except Exception:
            print(traceback.format_exc())
    
    def _register_notifications(self):
        """註冊通知"""
        try:
            center = NSNotificationCenter.defaultCenter()
            center.addObserver_selector_name_object_(
                self, 'textDidChange:', 'NSTextDidChangeNotification', self
            )
        except Exception:
            print(traceback.format_exc())
    
    def textDidChange_(self, notification):
        """文字變更時的回呼 - 委派給事件處理器並執行即時驗證"""
        try:
            # 保存當前游標位置
            current_selection = self.selectedRange()
            
            # 執行即時字符驗證
            if not self._programmatic_update:
                self._perform_real_time_validation()
            
            # 委派給事件處理器  
            if (hasattr(self, 'plugin') and self.plugin and 
                hasattr(self.plugin, 'event_handler')):
                # 如果是程式化更新，直接返回
                if not self._programmatic_update:
                    self.plugin.event_handler.search_field_callback(self)
                    
            # 恢復游標位置
            self.setSelectedRange_(current_selection)
            
        except Exception:
            print(traceback.format_exc())
        
        # 避免 notification 參數未使用警告
        _ = notification
    
    def _perform_real_time_validation(self):
        """執行即時驗證並套用視覺標注（整合 VisualFeedbackService）"""
        try:
            current_text = self.string()
            
            if not current_text:
                # 空文字：顯示預設提示
                self.setToolTip_(localize('tooltip_search_input'))
                return
            
            # 執行字符驗證
            from ..core.input_recognition import InputRecognitionService, VisualFeedbackService
            validation_result = InputRecognitionService.validate_glyph_input(current_text)
            
            # 套用視覺標注（紅色底線標記無效字符）
            VisualFeedbackService.apply_visual_feedback(self, validation_result)
            
            # 更新工具提示
            if validation_result['valid']:
                valid_count = len(validation_result['valid_glyphs'])
                if valid_count > 0:
                    self.setToolTip_(f"搜尋文字：{valid_count} 個有效字符")
                else:
                    self.setToolTip_(localize('tooltip_search_input'))
            else:
                valid_count = len(validation_result['valid_glyphs'])
                invalid_count = len(validation_result['invalid_chars'])
                if valid_count > 0:
                    self.setToolTip_(f"搜尋文字：{valid_count} 個有效字符，{invalid_count} 個無效字符")
                else:
                    self.setToolTip_(f"發現 {invalid_count} 個無效字符")
                
        except Exception:
            print(traceback.format_exc())
    
    def _update_tooltip_with_invalid_chars(self, validation_result):
        """更新工具提示以顯示無效字符資訊（已廢棄，保留相容性）"""
        # 減法重構：移除複雜邏輯，簡化為基本提示
        try:
            self.setToolTip_("搜尋文字已輸入")
        except Exception:
            print(traceback.format_exc())
    
    def stringValue(self):
        """提供與 NSTextField 相容的 stringValue 方法"""
        return self.string()
    
    def setStringValue_(self, value):
        """提供與 NSTextField 相容的 setStringValue 方法"""
        try:
            # 保存當前游標位置
            current_selection = self.selectedRange()
            
            if value:
                self.setString_(value)
            else:
                self.setString_("")
                
            # 恢復游標位置
            self.setSelectedRange_(current_selection)
            
            # 程式化更新後執行視覺標注
            try:
                from ..core.input_recognition import VisualFeedbackService
                VisualFeedbackService.apply_visual_feedback_to_text(self)
            except Exception:
                print(traceback.format_exc())
            
        except Exception:
            print(traceback.format_exc())
    
    def menuForEvent_(self, event):
        """建立並返回搜尋文字框右鍵選單（官方推薦方式）"""
        try:
            from ..core.menu_manager import MenuManager
            return MenuManager.create_text_field_menu(
                self, 
                include_glyph_picker=True, 
                include_tab_actions=True
            )
        except Exception:
            print(traceback.format_exc())
            return None
    
    def pickGlyphAction_(self, sender):
        """字符選擇器 action - 搜尋框特殊的多字符插入邏輯"""
        try:
            from ..core.menu_manager import MenuManager
            
            # 獲取選中的字符列表
            success, selected_glyphs = MenuManager.get_selected_glyphs()
            if success and selected_glyphs:
                # 處理多字符插入
                self._insert_glyphs(selected_glyphs)
                
        except Exception:
            print(traceback.format_exc())
    
    def _insert_glyphs(self, glyphs):
        """插入多個字符到搜尋框（支援選取替換）"""
        try:
            # 將所有字符名稱組合成一個字符串（用空格分隔）
            glyph_names = [glyph.name for glyph in glyphs]
            insert_text = ' '.join(glyph_names)
            
            # 獲取當前選取範圍
            current_range = self.selectedRange()
            
            # 使用 NSTextView 的 insertText: 方法（會自動處理選取替換）
            if hasattr(self, 'insertText_'):
                self.insertText_(insert_text)
            else:
                # 備用方案：手動處理選取和插入
                current_text = self.string()
                new_text = (current_text[:current_range.location] + 
                           insert_text + 
                           current_text[current_range.location + current_range.length:])
                self.setString_(new_text)
                
                # 設定新的游標位置（插入內容的末尾）
                new_cursor_pos = current_range.location + len(insert_text)
                try:
                    self.setSelectedRange_((new_cursor_pos, 0))
                except:
                    pass
            
            # 顯示成功通知
            from ..core.glyphs_service import get_glyphs_service
            glyphs_service = get_glyphs_service()
            
            glyph_count = len(glyphs)
            if glyph_count == 1:
                glyphs_service.show_notification(
                    "九宮格預覽",
                    f"已插入字符：{glyph_names[0]}"
                )
            else:
                glyphs_service.show_notification(
                    "九宮格預覽",
                    f"已插入 {glyph_count} 個字符"
                )
                    
        except Exception:
            print(traceback.format_exc())
    
    def insertGlyphToCurrentTab_(self, sender):
        """插入字符到目前分頁 action - 委派給 MenuManager"""
        try:
            from ..core.menu_manager import MenuManager
            MenuManager.insert_glyph_to_current_tab(self)
        except Exception:
            print(traceback.format_exc())
    
    def openGlyphInNewTab_(self, sender):
        """在新分頁開啟字符 action - 委派給 MenuManager"""
        try:
            from ..core.menu_manager import MenuManager
            MenuManager.open_glyph_in_new_tab(self)
        except Exception:
            print(traceback.format_exc())

    def dealloc(self):
        """解構式"""
        try:
            NSNotificationCenter.defaultCenter().removeObserver_(self)
        except Exception:
            try:
                print(traceback.format_exc())
            except:
                pass
        objc.super(SearchTextView, self).dealloc()

class SearchPanel(NSView):
    """搜尋面板 - 基於原版架構的完整復刻"""
    
    def initWithFrame_plugin_(self, frame, plugin):
        """初始化搜尋面板"""
        self = objc.super(SearchPanel, self).initWithFrame_(frame)
        if self:
            self.plugin = plugin
            self.searchField = None
            self.scrollView = None
            self.setAutoresizingMask_(NSViewWidthSizable | NSViewHeightSizable)
            self._setup_ui()
        return self
    
    def _setup_ui(self):
        """設定介面 - 基於原版設定，使用系統標準設定"""
        bounds = self.bounds()
        
        # 搜尋面板內部邊距（基於原版常數）
        SEARCH_PANEL_INTERNAL_SCROLLVIEW_MARGIN = 5
        vertical_margin = SEARCH_PANEL_INTERNAL_SCROLLVIEW_MARGIN
        horizontal_margin = 0
        
        scrollRect = NSMakeRect(
            horizontal_margin, vertical_margin, 
            bounds.size.width - 2 * horizontal_margin, 
            bounds.size.height - 2 * vertical_margin
        )
        
        # 建立滾動視圖
        from AppKit import NSScrollView
        self.scrollView = NSScrollView.alloc().initWithFrame_(scrollRect)
        self.scrollView.setAutoresizingMask_(NSViewWidthSizable | NSViewHeightSizable)
        
        self.scrollView.setBorderType_(2)  # NSBezelBorder
        self.scrollView.setHasVerticalScroller_(True)
        self.scrollView.setHasHorizontalScroller_(False)
        
        # 自動調整內容邊距
        if hasattr(self.scrollView, 'setAutomaticallyAdjustsContentInsets_'):
            self.scrollView.setAutomaticallyAdjustsContentInsets_(False)
        if hasattr(self.scrollView, 'setContentInsets_'):
            self.scrollView.setContentInsets_((0, 0, 0, 0))
        
        self.scrollView.setFocusRingType_(NSFocusRingTypeDefault)
        self.scrollView.setBackgroundColor_(NSColor.textBackgroundColor())
        
        # 建立文字視圖
        contentSize = self.scrollView.contentSize()
        textViewFrame = NSMakeRect(0, 0, contentSize.width, contentSize.height)
        
        self.searchField = SearchTextView.alloc().initWithFrame_plugin_(
            textViewFrame, self.plugin
        )
        
        self.searchField.setAutoresizingMask_(NSViewWidthSizable | NSViewHeightSizable)
        
        # 設定文字視圖大小調整
        self.searchField.setVerticallyResizable_(True)
        self.searchField.setHorizontallyResizable_(False)
        self.searchField.setMinSize_(NSMakeRect(0, 0, 0, 0).size)
        self.searchField.setMaxSize_(NSMakeRect(0, 0, 1000000, 1000000).size)
        
        if self.searchField.textContainer():
            self.searchField.textContainer().setContainerSize_(
                NSMakeRect(0, 0, contentSize.width, 1000000).size
            )
        
        # 設定檔案視圖
        self.scrollView.setDocumentView_(self.searchField)
        self.addSubview_(self.scrollView)
        
    
    def update_content(self, plugin_state):
        """更新搜尋欄位內容（程式化更新 + 減法重構：狀態檢查）"""
        try:
            if hasattr(plugin_state, 'lastInput') and self.searchField:
                input_value = plugin_state.lastInput or ""
                
                # 減法重構：檢查是否真的需要更新
                current_value = self.searchField.stringValue()
                if current_value == input_value:
                    return
                
                # 設定程式化更新標記，避免觸發重新生成排列
                self.searchField._programmatic_update = True
                
                try:
                    self.searchField.setStringValue_(input_value)
                finally:
                    # 確保標記被清除
                    self.searchField._programmatic_update = False
                    
        except Exception:
            print(traceback.format_exc())
            # 發生錯誤時也要確保清除標記
            if hasattr(self, 'searchField') and self.searchField:
                self.searchField._programmatic_update = False
    
    def get_search_value(self):
        """取得搜尋欄位的值"""
        if self.searchField:
            return self.searchField.stringValue()
        return ""
    
    def set_search_value(self, value):
        """設定搜尋欄位的值（程式化更新）"""
        if self.searchField:
            # 設定程式化更新標記，避免觸發重新生成排列
            self.searchField._programmatic_update = True
            
            try:
                self.searchField.setStringValue_(value)
            finally:
                # 確保標記被清除
                self.searchField._programmatic_update = False
    
    # 向後相容方法
    def getTextString(self):
        """取得文字內容（向後相容）"""
        return self.get_search_value()
    
    def setTextString_(self, text):
        """設定文字內容（向後相容，使用 Objective-C 命名慣例）"""
        self.set_search_value(text or "")
    
    @property
    def textView(self):
        """提供向後相容的 textView 屬性"""
        return self.searchField
    
    def dealloc(self):
        """解構式"""
        objc.super(SearchPanel, self).dealloc()