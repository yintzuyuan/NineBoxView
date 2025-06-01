# encoding: utf-8
"""
階段 3-2 測試腳本
測試清空所有欄位按鈕功能
"""

import traceback
from GlyphsApp import Glyphs

def test_stage_3_2():
    """測試階段 3-2 的功能"""
    print("\n" + "="*50)
    print("開始測試階段 3-2：清空所有欄位按鈕")
    print("="*50)
    
    try:
        # 1. 檢查外掛是否載入
        print("\n1. 檢查外掛載入狀態...")
        plugin = None
        for p in Glyphs.plugins:
            if hasattr(p, '__class__') and p.__class__.__name__ == 'NineBoxView':
                plugin = p
                break
        
        if not plugin:
            print("❌ 錯誤：Nine Box View 外掛未載入")
            return False
        print("✅ 外掛已載入")
        
        # 2. 檢查視窗控制器
        print("\n2. 檢查視窗控制器...")
        if not hasattr(plugin, 'windowController') or not plugin.windowController:
            print("❌ 視窗未開啟，請先開啟 Nine Box Preview 視窗")
            return False
        print("✅ 視窗控制器存在")
        
        # 3. 檢查控制面板
        print("\n3. 檢查控制面板...")
        controls_panel = plugin.windowController.controlsPanelView
        if not controls_panel:
            print("❌ 控制面板不存在")
            return False
        print("✅ 控制面板存在")
        
        # 4. 檢查清空按鈕
        print("\n4. 檢查清空按鈕...")
        if not hasattr(controls_panel, 'clearAllButton'):
            print("❌ 清空按鈕不存在")
            return False
        
        clear_button = controls_panel.clearAllButton
        print(f"✅ 清空按鈕存在")
        print(f"   - 標題: {clear_button.title()}")
        print(f"   - 提示: {clear_button.toolTip()}")
        print(f"   - 動作: {clear_button.action()}")
        
        # 5. 測試準備：設定測試資料
        print("\n5. 準備測試資料...")
        # 設定搜尋欄位
        test_input = "ABCDEFGHIJKLMNOP"
        controls_panel.searchField.setStringValue_(test_input)
        plugin.searchFieldCallback(controls_panel.searchField)
        print(f"   - 已設定搜尋欄位: {test_input}")
        
        # 設定鎖定字符
        test_locked_chars = {
            0: "X",
            3: "Y", 
            7: "Z"
        }
        
        for position, char in test_locked_chars.items():
            if position in controls_panel.lockFields:
                controls_panel.lockFields[position].setStringValue_(char)
                # 手動觸發 callback
                plugin.smartLockCharacterCallback(controls_panel.lockFields[position])
        
        print(f"   - 已設定鎖定字符: {test_locked_chars}")
        
        # 6. 測試上鎖狀態下的清空
        print("\n6. 測試上鎖狀態下的清空功能...")
        # 確保在上鎖狀態
        if controls_panel.isInClearMode:
            controls_panel.toggleLockMode_(None)
        
        print(f"   - 當前鎖頭狀態: {'🔓 解鎖' if controls_panel.isInClearMode else '🔒 上鎖'}")
        print(f"   - 清空前 lockedChars: {plugin.lockedChars}")
        
        # 執行清空
        controls_panel.clearAllFields_(None)
        
        # 檢查結果
        all_empty = True
        for position, field in controls_panel.lockFields.items():
            if field.stringValue():
                all_empty = False
                print(f"   ❌ 位置 {position} 未清空: {field.stringValue()}")
        
        if all_empty:
            print("   ✅ 所有輸入框已清空")
        
        if plugin.lockedChars:
            print(f"   ❌ lockedChars 未清空: {plugin.lockedChars}")
        else:
            print("   ✅ lockedChars 已清空")
        
        # 7. 測試解鎖狀態下的清空
        print("\n7. 測試解鎖狀態下的清空功能...")
        # 重新設定測試資料
        for position, char in test_locked_chars.items():
            if position in controls_panel.lockFields:
                controls_panel.lockFields[position].setStringValue_(char)
        
        # 切換到解鎖狀態
        if not controls_panel.isInClearMode:
            controls_panel.toggleLockMode_(None)
        
        print(f"   - 當前鎖頭狀態: {'🔓 解鎖' if controls_panel.isInClearMode else '🔒 上鎖'}")
        
        # 執行清空
        controls_panel.clearAllFields_(None)
        
        # 檢查結果
        all_empty = True
        for position, field in controls_panel.lockFields.items():
            if field.stringValue():
                all_empty = False
                print(f"   ❌ 位置 {position} 未清空: {field.stringValue()}")
        
        if all_empty:
            print("   ✅ 所有輸入框已清空（解鎖狀態）")
        
        # 8. 檢查搜尋欄位
        print("\n8. 檢查搜尋欄位...")
        search_value = controls_panel.searchField.stringValue()
        if search_value == test_input:
            print(f"   ✅ 搜尋欄位未受影響: {search_value}")
        else:
            print(f"   ❌ 搜尋欄位被意外修改: {search_value}")
        
        print("\n" + "="*50)
        print("✅ 階段 3-2 測試完成！")
        print("="*50)
        return True
        
    except Exception as e:
        print(f"\n❌ 測試過程中發生錯誤: {e}")
        print(traceback.format_exc())
        return False

# 執行測試
if __name__ == "__main__":
    test_stage_3_2()
