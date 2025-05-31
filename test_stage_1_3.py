# encoding: utf-8
"""
階段 1.3 測試腳本
用於測試視窗交互狀態功能
"""

from __future__ import division, print_function, unicode_literals
import time
from GlyphsApp import Glyphs

def test_stage_1_3():
    """測試階段 1.3 功能"""
    print("=== 開始測試階段 1.3：視窗交互狀態 ===\n")
    
    # 檢查是否有開啟的字型
    if not Glyphs.font:
        print("❌ 錯誤：請先開啟一個字型檔案")
        return
    
    print("✅ 已檢測到開啟的字型：%s" % Glyphs.font.familyName)
    
    # 嘗試開啟外掛視窗
    print("\n1. 測試外掛載入...")
    try:
        # 觸發外掛選單動作
        print("   請從選單選擇 Window > Nine Box Preview 開啟外掛")
        print("   等待外掛視窗開啟...")
        
        # 給使用者時間開啟外掛
        time.sleep(3)
        
        print("\n2. 視窗交互測試指示：")
        print("   a) 調整主視窗大小：")
        print("      - 拖動視窗邊緣或角落調整大小")
        print("      - 觀察預覽區域是否正確填滿視窗")
        print("      - 觀察控制面板高度是否同步調整")
        print("      - 觀察控制面板寬度是否保持固定")
        
        print("\n   b) 移動主視窗：")
        print("      - 拖動視窗標題列移動視窗")
        print("      - 觀察控制面板是否跟隨移動")
        print("      - 觀察控制面板是否保持在右側固定距離")
        
        print("\n   c) 極端測試：")
        print("      - 將視窗調整到最小尺寸")
        print("      - 將視窗調整到最大尺寸")
        print("      - 快速連續調整視窗大小")
        print("      - 檢查是否有錯誤或異常")
        
        print("\n3. 檢查控制台輸出：")
        print("   觀察 Macro 面板中的除錯訊息，應該看到：")
        print("   - [階段1.3] 視窗調整：寬x高")
        print("   - [階段1.3] 預覽視圖框架變更")
        print("   - [階段1.3] 控制面板框架變更")
        print("   - [階段1.3] 主視窗移動到：(x, y)")
        
        print("\n4. 持久化測試：")
        print("   a) 調整視窗到特定大小")
        print("   b) 關閉外掛視窗")
        print("   c) 重新開啟外掛")
        print("   d) 確認視窗大小被正確恢復")
        
    except Exception as e:
        print("❌ 錯誤：%s" % str(e))
        import traceback
        traceback.print_exc()
    
    print("\n=== 測試結束 ===")
    print("如果所有功能都正常運作，階段 1.3 驗收完成！")

# 執行測試
if __name__ == "__main__":
    test_stage_1_3()
