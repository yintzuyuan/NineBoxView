# encoding: utf-8

###########################################################################################################
#
#
# General Plugin
#
# Read the docs:
# https://github.com/schriftgestalt/GlyphsSDK/tree/master/Python%20Templates/General%20Plugin
#
#
###########################################################################################################

from __future__ import division, print_function, unicode_literals
import objc
import traceback
from GlyphsApp import Glyphs, WINDOW_MENU, DOCUMENTACTIVATED, DOCUMENTOPENED, UPDATEINTERFACE, DOCUMENTWILLCLOSE
from GlyphsApp.plugins import GeneralPlugin
from AppKit import NSMenuItem

class NineBoxView(GeneralPlugin):
    """九宮格預覽外掛"""
    
    @objc.python_method
    def settings(self):
        """設定外掛基本資訊 (ReporterPlugin 模式)"""
        # ReporterPlugin 使用 menuName 而非 name
        self.name = Glyphs.localize({
            'en': u'NineBoxView',
            'zh-Hant': u'九宮格預覽',
            'zh-Hans': u'九宫格预览',
            'ja': u'九マスビュー',
            'ko': u'나인박스뷰',
        })
        
        # 主控制器（延遲載入）
        self.controller = None
        self.window_controller = None


    @objc.python_method
    def start(self):
        """啟動外掛並註冊選單"""
        newMenuItem = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(self.name, self.showWindow_, "")
        newMenuItem.setTarget_(self)
        Glyphs.menu[WINDOW_MENU].append(newMenuItem)
    
    def showWindow_(self, sender):
        """顯示視窗（官方標準模式）"""
        # 建立控制器（如果尚未建立）
        if self.controller is None:
            from NineBoxViewController import NineBoxViewController
            self.controller = NineBoxViewController(parent_plugin=self)
        
        # 切換視窗顯示（新架構：純入口點職責）
        self._toggle_window()
        
        # 拆分事件註冊：Plugin 作為唯一的 Glyphs 事件入口點
        Glyphs.addCallback(self.update_plugin, UPDATEINTERFACE)
        Glyphs.addCallback(self.handle_document_activated, DOCUMENTACTIVATED)  
        Glyphs.addCallback(self.handle_document_opened, DOCUMENTOPENED)
        Glyphs.addCallback(self.handle_document_will_close, DOCUMENTWILLCLOSE)
        
        # 立即更新一次
        self.update_plugin(None)
    
    @objc.python_method
    def create_window_for_controller(self, controller):
        """為控制器建立視窗（依賴注入模式）
        
        Args:
            controller: 要綁定的控制器實例
            
        Returns:
            NineBoxWindow: 視窗控制器實例
        """
        try:
            from NineBoxViewWindow import NineBoxWindow
            return NineBoxWindow.alloc().initWithPlugin_(controller)
        except Exception:
            print(traceback.format_exc())
            return None
    
    @objc.python_method
    def _toggle_window(self):
        """切換視窗顯示狀態（純視窗管理職責）"""
        try:
            if self.window_controller is None:
                # 委派給控制器請求建立視窗
                self.window_controller = self.controller.request_window_creation()
                if self.window_controller is None:
                    return
            
            # 顯示視窗
            if self.window_controller is not None:
                self.window_controller.makeKeyAndOrderFront()
                
        except Exception:
            print(traceback.format_exc())

    @objc.python_method 
    def cleanup_window_controller(self):
        """清理視窗控制器引用（由視窗層呼叫）"""
        self.window_controller = None
    
    @objc.python_method
    def has_active_preview_window(self):
        """檢查是否有活躍的預覽視窗（抽象視窗介面實作）
        
        Returns:
            bool: True 如果有活躍的預覽視窗
        """
        try:
            if (self.window_controller and 
                hasattr(self.window_controller, 'previewView') and
                self.window_controller.previewView):
                return True
            return False
        except Exception:
            print(traceback.format_exc())
            return False
    
    @objc.python_method
    def update_preview_arrangement(self, arrangement):
        """更新預覽排列（抽象視窗介面實作）
        
        Args:
            arrangement: 要更新的排列資料
            
        Returns:
            bool: True 如果更新成功
        """
        try:
            if self.has_active_preview_window():
                self.window_controller.previewView.currentArrangement = arrangement
                return True
            return False
        except Exception:
            print(traceback.format_exc())
            return False
    
    @objc.python_method
    def trigger_preview_redraw(self, use_refresh=False):
        """觸發預覽重繪（抽象視窗介面實作）
        
        Args:
            use_refresh: True 使用完整重繪， False 使用快速重繪
            
        Returns:
            bool: True 如果重繪成功
        """
        try:
            if self.has_active_preview_window():
                preview_view = self.window_controller.previewView
                if use_refresh and hasattr(preview_view, 'refresh'):
                    preview_view.refresh()  # 清除快取的完整重繪
                else:
                    preview_view.setNeedsDisplay_(True)
                return True
            return False
        except Exception:
            print(traceback.format_exc())
            return False
    
    @objc.python_method
    def update_plugin(self, sender):
        """UPDATEINTERFACE 處理方法（只處理檔案內即時操作）"""
        try:
            # 檢查控制器是否存在
            if self.controller:
                # 委派給控制器的即時介面更新（檔案內操作）
                self.controller.update_interface(sender)
                    
        except Exception:
            print(traceback.format_exc())
        
        # 避免未使用參數警告
        _ = sender
    
    @objc.python_method
    def handle_document_opened(self, sender):
        """處理文件開啟事件（DOCUMENTOPENED）"""
        try:
            # 檢查控制器是否存在
            if self.controller:
                # 委派給控制器的文件開啟處理
                self.controller.handle_document_opened(sender)
                    
        except Exception:
            print(traceback.format_exc())
        
        # 避免未使用參數警告
        _ = sender

    @objc.python_method
    def handle_document_activated(self, sender):
        """處理文件啟動事件（DOCUMENTACTIVATED）"""
        try:
            # 檢查控制器是否存在
            if self.controller:
                # 委派給控制器的文件啟動處理
                self.controller.handle_document_activated(sender)
                    
        except Exception:
            print(traceback.format_exc())
        
        # 避免未使用參數警告
        _ = sender

    @objc.python_method
    def handle_document_will_close(self, sender):
        """處理文件即將關閉事件（DOCUMENTWILLCLOSE）"""
        try:
            # 檢查控制器是否存在
            if self.controller:
                # 委派給控制器的文件關閉處理
                self.controller.handle_document_will_close(sender)
                    
        except Exception:
            print(traceback.format_exc())
        
        # 避免未使用參數警告
        _ = sender

    @objc.python_method
    def __file__(self):
        """Please leave this method unchanged"""
        return __file__
