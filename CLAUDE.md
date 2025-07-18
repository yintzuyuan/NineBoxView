# Glyphs SDK 專案

## 載入核心設定
@~/.claude/author.md
@~/.claude/languages/python.md
@.claude/glyphs-essentials.md

## 開發資源（根據專案類型自動載入）

### 專案類型判斷
根據目錄結構自動判斷：
- 如果有 `.glyphsPlugin` 結尾的目錄 → **外掛專案**
- 如果在 `Scripts` 目錄下或檔案以 `.py` 結尾 → **腳本專案**

### 自動載入規則
<!-- 外掛專案：需要模組化和 PyObjC GUI -->
<!-- @.claude/glyphs-templates.md#外掛模板 -->

<!-- 腳本專案：單檔案和 vanilla GUI -->
<!-- @.claude/glyphs-templates.md#腳本模板 -->

<!-- 快速參考（始終可用） -->
@.claude/glyphs-reference.md

## 目前專案資訊
- **專案路徑**：`{{cwd}}`
- **專案類型**：`{{auto-detected: Plugin/Script}}`
- **GUI 框架**：`{{auto-selected: PyObjC/vanilla}}`

## 專案結構規範

### 外掛專案（偵測到 .glyphsPlugin）
```
YourPlugin.glyphsPlugin/
├── Contents/
│   ├── Info.plist
│   ├── MacOS/
│   └── Resources/
│       ├── plugin.py           # 主入口
│       └── lib/               # 模組化程式碼
│           ├── __init__.py
│           ├── ui/            # PyObjC GUI
│           └── core/          # 業務邏輯
```
- 使用模組化架構（300行限制）
- 使用 PyObjC 建立原生 GUI
- 相對匯入避免衝突

### 腳本專案（偵測到 Scripts/ 或 .py）
```
Scripts/
└── YourScript.py              # 單一檔案
```
- 保持單檔案簡潔
- 使用 vanilla 建立簡單 GUI
- 快速開發和測試

## 專案特定規則
<!-- 在此加入專案獨特的規則或偏好 -->

### 此專案的特殊要求
- 

### 開發檢查清單
#### 通用
- [ ] 遵循 TDD 開發流程
- [ ] 不超過 300 行限制（需要時拆分模組）
- [ ] 無硬編碼路徑
- [ ] 包含錯誤處理
- [ ] 移除 print 除錯輸出

#### 外掛專用
- [ ] 正確的目錄結構
- [ ] 所有模組有 __init__.py
- [ ] 使用相對匯入
- [ ] PyObjC GUI 實作

#### 腳本專用  
- [ ] MenuTitle 註解
- [ ] 單檔案實作
- [ ] vanilla GUI（如需要）

---
記得：根據專案類型自動選擇正確的架構和 GUI 框架
