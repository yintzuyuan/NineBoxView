# 九宮格預覽 | Nine Box Preview

[繁體中文](#繁體中文) | [English](#english)

![九宮格預覽視窗](NineBoxView_image1.png "九宮格預覽")

---

## 繁體中文
**(v3.0.0 - 2025 年 6 月更新)**

這是一個為 [Glyphs 字型編輯軟體](http://glyphsapp.com/) 開發的外掛，專為字型設計師提供即時預覽功能。透過 Python、Objective-C 和 AppKit 框架實作，利用 NSView 的子類別實現繪製功能。此工具讓設計師能同時預覽字符在不同環境下的搭配效果。

第三版 (v3.0.0) 進行了大幅重構，引入了可收合的獨立控制面板、參考字符鎖定以及更緊密整合 Glyphs 原生功能的設計，旨在提供更專注、更高效的預覽體驗。

### 主要功能

- 即時顯示正在編輯的字符
- 透過獨立控制面板設定上下文參考字符
    - 支援批量輸入字符或 Nice Name
    - 可鎖定特定位置的參考字符
- 自動適應 Glyphs 預覽區的明暗主題
- 點擊預覽區重新隨機排列未鎖定的參考字符
- 整合 Glyphs 官方字符選擇器 (PickGlyphs API)
- 可調整預覽縮放比例
- 多國語言支援

## 使用方法

1. 從「視窗」選單中開啟「九宮格預覽」外掛。
2. 預覽畫面中央會顯示目前正在編輯的字符。
3. 點擊主視窗標題列的「⚙」按鈕可開關獨立的控制面板。
4. 在控制面板中：
    - 使用「批量輸入」文字框輸入多個參考字符 (以空格分隔)。
    - 使用 8 個鎖定輸入框為特定位置指定固定字符。
    - 點擊鎖頭圖示 (🔒/🔓) 切換鎖定模式。鎖定模式下，鎖定框字符固定；解鎖模式下，所有字符參與隨機排列。
    - 點擊「清空鎖定」按鈕清除所有鎖定框內容。
    - 右鍵點擊「批量輸入」框可使用官方字符選擇器 (🔣)。
5. 點擊預覽畫面可重新隨機排列周圍未鎖定的字符。
6. 預覽的明暗模式會自動跟隨 Glyphs 預覽區的設定。
7. 可縮放主預覽視窗，內容會相應調整。

### 安裝方式

1. 從「視窗」選單開啟「外掛程式管理員」。
2. 找到「九宮格預覽」並點擊「安裝」按鈕。
3. 重新啟動 Glyphs 即可使用。
<!-- 🌿 注意：v3.0.0 版本已移除對 Vanilla 模組的依賴。 -->

### 系統需求

此外掛在 Glyphs 3.2.3 版本或更高版本中測試通過。部分功能 (如官方字符選擇器 PickGlyphs API) 需要 Glyphs 3.2 或更高版本。

### 技術特點與改進

九宮格預覽 v3.0.0 版本帶來了全面的架構重構與功能升級，專注於提升使用體驗和效能：

- **原生 UI 實現：** 移除了對外部 Vanilla 模組的依賴，完全採用 macOS 原生 Cocoa 框架 (Objective-C 橋接) 和 Glyphs API 構建介面，提升了穩定性與整合度。
- **模듈化架構：** 程式碼被重構為多個獨立模組 (`plugin.py`, `window_controller.py`, `preview_view.py`, `controls_panel_view.py`, `search_panel.py`, `lock_fields_panel.py`, `event_handlers.py`, `utils.py`, `constants.py`)，提高了可讀性、可維護性和擴展性。
- **獨立控制面板：**
    - 將所有控制項移至一個可開關的獨立子視窗，主預覽視窗在控制面板隱藏時可提供更沉浸的檢視體驗。
    - 控制面板寬度固定，高度與主視窗同步，無標題列設計，更簡潔。
- **參考字符鎖定：**
    - 新增 8 個獨立輸入框，可將特定字符鎖定在九宮格的周圍位置。
    - 提供鎖定模式切換 (🔒/🔓)，允許在固定參考字和全隨機排列之間選擇。
    - 支援清空所有鎖定和特定情況下的排列回復機制。
- **增強的字符輸入：**
    - 批量輸入框支援多字符或以空格分隔的 Nice Names。
    - 整合 Glyphs 官方 `PickGlyphs()` API，提供原生字符選擇器體驗 (支援搜尋與多選)。
- **智慧主題適應：** 預覽畫面自動偵測並適應 Glyphs 預覽區域的明暗主題，無需手動切換。
- **即時與穩定預覽：**
    - 中央字符隨 Glyphs 編輯、切換字符或選擇圖層即時更新。
    - 預覽佈局基於字身寬度 (`layer.width`)，確保編輯時框架穩定。
    - 支援預覽內容縮放。
- **效能優化：**
    - 採用字符快取 (`_glyph_cache`, `_width_cache`) 提升字符查找與寬度計算速度。
    - 實現繪製節流 (`REDRAW_THRESHOLD`) 和更新請求節流 (`_update_scheduled`)，確保操作流暢。
- **偏好設定增強：** 記住視窗大小、位置、控制面板顯示狀態及所有字符設定。

### 回饋與建議

如果你在使用過程中發現任何問題或有改進建議，歡迎透過 [GitHub Issues](https://github.com/yintzuyuan/NineBoxView/issues) 回報。
所有錯誤回報都使用 `traceback` 模組進行記錄。

### 致謝

特別感謝 Aaron Bell 的 [RotateView](https://github.com/aaronbell/RotateView) 外掛，讓我了解如何使用 NSView 子類別實現即時預覽。
也要感謝大曲都市的 [Waterfall](https://github.com/Tosche/Waterfall) 外掛，啟發了我如何實作 UI 互動功能。

此次 v3.0.0 的大規模重構，深度依賴 AI 輔助工具進行程式碼撰寫、架構設計與 Objective-C 橋接等技術難點攻克。透過產品需求 (PRD)、技術規格 (TSD) 等文件與 AI 協作，逐步完成了這個更複雜版本的開發。

同時感謝 Mark2Mark 的 Variable Font Preview 外掛，其 UI 佈局和使用者體驗設計為此版本帶來許多啟發。

最後，感謝所有使用這個外掛並提供回饋的設計師們。
你們的意見幫助我持續優化程式碼架構和使用體驗。

### 版權聲明

此外掛由殷慈遠於 2023 年 1 月首次發布，並於 2025 年 6 月進行 v3.0.0 重大更新。
本專案採用 Apache License 2.0 授權。源碼開放於 GitHub，詳細授權條款請參閱專案中的 LICENSE 文件。

---

## English
**(v3.0.0 - Updated June 2025)**

This is a plugin developed for Glyphs font editing software, providing real-time preview functionality for font designers. Implemented using Python, Objective-C, and the AppKit framework, it utilizes an NSView subclass for drawing functionality. This tool allows designers to preview character combinations in different contexts simultaneously.

Version 3.0.0 introduces a significant refactor, featuring a collapsible independent control panel, reference character locking, and tighter integration with Glyphs' native features, aiming for a more focused and efficient preview experience.

### Main Features

- Real-time display of the character being edited
- Configure context reference characters via a separate, toggleable control panel
    - Supports batch input of characters or Nice Names
    - Allows locking reference characters in specific positions
- Automatically adapts to Glyphs' preview area light/dark theme
- Click preview area to randomly rearrange unlocked reference characters
- Integrates Glyphs' official character picker (PickGlyphs API)
- Adjustable preview zoom factor
- Multi-language support

### How to Use

1. Open the "Nine Box Preview" plugin from the "Window" menu.
2. The preview screen will display the character currently being edited in the center.
3. Click the "⚙" (gear) button on the main window's title bar to toggle the separate control panel.
4. In the control panel:
    - Use the "Batch Input" text view to enter multiple reference characters (space-separated).
    - Use the 8 lock input fields to assign fixed characters to specific positions.
    - Click the lock icon (🔒/🔓) to toggle lock mode. In lock mode, locked characters are fixed; in unlock mode, all characters participate in random arrangement.
    - Click the "Clear All Locks" button to clear all lock field contents.
    - Right-click the "Batch Input" field to use the official Glyph Picker (🔣).
5. Click the preview area to randomly rearrange surrounding unlocked characters.
6. The preview's light/dark mode automatically follows Glyphs' preview area settings.
7. The main preview window can be resized, and the content will adjust accordingly.

### Installation

1. Open the "Plugin Manager" from the "Window" menu.
2. Find "Nine Box Preview" and click the "Install" button.
3. Restart Glyphs to use the plugin.

<!-- 🌿 Note: Version 3.0.0 has removed the dependency on the Vanilla module. -->

### System Requirements

This plugin has been tested on Glyphs 3.2.3 or higher. Some features (like the official PickGlyphs API character picker) require Glyphs 3.2 or higher.

### Technical Features and Improvements

Nine Box Preview v3.0.0 brings a comprehensive architectural overhaul and feature upgrade, focusing on enhancing user experience and performance:

- **Native UI Implementation:** Removed dependency on the external Vanilla module. The interface is now built entirely using macOS native Cocoa framework (via Objective-C bridging) and Glyphs API, improving stability and integration.
- **Modular Architecture:** The codebase has been refactored into multiple independent modules (e.g., `plugin.py`, `window_controller.py`, `preview_view.py`, `controls_panel_view.py`), enhancing readability, maintainability, and scalability.
- **Independent Control Panel:**
    - All controls are moved to a separate, toggleable sub-window. Hiding the control panel allows for a more immersive viewing experience in the main preview window.
    - The control panel has a fixed width, synchronized height with the main window, and a titleless design for a cleaner look.
- **Reference Character Locking:**
    - Added 8 individual input fields to lock specific characters in the surrounding positions of the 3x3 grid.
    - Features a lock mode toggle (🔒/🔓), allowing users to choose between fixed reference characters and fully random arrangements.
    - Supports clearing all locks and a mechanism for restoring previous arrangements in certain situations.
- **Enhanced Character Input:**
    - The batch input field supports multiple characters or space-separated Nice Names.
    - Integrates Glyphs' official `PickGlyphs()` API, providing a native character picker experience (with search and multi-select).
- **Smart Theme Adaptation:** The preview automatically detects and adapts to the light/dark theme of Glyphs' preview area, eliminating manual switching.
- **Real-time and Stable Preview:**
    - The central glyph updates in real-time as users edit, switch glyphs, or select layers in Glyphs.
    - The preview layout is based on glyph `layer.width`, ensuring frame stability during editing.
    - Supports zooming of the preview content.
- **Performance Optimizations:**
    - Utilizes glyph caching (`_glyph_cache`, `_width_cache`) to speed up glyph lookup and width calculations.
    - Implements drawing throttling (`REDRAW_THRESHOLD`) and update request throttling (`_update_scheduled`) for smooth operation.
- **Enhanced Preferences:** Remembers window size, position, control panel visibility state, and all character settings.

### Feedback and Suggestions

If you encounter any issues or have suggestions for improvement while using the plugin, please report them via [GitHub Issues](https://github.com/yintzuyuan/NineBoxView/issues). All error reports are logged using the traceback module.

### Acknowledgements
Special thanks to Aaron Bell's [RotateView](https://github.com/aaronbell/RotateView) plugin, which helped me understand how to implement real-time preview using NSView subclasses. Also thanks to Toshi Omagari's [Waterfall](https://github.com/Tosche/Waterfall) plugin, which inspired me on how to implement UI interaction functionality.

The extensive refactoring of v3.0.0 heavily relied on AI-assisted tools for code generation, architectural design, and tackling technical challenges like Objective-C bridging. Collaborating with AI using documents such as Product Requirements (PRD) and Technical Specifications (TSD) was instrumental in progressively developing this more complex version.

Additionally, thanks to Mark2Mark's Variable Font Preview plugin, whose UI layout and user experience design provided much inspiration for this version.

Lastly, thanks to all the designers who use this plugin and provide feedback. Your opinions help me continuously optimize the code structure and user experience.

### Copyright Notice

This plugin was first released by Tzuyuan Yin in January 2023 and underwent a major v3.0.0 update in June 2025. This project is licensed under the Apache License 2.0. The source code is open on GitHub, for detailed license terms please refer to the LICENSE file in the project.
