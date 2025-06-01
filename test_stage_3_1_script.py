# encoding: utf-8
"""
測試腳本：階段 3-1 - 全局鎖頭按鈕功能
Test Script: Stage 3-1 - Global Lock Button Functionality

在 Glyphs 3 的 Macro 面板中執行此腳本。
Execute this script in Glyphs 3's Macro panel.
"""

import traceback
from GlyphsApp import Glyphs, Message
import time

def run_test():
    """執行階段 3-1 測試"""
    print("=" * 60)
    print("測試階段 3-1：全局鎖頭按鈕功能")
    print("=" * 60)
    
    try:
        # 檢查是否有開啟的字型
        if not Glyphs.font:
            Message("請先開啟一個字型檔案", "測試需要有開啟的字型")
            return
            
        # 取得外掛實例
        plugin = None
        for p in Glyphs.plugins:
            if hasattr(p, '__class__') and p.__class__.__name__ == 'NineBoxView':
                plugin = p
                break
                
        if not plugin:
            Message("找不到 Nine Box View 外掛", "請確認外掛已正確安裝")
            return
            
        print("\n1. 檢查外掛初始狀態")
        print("-" * 40)
        
        # 檢查視窗控制器
        if hasattr(plugin, 'windowController') and plugin.windowController:
            window_controller = plugin.windowController
            print("✓ 視窗控制器存在")
            
            # 檢查控制面板
            if hasattr(window_controller, 'controlsPanelView'):
                controls_panel = window_controller.controlsPanelView
                if controls_panel:
                    print("✓ 控制面板視圖存在")
                    
                    # 檢查鎖頭按鈕
                    if hasattr(controls_panel, 'lockButton'):
                        lock_button = controls_panel.lockButton
                        if lock_button:
                            print("✓ 鎖頭按鈕存在")
                            
                            # 檢查初始狀態
                            is_in_clear_mode = getattr(controls_panel, 'isInClearMode', None)
                            print(f"  - isInClearMode: {is_in_clear_mode}")
                            print(f"  - 預期: False (上鎖狀態)")
                            
                            if is_in_clear_mode == False:
                                print("✓ 初始狀態正確（預設為上鎖）")
                            else:
                                print("✗ 初始狀態錯誤（應該預設為上鎖）")
                                
                            # 檢查按鈕顯示
                            button_title = lock_button.title()
                            button_state = lock_button.state()
                            print(f"  - 按鈕文字: '{button_title}'")
                            print(f"  - 按鈕狀態: {button_state}")
                            
                            if button_title == "🔒":
                                print("✓ 按鈕顯示正確的鎖定圖示")
                            else:
                                print("✗ 按鈕未顯示正確的圖示")
                        else:
                            print("✗ 鎖頭按鈕不存在")
                    else:
                        print("✗ 控制面板沒有 lockButton 屬性")
                else:
                    print("✗ 控制面板視圖為 None")
            else:
                print("✗ 視窗控制器沒有 controlsPanelView 屬性")
        else:
            print("✗ 視窗控制器不存在，請先開啟 Nine Box View 視窗")
            Message("請先開啟 Nine Box View 視窗", "從選單選擇 Window > Nine Box Preview")
            return
            
        print("\n2. 測試鎖定輸入")
        print("-" * 40)
        
        # 在搜尋欄位輸入一些字符
        if hasattr(controls_panel, 'searchField'):
            search_field = controls_panel.searchField
            test_input = "ABCDEFGH"
            search_field.setStringValue_(test_input)
            
            # 觸發搜尋功能
            if hasattr(plugin, 'searchFieldCallback'):
                plugin.searchFieldCallback(search_field)
                print(f"✓ 已輸入測試字符: {test_input}")
                
                # 等待更新
                time.sleep(0.1)
                
                # 檢查是否生成了排列
                if hasattr(plugin, 'currentArrangement'):
                    arrangement = plugin.currentArrangement
                    print(f"✓ 當前排列: {arrangement}")
                else:
                    print("✗ 無法取得當前排列")
            else:
                print("✗ 外掛沒有 searchFieldCallback 方法")
        else:
            print("✗ 控制面板沒有搜尋欄位")
            
        print("\n3. 測試鎖定字符輸入")
        print("-" * 40)
        
        # 在某個鎖定輸入框中輸入字符
        if hasattr(controls_panel, 'lockFields'):
            lock_fields = controls_panel.lockFields
            if len(lock_fields) > 0:
                # 在位置 0 輸入 'X'
                field_0 = lock_fields.get(0)
                if field_0:
                    field_0.setStringValue_("X")
                    
                    # 觸發智能鎖定
                    if hasattr(plugin, 'smartLockCharacterCallback'):
                        plugin.smartLockCharacterCallback(field_0)
                        print("✓ 已在位置 0 輸入 'X'")
                        
                        # 檢查鎖定字符
                        if hasattr(plugin, 'lockedChars'):
                            locked = plugin.lockedChars.get(0)
                            print(f"  - 位置 0 的鎖定字符: '{locked}'")
                            if locked == "X":
                                print("✓ 鎖定字符正確儲存")
                            else:
                                print("✗ 鎖定字符未正確儲存")
                        else:
                            print("✗ 外掛沒有 lockedChars 屬性")
                    else:
                        print("✗ 外掛沒有 smartLockCharacterCallback 方法")
                else:
                    print("✗ 找不到位置 0 的鎖定輸入框")
            else:
                print("✗ 沒有鎖定輸入框")
        else:
            print("✗ 控制面板沒有 lockFields 屬性")
            
        print("\n" + "=" * 60)
        print("測試說明：")
        print("1. 檢查鎖頭按鈕是否顯示在九宮格中央")
        print("2. 確認按鈕顯示為 🔒（上鎖）圖示")
        print("3. 點擊按鈕，應該切換為 🔓（解鎖）圖示")
        print("4. 再次點擊，應該切換回 🔒（上鎖）圖示")
        print("5. 觀察每次切換時，預覽畫面是否立即重繪")
        print("6. 在上鎖狀態下，位置 0 應該顯示 'X'")
        print("7. 在解鎖狀態下，位置 0 的 'X' 應該不受鎖定影響")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n錯誤：{e}")
        print(traceback.format_exc())

# 執行測試
if __name__ == "__main__":
    run_test()
