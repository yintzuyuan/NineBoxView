# 視窗位置記憶功能修正

## 問題描述
目前的九宮格預覽外掛只有記憶視窗的長寬尺寸，但沒有記憶視窗在螢幕中的位置。每次重新開啟視窗時，視窗都會回到預設位置，而不是上次關閉時的位置。

## 更新：發現第二個問題
Glyphs.defaults 返回的視窗位置是 Objective-C 的 NSArray 類型，而不是 Python 的 list 或 tuple。原本的程式碼使用 `isinstance(window_pos, (list, tuple))` 檢查，導致 NSArray 類型無法通過檢查。

## 修正內容

### 1. 統一資料格式 (utils.py)
- **問題**：視窗位置的儲存和載入格式不一致，導致位置無法正確恢復
- **修正**：
  - 統一使用 Python list 格式 `[x, y]` 儲存和載入視窗位置
  - 在 `load_preferences` 函數中支援從 list 格式載入
  - 向後相容舊的 dict 格式 `{'x': x, 'y': y}`
  - 在 `save_preferences` 函數中統一使用 list 格式儲存
  - 增加詳細的除錯日誌以便追蹤問題

### 2. 修正視窗控制器 (window_controller.py)
- **問題**：載入的視窗位置沒有被正確套用
- **修正**：
  - 移除對 NSArray 類型的不必要檢查
  - 在 `initWithPlugin_` 方法中正確套用載入的視窗位置
  - 在 `makeKeyAndOrderFront` 方法中確保視窗位置被恢復
  - 在 `windowDidMove_` 方法中正確儲存視窗位置到偏好設定

### 3. 處理 NSArray 類型 (utils.py 和 window_controller.py)
- **問題**：Glyphs.defaults 返回的是 Objective-C 的 NSArray，不是 Python 的 list/tuple
- **修正**：
  - 不使用 `isinstance()` 檢查類型
  - 直接嘗試使用 `len()` 和索引存取（NSArray 支援這些操作）
  - 使用 try-except 處理可能的錯誤
  - 同時修正 utils.py 的 `load_preferences` 和 window_controller.py 的相關檢查

### 4. 修正初始化流程 (plugin.py)
- **重要修正**：修正了 `_initialize_properties` 中的初始化順序
- 之前的問題：載入偏好設定後又將 `windowPosition` 設為 `None`，覆蓋了載入的值
- 現在的做法：先設定預設值，再載入偏好設定，確保載入的視窗位置不會被覆蓋

### 5. 更新技術文件 (tsd.mdc)
- 記錄了這次修正的內容
- 文件版本從 1.16 更新到 1.17

### 6. 開啟除錯模式 (constants.py)
- 將 DEBUG_MODE 設為 True，以便查看詳細的載入和儲存日誌
- 建議在測試完成後將其改回 False

## 主要問題原因
1. **初始化順序問題**：`plugin.py` 的 `_initialize_properties` 方法中，載入偏好設定後又重新初始化了 `windowPosition = None`，導致剛載入的視窗位置被覆蓋成 None。

2. **NSArray 類型問題**：Glyphs.defaults 返回的是 Objective-C 的 NSArray 類型，原本的 `isinstance(window_pos, (list, tuple))` 檢查無法處理這種類型。

## 測試方法
1. 開啟九宮格預覽視窗
2. 將視窗移動到螢幕的特定位置
3. 關閉視窗
4. 重新開啟視窗
5. 視窗應該出現在上次關閉時的位置
6. 檢查 Macro 視窗的除錯日誌，確認 windowPosition 正確載入

## 相容性
- 新的程式碼向後相容舊的偏好設定格式
- 如果偏好設定中存有舊格式的視窗位置（字典格式），仍然可以正確載入
- 儲存時會自動轉換為新的 list 格式

## 修正完成
這個修正解決了兩個主要問題：
1. 初始化順序問題導致視窗位置被覆蓋
2. NSArray 類型無法通過 isinstance 檢查的問題

現在外掛能夠記憶視窗的完整狀態（包括尺寸和位置），提供更好的使用體驗。所有修改都保持向後相容，不會影響現有使用者的設定。

## 測試工具
- `test_nsarray_handling.py` - 測試 NSArray 處理的腳本
- `test_window_position_complete.py` - 完整的視窗位置測試
- `toggle_debug_mode.py` - 快速切換除錯模式
