# Glyphs 快速參考手冊

## 物件存取速查表

### 基本物件取得
```python
# 應用程式與字型
app = Glyphs.app
font = Glyphs.font                    # 目前開啟的字型
fonts = Glyphs.fonts                  # 所有開啟的字型

# 字符存取
glyph = font.glyphs["A"]              # 依名稱取得
glyph = font.glyphs[0]                # 依索引取得
selectedGlyphs = font.selectedGlyphs  # 選中的字符

# 圖層存取
layer = glyph.layers[masterID]        # 透過 masterID（推薦）
layer = glyph.layers["Regular"]       # 透過主板名稱
layer = glyph.layers[0]               # 透過索引（不推薦）
```

### ID 關係速查
```python
# Master ID 用法
master = font.masters[0]
masterID = master.id
layer = glyph.layers[masterID]        # 正確方式

# Axis ID 用法
axis = font.axes[0]
axisID = axis.id
instance = font.instances[0]
axisValue = instance.axes[axisID]     # 該軸線的數值

# 當前選中的圖層
currentLayer = font.selectedLayers[0]
```

### 常見遍歷模式
```python
# 遍歷所有字符的所有圖層
for glyph in font.glyphs:
    for layer in glyph.layers:
        # 處理圖層
        pass

# 遍歷選中字符的特定主板
masterID = font.masters[0].id
for glyph in font.selectedGlyphs:
    layer = glyph.layers[masterID]
    # 處理圖層

# 遍歷路徑和節點
for path in layer.paths:
    for node in path.nodes:
        # 修改節點位置
        node.x += 10
        node.y += 10
```

### 元件操作
```python
# 建立元件
component = GSComponent("A")          # 參照字符 A
component.transform = (1, 0, 0, 1, 100, 0)  # 設定變換
layer.components.append(component)

# 存取元件參照
for component in layer.components:
    baseGlyph = component.component   # 原始字符
    baseName = component.componentName # 原始字符名稱
```

## 常見錯誤與正確寫法

### ❌ 錯誤模式
```python
# 錯誤：直接使用索引，可能不是預期的圖層
layer = glyph.layers[0]

# 錯誤：假設特定主板存在
layer = glyph.layers["Bold"]  # 可能不存在

# 錯誤：直接修改座標系統
node.x = 100  # 沒有考慮座標系統
```

### ✅ 正確模式
```python
# 正確：使用 masterID 確保正確的圖層
masterID = font.masters[0].id
layer = glyph.layers[masterID]

# 正確：檢查主板是否存在
if "Bold" in [m.name for m in font.masters]:
    layer = glyph.layers["Bold"]

# 正確：考慮座標系統的修改
layer.LSB += 10  # 修改左側邊距
layer.RSB += 10  # 修改右側邊距
```

## 效能優化技巧

### 批次操作
```python
# 停用介面更新以提升效能
font.disableUpdateInterface()
try:
    # 批次處理
    for glyph in font.glyphs:
        # 修改操作
        pass
finally:
    # 重新啟用更新
    font.enableUpdateInterface()
```

### 快取常用物件
```python
# 快取主板 ID
masterIDs = [m.id for m in font.masters]

# 快取常用圖層
layers = {}
for glyph in font.glyphs:
    layers[glyph.name] = glyph.layers[masterIDs[0]]
```

## 除錯技巧

### 物件資訊檢查
```python
# 檢查物件類型
print(type(glyph))  # <class 'GSGlyph'>
print(type(layer))  # <class 'GSLayer'>

# 檢查可用屬性
print(dir(glyph))   # 列出所有屬性和方法

# 檢查 ID 關係
print(f"Layer masterID: {layer.masterID}")
print(f"Master ID: {font.masters[0].id}")
```

### 常用除錯輸出
```python
# 顯示巨集視窗
Glyphs.showMacroWindow()

# 清除巨集視窗
Glyphs.clearLog()

# 輸出物件資訊
print(f"字型：{font.familyName}")
print(f"字符：{glyph.name} (Unicode: {glyph.unicode})")
print(f"圖層：{layer.name} (Master: {layer.masterID})")
```

## 座標系統參考

### 字型座標
```python
# 基線在 y=0
# 向上為正 y 方向
# 向右為正 x 方向

# 常用度量
print(f"字面寬度：{layer.width}")
print(f"左側邊距：{layer.LSB}")
print(f"右側邊距：{layer.RSB}")
print(f"上升部：{font.masters[0].ascender}")
print(f"下降部：{font.masters[0].descender}")
```

### 邊界框
```python
# 取得路徑邊界
bounds = layer.bounds
if bounds:
    print(f"邊界：{bounds}")  # NSRect
    print(f"寬度：{bounds.size.width}")
    print(f"高度：{bounds.size.height}")
```

## 檔案操作

### 儲存和匯出
```python
# 儲存字型
font.save()

# 另存新檔
font.saveAs(path)

# 匯出實體
for instance in font.instances:
    instance.generate()
```

### 匯入字符
```python
# 從其他字型匯入
sourceFont = Glyphs.open(path)
targetFont = Glyphs.font

for glyph in sourceFont.glyphs:
    targetFont.glyphs.append(glyph.copy())
```

## 常用 Glyphs 方法

### 對話框
```python
# 訊息對話框
Message("標題", "訊息內容")

# 確認對話框
result = AskString("輸入", "請輸入名稱：", "預設值")

# 檔案選擇
filepath = GetOpenFile("選擇檔案", ["glyphs", "glyphx"])
savepath = GetSaveFile("儲存檔案", ["glyphs"])

# 資料夾選擇
folder = GetFolder("選擇資料夾")
```

### 偏好設定
```python
# 註冊預設值
Glyphs.registerDefault("com.YinTzuYuan.key", defaultValue)

# 讀取設定
value = Glyphs.defaults["com.YinTzuYuan.key"]

# 儲存設定
Glyphs.defaults["com.YinTzuYuan.key"] = newValue
```

### 本地化
```python
# 多語言支援
text = Glyphs.localize({
    'en': 'Hello',
    'de': 'Hallo',
    'zh-Hant': '你好',
    'ja': 'こんにちは'
})
```

## 常用常數

### 節點類型
```python
GSLINE = 1          # 直線
GSCURVE = 35        # 曲線
GSOFFCURVE = 65     # 控制點
```

### 選單位置
```python
FILE_MENU = 0
EDIT_MENU = 1
GLYPH_MENU = 2
VIEW_MENU = 3
WINDOW_MENU = 5
```

### 回呼事件
```python
DOCUMENTOPENED = "GSDocumentOpenedNotification"
DOCUMENTCLOSED = "GSDocumentClosedNotification"
DOCUMENTACTIVATED = "GSDocumentActivatedNotification"
UPDATEINTERFACE = "GSUpdateInterface"
```
