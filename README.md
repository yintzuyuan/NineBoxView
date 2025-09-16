# 九宮格預覽 | Nine Box Preview

[繁體中文](#繁體中文) | [English](#english)

![九宮格預覽視窗](NineBoxView_image1.png "九宮格預覽")

---

## 繁體中文

這是一個為 [Glyphs 字型編輯軟體](http://glyphsapp.com/) 開發的外掛，專為字型設計師提供即時預覽功能。透過 Python、Objective-C 和 AppKit 框架實作，利用 NSView 的子類別實作繪製功能。此工具讓設計師能同時預覽字符在不同環境下的搭配效果。

第三版經歷了從 v3.0.0 到 v3.3.2 的漸進式發展，從初期的模組化重構，發展至當前的多國語言支援、智慧主題監測和三層即時重繪系統。整個開發歷程跨越兩個儲存庫，結合了社群回饋和 AI 協作開發，旨在提供更專注、更高效、更國際化的預覽體驗。

### 主要功能

#### ⚡ 即時預覽系統

  - **三層即時重繪：** 中央格與周圍格零延遲同步更新
  - **備份圖層支援：** 即時預覽不同版本和主板的字符
  - **[Light Table](https://formkunft.com/light-table/) 整合：** 支援前後版本對照顯示

#### 🗔️ 進階控制功能

  - **智慧字符過濾：** 自動驗證 CJK、Nice Names、Unicode Names
  - **獨立控制面板：** 可收合設計，支援加入參考字符和精確鎖定
  - **右鍵選單增強：** 支援字符選擇器和插入功能

#### 🎨 使用者體驗

  - **視覺回饋系統：** 無效字符標註
  - **響應式佈局：** 九宮格隨視窗大小自動縮放
  - **偏好記憶：** 視窗大小、位置、設定狀態完整保存

## 使用方法

### 基本操作

1.  從「視窗」選單中開啟「九宮格預覽」外掛。
2.  預覽畫面中央會即時顯示目前正在編輯的字符。
3.  點擊主視窗標題列的「⚙」按鈕可開關獨立的控制面板。

### 控制面板功能

4.  在控制面板中：
      - **參考輸入框：** 輸入多個參考字符（以空格分隔），外掛會將其隨機排列於周圍的格子中。支援 CJK、Nice Names、Unicode Names。
      - **鎖定輸入框：** 8 個獨立輸入框，為特定位置指定固定字符。
      - **鎖頭圖示：** 點擊（🔒/🔓）切換鎖定模式。
      - **清空鎖定：** 一鍵清除所有鎖定框內容。
      - **字符選擇器：** 右鍵點擊輸入框使用官方「字符選擇器」，方便加入多個字符。

### 進階特性

5.  **互動重排：** 點擊預覽畫面重新隨機排列未鎖定的字符。
6.  **主題自適應：** 主題自動跟隨當前分頁的預覽區設定。
7.  **縮放支援：** 主預覽視窗可縮放，內容自動適應。
8.  **多語言：** 介面自動跟隨 Glyphs 系統語言設定。

### 安裝方式

1.  從「視窗」選單開啟「外掛程式管理員」。
2.  找到「九宮格預覽」並點擊「安裝」按鈕。
3.  重新啟動 Glyphs 即可使用。

### 系統需求

此外掛在 Glyphs 3.2.3 版本或更高版本中測試通過。部分功能（如官方字符選擇器 PickGlyphs API）需要 Glyphs 3.2 或更高版本。

### 技術特點與改進

九宮格預覽 v3.3.2 經歷了從 v3.0.0 到當前版本的全面演進，專注於使用者體驗、效能和國際化：

#### 🏗️ **借鑑 [DrawBot](https://github.com/schriftgestalt/DrawBotGlyphsPlugin) 模式架構**

  - **高度模組化架構**：程式碼被組織在 15 個專業模組中，採用 Glyphs 官方推薦的架構模式，大幅提升外掛的穩定性與可維護性。
  - **平面座標系統**：採用 0-8 直觀座標管理，替代了原始較為複雜的三層架構。
  - **模組化設計**：Document、Window、UI、Core、Data 模組齊備，職責分離，易於未來擴充。

#### 🌍 **多國語言支援系統重構**

  - **集中化翻譯管理**：將既有的多國語言功能重構成`localization.py` 模組，統一管理所有 UI 文字，使翻譯的擴充與維護更加容易。
  - **5 語言完整支援**：完整支援英文、繁體中文、簡體中文、日文、韓文。
  - **Glyphs API 整合**：使用官方 `Glyphs.localize()` API 實現自動語言切換，無縫接軌軟體環境。

#### ⚡ **三層即時重繪系統**

  - **三層資料架構**：`base_glyphs`（即時）→ `base_arrangement`（參考）→ `lock_inputs`（鎖定），透過清晰的資料覆蓋順序，實現複雜的顯示邏輯。
  - **中央格即時重繪**：當你在 Glyphs 中切換或編輯字符時，中央格能零延遲響應。
  - **完整即時體驗**：中央格與周圍格同步更新，提供流暢的預覽體驗。

#### 🖥️ **分頁層級主題監測**

  - **精準的主題偵測**：修正了以往的全域偵測方式，改為偵測當前編輯分頁的主題設定，確保預覽視窗的顏色與你當下的工作區完全同步。
  - **官方建議**：採用 Glyphs 官方開發者[建議](https://forum.glyphsapp.com/t/inverted-negativebutton-in-preview-panel-vs-preview-area-at-bottom-of-edit-view/7442/2)的 `Font.currentTab.previewView().setBlack_()` API，確保穩定性與相容性。
  - **智慧復原機制**：新增 `theme_detector.py` 實作多層級偵測器，在無法偵測到分頁時能優雅地回復至備用方案。

#### 🔍 **統一字符辨識系統**

  - **InputRecognitionService**：建立統一的服務來處理所有字符輸入，無論是參考輸入框或鎖定框。
  - **完整字符支援**：全面支援 CJK 字元、Nice Names 與 Unicode Names 的辨識。
  - **智慧鎖定輸入**：能夠精準辨識以空格分隔的多個字符或名稱。

#### 🗂️ **獨立控制面板與 UI 增強**

  - **可收合設計**：主預覽視窗可隱藏控制面板，提供沉浸式體驗。
  - **右鍵選單增強**：新增插入字符到分頁、在新分頁開啟等實用功能。
  - **8 個鎖定輸入框**：讓你精確控制九宮格周圍位置的參考字符。
  - **官方字符選擇器**：整合 `PickGlyphs` API，支援搜尋與多選。

#### 📊 **效能與穩定性優化**

  - **Light Table 整合**：支援在 Light Table 外掛的工作模式下，即時預覽前後版本的差異。此外掛具備優雅降級機制，即使未安裝 Light Table 也能正常運作。
  - **備份圖層支援**：可即時預覽不同主板和備份圖層的內容。
  - **減法重構原則**：秉持「統一而非新增」的設計哲學，消除重複的程式碼，提升穩定性。
  - **測試驅動開發（TDD）**：擁有完整的單元測試套件（`test_localization.py` 等），確保每次更新的功能都經過驗證，提供更可靠的使用體驗。

### 回饋與建議

如果你在使用過程中發現任何問題或有改進建議，歡迎透過公開儲存庫回報：

  - **問題回報：** [NineBoxView Issues](https://github.com/yintzuyuan/NineBoxView/issues)

所有錯誤回報都使用 `traceback` 模組進行記錄。

### 致謝

特別感謝 Aaron Bell 的 [RotateView](https://github.com/aaronbell/RotateView) 外掛，讓我了解如何使用 NSView 子類別實作即時預覽。
也要感謝大曲都市的 [Waterfall](https://github.com/Tosche/Waterfall) 外掛，啟發了我如何實作 UI 互動功能。

感謝 Light Table 外掛作者的幫助（相關討論見 [Issue #59](https://github.com/yintzuyuan/NineBoxView/issues/59)），讓九宮格預覽能夠整合 Light Table 的版本比對功能。由於 Light Table 是一個獨立的外掛工具而非 Glyphs 內建功能，本外掛也為此設計了優雅降級（graceful degradation）機制，即使你沒有安裝 Light Table 也能正常使用所有核心功能。

從 v3.0.0 到 v3.3.2 的漸進式發展，深度依賴現代化 AI 協作開發模式。特別是利用 Claude Code 工具進行 TDD 測試驅動開發、程式碼重構和多國語言本地化。整個開發歷程跨越兩個儲存庫（原始版→開發版），結合了社群回饋、官方論壇建議和 AI 輔助的技術實作。

同時感謝 Mark2Mark 的 [Variable Font Preview](https://github.com/Mark2Mark/variable-font-preview) 外掛，其 UI 佈局和使用者體驗設計為此版本帶來許多啟發。

最後，感謝所有使用這個外掛並提供回饋的設計師們。
你們的意見幫助我持續優化程式碼架構和使用體驗。

### 版權聲明

此外掛由殷慈遠於 2023 年 1 月首次發布，經歷 v3.0.0（2025年 6月）到 v3.3.2（2025年 9月）的漸進式發展。

本專案採用 Apache License 2.0 授權。源碼開放於 GitHub，詳細授權條款請參閱專案中的 LICENSE 文件。

---

## English

This is a plugin developed for [Glyphs font editing software](http://glyphsapp.com/), providing real-time preview functionality for font designers. Implemented using Python, Objective-C, and the AppKit framework, it utilizes an NSView subclass for drawing functionality. This tool allows designers to preview character combinations in different contexts simultaneously.

The third version has undergone progressive development from v3.0.0 to v3.3.2, evolving from initial modular refactoring to current multi-language support, intelligent theme detection, and a three-tier real-time redraw system. The entire development process spans two repositories, combining community feedback and AI-collaborative development, aiming to provide a more focused, efficient, and internationalized preview experience.

### Main Features

#### ⚡ Real-time Preview System

  - **Three-tier Real-time Redraw:** Center grid and surrounding grids zero-delay synchronized updates
  - **Backup Layer Support:** Real-time preview of different versions and master layers
  - **[Light Table](https://formkunft.com/light-table/) Integration:** Supports before/after version comparison display

#### 🗔️ Advanced Control Features

  - **Smart Character Filtering:** Automatic validation of CJK, Nice Names, Unicode Names
  - **Independent Control Panel:** Collapsible design, supports adding reference characters and precise locking
  - **Enhanced Right-click Menu:** Supports Glyph Picker and insertion functions

#### 🎨 User Experience

  - **Visual Feedback System:** invalid character annotations
  - **Responsive Layout:** Grid auto-scales with window resizing
  - **Preference Memory:** Complete preservation of window size, position, settings state

### How to Use

#### Basic Operations

1.  Open the "Nine Box Preview" plugin from the "Window" menu.
2.  The preview screen will display the character currently being edited in the center in real-time.
3.  Click the "⚙" button on the main window's title bar to toggle the independent control panel.

#### Control Panel Functions

4.  In the control panel:
      - **Reference Input Field:** Enter multiple reference characters (space-separated), the plugin will randomly arrange them in surrounding grids. Supports CJK, Nice Names, Unicode Names.
      - **Lock Input Fields:** 8 independent input fields to assign fixed characters to specific positions.
      - **Lock Icon:** Click (🔒/🔓) to toggle lock mode.
      - **Clear All Locks:** One-click to clear all lock field contents.
      - **Glyph Picker:** Right-click input fields to use official "Glyph Picker" for convenient multi-character addition.

#### Advanced Features

5.  **Interactive Rearrangement:** Click the preview area to randomly rearrange unlocked glyphs.
6.  **Theme Auto-adaptation:** Theme automatically follows current tab's preview area settings.
7.  **Zoom Support:** Main preview window can be zoomed, content auto-adapts.
8.  **Multi-language:** Interface automatically follows Glyphs system language settings.

### Installation

1.  Open the "Plugin Manager" from the "Window" menu.
2.  Find "Nine Box Preview" and click the "Install" button.
3.  Restart Glyphs to use the plugin.

### System Requirements

This plugin has been tested on Glyphs 3.2.3 or higher. Some features (like the official PickGlyphs API character picker) require Glyphs 3.2 or higher.

### Technical Features and Improvements

Nine Box Preview v3.3.2 has undergone comprehensive evolution from v3.0.0 to the current version, focusing on user experience, performance, and internationalization:

#### 🏗️ **Redesigned [DrawBot](https://github.com/schriftgestalt/DrawBotGlyphsPlugin) Mode Architecture**

  - **Highly Modular Architecture:** Code is organized in 15 professional modules, adopting Glyphs official recommended architectural patterns, significantly improving plugin stability and maintainability.
  - **Flat Coordinate System:** Uses intuitive 0-8 coordinate management, replacing the original more complex three-tier architecture.
  - **Modular Design:** Complete Document, Window, UI, Core, Data modules with separated responsibilities, easy for future expansion.

#### 🌍 **Multi-language Support System Refactoring**

  - **Centralized Translation Management:** Refactored existing multi-language functionality into `localization.py` module, unified management of all UI text, making translation expansion and maintenance easier.
  - **5 Language Complete Support:** Full support for English, Traditional Chinese, Simplified Chinese, Japanese, Korean.
  - **Glyphs API Integration:** Uses official `Glyphs.localize()` API for automatic language switching, seamless integration with software environment.

#### ⚡ **Three-tier Real-time Redraw System**

  - **Three-tier Data Architecture:** `base_glyphs` (real-time) → `base_arrangement` (reference) → `lock_inputs` (locked), achieving complex display logic through clear data overlay sequence.
  - **Center Grid Real-time Redraw:** When you switch or edit glyph in Glyphs, the center grid responds with zero delay.
  - **Complete Real-time Experience:** Center grid and surrounding grids update synchronously, providing smooth preview experience.

#### 🖥️ **Tab-level Theme Detection**

  - **Precise Theme Detection:** Fixed previous global detection method, changed to detect current editing tab's theme settings, ensuring preview window colors are completely synchronized with your current workspace.
  - **Official Recommendation:** Adopts Glyphs official developer [recommended](https://forum.glyphsapp.com/t/inverted-negativebutton-in-preview-panel-vs-preview-area-at-bottom-of-edit-view/7442/2) `Font.currentTab.previewView().setBlack_()` API, ensuring stability and compatibility.
  - **Smart Restoration Mechanism:** Added `theme_detector.py` implementing multi-level detectors, gracefully falling back to backup solutions when unable to detect tabs.

#### 🔍 **Unified Character Recognition System**

  - **InputRecognitionService:** Established unified service to handle all character input, whether reference input fields or lock fields.
  - **Complete Character Support:** Comprehensive support for CJK characters, Nice Names, and Unicode Names recognition.
  - **Smart Lock Input:** Accurately recognizes multiple characters or names separated by spaces.

#### 🗂️ **Independent Control Panel & UI Enhancements**

  - **Collapsible Design:** Main preview window can hide control panel, providing immersive experience.
  - **Enhanced Right-click Menu:** Added practical functions like inserting glyphs to tabs, opening in new tabs.
  - **8 Lock Input Fields:** Precisely control reference glyphs in surrounding positions of the nine-grid.
  - **Official Glyph Picker:** Integrates `PickGlyphs` API, supports search and multi-select.

#### 📊 **Performance and Stability Optimizations**

  - **Light Table Integration:** Supports real-time preview of before/after version differences in Light Table plugin work mode. This plugin has graceful degradation mechanism, functioning normally even without Light Table installed.
  - **Backup Layer Support:** Can preview content from different masters and backup layers in real-time.
  - **Subtraction Refactoring Principle:** Following "unify rather than add" design philosophy, eliminating duplicate code, improving stability.
  - **Test-Driven Development (TDD):** Complete unit test suite (`test_localization.py` etc.), ensuring every update's functionality is verified, providing more reliable user experience.

### Feedback and Suggestions

If you encounter any issues or have suggestions for improvement while using the plugin, please report them via the public repository:

  - **Issue Reports:** [NineBoxView Issues](https://github.com/yintzuyuan/NineBoxView/issues)

All error reports are logged using the `traceback` module.

### Acknowledgements

Special thanks to Aaron Bell's [RotateView](https://github.com/aaronbell/RotateView) plugin, which helped me understand how to implement real-time preview using NSView subclasses.
Also thanks to Toshi Omagari's [Waterfall](https://github.com/Tosche/Waterfall) plugin, which inspired me on how to implement UI interaction functionality.

Thanks to the Light Table plugin author's help (related discussion in [Issue #59](https://github.com/yintzuyuan/NineBoxView/issues/59)), allowing Nine Box Preview to integrate Light Table's version comparison functionality. Since Light Table is an independent plugin tool rather than a built-in Glyphs feature, this plugin is designed with graceful degradation mechanism, functioning normally with all core features even without Light Table installed.

The progressive development from v3.0.0 to v3.3.2 heavily relied on modern AI-collaborative development mode. Particularly utilizing Claude Code tools for TDD test-driven development, code refactoring, and multi-language localization. The entire development process spans two repositories (original version → development version), combining community feedback, official forum suggestions, and AI-assisted technical implementation.

Additionally, thanks to Mark2Mark's [Variable Font Preview](https://github.com/Mark2Mark/variable-font-preview) plugin, whose UI layout and user experience design provided much inspiration for this version.

Lastly, thanks to all the designers who use this plugin and provide feedback.
Your opinions help me continuously optimize the code structure and user experience.

### Copyright Notice

This plugin was first released by Tzuyuan Yin in January 2023, undergoing progressive development from v3.0.0 (June 2025) to v3.3.2 (September 2025).

This project is licensed under the Apache License 2.0. The source code is open on GitHub, for detailed license terms please refer to the LICENSE file in the project.
