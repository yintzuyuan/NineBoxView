# 九宮格預覽 | Nine Box Preview

[繁體中文](#繁體中文) | [English](#english)

![九宮格預覽視窗](NineBoxView_image1.png "九宮格預覽")

---

## 繁體中文

這是一個為 [Glyphs 字型編輯軟體](http://glyphsapp.com/) 開發的外掛，專為字型設計師提供即時預覽功能。
透過 Python 實作，利用 NSView 的子類別實現繪製功能。
此工具讓設計師能同時預覽字符在不同環境下的搭配效果。

### 主要功能

- 即時顯示正在編輯的字符
- 支援自訂周圍參考字符
- 提供明亮／黑暗兩種顯示模式
- 點擊預覽區重新隨機排列參考字符
- 使用純黑白色彩呈現字符，增強對比度
- 多國語言支援

## 使用方法

1. 從「視窗」選單中開啟「九宮格預覽」外掛。
2. 預覽畫面中央會顯示目前正在編輯的字符。
3. 使用下方的輸入框可同時修改顯示在周圍的參考字。
4. 點擊右下方 🌙/☀️ 按鈕可切換明亮／黑暗顯示模式。
5. 點擊預覽畫面可重新隨機排列周圍字符。
6. 使用字符選擇器按鈕 🔣 可快速選擇參考字符。

### 安裝方式

1. 從「視窗」選單開啟「外掛程式管理員」。
2. 找到「九宮格預覽」並點擊「安裝」按鈕。
3. 重新啟動 Glyphs 即可使用。

### 系統需求

此外掛在 Glyphs 3.2.3 版本中測試通過。字符選擇器功能需要 Glyphs 3.2 或更高版本。

### 回饋與建議

如果你在使用過程中發現任何問題或有改進建議，歡迎透過 [GitHub Issues](https://github.com/yintzuyuan/NineBoxView/issues) 回報。

### 致謝

特別感謝 Aaron Bell 的 [RotateView](https://github.com/aaronbell/RotateView) 外掛，讓我了解如何使用 NSView 子類別實現即時預覽。
也要感謝大曲都市的 [Waterfall](https://github.com/Tosche/Waterfall) 外掛，啟發了我如何實作 UI 互動功能。

這次的改版要特別感謝 AI 輔助工具，它幫助我解決了許多有關 Objective-C 橋接和 Cocoa 框架的技術問題。

最後，感謝所有使用這個外掛並提供回饋的設計師們。
你們的意見幫助我持續優化程式碼架構和使用體驗。

### 版權聲明

此外掛由殷慈遠於 2023 年 1 月首次發布，並於 2025 年持續更新。
本專案採用 Apache License 2.0 授權。源碼開放於 GitHub，詳細授權條款請參閱專案中的 LICENSE 文件。

---

## English

This is a plugin developed for [Glyphs font editing software](http://glyphsapp.com/), providing real-time preview functionality for font designers. Implemented using Python, it utilizes an NSView subclass for drawing functionality. This tool allows designers to preview character combinations in different contexts simultaneously.

### Main Features

- Real-time display of the character being edited
- Support for customizing surrounding reference characters
- Light/Dark display modes
- Click preview area to randomly rearrange reference characters
- Pure black and white color scheme for maximum contrast
- Multi-language support

### How to Use

1. Open the "Nine Box Preview" plugin from the "Window" menu.
2. The preview screen will display the character currently being edited in the center.
3. Use the input box at the bottom to modify the reference characters displayed around.
4. Click the 🌙/☀️ button in the lower right to switch between Light/Dark display modes.
5. Click the preview area to randomly rearrange surrounding characters.
6. Use the Glyph Picker button 🔣 to quickly select reference characters.

### Installation

1. Open the "Plugin Manager" from the "Window" menu.
2. Find "Nine Box Preview" and click the "Install" button.
3. Restart Glyphs to use the plugin.

### System Requirements

This plugin has been tested on Glyphs 3.2.3. The Glyph Picker feature requires Glyphs 3.2 or higher.

### Feedback and Suggestions

If you encounter any issues or have suggestions for improvement while using the plugin, please report them via [GitHub Issues](https://github.com/yintzuyuan/NineBoxView/issues).

### Acknowledgements

Special thanks to Aaron Bell's [RotateView](https://github.com/aaronbell/RotateView) plugin, which helped me understand how to implement real-time preview using NSView subclasses. Also thanks to Toshi Omagari's [Waterfall](https://github.com/Tosche/Waterfall) plugin, which inspired me on how to implement UI interaction functionality.

### Copyright Notice

This plugin was first released by Tzuyuan Yin in January 2023 and has been continuously updated throughout 2025. This project is licensed under the Apache License 2.0. The source code is open on GitHub, for detailed license terms please refer to the LICENSE file in the project.
