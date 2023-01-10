![NineBoxView window](NineBoxView_image1.png "NineBoxView")

# 繁體中文
## 九宮格預覽
這是一個 [字型編輯軟體 Glyphs](http://glyphsapp.com/) 的外掛，用於方塊字製作的即時預覽。有鑒於漢字（東亞方塊字）造型需要同時兼顧直排與橫排，與其不斷切換預覽方式不如同時顯示吧。

## 使用方法
* 從 *視窗* 下拉選單打開 *九宮格預覽* 外掛。
* 預覽畫面的正中央會即時顯示正在編輯的字符。
* 使用上方的輸入框可同時修改所有要顯示在周圍的參考字。
* 使用右上方的按鈕可切換顯示模式（明亮模式 / 黑暗模式）。

## 安裝方式
從 *視窗* 下拉選單打開 *外掛程式管理員* 點擊左側的 *安裝* 按鈕安裝。退出並重新啟動 Glyphs 即可使用。

🌿 九宮格預覽需要使用 *Vanilla* 模組才能使用。透過 *視窗* 下拉選單打開 *外掛程式管理員* 進入 *模組* 分頁進行安裝。

## 版本要求
此外掛在 Glyphs 3 測試。

## 已知問題
此外掛還有一些問題尚待解決，短期內不會修正它們。如果有急需願意提供幫忙歡迎使用 [拉取請求](https://github.com/yintzuyuan/NineBoxView/pulls) 的方式提供協助。
* 字符對齊方式為靠左對齊。因此如果製作的是不等寬字型，將導致主要字與參考字無法居中對齊。
* 輸入框只支援字元輸入，不支援字符名稱（例：uni6771）。私心希望輸入功能類似於 [Kernkraft](https://github.com/bBoxType/Kernkraft) 外掛可以兩者都支援。
* 顯示的字符大小固定，無法跟隨視窗縮放變更大小。
* 在編輯畫面沒有選擇字符的狀況，預覽畫面會完全空白。

如果你發現的問題不在這裡，歡迎透過 [問題回報](https://github.com/yintzuyuan/NineBoxView/issues) 功能讓我知道。

## 感謝
特別感謝 Aaron Bell 的外掛 [RotateView](https://github.com/aaronbell/RotateView) 讓我知道如何即時顯示正在編輯中的字符。以及大曲都市的外掛 [Waterfall](https://github.com/Tosche/Waterfall) 讓我知道如何顯示輸入文字和變更預覽畫面的顯示顏色。

## 版權聲明
此外掛於2023年1月由殷慈遠發布。詳細版權聲明文件在文末。

# English
## NineBoxView
[Glyphs font editor](http://glyphsapp.com/) plug-in for surround the preview with others when making Chinese characters.

Code is written by Tzuyuan Yin.

## Usage
* Open the *Nine Box View* plugin from the *Window* menu.
* The central box will automatically display the currently selected glyph.
* Use the input box to change the surrounding glyphs at the same time.
* Use the button can change the display mode (Light/Dark).

## Installation
Install by clicking its *Install* button in *Window > Plugin Manager > Plugins* . Restart Glyphs once.

🌿 Nine Box View depends on the *Vanilla* module. Please install it via *Window > Plugin Manager > Modules* .

## Requirements
Tested on Glyphs 3.

## known Issues
This plug-in still has some bugs that not yet to be resolved, and they won't be fixed anytime soon. If you need it and want to help, welcome to use  [Pull requests](https://github.com/yintzuyuan/NineBoxView/pulls) to provide assistance.
* Glyphs are displayed left-aligned. So if you make a proportional typeface, it will make the main and reference glyphs misaligned.
* The input box only supports glyph input, not glyph names (e.g., uni6771). Hope that the input function is like [Kernkraft](https://github.com/bBoxType/Kernkraft) can support both.
* The displayed glyphs size is fixed and cannot be changed with the zoom of the window.
* When no glyph is selected on the edit view, the Viewer will be completely blank.

If you find any bugs not above. Let me know by [Issues](https://github.com/yintzuyuan/NineBoxView/issues) .

## Special Thanks
Special thanks to Aaron Bell's [RotateView](https://github.com/aaronbell/RotateView) plugin that explained how to automatically display outlines and to Toshi Omagari's [Waterfall](https://github.com/Tosche/Waterfall) plugin that explained how to use input box and change display colors.

## License
Copyright 2023 Tzuyuan Yin

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
