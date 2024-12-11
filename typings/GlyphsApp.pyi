# encoding: utf-8
#===============================================================================
# Glyphs.app Python Scripting API 文件
# 這是字型設計軟體 [Glyphs.app](https://glyphsapp.com) 的 [Python Scripting API 文件](https://docu.glyphsapp.com/index.html) 的翻譯。
#===============================================================================
# 關於本文件
# 本文件涵蓋了在 Python 封裝中實作的所有方法。通過 PyObjC 橋接，還有更多的函數和物件可用。詳細訊息請參閱文檔的核心部分。
#===============================================================================
# API 的變更
# 這些變更可能會破壞您的代碼，因此您需要跟蹤它們。請參閱 GSApplication.versionNumber 以了解如何在代碼中檢查應用程式版本。真的，請閱讀它。有一個陷阱。
#===============================================================================
"""
Glyphs.app 物件模型結構
-
主程式 `GSApplication`\n
║
Fonts: 主要的字型容器，包含字型的全域訊息和結構。
╟ Masters: 主板 -> masterID -> Layers
║   ╟ AxisValues: 主板對應的軸數值。
║   ╙ Guides: 參考線
╟ Glyphs: 字符
║   ╙ Layers: 圖層
║       ╟ Shapes: 包括路徑和組件的總稱。
║       ║   ╟ Paths: 路徑
║       ║   ║  ╙ Nodes: 節點
║       ║   ╙ Components: 組件
║       ╟ Anchors: 錨點
║       ╟ Guides: 參考線
║       ╙ Hints: 用於改進螢幕顯示效果。
╟ Styles: 樣式變體，如斜體或小型大寫字母。
║   ╙ AxisValues: 每個樣式變體的軸數值。
╟ Axes: 包含所有設計軸的資訊 -> axisID -> AxisValues
╟ Features: OpenType 功能，包含所有高級排版特性。
╙ Classes: 字型分類群組，用於組織和應用特性。

每個元素都可以有更多的屬性和細節，這個註釋結構提供了一個總覽，
幫助開發者理解字型檔案中元素的階層和相互關係。
"""

from typing import Any, Callable, List, Dict, Optional, Union, Final, Tuple, TypeVar, TypedDict
from typing_extensions import Literal
from Foundation import NSPoint, NSRect, NSColor, NSBezierPath, NSDocument, NSAffineTransform, NSAffineTransformStruct, NSImage
import datetime

T = TypeVar('T')

class GSFont: ...
class GSFontMaster: ...
class GSGlyph: ...
class GSLayer: ...
class GSComponent: ...
class GSPath: ...
class GSNode: ...
class GSAnchor: ...
class GSInstance: ...
class GSCustomParameter: ...
class GSClass: ...
class GSFeature: ...
class GSFeaturePrefix: ...
class GSAlignmentZone: ...
class GSSmartComponentAxis: ...
class GSGuideLine: ...
class GSAnnotation: ...
class GSBackgroundImage: ...



class GSApplication: # 類別
    def __init__(self) -> None: ...

    #region 屬性(Properties)
    @property
    def currentDocument(self) -> Optional['GSDocument']:
        """
        -> `GSDocument` 文件或 `None`

        當前活動的 GSDocument 對象或 None。
        
        ```python
        # 最上層開啟的文件
        document = Glyphs.currentDocument
        ```
        """
    @property
    def documents(self) -> List['GSDocument']:
        """
        -> `List[GSDocument]`

        開啟的 GSDocument 對象列表。
        """
    
    def open(self, path: str, showInterface: bool = True) -> Optional['GSFont']:
        """
        打開一個文件

        參數:
        - path: 文件所在的路徑。
        - showInterface: 是否應該打開文件窗口。默認值：True

        返回:
        打開的文件對象或 None。
        """

    @property
    def font(self) -> Optional[GSFont]: 
        """
        -> `GSFont` 字型或 `None`
        """
        ...
    # def font(self, value: GSFont): ...
    @property
    def fonts(self) -> List[GSFont]:
        """
        -> `List[GSFont]` 字型串列

        請注意，順序是由最後使用的字型決定的。通常，追加和擴充一般不會插入到列表的末端。
        ```
        # 存取所有已開啟的字型
        for font in Glyphs.fonts:
            print(font.familyName)
        # 新增一個字型
        font = GSFont()
        font.familyName = "My New Font"
        Glyphs.fonts.append(font)
        """
        ...
    @fonts.setter
    def fonts(self, value: List[GSFont]): ...

    @property
    def reporters(self) -> List[object]:
        """
        -> `List[object]` 物件串列

        可用的報告外掛列表（與“檢視”選單底部的部分相同）。這些是實際的物件。您可以使用`object.__class__.__name__`獲取它們的名稱。

        另請參閱面的`GSApplication.activateReporter()`和`GSApplication.deactivateReporter()`方法以啟動/停用它們。
        ```        
        # 所有報告外掛的列表
        print(Glyphs.reporters)
        # 個別外掛的類名
        for reporter in Glyphs.reporters:
            print(reporter.__class__.__name__)
        # 啟動外掛
        Glyphs.activateReporter(Glyphs.reporters[0]) # 通過物件
        Glyphs.activateReporter('GlyphsMasterCompatibility') # 通過類名
        """
        ...
    @property
    def activeReporters(self) -> list:
        """
        -> `list` 串列

        已啟用的報告外掛列表。
        ```
        # 啟用一個外掛
        Glyphs.activateReporter(Glyphs.reporters[0])
        # 目前已啟用的報告外掛列表
        activeReporters = Glyphs.activeReporters
        """
        ...
    @property
    def filters(self) -> list:
        """
        -> `list`

        可用過濾器的列表（與“過濾器”選單相同）。這些是實際的物件。

        以下示例代碼展示了如何獲取特定的過濾器並使用它。您可以使用`processFont_withArguments_()`函數來呼叫舊外掛，或者使用`filter()`函數來呼叫新外掛。作為參數，您可以使用在過濾器對話框（齒輪圖示）中點擊“拷貝自訂參數”按鈕獲取並將其轉換為列表。在`include`選項中，您可以提供一個逗號分隔的字符名稱列表。
        ```
        # 所有可用過濾器的列表
        print(Glyphs.filters)
        # 過濾器的類名
        for filter in Glyphs.filters:
            print(filter.__class__.__name__)
        ```
        從版本 2.4.2 開始新增
        """
        ...
    @property
    def defaults(self) -> dict:
        """
        -> `dict`

        用於儲存偏好設定的類似字典的物件。您可以獲取和設定鍵值對。

        請小心您的鍵。使用一個使用反向域名的前綴。例如 `com.MyName.foo.bar`。
        ```
        # 檢查偏好是否存在
        if "com.MyName.foo.bar" in Glyphs.defaults:
            # 做一些事情
        # 獲取和設定值
        value = Glyphs.defaults["com.MyName.foo.bar"]
        Glyphs.defaults["com.MyName.foo.bar"] = newValue
        # 刪除值
        # 這將恢復預設值
        del Glyphs.defaults["com.MyName.foo.bar"]
        """
    @defaults.setter
    def defaults(self, value: dict): ...

    @property
    def boolDefaults(self) -> bool:
        """
        -> `bool`

        取用預設設定轉換為布林值。
        ```
        if Glyphs.boolDefaults["com.MyName.foo.bar"]:
            print('"com.MyName.foo.bar" is set')
        """
        ...
    @property
    def scriptAbbreviations(self) -> dict:
        """
        -> `dict`

        語系名稱到標籤對應的字典，例如，'arabic': 'arab' 或 'devanagari': 'dev2'。
        """
        ...
    @property
    def scriptSuffixes(self) -> dict:
        """
        -> `dict`

        語系名稱後綴到語系名稱的字典，例如，'cy': 'cyrillic'。
        """
        ...
    @property
    def languageScripts(self) -> dict:
        """
        -> `dict`

        語言標籤到語系標籤的字典，例如，'ENG': 'latn'。
        """
        ...
    @property
    def languageData(self) -> list:
        """
        -> `list`

        包含更詳細的語言訊息的字典列表。
        """
        ...
    @property
    def unicodeRanges(self) -> list:
        """
        -> `list`

        Unicode 範圍的名稱列表。
        """
        ...
    @property
    def editViewWidth(self) -> int:
        """
        -> `int`
        
        編輯畫面的寬度。對應於偏好設定中的“文字預覽面板寬度”設定。
        """
    @editViewWidth.setter
    def editViewWidth(self, value: int): ...

    @property
    def handleSize(self) -> int:
        """
        -> `int`

        字符編輯畫面中貝塞爾手柄的大小。可能的值為 0-2。對應於偏好設定中的“手柄大小”設定。

        要在報告外掛中使用手柄大小進行繪製，您需要將手柄大小轉換為點大小，並除以畫面的比例因子。參見下面的示例。
        ```        
        # 計算手柄大小
        handSizeInPoints = 5 + Glyphs.handleSize * 2.5 # (= 5.0 or 7.5 or 10.0)    
        scaleCorrectedHandleSize = handSizeInPoints / Glyphs.font.currentTab.scale
        # 在手柄大小的大小中繪製點
        point = NSPoint(100, 100)
        NSColor.redColor.set()
        rect = NSRect((point.x - scaleCorrectedHandleSize * 0.5, point.y - scaleCorrectedHandleSize * 0.5), (scaleCorrectedHandleSize, scaleCorrectedHandleSize))
        bezierPath = NSBezierPath.bezierPathWithOvalInRect_(rect)
        bezierPath.fill()
        """
    @handleSize.setter
    def handleSize(self, value: int): 
        if not 0 <= value <= 2:
            raise ValueError('Handle size must be between 0 and 2')

    @property
    def versionString(self) -> str:
        """
        -> `str` 字串

        包含 Glyph.app 的版本號的字符串。也可能包含字母，如 '2.3b'。要檢查特定版本，請使用`Glyphs.versionNumber`。
        """
    @property
    def versionNumber(self) -> float:
        """
        -> `float`

        Glyph.app 的版本號。使用此版本號在代碼中進行版本檢查。
        """
    @property
    def buildNumber(self) -> float:
        """
        -> `float`

        Glyph.app 的構建號。

        特別是如果您使用預覽版本，則此數字對您的重要性可能比版本號更重要。構建號隨每個發布的構建而增加，是新 Glyphs 版本的最重要證據，而版本號則是任意設定，直到下一個穩定版本。
        """
    @property
    def menu(self) -> dict:
        """
        -> `dict`

        主選單的字典。您可以使用這個字典來新增選單項目。

        以下常數用於取用選單：`APP_MENU、FILE_MENU、EDIT_MENU、GLYPH_MENU、PATH_MENU、FILTER_MENU、VIEW_MENU、SCRIPT_MENU、WINDOW_MENU、HELP_MENU`
        ```
        def doStuff(sender):
            # 做一些事情
        newMenuItem = NSMenuItem('我的選單標題', doStuff)
        Glyphs.menu[EDIT_MENU].append(newMenuItem)
        """
    @menu.setter
    def menu(self, value: dict): ...

    #endregion
    #region 函數(Functions)
    def open(self, 
          Path: 'str', 
          showInterface: 'bool'=True
          ) -> Optional[GSFont]:
        """
        打開一個檔案
        
        參數:
        - Path – 檔案所在的路徑。
        - showInterface – 是否應該打開檔案視窗。預設值：True

        回傳:
        打開的檔案物件或 None。
        """
        ...
    def showMacroWindow(self):
        """
        打開巨集面板
        """
    def clearLog(self):
        """
        清除巨集面板中的內容
        """
    def showGlyphInfoPanelWithSearchString(self, String: str):
        """
        顯示帶有預設搜尋字符串的字符訊息視窗
        
        參數:
        - String – 搜尋字符串
        """
    def glyphInfoForName(self,
            name: 'str', 
            font=None
            ) -> GSGlyphInfo: 
        """
        為給定的字符名稱生成字型資訊物件

        參數:
        - name – 字符名稱
        - font – 如果新增了字型，並且該字型具有本地字符訊息，則將使用它，而不是全域訊息資料。
        """
        ...
    def glyphInfoForUnicode(self, 
            Unicode: 'str', 
            font=None
            ) -> GSGlyphInfo:
        """
        為給定的十六進制 Unicode 生成`GSGlyphInfo`物件
        
        參數:
        - Unicode – 十六進制 Unicode
        - font – 如果新增了字型，並且該字型具有本地字符訊息，則將使用它，而不是全域訊息資料。
        """
        ...
    def niceGlyphName(self,
            name: 'str', 
            font: 'GSFont'=None
            ) -> str:
        """
        將字符名稱轉換為易於閱讀的形式（例如 afii10017 或 uni0410 轉換為 A-cy）

        參數:
        name – 字符名稱
        font – 如果新增了字型，並且該字型具有本地字符訊息，則將使用它，而不是全域訊息資料。
        """

    def productionGlyphName(self,
            name: 'str', 
            font: 'GSFont'=None
            ) -> str:
        """
        將字符名稱轉換為產品字符名稱（例如 afii10017 或 A-cy 轉換為 uni0410）

        參數:
        name – 字符名稱
        font – 如果新增了字型，並且該字型具有本地字符訊息，則將使用它，而不是全域訊息資料。
        """

    def ligatureComponents(self, 
            String: 'str',
            font: 'GSFont'=None
            ) -> list:
        """
        如果在字符資料庫中定義為連字，則此函數回傳此連字可以由哪些字符組成的字符名稱列表。

        String – 字符名稱

        font – 如果新增了字型，並且該字型具有本地字符訊息，則將使用它，而不是全域訊息資料。
        ```            
        print(Glyphs.ligatureComponents('allah-ar'))
        >> (
            "alef-ar",
            "lam-ar.init",
            "lam-ar.medi",
            "heh-ar.fina"
        )
        """

    def addCallback(self,
            function: GSLayer | dict,
            hook: 'int'
            ):
        """
        新增用戶定義函數到字符視窗的繪製操作中，前景和背景為使用中字符以及非使用中字符。

        函數名稱用於新增/刪除鉤子中的函數，因此請確保使用唯一的函數名稱。

        您的函數需要接受兩個值：包含我們正在處理的圖層的相應`GSLayer`物件層和包含縮放值（目前）的資訊字典。

        對於這些鉤子，這些常數被定義為：`DRAWFOREGROUND、DRAWBACKGROUND、DRAWINACTIVE、DOCUMENTWASSAVED、DOCUMENTOPENED、TABDIDOPEN、TABWILLCLOSE、UPDATEINTERFACE、MOUSEMOVED`。有關更多訊息，請查看常數部分。
        ```        
        def drawGlyphIntoBackground(layer, info):
            # 由於內部 Glyphs.app 結構，我們需要捕獲並打印這些回呼函數的異常，例如：
            try: # 在這裡繪製您的代碼
                NSColor.redColor().set()
                layer.bezierPath.fill()
            except: # 錯誤。打印異常。
                import traceback
                print(traceback.format_exc())
        # 將您的函數新增到鉤子中
        Glyphs.addCallback(drawGlyphIntoBackground, DRAWBACKGROUND)
        """
    def removeCallback(self,
            function
            ):
        """
        刪除您之前新增的函數。
        ```
        # 從鉤子中刪除您的函數
        Glyphs.removeCallback(drawGlyphIntoBackground)
        """
    def redraw(self):
        """
        重新繪製所有編輯畫面和預覽畫面。
        """
    def showNotification(self,
            title: 'str',
            message: 'str'
            ):
        """
        在 Mac 的通知中心向用戶顯示通知。
        ```
        Glyphs.showNotification('匯出字型', '字型匯出成功。')
        """
    def localize(self,
            localization: Dict[str, str]
            ) -> str:
        """
        回傳一個字符串，該字符串使用 Glyphs.app 的 UI 地區設定的語言。

        參數是一個字典，格式為`languageCode: translatedString`。

        您不需要提供 Glyphs.app UI 支持的所有語言中的字符串。一個子集就可以。只需確保在所有其他翻譯字符串旁邊新增至少一個英文字符串以預設到下一個。還不要忘記將包含非 ASCII 內容的字符串標記為 Unicode 字符串（`'öäüß'`），以便進行正確編碼，並在所有 .py 檔案的頂部新增 ＃encoding: utf-8。

        Hint：您可以在此處找到 Glyphs 的本地化語言`Glyphs.defaults["AppleLanguages"]`。
        ```
        print(Glyphs.localize({
            'en': 'Hello World',
            'de': 'Hallöle Welt',
            'fr': 'Bonjour tout le monde',
            'es': 'Hola Mundo',
        }))
        # 假設您的 Mac 系統語言設定為德語
        # 並且 Glyphs.app UI 設定為使用本地化（在應用程式設定中更改），
        # 它將打印：
        >> Hallöle Welt
        """

    def activateReporter(self,
            reporter
            ):
        """
        通過其物件（參見`Glyphs.reporters`）或類別名啟用報告外掛。
        ```
        Glyphs.activateReporter('GlyphsMasterCompatibility')
        """
    def deactivateReporter(self,
            reporter
            ):
        """
        通過其物件（參見`Glyphs.reporters`）或類別名停用報告外掛。
        ```
        Glyphs.deactivateReporter('GlyphsMasterCompatibility')
        """
    #endregion
            
class GSDocument(): # 類別
    """
    文件類別
    """
    def __init__(self):
        self.font = GSFont()

    #region 屬性(Properties)
    @property
    def font(self) -> GSFont:
        """
        -> `GSFont` 字型檔
        """
    @property
    def filePath(self) -> str:
        """
        -> `str` 字串

        最後儲存的檔案路徑位置。
        """
    #endregion

class GSFont(): # 類別
    """    
    字型物件的實作。這個物件包含了用於內插的主板。即使沒有內插的情況下，為了物件模型的一致性，仍然會有一個主板和一個實體來代表單一字型。

    此外，字符附加到字型物件本身，而不是附加到主板。不同主板的字符作為圖層附加在這裡所附的字符物件上。
    """
    def __init__(self):
        self.parent = NSDocument()
        self.masters = GSFontMaster()
        self.instances = GSInstance()
        self.axes = GSAxis()
        self.properties = [GSFontInfoValueSingle(), GSFontInfoValueLocalized()]
        self.metrics = GSMetric()
        self.stems = GSMetric()
        self.numbers = GSMetric()
        self.glyphs = GSGlyph()
        self.classes = GSClass()
        self.features = GSFeature()
        self.featurePrefixes = GSFeaturePrefix()
        self.customParameters = GSCustomParameter()
        self.selection = GSGlyph()
        self.selectedLayers = GSLayer()
        self.selectedFontMaster = GSFontMaster()
        self.tabs = GSEditViewController()
        self.fontView = GSFontViewController()
        self.currentTab = GSEditViewController()

    #region 屬性(Properties)
    @property
    def parent(self) -> 'NSDocument':
        """
        -> `NSDocument` 內部文件（唯讀）
        """
    @property
    def masters(self) -> List[GSFontMaster]:
        """
        -> `List[GSFontMaster]`
        """

    @property
    def instances(self) -> List[GSInstance]:
        """
        -> `List[GSInstance]` 實體串列
        ```
        for instance in font.instances:
            print(instance)
        # 新增一個新的實體
        instance = GSInstance()
        instance.name = "實體"
        font.instances.append(instance)
        # 刪除一個實體
        del font.instances[0]
        font.instances.remove(someInstance)
        """
    @instances.setter
    def instances(self, value: List[GSInstance]): ...
    @instances.deleter
    def instances(self): ...

    @property
    def axes(self) -> List[GSAxis]:
        """
        -> `List[GSAxis]` 軸串列
        ```        
        for axis in font.axes:
            print(axis)
        # 新增一個新的軸
        axis = GSAxis()
        axis.name = "自訂軸"
        axis.axisTag = "SCAX"
        font.axes.append(axis)
        # 刪除一個軸
        del font.axes[0]
        font.axes.remove(someAxis)
        ```
        2.5新增功能。

        版本3中更改。
        """

    @property
    def properties(self) -> List[GSFontInfoValueSingle | GSFontInfoValueLocalized]:
        """
        -> `List[GSFontInfoValueSingle | GSFontInfoValueLocalized]` 字型資訊值串列

        本地化值使用中間列中定義的語言標籤：https://docs.microsoft.com/en-us/typography/opentype/spec/languagetags

        名稱列在常數中：Info Property Keys
        ```
        # 查找特定值：
        font.propertyForName_(name)
        # 或
        font.propertyForName_languageTag_(name, languageTag).
        # 新增條目：
        font.setProperty_value_languageTag_(GSPropertyNameFamilyNamesKey, "SomeName", None)
        ```
        版本3中新增功能。
        """
    @properties.setter
    def properties(self, value: List[GSFontInfoValueSingle | GSFontInfoValueLocalized]): ...

    @property
    def metrics(self) -> List[GSMetric]:
        """
        -> `List[GSMetric]` 度量串列
        ```
        # 新增一個新的度量
        metric = GSMetric(GSMetricsTypexHeight)
        font.metrics.append(metric)
        metricValue = master.metricValues[metric.id]
        metricValue.position = 543
        metricValue.overshoot = 17
        """
    
    @property
    def stems(self) -> List[GSMetric] | Dict[str, int]:
        """
        -> `List[GSMetric]` 度量串列或 `Dict[str, int]` 字典

        字幹。
        一個`GSMetric`物件的列表。對於每個度量，都有一個在主板中的`metricsValue`，通過ID連接。

        ```            
        font.stems[0].horizontal = False
        # 新增一個字幹
        stem = GSMetric()
        stem.horizontal = False
        stem.name = "名稱"
        font.stems.append(stem)
        master.stems[stem.name] = 123
        """
    @property
    def numbers(self) -> List[GSMetric] | Dict[str, int]:
        """
        -> `List[GSMetric]` 度量串列或 `Dict[str, int]` 字典

        數字。
        一個`GSMetric`物件的列表。對於每個數字，都有一個在主板中的`metricsValue`，通過ID連接。

        ```            
        print(font.numbers[0].name)
        # 新增一個數字
        number = GSMetric()
        number.horizontal = False
        number.name = "名稱"
        font.numbers.append(number)
        master.numbers[number.name] = 123
        """
    @property
    def glyphs(self) -> List[GSGlyph] | Dict[Union[str, chr], int]:
        """
        -> `List[GSGlyph]` 字符串列或 `dict` 字典

        `GSGlyph`物件的集合。回傳一個列表，但您也可以通過索引或字符名稱或字符作為鍵來呼叫字符。

        ```            
        # 取用所有字符
        for glyph in font.glyphs:
            print(glyph)
        >> <GSGlyph "A" with 4 layers>
        >> <GSGlyph "B" with 4 layers>
        >> <GSGlyph "C" with 4 layers>
        ...
        # 取用一個字符
        print(font.glyphs['A'])
        >> <GSGlyph "A" with 4 layers>
        # 通過字元取用一個字符(新增於版本2.4.1)
        print(font.glyphs['Ư'])
        >> <GSGlyph "Uhorn" with 4 layers>
        # 通過 Unicode 取用一個字符(新增於版本2.4.1)
        print(font.glyphs['01AF'])
        >> <GSGlyph "Uhorn" with 4 layers>
        # 通過索引取用一個字符
        print(font.glyphs[145])
        >> <GSGlyph "Uhorn" with 4 layers>
        # 新增一個字符
        font.glyphs.append(GSGlyph('adieresis'))
        # 在不同名稱下拷貝一個字符
        newGlyph = font.glyphs['A'].copy()
        newGlyph.name = 'A.alt'
        font.glyphs.append(newGlyph)
        # 刪除一個字符
        del font.glyphs['A.alt']
        """
    @glyphs.setter
    def glyphs(self, value: List[GSGlyph] | Dict[Union[str, chr], int]): ...
    @glyphs.deleter
    def glyphs(self): ...

    @property
    def characterForGlyph(self, glyph) -> str:
        """
        -> `str` 字串

        為編輯畫面中使用的字符回傳（內部）字符。如果字符具有 Unicode 則使用它，否則分配臨時代碼。這可能會隨時間而變化，因此不要依賴它。這主要用於查看編輯畫面分頁的字符串。

        版本3.1中新增功能。
        """

    @property
    def classes(self) -> List[GSClass]:
        """
        -> `List[GSClass]` 類別串列
        
        表示 OpenType 字元類別。
        ```            
        # 新增一個類別
        font.classes.append(GSClass('uppercaseLetters', 'A B C D E'))
        # 取用所有類別
        for class in font.classes:
            print(class.name)
        # 取用一個類別
        print(font.classes['uppercaseLetters'].code)
        # 刪除一個類別
        del font.classes['uppercaseLetters']
        """
    @classes.setter
    def classes(self, value: List[GSClass]): ...
    @classes.deleter
    def classes(self): ...

    @property
    def features(self) -> List[GSFeature]:
        """
        -> `List[GSFeature]` 特性串列

        表示 OpenType 特性。
        ```            
        # 新增一個特性
        font.features.append(GSFeature('liga', 'sub f i by fi;'))
        # 取用所有特性
        for feature in font.features:
            print(feature.code)
        # 取用一個特性
        print(font.features['liga'].code)
        # 刪除一個特性
        del font.features['liga']
        """
    @features.setter
    def features(self, value: List[GSFeature]): ...
    @features.deleter
    def features(self): ...

    @property
    def featurePrefixes(self) -> List[GSFeaturePrefix]:
        """
        -> `List[GSFeaturePrefix]` 特性前綴串列

        包含在 OpenType 特性之外的東西。
        ```
        # 新增一個前綴
        font.featurePrefixes.append(GSFeaturePrefix('LanguageSystems', 'languagesystem DFLT dflt;'))
        # 取用所有前綴
        for prefix in font.featurePrefixes:
            print(prefix.code)
        # 取用一個前綴
        print(font.featurePrefixes['LanguageSystems'].code)
        # 刪除
        del font.featurePrefixes['LanguageSystems']
        """
    @featurePrefixes.setter
    def featurePrefixes(self, value: List[GSFeaturePrefix]): ...
    @featurePrefixes.deleter
    def featurePrefixes(self): ...

    @property
    def copyright(self) -> str:
        """
        -> `str` 字串

        著作權資訊，這只能取用預設值。可以通過`GSFont.properties`取用本地化值。
        """
    @property
    def copyrights(self) -> Dict[str, str]:
        """
        -> `dict` 字典
        著作權資訊，所有本地化版權值。有關詳細訊息，請參見`GSFont.properties`。
        ```            
        font.copyrights["ENG"] = "All rights reserved"
        ```
        3.0.3版新增
        """
    @property
    def license(self) -> str:
        """
        -> `str` 字串
        
        授權，這只能取用預設值。可以通過`GSFont.properties`取用本地化值。
        """
    @property
    def licenses(self) -> Dict[str, str]:
        """
        -> `dict` 字典

        授權，所有本地化許可值。有關詳細訊息，請參見`GSFont.properties`。
        ```            
        font.licenses["ENG"] = "This font may be installed on all of your machines and printers, but you may not sell or give these fonts to anyone else."
        ```
        3.0.3版新增
        """
    @property
    def compatibleFullName(self) -> str:
        """
        -> `str` 字串
        
        相容用全名，這只能取用預設值。可以通過`GSFont.properties`取用本地化值。

        3.0.3版新增
        """
    @property
    def compatibleFullNames(self) -> Dict[str, str]:
        """
        -> `dict` 字典

        相容用全名，所有本地化設計者值。有關詳細訊息，請參見`GSFont.properties`。
        ```            
        font.compatibleFullNames["ENG"] = "MyFont Condensed Bold"
        ```
        3.0.3版新增
        """
    @property
    def sampleText(self) -> str:
        """
        -> `str` 字串
        
        範例文字，這只能取用預設值。可以通過`GSFont.properties`取用本地化值。

        3.0.3版新增。
        """
    @property
    def sampleTexts(self) -> Dict[str, str]:
        """
        -> `dict` 字典

        範例文字，所有本地化設計者值。有關詳細訊息，請參見`GSFont.properties`。
        ```            
        font.sampleTexts["ENG"] = "This is my sample text"
        ```
        3.0.3版新增
        """
    @property
    def description(self) -> str:
        """
        -> `str` 字串
        
        描述，這只能取用預設值。可以通過`GSFont.properties`取用本地化值。

        3.0.3版新增
        """
    @property
    def descriptions(self) -> Dict[str, str]:
        """
        -> `dict` 字典

        描述，所有本地化設計者值。有關詳細訊息，請參見`GSFont.properties`。
        ```            
        font.descriptions["ENG"] = "This is my description"
        ```
        3.0.3版新增
        """
    @property
    def designer(self) -> str:
        """
        -> `str` 字串
        
        設計師，這只能取用預設值。可以通過`GSFont.properties`取用本地化值。
        """
    @property
    def designers(self) -> Dict[str, str]:
        """
        -> `dict` 字典

        設計師，所有本地化設計者值。有關詳細訊息，請參見`GSFont.properties`。
        ```            
        font.designers["ENG"] = "John Smith"
        ```
        版本3.0.3中新增功能。
        """
    @property
    def trademark(self) -> str:
        """
        -> `str` 字串
        
        商標，這只能取用預設值。可以通過`GSFont.properties`取用本地化值。

        版本3.0.3中新增功能。
        """
    @property
    def trademarks(self) -> Dict[str, str]:
        """
        -> `dict` 字典

        商標，所有本地化商標值。有關詳細訊息，請參見`GSFont.properties`。
        ```            
        font.trademarks["ENG"] = "ThisFont is a trademark by MyFoundry.com"
        ```
        版本3.0.3中新增功能。
        """
    @property
    def designerURL(self) -> str:
        """
        -> `str` 字串
        
        設計師網站
        """
    @property
    def manufacturer(self) -> str:
        """
        -> `str` 字串
        
        廠商，這只能取用預設值。可以通過`GSFont.properties`取用本地化值。
        """
    @property
    def manufacturers(self) -> Dict[str, str]:
        """
        -> `dict` 字典

        廠商，所有本地化製造商值。有關詳細訊息，請參見`GSFont.properties`。
        ```            
        font.manufacturers["ENG"] = "My English Corporation"
        ```
        版本3.0.3中新增功能。
        """
    @property
    def manufacturerURL(self) -> str:
        """
        -> `str` 字串
        
        廠商網站
        """
    @property
    def versionMajor(self) -> int:
        """
        -> `int` 整數

        版本
        """
    @property
    def versionMinor(self) -> int:
        """
        -> `int` 整數

        版本字串
        """
    @property
    def date(self) -> datetime.datetime:
        """
        -> `datetime.datetime` 日期時間

        建立日期。
        ```
        print(font.date)
        >> 2015-06-08 09:39:05
        # 將日期設定為現在
        font.date = datetime.datetime.now()
        # 使用NSDate
        font.date = NSDate.date()
        # 或者使用自紀元以來的秒數
        font.date = time.time()
        """
    @property
    def familyName(self) -> str:
        """
        -> `str` 字串
        
        字型家族名稱。
        """
    @property
    def familyNames(self) -> Dict[str, str]:
        """
        -> `dict` 字典

        所有本地化家族名稱值。有關詳細訊息，請參見`GSFont.properties`。
        ```            
        font.familyNames["ENG"] = "MyFamilyName"
        ```
        版本3.0.3中新增功能。
        """
    @property
    def upm(self) -> int:
        """
        -> `int` 整數

        每 Em 的單位。
        """
    @property
    def note(self) -> str:
        """
        -> `str` 字串
        """
    @property
    def kerning(self) -> Dict[str, int]:
        """
        -> `dict` 字典

        左到右寫作的調距。多級字典。第一級的鍵是`GSFontMaster.id`（每個主板都有自己的調距），第二級的鍵是第一個字符的`GSGlyph.id`或類別ID（@MMK_L_XX），第三級的鍵是第二個字符的字符ID或類別ID（@MMK_R_XX）。值是實際的調距值。

        要設定值，最好使用方法 `GSFont.setKerningForPair()`。這可以確保更好的資料完整性（並且更快）。
        """
    @property
    def kerningRTL(self) -> dict:
        """
        -> `dict` 字典

        右到左寫作的調距。多級字典。第一級的鍵是`GSFontMaster.id`（每個主板都有自己的調距），第二級的鍵是第一個字符的`GSGlyph.id`或類別ID（@MMK_L_XX），第三級的鍵是第二個字符的字符ID或類別ID（@MMK_R_XX）。值是實際的調距值。

        要設定值，最好使用方法 `GSFont.setKerningForPair()`。這可以確保更好的資料完整性（並且更快）。
        """
    @property
    def kerningVertical(self) -> dict:
        """
        -> `dict` 字典

        垂直寫作的調距。多級字典。第一級的鍵是`GSFontMaster.id`（每個主板都有自己的調距），第二級的鍵是第一個字符的`GSGlyph.id`或類別ID（@MMK_L_XX），第三級的鍵是第二個字符的字符ID或類別ID（@MMK_R_XX）。值是實際的調距值。

        要設定值，最好使用方法 `GSFont.setKerningForPair()`。這可以確保更好的資料完整性（並且更快）。
        """
    @property
    def userData(self) -> Dict[str, Union[bool, str, List, Dict, float, bytes]]:
        """
        -> `dict` 字典

        儲存用戶資料的字典。使用不重複鍵，並且只使用可以儲存在屬性列表中的物件（字符串、列表、字典、數字、NSData），否則將無法從儲存的檔案中恢復資料。
        ```            
        # 設定值
        font.userData['rememberToMakeCoffee'] = True
        # 刪除值
        del font.userData['rememberToMakeCoffee']
        """
    @userData.setter
    def userData(self, value: Dict[str, Union[bool, str, List, Dict, float, bytes]]): ...
    @userData.deleter
    def userData(self): ...

    @property
    def tempData(self) -> dict:
        """
        -> `dict` 字典

        儲存臨時資料的字典。使用不重複鍵。這不會儲存到檔案中。如果需要資料持續，請使用`layer.userData`。
        ```            
        # 設定值
        font.tempData['rememberToMakeCoffee'] = True
        # 刪除值
        del font.tempData['rememberToMakeCoffee']
        """
    @tempData.setter
    def tempData(self, value: Dict[str, Union[bool, str, List, Dict, float, bytes]]): ...
    @tempData.deleter
    def tempData(self): ...

    @property
    def disableNiceNames(self) -> bool:
        """
        -> `bool` 布林值

        對應於字型訊息對話框中的“不使用易懂的形式”設定。
        """
    @property
    def customParameters(self) -> List[GSCustomParameter] | Dict[str, GSCustomParameter]:
        """
        -> `List[GSCustomParameter]` 或 `Dict[str, GSCustomParameter]` 自訂參數串列或字典
        
        自訂參數，您可以按名稱或按索引取用它們。
        ```            
        # 取用所有參數
        for parameter in font.customParameters:
            print(parameter)
        # 設定參數
        font.customParameters['glyphOrder'] = ["a", "b", "c"]
        # 新增多個參數：
        parameter = GSCustomParameter("Name Table Entry", "1 1;"font name")
        font.customParameters.append(parameter)
        parameter = GSCustomParameter("Name Table Entry", "2 1;"style name")
        font.customParameters.append(parameter)
        # 刪除參數
        del font.customParameters['glyphOrder']
        """
    @customParameters.setter
    def customParameters(self, value: List[GSCustomParameter] | Dict[str, GSCustomParameter]): ...
    @customParameters.deleter
    def customParameters(self): ...

    @property
    def grid(self) -> int:
        """
        -> `int` 整數

        對應於字型資訊的其他分頁中的“格線單位間隔”設定。
        """
    @grid.setter
    def grid(self, value: int): ...

    @property
    def gridSubDivision(self) -> int:
        """
        -> `int` 整數

        對應於字型資訊的其他分頁中的“格線再細分”設定。
        """
    @gridSubDivision.setter
    def gridSubDivision(self, value: int): ...

    @property
    def gridLength(self) -> float:
        """
        -> `float` 浮點數

        預先計算的格線大小，用於四捨五入。格線與格線再細分的除法結果。
        """
    
    @property
    def disableAutomaticAlignment(self) -> bool:
        """
        -> `bool` 布林值
        """
    @property
    def keyboardIncrement(self) -> float:
        """
        -> `float` 浮點數

        箭頭鍵的移動距離。預設值：1
        """
    @keyboardIncrement.setter
    def keyboardIncrement(self, value: float): ...

    @property
    def keyboardIncrementBig(self) -> float:
        """
        -> `float` 浮點數

        箭頭加Shift鍵的移動距離。預設值：10

        版本3.0中新增功能。
        """
    @keyboardIncrementBig.setter
    def keyboardIncrementBig(self, value: float): ...

    @property
    def keyboardIncrementHuge(self) -> float:
        """
        -> `float` 浮點數
        
        箭頭加Command鍵的移動距離。預設值：100

        版本3.0中新增功能。
        """
    @keyboardIncrementHuge.setter
    def keyboardIncrementHuge(self, value: float): ...

    @property
    def snapToObjects(self) -> bool:
        """
        -> `bool` 布林值

        禁用對節點和背景的吸附。

        版本3.0.1新增功能。
        """
    @snapToObjects.setter
    def snapToObjects(self, value: bool): ...

    @property
    def previewRemoveOverlap(self) -> bool:
        """
        -> `bool` 布林值

        禁用預覽移除重疊。

        版本3.0.1新增功能。
        """
    @previewRemoveOverlap.setter
    def previewRemoveOverlap(self, value: bool): ...

    @property
    def selection(self) -> List[GSLayer]:
        """
        -> `List[GSLayer]` 圖層串列

        回傳字型畫面中的所有選定的字符列表。
        """

    @property
    def selectedLayers(self) -> List[GSLayer]:
        """
        -> `List[GSLayer]` 圖層串列

        回傳使用中分頁中的所有選定的圖層列表。

        如果正在編輯字符，則此列表將只包含此字符。否則，列表將包含使用文本工具選取的所有字符。
        """

    @property
    def selectedFontMaster(self) -> 'GSFontMaster':
        """
        -> `GSFontMaster` 主板

        回傳使用中主板（在工具列中選取的主板）。
        """

    @property
    def masterIndex(self) -> int:
        """
        -> `int` 整數

        回傳使用中主板的索引（在工具列中選取的主板）。
        """

    @property
    def currentText(self) -> str:
        """
        -> `str` 字串

        目前編輯畫面的文本。

        未編碼和非 ASCII 字符將使用斜杠和字符名稱。 （例如：/a.sc）。設定 Unicode 字符串有效。
        """
    @property
    def tabs(self) -> List[GSEditViewController]:
        """
        -> `List[GSEditViewController]` 編輯畫面分頁串列

        UI 中打開的編輯畫面分頁列表。
        ```
        # 打開新分頁與文本
        font.newTab('hello')
        # 取用所有分頁
        for tab in font.tabs:
            print(tab)
        # 關閉最後一個分頁
        font.tabs[-1].close()
        """
    @property
    def fontView(self) -> GSFontViewController:
        """
        -> `GSFontViewController` 字型畫面

        字型畫面。
        """
    @property
    def currentTab(self) -> GSEditViewController:
        """
        -> `GSEditViewController` 編輯畫面分頁

        使用中編輯畫面分頁。
        """
    @property
    def filepath(self) -> str:
        """
        -> `str` 字串

        字型檔案在硬碟中的位置。
        """
    @property
    def tool(self) -> str:
        """
        -> `str` 字串
        
        工具列中選取的工具名稱。

        有關可用名稱，包括以選擇性工具形式提供的第三方外掛，請參見`GSFont.tools`。
        ```            
        font.tool = 'SelectTool' # 內置工具
        font.tool = 'GlyphsAppSpeedPunkTool' # 第三方外掛
        """
    @property
    def tools(self) -> list | str:
        """
        -> `list` 串列或 `str` 字串

        可用工具名稱列表，包括第三方外掛。
        """
    @property
    def appVersion(self) -> str:
        """
        -> `str` 字串

        回傳檔案最後儲存的版本。

        版本2.5新增功能。
        """
    @property
    def formatVersion(self) -> int:
        """
        -> `int` 整數

        應該以哪種Glyphs版本的檔案格式寫入字型。可能的值有「2」和「3」。

        版本3新增功能。
        """
    @formatVersion.setter
    def formatVersion(self, value: int): 
        if value not in [2, 3]:
            raise ValueError("formatVersion must be 2 or 3")

    #endregion
    #region 函數(functions)
        
    def save(self, 
            path: Optional[str] = None, 
            formatVersion: int = 3, 
            makeCopy: bool = False
            ) -> None:
        """
        儲存字型。

        參數：
        - path: 選擇性檔案路徑。當直接加載字型（`GSFont(path)`）時，需要路徑參數。
        - formatVersion: 檔案格式版本，可以是 2 或 3。默認為 3。
        - makeCopy: 是否儲存為新檔案而不更改文件檔案路徑。如果為 True，則必須提供 path 參數。

        回傳：
        無
        """
    def close(self,
           ignoreChanges: bool = True
           ):
        """
        關閉字型。

        參數：
        - ignoreChanges - （選擇性的）忽略關閉時的更改
        """
    def disableUpdateInterface(self):
        """
        禁用界面更新，從而加快字符處理。在對字型或其字符進行大更改之前呼叫此函數。確保在完成後呼叫`font.enableUpdateInterface()`。
        """
    def enableUpdateInterface(self):
        """
        重新啟用界面更新。只有在之前禁用它時才有意義。
        """
    def show(self):
        """
        使字型檔案在應用程式中可見，通過將已打開的字型視窗置於最前，或者通過將以前不可見的字型物件（例如拷貝操作的結果）附加為應用程式的視窗。
        
        版本2.4.1新增功能。
        """
    def kerningForPair(self,
            fontMasterId: 'str', 
            leftKey: 'str', 
            rightKey: 'str', 
            direction: 'int'=0
            ) -> float:
        """
        回傳兩個指定字符或調距組鍵（@MMK_X_XX）的調值。

        參數：
        - fontMasterId - `GSFontMaster`的ID
        - leftKey - 字符名稱或類別名
        - rightKey - 字符名稱或類別名
        - direction - 寫作方向（參見常數；'LTR'（0）或'RTLTTB'）。預設為LTR。
        ```            
        # 目前選中主板的w和e之間的調距
        font.kerningForPair(font.selectedFontMaster.id, 'w', 'e')
        >> -15.0
        # 目前選中主板的T和A之間的調距
        # （'L' = 對組的左側和'R' = 對組的右側）
        font.kerningForPair(font.selectedFontMaster.id, '@MMK_L_T', '@MMK_R_A')
        >> -75.0
        # 在同一字型中，T和A之間的調距將為零，因為它們使用組調距。
        font.kerningForPair(font.selectedFontMaster.id, 'T', 'A')
        >> None
        """

    def setKerningForPair(self,
            fontMasterId: 'str', 
            leftKey: 'str', 
            rightKey: 'str', 
            value: 'float', 
            direction: 'str'=GSLTR,
            ):
        """
        設定兩個指定字符或調距組鍵（@MMK_X_XX）的調值。

        參數：
        - fontMasterId - `FontMaster`的ID
        - leftKey - 字符名稱或類別名
        - rightKey - 字符名稱或類別名
        - value (float) - 調距值
        - direction - 選擇性；寫作方向（參見常數）。預設為GLTR。
        ```            
        # 為目前選中主板的T和A設定調距
        # （'L' = 對組的左側和'R' = 對組的右側）
        font.setKerningForPair(font.selectedFontMaster.id, '@MMK_L_T', '@MMK_R_A', -75)
        """
    def removeKerningForPair(self,
            fontMasterId: 'str', 
            leftKey: 'str', 
            rightKey: 'str', 
            direction: 'int'=GSLTR,
            ):
        """
        刪除兩個指定字符或調距組鍵（@MMK_X_XX）的調值。

        參數：
        - fontMasterId - `FontMaster`的ID
        - leftKey - 字符名稱或類別名
        - rightKey - 字符名稱或類別名
        - direction - 選擇性；寫作方向（參見常數；'LTR'（0）或'RTLTTB'）。預設為GSLTR(2.6.6新增)。
        ```
        # 刪除所有主板的T和A之間的調距
        # （'L' = 對組的左側和'R' = 對組的右側）
        for master in font.masters:
            font.removeKerningForPair(master.id, '@MMK_L_T', '@MMK_R_A')
        """
    def newTab(self, 
            tabText: str | list=None
            ) -> GSEditViewController:
        """
        在目前文檔視窗中打開一個新分頁，選擇性地帶有文本，並回傳該分頁物件。

        參數：
        - tabText - 選擇性；文本或以`/`轉義的字符名稱，或者圖層列表。
        ```
        # 打開新分頁
        tab = font.newTab('abcdef')
        print(tab)
        # 或
        tab = font.newTab([layer1, layer2])
        print(tab)
        """

    def updateFeatures(self
            ):
        """
        一次更新所有 OpenType 特性和類別，包括生成必要的新特性和類別。相當於特性面板中的“更新”按鈕。這已經包括特性的編譯（參見`font.compileFeatures()`）。

        版本2.4新增功能。
        """
    def compileFeatures(self
            ):
        """
        編譯特性，從而使新的特性代碼在編輯器中功能可用。相當於特性面板中的“編譯”按鈕。

        版本2.5新增功能。
        """
    #endregion
        
class GSAxis(): # 類別
    """
    軸物件的實作。
    """
    def __init__(self):
        self.font = GSFont()
    #region 屬性(Properties)
    @property
    def font(self) -> 'GSFont':
        """
        -> `GSFont` 字型

        包含軸的`GSFont`物件的引用。通常由應用程式設定。
        """
    @property
    def name(self) -> 'str':
        """
        -> `str` 字串

        軸的名稱
        """
    @name.setter
    def name(self, value: str): ...

    @property
    def axisTag(self) -> 'str':
        """
        -> `str` 字串
        
        軸標記。這是一個四字串。請參見 [OpenType Design-Variation Axis Tag Registry](https://learn.microsoft.com/en-us/typography/opentype/spec/dvaraxisreg) 。
        """
    @axisTag.setter
    def axisTag(self, value: str): ...

    @property
    def id(self) -> 'str':
        """
        -> `str` 字串
        
        用於連接主板中的值ID
        """
    @property
    def hidden(self) -> 'bool':
        """
        -> `bool` 布林值

        是否應該顯示軸
        """
    @hidden.setter
    def hidden(self, value: bool): ...

    #endregion
        
class GSMetric(): # 類別
    """
    度量物件的實作。它用於連接主板中的度量和字幹。
    """
    def __init__(self):
        self.font = GSFont()
    #region 屬性(Properties)
    @property
    def font(self) -> 'GSFont':
        """
        -> `GSFont` 字型

        包含度量的`GSFont`物件的引用。通常由應用程式設定。
        """
    @property
    def name(self) -> 'str':
        """
        -> `str` 字串
        
        度量或字幹的名稱
        """
    @name.setter
    def name(self, value: str): ...

    @property
    def id(self) -> 'str':
        """
        -> `str` 字串
        
        用於連接主板中的值ID
        """
    @property
    def title(self) -> 'str':
        """
        -> `str` 字串
        
        顯示在 UI 中的標題。它是唯讀的，因為它是由名稱、類型和濾鏡計算的。
        """
    @property
    def type(self) -> 'int':
        """
        -> `int` 整數

        度量類型
        """
    @type.setter
    def type(self, value: int): ...

    @property
    def filter(self) -> 'NSPredicate':
        """
        -> `NSPredicate` 述詞

        限制度量範圍的濾鏡。
        """
    @filter.setter
    def filter(self, value: NSPredicate): ...

    @property
    def horizontal(self) -> 'bool':
        """
        -> `bool` 布林值

        這用於字幹度量。因此，只能在 font.stems 中使用。
        """
    @horizontal.setter
    def horizontal(self, value: bool): ...
    #endregion

class GSFontMaster(): # 類別
    """
    主板物件的實作。這對應於字型訊息中的“主板”面板。在 Glyphs.app 中，每個主版的字符不是在這裡取用，而是作為附加到字型物件上的字符圖層。請參考頂部的資訊圖表以便更好地理解。
    """
    def __init__(self):
        self.font = GSFont()
    #region 屬性(Properties)
    @property
    def id(self) -> 'str':
        """
        -> `str` 字串
        
        用於識別字型中的圖層 ID

        參見`GSGlyph.layers`
        ```
        # 第一個主板的 ID
        print(font.masters[0].id)
        >> 3B85FBE0-2D2B-4203-8F3D-7112D42D745E
        # 使用這個主板來取用字符的對應圖層
        print(glyph.layers[font.masters[0].id])
        >> <GSLayer "Light" (A)>
        ```
        """
    @property
    def font(self) -> 'GSFont':
        """
        -> `GSFont` 字型

        引用包含主版的`GSFont`物件。通常這由應用程式設定，僅當實體實際上未被新增到字型中時，則手動設定此參數。

        2.5.2版新增
        """
    @font.setter
    def font(self, value: 'GSFont'): ...

    @property
    def name(self) -> 'str':
        """
        -> `str` 字串
        
        主板的人類可讀標識，例如“Bold Condensed”。
        """
    @name.setter
    def name(self, value: str): ...

    @property
    def iconName(self) -> 'str':
        """
        -> `str` 字串
        
        圖示的名稱
        """
    @iconName.setter
    def iconName(self, value: str): ...

    @property
    def axes(self) -> List[float]:
        """
        -> `List[float]` 浮點數串列

        指定每個軸位置的浮點數列表
        ```
        # 設定特定軸的值
        master.axes[2] = 12
        # 同時設定所有值
        master.axes = [100, 12, 3.5]
        ```
        2.5.2版新增

        自3.2版本起不建議使用
        """
    @axes.setter
    def axes(self, value: List[float]): ...

    @property
    def internalAxesValues(self) -> List[float]:
        """
        -> `List[float]` 浮點數串列

        指定每個軸位置的浮點數列表
        ```
        # 設定特定軸的值
        master.internalAxesValues[2] = 12
        # 或更精確
        master.internalAxesValues[axis.axisId] = 12
        # 同時設定所有值
        master.internalAxesValues = [100, 12, 3.5]
        ```
        3.2版新增
        """
    @internalAxesValues.setter
    def internalAxesValues(self, value: List[float]): ...

    @property
    def externalAxesValues(self) -> List[float]:
        """
        -> `List[float]` 浮點數串列

        浮點數列表，指定每個軸對於用戶面向值的位置。
        ```        
        # 設定特定軸的值
        master.externalAxesValues[2] = 12
        # 或更精確
        master.externalAxesValues[axis.axisId] = 12
        # 同時設定所有值
        master.externalAxesValues = [100, 12, 3.5]
        ```
        3.2版新增
        """
    @externalAxesValues.setter
    def externalAxesValues(self, value: List[float]): ...

    @property
    def properties(self) -> List[GSFontInfoValueSingle | GSFontInfoValueLocalized]:
        """
        -> `List[GSFontInfoValueSingle | GSFontInfoValueLocalized]` 字型資訊值串列
        保留字型訊息屬性的列表。可以是`GSFontInfoValueSingle`和`GSFontInfoValueLocalized`的實體。

        本地化值使用中間列中定義的語言標記：https://docs.microsoft.com/en-us/typography/opentype/spec/languagetags 。

        要查找特定值，請使用`master.propertyForName_(name)`或`master.propertyForName_languageTag_(name, languageTag)`。

        > 3.0版新增
        """
    @property
    def metrics(self) -> Dict[str, GSMetricValue]:
        """
        -> `Dict[str, GSMetricValue]` 字串與度量值字典

        所有`GSMetricValue`物件的字典。鍵是`font.metrics.id`
        ```
        for metric in Font.metrics:
            if metric.type == GSMetricsTypexHeight and metric.filter is None:
                metricValue = master.metricValues[metric.id]
                metricValue.position = 543
                metricValue.overshoot = 17
        ```
        3.0版新增
        """
    @property
    def ascender(self) -> 'float':
        """
        -> `float` 浮點數

        圖層上伸

        3.0.2版新增
        """
    @ascender.setter
    def ascender(self, value: float): ...

    @property
    def capHeight(self) -> 'float':
        """
        -> `float` 浮點數

        這是主板的預設大寫字高。可能有其他值是特定字符的。參見`master.metrics`和`layer.metrics`。
        """
    @property
    def xHeight(self) -> 'float':
        """
        -> `float` 浮點數

        這是主板的預設x高度。可能有其他值是特定字符的。參見`master.metrics`和`layer.metrics`。
        """
    @property
    def descender(self) -> 'float':
        """
        -> `float` 浮點數

        這是主板的預設下伸部。可能有其他值是特定字符的。參見`master.metrics`和`layer.metrics`。
        """
    @property
    def italicAngle(self) -> 'float':
        """
        -> `float` 浮點數

        斜體角度
        """
    @property
    def stems(self) -> 'list':
        """
        -> `list` 串列

        字幹，這是一個數字列表。
        ```    
        master.stems = [10, 11, 20]
        print(master.stems[0])
        master.stems[0] = 12
        master.stems["字幹名稱"] = 12
        """
    @stems.setter
    def stems(self, value: 'list'): ...

    @property
    def numbers(self) -> 'list':
        """
        -> `list` 串列

        數字。這是一個數字列表。
        ```            
        master.numbers = [10, 11, 20]
        print(master.numbers[0])
        master.numbers[0] = 12
        master.numbers["數字名稱"] = 12
        ```
        3.1版新增
        """
    @numbers.setter
    def numbers(self, value: 'list'): ...

    @property
    def alignmentZones(self) -> List[GSAlignmentZone]:
        """
        -> `List[GSAlignmentZone]` 對齊區串列

        `GSAlignmentZone`物件的集合（唯讀）
        """
    @property
    def blueValues(self) -> 'list':
        """
        -> `list` 串列

        從主板的對齊區計算的PS Hint藍值（唯讀）
        """
    @property
    def otherBlues(self) -> 'list':
        """
        -> `list` 串列

        從主板的對齊區計算的PS Hint其他藍值（唯讀）
        """
    @property
    def guides(self) -> List[GSGuide]:
        """
        -> `List[GSGuide]` 參考線串列

        `GSGuide`物件的集合。這些是字型寬度（實際上是主板寬度）的紅色參考線。對於字符級別的參考線（附加到圖層）請參見`GSLayer.guides`。
        """
    @guides.setter
    def guides(self, value: List[GSGuide]): ...

    @property
    def userData(self) -> Dict[str, Union[bool, str, List, Dict, float, bytes]]:
        """
        -> `dict` 字典

        儲存用戶資料的字典。使用不重複鍵，並且只使用可以儲存在屬性列表中的物件（字符串、列表、字典、數字、NSData），否則將無法從儲存的檔案中恢復資料。
        ```            
        # 設定值
        master.userData['rememberToMakeTea'] = True
        # 刪除值
        del master.userData['rememberToMakeTea']
        """
    @userData.setter
    def userData(self, value: Dict[str, Union[bool, str, List, Dict, float, bytes]]): ...
    @userData.deleter
    def userData(self): ...

    @property
    def customParameters(self) -> List[GSCustomParameter] | Dict[str, GSCustomParameter]:
        """
        -> `List[GSCustomParameter] | Dict[str, GSCustomParameter]` 自訂參數串列或字典
        自訂參數。`GSCustomParameter`物件的列表。您可以按名稱或按索引取用它們。
        ```            
        # 取用所有參數
        for parameter in master.customParameters:
            print(parameter)
        # 設定參數
        master.customParameters['glyphOrder'] = ["a", "b", "c"]
        # 新增多個參數：
        parameter = GSCustomParameter("Name Table Entry", "1 1;"font name")
        master.customParameters.append(parameter)
        parameter = GSCustomParameter("Name Table Entry", "2 1;"style name")
        master.customParameters.append(parameter)
        # 刪除參數
        del master.customParameters['glyphOrder']
        """
    @customParameters.setter
    def customParameters(self, value: List[GSCustomParameter] | Dict[str, GSCustomParameter]): ...
    @customParameters.deleter
    def customParameters(self): ...
    #endregion
        
class GSAlignmentZone: # 類別
    """
    對齊區物件的實作。

    藍色區域和其他區域之間沒有區別。所有負區域（除了位置為0的區域）將匯出為其他區域。

    基線的區域應該具有位置0（零）和負寬度。
    """
    def __init__(self, 
              pos: float = None, 
              size: float = None
              ):
        self.pos = pos
        self.size = size
        """
        參數：
        pos – 區域的位置
        size – 區域的大小
        """
    #region 屬性(Properties)
    @property
    def position(self) -> 'float':
        """
        -> `float` 浮點數

        區域的位置
        """
    @position.setter
    def position(self, value: 'float'): ...

    @property
    def size(self) -> 'float':
        """
        -> `float` 浮點數

        區域的大小
        """
    @size.setter
    def size(self, value: 'float'): ...

    #endregion

class GSInstance(): # 類別
    """
    實體物件的實作。這對應於字型資訊中的“匯出”面板。
    """
    def __init__(self):
        self.font = GSFont()

    #region 屬性(Properties)
    @property
    def exports(self) -> 'bool':
        """
        -> `bool` - 布林值

        匯出實體
        """
    @exports.setter
    def exports(self, value: bool): ...

    @property
    def visible(self) -> 'bool':
        """
        -> `bool` - 布林值

        編輯畫面的預覽可見狀態。
        """
    @visible.setter
    def visible(self, value: bool): ...

    @property
    def name(self) -> 'str':
        """
        -> `str` 字串
        
        實體的名稱。對應於字型資訊中的“樣式名稱”字段。這用於命名匯出的字型。
        """
    @name.setter
    def name(self, value: str): ...

    @property
    def type(self) -> int:
        """
        -> `int` 整數

        實體的類型。可以是`INSTANCETYPESINGLE`或`INSTANCETYPEVARIABLE`。
        """
    @type.setter
    def type(self, value: int): ...

    @property
    def weightClass(self) -> 'int':
        """
        -> `int` 整數

        設定在字型資訊中的字重類別，作為整數。支持1到1000的值，但建議使用100-900。

        要查看內插設計空間中的實際位置，請使用`GSInstance.axes`。
        """
    @weightClass.setter
    def weightClass(self, value: int): 
        if not 1 <= value <= 1000:
            raise ValueError("weightClass must be between 1 and 1000")

    @property
    def weightClassName(self) -> Optional[str]:
        """
        -> `str` 字串或 `None`

        與`GSInstance.weightClass`值對應的人類可讀名稱（唯讀）

        如果`GSInstance.weightClass`不是100的倍數，則可以為`None`。
        """
    @property
    def widthClass(self) -> 'int':
        """
        -> `int` 整數

        設定在字型資訊中的寬度類別，作為整數。支持1到9的值。

        要查看內插設計空間中的實際位置，請使用`GSInstance.axes`。
        """
    @widthClass.setter
    def widthClass(self, value: int): 
        if not 1 <= value <= 9:
            raise ValueError("widthClass must be between 1 and 9") 

    @property
    def widthClassName(self) -> 'str':
        """
        -> `str` 字串

        與`GSInstance.widthClass`值對應的人類可讀名稱（唯讀）
        """
    @property
    def axes(self) -> 'list':
        """
        -> `list` 串列

        每個軸位置的浮點數列表
        ```        
        # 設定特定軸的值
        instance.axes[2] = 12
        # 同時設定所有值
        instance.axes = [100, 12, 3.5] # 確保數字的數量與軸的數量相符
        ```
        2.5.2版新增

        自3.2版本起不建議使用。
        """
    @axes.setter
    def axes(self, value: 'list'): ...

    @property
    def internalAxesValues(self) -> List[float]:
        """
        -> `List[float]` - 浮點數串列

        每個軸位置的浮點數列表
        ```        
        # 設定特定軸的值
        instance.internalAxesValues[2] = 12
        # 或更精確
        instance.internalAxesValues[axis.axisId] = 12
        # 同時設定所有值
        instance.internalAxesValues = [100, 12, 3.5]
        ```
        3.2版新增
        """
    @internalAxesValues.setter
    def internalAxesValues(self, value: List[float]): ...

    @property
    def externalAxesValues(self) -> List[float]:
        """
        -> `List[float]` - 浮點數串列

        浮點數列表，指定每個軸對於用戶面向值的位置。
        ```        
        # 設定特定軸的值
        instance.externalAxesValues[2] = 12
        # 或更精確
        instance.externalAxesValues[axis.axisId] = 12
        # 同時設定所有值
        instance.externalAxesValues = [100, 12, 3.5]
        ```
        3.2版新增
        """
    @externalAxesValues.setter
    def externalAxesValues(self, value: List[float]): ...

    @property
    def properties(self) -> List[GSFontInfoValueSingle | GSFontInfoValueLocalized]:
        """
        -> `List[GSFontInfoValueSingle | GSFontInfoValueLocalized]` - 字型資訊值串列

        本地化值使用中間列中定義的語言標記：https://docs.microsoft.com/en-us/typography/opentype/spec/languagetags 。

        名稱在常數中列出：Info Property Keys
        ```
        # 查找特定值:
        instance.propertyForName_(name)
        # 或
        instance.propertyForName_languageTag_(name, languageTag).
        # 新增一個項目:
        instance.setProperty_value_languageTag_(GSPropertyNameFamilyNamesKey, "SomeName", None)
        ```
        3.0版新增
        """
    @properties.setter
    def properties(self, value: List[GSFontInfoValueSingle | GSFontInfoValueLocalized]): ...

    @property
    def isItalic(self) -> 'bool':
        """
        -> `bool` - 布林值

        斜體標誌，用於樣式連接。
        """

    @property
    def isBold(self) -> 'bool':
        """
        -> `bool` - 布林值

        粗體標誌，用於樣式連接。
        """

    @property
    def linkedStyle(self) -> 'str':
        """
        -> `str` 字串

        樣式連結
        """
    @linkedStyle.setter
    def linkedStyle(self, value: str): ...

    @property
    def preferredFamily(self) -> 'str':
        """
        -> `str` 字串
        
        建議的家族字型
        """
    @preferredFamily.setter
    def preferredFamily(self, value: str): ...

    @property
    def windowsFamily(self) -> 'str':
        """
        -> `str` 字串
        
        Windows 家族字型
        """
    @windowsFamily.setter
    def windowsFamily(self, value: str): ...

    @property
    def windowsStyle(self) -> 'str':
        """
        -> `str` 字串（唯讀）
        
        這是從“isBold”和“isItalic”計算出來的
        """
    @property
    def windowsLinkedToStyle(self) -> 'str':
        """
        -> `str` 字串（唯讀）

        Windows 連接到樣式
        """
    @property
    def fontName(self) -> 'str':
        """
        -> `str` 字串
        
        字型名稱(`postscriptFontName`)
        """
    @fontName.setter
    def fontName(self, value: str): ...

    @property
    def fullName(self) -> 'str':
        """
        -> `str` 字串

        全名（`postscriptFullName`）
        """
    @fullName.setter
    def fullName(self, value: str): ...

    @property
    def compatibleFullName(self) -> 'str':
        """
        -> `str` 字串

        這僅取用預設值。可以通過`GSInstance.properties`取用本地化值。
        
        3.0.3版新增
        """
    @property
    def compatibleFullNames(self) -> Dict[str, str]:
        """
        -> `dict` 字典

        相容用全名，取用所有本地化的`compatibleFullName`值。有關詳細訊息，請參見`GSInstance.properties`。

        ```            
        instance.compatibleFullNames["ENG"] = "MyFont Condensed Bold"
        ```
        3.0.3版新增
        """
    @compatibleFullName.setter
    def compatibleFullName(self, value: str): ...

    @property
    def copyright(self) -> 'str':
        """
        -> `str` 字串

        授權，這僅取用預設值。可以通過`GSInstance.properties`取用本地化值。
        
        3.0.2版新增
        """
    @property
    def copyrights(self) -> Dict[str, str]:
        """
        -> `dict` 字典

        授權，這取用所有本地化的值。有關詳細訊息，請參見`GSInstance.properties`。
        ```
        instance.copyrights["ENG"] = "All rights reserved"
        ```
        3.0.3版新增
        """
    @property
    def description(self) -> 'str':
        """
        -> `str` 字串

        描述，僅取用預設值。可以通過`GSInstance.properties`取用本地化值。
        
        3.0.3版新增
        """
    @property
    def descriptions(self) -> Dict[str, str]:
        """
        -> `dict` 字典

        描述，取用所有本地化的描述值。有關詳細訊息，請參見`GSInstance.properties`。
        ```
        instance.descriptions["ENG"] = "This is my description"
        ```
        3.0.3版新增
        """
    @descriptions.setter
    def descriptions(self, value: Dict[str, str]): ...

    @property
    def designer(self) -> 'str':
        """
        -> `str` 字串

        僅取用設計師預設值。可以通過`GSInstance.properties`取用本地化值。
        
        3.0.2版新增
        """
    @property
    def designerURL(self) -> 'str':
        """
        -> `str` 字串

        設計師網址

        3.0.2版新增
        """
    @designerURL.setter
    def designerURL(self, value: str): ...

    @property
    def designers(self) -> Dict[str, str]:
        """
        -> `dict` 字典

        取用所有本地化的設計師值。有關詳細訊息，請參見`GSInstance.properties`。
        ```
        instance.designers["ENG"] = "John Smith"
        ```
        3.0.3版新增
        """
    @designers.setter
    def designers(self, value: Dict[str, str]): ...

    @property
    def familyName(self) -> 'str':
        """
        -> `str` 字串

        家族名稱
        """
    @property
    def familyNames(self) -> Dict[str, str]:
        """
        -> `dict` 字典

        取用所有本地化的家族名稱值。有關詳細訊息，請參見`GSInstance.properties`。
        ```
        instance.familyNames["ENG"] = "MyFamilyName"
        ```
        3.0.3版新增
        """
    @familyNames.setter
    def familyNames(self, value: Dict[str, str]): ...

    @property
    def license(self) -> 'str':
        """
        -> `str` 字串

        授權，僅取用許可證預設值。可以通過`GSInstance.properties`取用本地化值。
        
        3.0.3版新增
        """
    @property
    def licenses(self) -> Dict[str, str]:
        """
        -> `dict` 字典

        授權，用於取用所有本地化的許可證值。詳情見`GSInstance.properties`
        ```
        instance.licenses["ENG"] = "This font may be installed on all of your machines and printers, but you may not sell or give these fonts to anyone else."
        ```
        3.0.3版新增
        """
    @licenses.setter
    def licenses(self, value: Dict[str, str]): ...

    @property
    def manufacturer(self) -> 'str':
        """
        -> `str` 字串

        僅取用製造商預設值。可以通過`GSInstance.properties`取用本地化值。
        
        3.0.2版新增
        """
    @property
    def manufacturers(self) -> Dict[str, str]:
        """
        -> `dict` 字典

        取用所有本地化的製造商值。有關詳細訊息，請參見`GSInstance.properties`。
        ```
        instance.manufacturers["ENG"] = "My English Corporation"
        ```
        3.0.3版新增
        """
    @manufacturers.setter
    def manufacturers(self, value: Dict[str, str]): ...

    @property
    def preferredFamilyName(self) -> 'str':
        """
        -> `str` 字串

        僅取用建議的家族名稱預設值。可以通過`GSInstance.properties`取用本地化值。
        
        3.0.3版新增
        """
    @property
    def preferredFamilyNames(self) -> Dict[str, str]:
        """
        -> `dict` 字典

        取用所有本地化的建議的家族名稱值。有關詳細訊息，請參見`GSInstance.properties`。
        ```
        instance.preferredFamilyNames["ENG"] = "MyFamilyName"
        ```
        3.0.3版新增
        """
    @preferredFamilyNames.setter
    def preferredFamilyNames(self, value: Dict[str, str]): ...

    @property
    def preferredSubfamilyName(self) -> 'str':
        """
        -> `str` 字串

        建議的子家族名稱
        """
    @property
    def preferredSubfamilyNames(self) -> Dict[str, str]:
        """
        -> `dict` 字典

        取用所有本地化的建議的子家族名稱值。有關詳細訊息，請參見`GSInstance.properties`。
        ```
        instance.preferredSubfamilyNames["ENG"] = "Regular"
        ```
        3.0.3版新增
        """
    @preferredSubfamilyNames.setter
    def preferredSubfamilyNames(self, value: Dict[str, str]): ...

    @property
    def sampleText(self) -> 'str':
        """
        -> `str` 字串

        僅取用範例文字預設值。可以通過`GSInstance.properties`取用本地化值。
        
        3.0.3版新增
        """
    @property
    def sampleTexts(self) -> Dict[str, str]:
        """
        -> `dict` 字典

        取用所有本地化的範例文字值。有關詳細訊息，請參見`GSInstance.properties`。
        ```
        instance.sampleTexts["ENG"] = "This is my sample text"
        ```
        3.0.3版新增
        """
    @sampleTexts.setter
    def sampleTexts(self, value: Dict[str, str]): ...

    @property
    def styleMapFamilyName(self) -> 'str':
        """
        -> `str` 字串

        僅取用表定家族名稱預設值。可以通過`GSInstance.properties`取用本地化值。
        
        3.0.3版新增
        """
    @property
    def styleMapFamilyNames(self) -> Dict[str, str]:
        """
        -> `dict` 字典

        取用所有本地化的表定家族名稱值。有關詳細訊息，請參見`GSInstance.properties`。
        ```
        instance.styleMapFamilyNames["ENG"] = "MyFamily Bold"
        ```
        3.0.3版新增
        """
    @property
    def styleMapStyleName(self) -> 'str':
        """
        -> `str` 字串

        僅取用樣式表定樣式名稱預設值。可以通過`GSInstance.properties`取用本地化值。
        
        3.0.3版新增
        """
    @property
    def styleMapStyleNames(self) -> Dict[str, str]:
        """
        -> `dict` 字典

        取用所有本地化的表定樣式名稱值。有關詳細訊息，請參見`GSInstance.properties`。
        ```
        instance.styleMapStyleNames["ENG"] = "Bold"
        ```
        3.0.3版新增
        """
    @styleMapStyleNames.setter
    def styleMapStyleNames(self, value: Dict[str, str]): ...

    @property
    def styleName(self) -> 'str':
        """
        -> `str` 字串

        僅取用樣式名稱預設值。可以通過`GSInstance.properties`取用本地化值。
        
        3.0.3版新增
        """
    @property
    def styleNames(self) -> Dict[str, str]:
        """
        -> `dict` 字典

        取用所有本地化的樣式名稱值。有關詳細訊息，請參見`GSInstance.properties`。
        ```
        instance.styleNames["ENG"] = "Regular"
        ```
        3.0.3版新增
        """
    @styleNames.setter
    def styleNames(self, value: Dict[str, str]): ...

    @property
    def trademark(self) -> 'str':
        """
        -> `str` 字串

        僅取用商標預設值。可以通過`GSInstance.properties`取用本地化值。
        
        3.0.3版新增
        """
    @property
    def trademarks(self) -> Dict[str, str]:
        """
        -> `dict` 字典

        取用所有本地化的商標值。有關詳細訊息，請參見`GSInstance.properties`。
        ```
        instance.trademarks["ENG"] = "ThisFont is a trademark by MyFoundry.com"
        ```
        3.0.3版新增
        """
    @trademarks.setter
    def trademarks(self, value: Dict[str, str]): ...

    @property
    def variableStyleName(self) -> 'str':
        """
        -> `str` 字串

        僅取用可變字型樣式名稱預設值。可以通過`GSInstance.properties`取用本地化值。
        
        3.0.3版新增
        """
    @property
    def variableStyleNames(self) -> Dict[str, str]:
        """
        -> `dict` 字典

        取用所有本地化的可變字型樣式名稱值。有關詳細訊息，請參見`GSInstance.properties`。
        ```
        instance.variableStyleNames["ENG"] = "Roman"
        ```
        3.0.3版新增
        """
    @variableStyleNames.setter
    def variableStyleNames(self, value: Dict[str, str]): ...

    @property
    def manufacturerURL(self) -> 'str':
        """
        -> `str` 字串

        製造商網址

        3.0.2版新增
        """
    @manufacturerURL.setter
    def manufacturerURL(self, value: str): ...

    @property
    def font(self) -> 'GSFont':
        """
        -> `GSFont` 字型

        引用包含實體的`GSFont`物件。通常這由應用程式設定，僅當實體實際上未被新增到字型中時，則手動設定此參數。

        2.5.1版新增
        """
    @font.setter
    def font(self, value: 'GSFont'): ...

    @property
    def customParameters(self) -> List[GSCustomParameter] | Dict[str, GSCustomParameter]:
        """
        -> `List[GSCustomParameter]` 自訂參數串列或 `Dict[str, GSCustomParameter]` 自訂參數字典
        
        自訂參數的列表，您可以按名稱或按索引取用它們。
        ```            
        # 取用所有參數
        for parameter in instance.customParameters:
            print(parameter)
        # 設定參數
        instance.customParameters['hheaLineGap'] = 10
        # 新增多個參數：
        parameter = GSCustomParameter("Name Table Entry", "1 1;"font name")
        instance.customParameters.append(parameter)
        parameter = GSCustomParameter("Name Table Entry", "2 1;"style name")
        instance.customParameters.append(parameter)
        # 刪除參數
        del instance.customParameters['hheaLineGap']
        """
    @customParameters.setter
    def customParameters(self, value: List[GSCustomParameter] | Dict[str, GSCustomParameter]): ...
    @customParameters.deleter
    def customParameters(self): ...

    @property
    def userData(self) -> Dict[str, Union[bool, str, List, Dict, float, bytes]]:
        """
        -> `dict` 字典

        儲存用戶資料的字典。使用不重複鍵，並且只使用可以儲存在屬性列表中的物件（字符串、列表、字典、數字、NSData），否則將無法從儲存的檔案中恢復資料。
        ```            
        # 設定值
        instance.userData['rememberToMakeCoffee'] = True
        # 刪除值
        del instance.userData['rememberToMakeCoffee']
        """
    @userData.setter
    def userData(self, value: Dict[str, Union[bool, str, List, Dict, float, bytes]]): ...
    @userData.deleter
    def userData(self): ...

    @property
    def tempData(self) -> 'dict':
        """
        -> `dict` 字典

        用於暫存資料的字典。使用不重複鍵。這不會儲存到檔案。如果需要資料持續，請使用`instance.userData`
        ```            
        # 設定值
        instance.tempData['rememberToMakeCoffee'] = True
        # 刪除值
        del instance.tempData['rememberToMakeCoffee']
        """
    @tempData.setter
    def tempData(self, value: Dict[str, Union[bool, str, List, Dict, float, bytes]]): ...
    @tempData.deleter
    def tempData(self): ...

    @property
    def instanceInterpolations(self) -> 'dict':
        """
        -> `dict` 字典

        包含每個主板內插係數的字典。如果更改`interpolationWeight`、`interpolationWidth`、`interpolationCustom`則會自動更新。它包含字型主板ID作為鍵，並將該主板的係數作為值。或者，如果將`manualInterpolation`設定為`True`，則可以手動設定它。沒有UI，因此您需要使用腳本來完成。
        """
    @instanceInterpolations.setter
    def instanceInterpolations(self, value: 'dict'): ...

    @property
    def manualInterpolation(self) -> 'bool':
        """
        -> `bool` 布林值

        禁用自動計算`instanceInterpolations`。這允許手動設定`instanceInterpolations`。
        """
    @manualInterpolation.setter
    def manualInterpolation(self, value: bool): ...

    @property
    def interpolatedFontProxy(self):
        """
        一個代理字型，它的行為類似於普通字型物件，但僅為您要求的字符進行內插。

        尚未正確封裝。因此，您需要直接使用ObjectiveC方法。
        """
    @interpolatedFontProxy.setter
    def interpolatedFontProxy(self, value): ...

    @property
    def interpolatedFont(self) -> GSFont:
        """
        -> `GSFont` 字型

        回傳一個準備好的內插`GSFont`物件，表示此實體。除了原物件之外，此內插字型將僅包含一個主板和一個實體。

        注意：當連續取用該實體的多個屬性時，建議將實體建立一次到變量中，然後使用該變量。否則，每次取用時，實體物件將完全進行內插。參見下面的示例。
        ```            
        # 建立實體一次
        interpolated = Glyphs.font.instances[0].interpolatedFont
        # 然後多次取用它
        print(interpolated.masters)
        >> (<GSFontMaster "Light" width 100.0 weight 75.0>)
        print(interpolated.instances)
        >> (<GSInstance "Web" width 100.0 weight 75.0>)
        """
    @interpolatedFont.setter
    def interpolatedFont(self, value: GSFont): ...

    #endregion
    #region 函數(Functions)
    def generate(self, 
            format: str = 'OTF', 
            fontPath: str = None, 
            autoHint: bool = True, 
            removeOverlap: bool = True, 
            useSubroutines: bool = True, 
            useProductionNames: bool = True, 
            containers: List[str] = [], 
            decomposeSmartStuff: bool = True
            ) -> Union[bool, List[str]]:
        """
        將實體生成為字型。

        參數：
        - format – 輪廓的格式：OTF或TTF。預設：OTF
        - fontPath – 最終字型的目的地路徑。如果為None，則使用匯出對話框中設定的預設位置
        - autoHint – 是否應用自動Hint。預設：True
        - removeOverlap – 是否移除重疊。預設：True
        - useSubroutines – 是否使用子程式進行CFF。預設：True
        - useProductionNames – 是否使用產品名稱。預設：True
        - containers (list) – 容器格式列表。使用以下任何常數：PLAIN、WOFF、WOFF2、EOT。預設：PLAIN
        - decomposeSmartStuff – 是否拆開智慧組件。預設：True

        回傳：
        成功時為True；失敗時為錯誤訊息。
        ```        
        # 將所有實體匯出為OpenType（.otf）和WOFF2到用戶的字型檔案夾
        exportFolder = '/Users/myself/Library/Fonts'
        for instance in Glyphs.font.instances:
            instance.generate(FontPath=exportFolder, Containers=[PLAIN, WOFF2])
        Glyphs.showNotification('匯出字型', '已成功匯出字型 %s ' % (Glyphs.font.familyName))
        lastExportedFilePath
        """

    def lastExportedFilePath(self) -> 'GSFont':
        """
        回傳一個準備好的內插`GSFont`物件，表示此實體。除了原物件之外，此內插字型將僅包含一個主板和一個實體。

        注意：當連續取用該實體的多個屬性時，建議將實體建立一次到變量中，然後使用該變量。否則，每次取用時，實體物件將完全進行內插。參見下面的示例。
        ```                
        # 建立實體一次
        interpolated = Glyphs.font.instances[0].interpolatedFont
        # 然後多次取用它
        print(interpolated.masters)
        >> (<GSFontMaster "Light" width 100.0 weight 75.0>)
        print(interpolated.instances)
        >> (<GSInstance "Web" width 100.0 weight 75.0>)
        """

    def addAsMaster(self):
        """
        將此實體作為新的主板新增到字型中。與字型資訊的實體作為主板選單項目相同。

        2.6.2版新增
        """
    #endregion
            
class GSCustomParameter: # 類別
    """
    自訂參數物件的實作。它儲存一個名稱/值對。

    您可以將`GSCustomParameter`物件附加到`GSFont.customParameters`，但這樣可能會導致重複。最好通過其字典介面取用自訂參數，如下所示：
    ```        
    # 取用所有參數
    for parameter in font.customParameters:
        print(parameter)
    # 設定參數
    font.customParameters['trademark'] = 'ThisFont is a trademark by MyFoundry.com'
    # 新增多個參數：
    parameter = GSCustomParameter("Name Table Entry", "1 1;"font name")
    font.customParameters.append(parameter)
    parameter = GSCustomParameter("Name Table Entry", "2 1;"style name")
    font.customParameters.append(parameter)
    # 刪除參數
    del font.customParameters['trademark']
    """
    def __init__(self, 
              name: str = None, 
              value: Union[str, list, dict, int, float] = None
              ):
        self.name = name
        self.value = value
        self.parent = [GSFont(), GSFontMaster(), GSInstance()]
        """
        參數：
        name – 名稱
        value – 數值
        """
    #region 屬性(Properties)
    @property
    def name(self) -> 'str':
        """
        -> `str` 字串
        
        名稱
        """
    @name.setter
    def name(self, value: str): ...
    @name.deleter
    def name(self): ...

    @property
    def value(self) -> Union[str, list, dict, int, float]:
        """
        -> `str`, `list`, `dict`, `int`, `float`

        字串、串列、字典、整數或浮點數
        """
    @value.setter
    def value(self, value: Union[str, list, dict, int, float]): ...
    @value.deleter
    def value(self): ...

    @property
    def active(self) -> 'bool':
        """
        -> `bool` 布林值

        參數是否啟用
        """
    @active.setter
    def active(self, value: bool): ...

    @property
    def parent(self) -> GSFont | GSFontMaster | GSInstance:
        """
        -> `GSFont` 字型 `GSFontMaster` 主板 `GSInstance` 或實體

        父物件
        """

    #endregion

class GSClass(): # 類別
    """
    類別物件的實作。用於儲存OpenType類別。

    有關如何取用它們的詳細訊息，請查看`GSFont.classes`
    """
    def __init__(self, 
              tag: str = None, 
              code: str = None
              ):
        self.tag = tag
        self.code = code
        """
        參數：
        tag – 類別名稱
        code – 由空格或換行符分隔的字符名稱列表
        """
    #region 屬性(Properties)
    @property
    def name(self) -> 'str':
        """
        -> `str` 字串

        類別名稱
        """
    @name.setter
    def name(self, value: str): ...
    @name.deleter
    def name(self): ...

    @property
    def code(self) -> 'str':
        """
        -> `str` 字串
        
        由空格分隔的字符名稱的字符串。
        """
    @code.setter
    def code(self, value: str): ...
    @code.deleter
    def code(self): ...

    @property
    def automatic(self) -> 'bool':
        """
        -> `bool` 布林值

        定義按下字型資訊中的“更新”按鈕時，是否自動生成此類別。
        """
    @automatic.setter
    def automatic(self, value: bool): ...

    @property
    def active(self) -> 'bool':
        """
        -> `bool` 布林值

        啟用狀態

        2.5版新增
        """
    @active.setter
    def active(self, value: bool): ...

    @property
    def tempData(self) -> 'dict':
        """
        -> `dict` 字典

        用於暫存資料的字典。使用不重複鍵。這不會儲存到檔案。如果需要資料持續，請使用`class.userData`
        ```            
        # 設定值
        class.tempData['rememberToMakeCoffee'] = True
        # 刪除值
        del class.tempData['rememberToMakeCoffee']
        """
    @tempData.setter
    def tempData(self, value: Dict[str, Union[bool, str, List, Dict, float, bytes]]): ...
    @tempData.deleter
    def tempData(self): ...

    #endregion

class GSFeaturePrefix(): # 類別
    """
    特性前綴物件的實作。用於儲存需要在特性之外的東西，如單獨查找。

    有關如何取用它們的詳細訊息，請查看`GSFont.featurePrefixes`
    """
    def __init__(self, 
              tag: str = None, 
              code: str = None
              ):
        self.tag = tag
        self.code = code
        """
        參數：
        tag – 前綴名稱
        code – Adobe FDK語法中的特性代碼
        """
    #region 屬性
    @property
    def name(self) -> 'str':
        """
        -> `str` 字串
        
        特性前綴名稱
        """
    @name.setter
    def name(self, value: str): ...
    @name.deleter
    def name(self): ...

    @property
    def code(self) -> 'str':
        """
        -> `str` 字串
        
        包含特性代碼的字符串。
        """
    @code.setter
    def code(self, value: str): ...
    @code.deleter
    def code(self): ...

    @property
    def automatic(self) -> 'bool':
        """
        -> `bool` 布林值

        定義是否按下字型資訊中的“更新”按鈕時自動生成此特性。
        """
    @automatic.setter
    def automatic(self, value: bool): ...

    @property
    def active(self) -> 'bool':
        """
        -> `bool` 布林值

        啟用狀態

        2.5版新增
        """
    @active.setter
    def active(self, value: bool): ...

    #endregion

class GSFeature(): # 類別
    """
    特性物件的實作。用於在字型資訊中實作OpenType特性。

    有關如何取用它們的詳細訊息，請查看`GSFont.features`
    """
    def __init__(self, 
              tag: str = None, 
              code: str = None
              ):
        self.tag = tag
        self.code = code
        """
        參數：
        tag – 特性名稱
        code – Adobe FDK語法中的特性代碼
        """
    #region 屬性(Properties)
    @property
    def name(self) -> 'str':
        """
        -> `str` 字串
        
        特性名稱
        """
    @name.setter
    def name(self, value: str): ...
    @name.deleter
    def name(self): ...

    @property
    def code(self) -> 'str':
        """
        -> `str` 字串
        
        Adobe FDK語法中的特性代碼。
        """
    @code.setter
    def code(self, value: str): ...
    @code.deleter
    def code(self): ...

    @property
    def automatic(self) -> 'bool':
        """
        -> `bool` 布林值

        定義是否按下字型資訊中的“更新”按鈕時自動生成此特性。
        """
    @automatic.setter
    def automatic(self, value: bool): ...

    @property
    def notes(self) -> 'str':
        """
        -> `str` 字串
        
        一些額外的文本。顯示在特性視窗的底部，包含字符集名稱參數。
        """
    @notes.setter
    def notes(self, value: str): ...
    @notes.deleter
    def notes(self): ...

    @property
    def active(self) -> 'bool':
        """
        -> `bool` 布林值

        啟用狀態

        2.5版新增
        """
    @active.setter
    def active(self, value: bool): ...

    @property
    def labels(self) -> 'list':
        """
        -> `list` 串列

        字符集特性名稱列表
        """
    @labels.setter
    def labels(self, value: list): ...
    @labels.deleter
    def labels(self): ...

    @property
    def tempData(self) -> 'dict':
        """
        -> `dict` 字典

        用於暫存資料的字典。使用不重複鍵。這不會儲存到檔案。如果需要資料持續，請使用`feature.userData`
        ```            
        # 設定值
        feature.tempData['rememberToMakeCoffee'] = True
        # 刪除值
        del feature.tempData['rememberToMakeCoffee']
        """
    @tempData.setter
    def tempData(self, value: Dict[str, Union[bool, str, List, Dict, float, bytes]]): ...
    @tempData.deleter
    def tempData(self): ...

    #endregion
    #region 函數(Funtions)
    def update(self):
        """
        呼叫此特性的自動特性代碼生成器。您可以使用此功能在匯出之前更新所有OpenType特性。
        ```            
        # 首先更新所有特性
        for feature in font.features:
            if feature.automatic:
                feature.update()
        # 然後匯出字型
        for instance in font.instances:
            if instance.active:
                instance.generate()
        """
    #endregion

class GSGlyph(): #類別
    """
    字符物件的實作。

    有關如何取用它們的詳細訊息，請查看`GSFont.glyphs`
    """
    def __init__(self, 
              name: str = None, 
              autoName: bool = True
              ):
        self.name = name
        self.autoName = autoName
        self.parent = GSFont()
        self.layers = GSLayer()
        self.glyphInfo = GSGlyphInfo()
        self.colorObject = NSColor()
        """
        參數：
        name – 字符名稱
        autoName – 自動將名稱轉換為易懂的形式（afii10017轉換為A-cy）
        """
    #region 屬性(Properties)
    @property
    def parent(self) -> 'GSFont':
        """
        -> `GSFont` 字型

        引用包含字符的`GSFont`物件。
        """
    @property
    def layers(self) -> Union[List[GSLayer], Dict[GSFontMaster, GSLayer]]:
        """
        -> `List[GSLayer]` 圖層串列或 `Dict[GSFontMaster, GSLayer]` 主板圖層字典

        字符圖層，您可以通過索引或圖層ID取用它們，圖層ID可以是`GSFontMaster.id`。圖層ID通常是由Glyphs.app選取的唯一字符串，而不是手動設定。它們可能看起來像這樣：3B85FBE0-2D2B-4203-8F3D-7112D42D745E
        ```            
        # 獲取使用中圖層
        layer = font.selectedLayers[0]
        # 獲取此層的字符
        glyph = layer.parent
        # 取用字符的所有圖層
        for layer in glyph.layers:
            print(layer.name)
        # 取用目前字符主板的圖層...
        # （也用於取用在字型檢視中選中字符的特定圖層）
        layer = glyph.layers[font.selectedFontMaster.id]
        # 直接取用目前使用中字符的“Bold”圖層
        for master in font.masters:
            if master.name == 'Bold':
                id = master.id
                break
        layer = glyph.layers[id]
        # 新增新圖層
        newLayer = GSLayer()
        newLayer.name = '{125, 100}' #（字符級中間主板示例）
        # 您可以設定此圖層將關聯的主板ID，否則將使用第一個主板
        newLayer.associatedMasterId = font.masters[-1].id
        font.glyphs['a'].layers.append(newLayer)
        # 拷貝不同名稱的圖層
        newLayer = font.glyphs['a'].layers[0].copy()
        newLayer.name = 'Copy of layer'
        # 提供參考，此時仍將是舊的圖層ID（在拷貝時）
        print(newLayer.layerId)
        font.glyphs['a'].layers.append(newLayer)
        # 提供參考，此圖層將在附加後被分配新的圖層ID
        print(newLayer.layerId)
        # 用另一個圖層替換第二主板圖層
        newLayer = GSLayer()
        newLayer.layerId = font.masters[1].id
        font.glyphs['a'].layers[font.masters[1].id] = newLayer
        # 刪除字符的最後一個圖層
        # （對於主板圖層也有效。它們將被清空）
        del font.glyphs['a'].layers[-1]
        # 刪除目前使用中圖層
        del font.glyphs['a'].layers[font.selectedLayers[0].layerId]
        """
    @layers.setter
    def layers(self, value: Union[List[GSLayer], Dict[GSFontMaster, GSLayer]]): ...
    @layers.deleter
    def layers(self): ...

    @property
    def name(self) -> 'str':
        """
        -> `str` 字串

        字符名稱。它將轉換為易懂的形式（afii10017轉換為A-cy）（您可以在字型資訊或應用程式偏好設定中禁用此行為）
        """
    @name.setter
    def name(self, value: str): ...

    @property
    def unicode(self) -> 'str':
        """
        -> `str` 字串

        字符的Unicode值，如果有的話。
        """
    @unicode.setter
    def unicode(self, value: str): ...
    @unicode.deleter
    def unicode(self): ...

    @property
    def unicodes(self) -> 'list':
        """
        -> `list` 串列

        字符的Unicode值列表，如果有的話。
        """
    @unicodes.setter
    def unicodes(self, value: list): ...
    @unicodes.deleter
    def unicodes(self): ...

    @property
    def string(self) -> 'str':
        """
        -> `str` 字串

        如果編碼，則回傳字符的字符串表示。這與將字符拷貝到剪貼板時獲得的字符串表示形式類似。
        """
    @property
    def id(self) -> 'str':
        """
        -> `str` 字串

        每個字符的唯一ID
        """
    @property
    def locked(self) -> 'bool':
        """
        -> `bool` 布林值

        如果字符被鎖定 TODO
        """
    @locked.setter
    def locked(self, value: bool): ...

    @property
    def category(self) -> 'str':
        """
        -> `str` 字串

        字符的類別。例如：'Letter'（字母）、'Symbol'（符號）。僅在設定了`GSGlyph.storeCategory`（參見下文）時才有效。
        """
    @category.setter
    def category(self, value: str): 
        if GSGlyph.storeCategory is False:
            raise AttributeError('GSGlyph.storeCategory is False')

    @property
    def storeCategory(self) -> 'bool':
        """
        -> `bool` 布林值

        設定為`True`以操作字符的`GSGlyph.category`（參見上文）。使得可以在不使用單獨的 GlyphData 檔案的情況下在 .glyphs 檔案中發送自訂字符資料。與 UI 中的 Cmd-Alt-i 對話框相同。
        """
    @storeCategory.setter
    def storeCategory(self, value: bool): ...

    @property
    def subCategory(self) -> 'str':
        """
        -> `str` 字串

        字符的子類別。例如：'Currency'（貨幣）、'Math'（數學）。僅在設定了`GSGlyph.storeSubCategory`（參見下文）時才有效。
        """
    @subCategory.setter
    def subCategory(self, value: str): 
        if GSGlyph.storeSubCategory is False:
            raise AttributeError('GSGlyph.storeSubCategory is False')

    @property
    def storeSubCategory(self) -> 'bool':
        """
        -> `bool` 布林值

        設定為`True`以操作字符的`GSGlyph.subCategory`（參見上文）。使得可以在不使用單獨的 GlyphData 檔案的情況下在 .glyphs 檔案中發送自訂字符資料。與 UI 中的 Cmd-Alt-i 對話框相同。
        """
    @storeSubCategory.setter
    def storeSubCategory(self, value: bool): ...

    @property
    def case(self) -> int:
        """
        -> `int` 整數

        字符的大小寫: `GSUppercase`, `GSLowercase`, `GSSmallcaps`。

        3.0版新增
        """
    @case.setter
    def case(self, value: int): ...

    @property
    def storeCase(self) -> 'bool':
        """
        -> `bool` 布林值

        設定為`True`以操作字符的`GSGlyph.case`（參見上文）。使得可以在不使用單獨的 GlyphData 檔案的情況下在 .glyphs 檔案中發送自訂字符資料。與 UI 中的 Cmd-Alt-i 對話框相同。

        3.0版新增
        """
    @storeCase.setter
    def storeCase(self, value: bool): ...

    @property
    def direction(self) -> 'int':
        """
        -> `int` 整數

        字符的書寫方向。

        參見`書寫方向`常數
        ```            
            glyph.direction = GSRTL

        3.0版新增
        """
    @direction.setter
    def direction(self, value: int): ...

    @property
    def storeDirection(self) -> 'bool':
        """
        -> `bool` 布林值

        設定為`True`以操作字符的`GSGlyph.direction`（參見上文）。使得可以在不使用單獨的 GlyphData 檔案的情況下在 .glyphs 檔案中發送自訂字符資料。與 UI 中的 Cmd-Alt-i 對話框相同。

        3.0版新增
        """
    @storeDirection.setter
    def storeDirection(self, value: bool): ...

    @property
    def script(self) -> 'str':
        """
        -> `str` 字串

        字符的語系，例如'latin'、'arabic'。僅在設定了`GSGlyph.storeScript`（參見下文）時才有效。
        """
    @script.setter
    def script(self, value: str): 
        if GSGlyph.storeScript is False:
            raise AttributeError('GSGlyph.storeScript is False')

    @property
    def storeScript(self) -> 'bool':
        """
        -> `bool` 布林值

        設定為`True`以操作字符的`GSGlyph.script`（參見上文）。使得可以在不使用單獨的 GlyphData 檔案的情況下在 .glyphs 檔案中發送自訂字符資料。與 UI 中的 Cmd-Alt-i 對話框相同。
        """
    @storeScript.setter
    def storeScript(self, value: bool): ...

    @property
    def productionName(self) -> 'str':
        """
        -> `str` 字串

        字符的產品名稱。僅在設定了`GSGlyph.storeProductionName`（參見下文）時才有效。
        """
    @productionName.setter
    def productionName(self, value: str): 
        if GSGlyph.storeProductionName is False:
            raise AttributeError('GSGlyph.storeProductionName is False')

    @property
    def storeProductionName(self) -> 'bool':
        """
        -> `bool` 布林值

        設定為`True`以操作字符的`GSGlyph.productionName`（參見上文）。使得可以在不使用單獨的 GlyphData 檔案的情況下在 .glyphs 檔案中發送自訂字符資料。與 UI 中的 Cmd-Alt-i 對話框相同。
        """
    @storeProductionName.setter
    def storeProductionName(self, value: bool): ...

    @property
    def tags(self) -> 'list':
        """
        -> `list` 串列

        儲存可以用於篩選字符或使用標記過濾器構建OT類別字符串
        """
    @tags.setter
    def tags(self, value: list): ...
    @tags.deleter
    def tags(self): ...

    @property
    def glyphInfo(self) -> 'GSGlyphInfo':
        """
        -> `GSGlyphInfo` 字型資訊

        此字符的`GSGlyphInfo`物件，包含詳細訊息。
        """
    @glyphInfo.setter
    def glyphInfo(self, value: GSGlyphInfo): ...

    @property
    def sortName(self) -> 'str':
        """
        -> `str` 字串

        用於在 UI 中排序字符的替代名稱。
        """
    @sortName.setter
    def sortName(self, value: str): ...

    @property
    def sortNameKeep(self) -> 'str':
        """
        -> `str` 字串

        用於在 UI 中排序字符的替代名稱，當在字型資訊中使用“保留替代字符”時。
        參見`GSGlyph.storeSortName`
        """
    @sortNameKeep.setter
    def sortNameKeep(self, value: str): ...

    @property
    def storeSortName(self) -> 'bool':
        """
        -> `bool` 布林值

        設定為`True`以操作字符的`GSGlyph.sortName`和`GSGlyph.sortNameKeep`（參見上文）。使得可以在不使用單獨的 GlyphData 檔案的情況下在 .glyphs 檔案中發送自訂字符資料。與 UI 中的 Cmd-Alt-i 對話框相同。
        """
    @storeSortName.setter
    def storeSortName(self, value: bool): ...

    @property
    def leftKerningGroup(self) -> 'str':
        """
        -> `str` 字串

        字符的左側調距群組。所有在調距群組中具有相同文字的字符將被分配到相同的調距類別中。
        """
    @leftKerningGroup.setter
    def leftKerningGroup(self, value: str): ...
    @leftKerningGroup.deleter
    def leftKerningGroup(self): ...

    @property
    def rightKerningGroup(self) -> 'str':
        """
        -> `str` 字串

        字符的右側調距群組。所有在調距群組中具有相同文字的字符將被分配到相同的調距類別中。
        """
    @rightKerningGroup.setter
    def rightKerningGroup(self, value: str): ...
    @rightKerningGroup.deleter
    def rightKerningGroup(self): ...

    @property
    def topKerningGroup(self) -> 'str':
        """
        -> `str` 字串

        字符的上側調距群組。所有在調距群組中具有相同文字的字符將被分配到相同的調距類別中。
        """
    @topKerningGroup.setter
    def topKerningGroup(self, value: str): ...
    @topKerningGroup.deleter
    def topKerningGroup(self): ...

    @property
    def bottomKerningGroup(self) -> 'str':
        """
        -> `str` 字串

        字符的下側調距群組。所有在調距群組中具有相同文字的字符將被分配到相同的調距類別中。
        """
    @bottomKerningGroup.setter
    def bottomKerningGroup(self, value: str): ...
    @bottomKerningGroup.deleter
    def bottomKerningGroup(self): ...

    @property
    def leftKerningKey(self) -> 'str':
        """
        -> `str` 字串

        用於調距函數的左側鍵（`GSFont.kerningForPair()`、`GSFont.setKerningForPair()`、`GSFont.removeKerningForPair()`）。

        如果字符具有`leftKerningGroup`屬性，則將回傳內部使用的 @MMK_R_xx 表示法（請注意，其中的R表示LTR字型的調距對的右側，對應於字符的左側調距群組）。如果未給出組，則將回傳字符的名稱。
        ```            
        # 為'T'和所有'a'調距類別成員設定調距
        # 對於LTR字型，始終使用第一（左）字符的.rightKerningKey，第二（右）字符的.leftKerningKey。
        font.setKerningForPair(font.selectedFontMaster.id, font.glyphs['T'].rightKerningKey, font.glyphs['a'].leftKerningKey, -60)
        # 對應於：
        font.setKerningForPair(font.selectedFontMaster.id, 'T', '@MMK_R_a', -60)
        """
    @leftKerningKey.setter
    def leftKerningKey(self, value: str): ...
    @leftKerningKey.deleter
    def leftKerningKey(self): ...

    @property
    def rightKerningKey(self) -> 'str':
        """
        -> `str` 字串

        用於調距函數的右側鍵（`GSFont.kerningForPair()`、`GSFont.setKerningForPair()`、`GSFont.removeKerningForPair()`）。

        如果字符具有`rightKerningGroup`屬性，則將回傳內部使用的 @MMK_L_xx 表示法（請注意，其中的L表示LTR字型的調距對的左側，對應於字符的右側調距群組）。如果未給出組，則將回傳字符的名稱。
        
        參見上文的示例。

        2.4版新增
        """
    @rightKerningKey.setter
    def rightKerningKey(self, value: str): ...
    @rightKerningKey.deleter
    def rightKerningKey(self): ...

    @property
    def topKerningKey(self) -> 'str':
        """
        -> `str` 字串

        用於調距函數的上側鍵（`GSFont.kerningForPair()`、`GSFont.setKerningForPair()`、`GSFont.removeKerningForPair()`）。
        
        3.0版新增
        """
    @topKerningKey.setter
    def topKerningKey(self, value: str): ...
    @topKerningKey.deleter
    def topKerningKey(self): ...

    @property
    def bottomKerningKey(self) -> 'str':
        """
        -> `str` 字串

        用於調距函數的下側鍵（`GSFont.kerningForPair()`、`GSFont.setKerningForPair()`、`GSFont.removeKerningForPair()`）。
        
        3.0版新增
        """
    @bottomKerningKey.setter
    def bottomKerningKey(self, value: str): ...
    @bottomKerningKey.deleter
    def bottomKerningKey(self): ...

    @property
    def leftMetricsKey(self) -> 'str':
        """
        -> `str` 字串

        字符的左側度量鍵。引用自另一個字符的名稱或公式。用於與連結的字符同步度量。
        """
    @leftMetricsKey.setter
    def leftMetricsKey(self, value: str): ...

    @property
    def rightMetricsKey(self) -> 'str':
        """
        -> `str` 字串
        
        字符的右側度量鍵。引用自另一個字符的名稱或公式。用於與連結的字符同步度量。
        """
    @rightMetricsKey.setter
    def rightMetricsKey(self, value: str): ...

    @property
    def widthMetricsKey(self) -> 'str':
        """
        -> `str` 字串
        
        字符的寬度度量鍵。引用自另一個字符的名稱或公式。用於與連結的字符同步度量。
        """
    @widthMetricsKey.setter
    def widthMetricsKey(self, value: str): ...

    @property
    def export(self) -> 'bool':
        """
        -> `bool` 布林值

        定義字型生成時是否匯出字符。
        """
    @export.setter
    def export(self, value: bool): ...

    @property
    def color(self) -> 'int':
        """
        -> `int` 整數

        字符在 UI 中的顏色標籤
        ```        
        glyph.color = 0         # 紅色
        glyph.color = 1         # 橙色
        glyph.color = 2         # 褐色
        glyph.color = 3         # 黃色
        glyph.color = 4         # 淺綠色
        glyph.color = 5         # 深綠色
        glyph.color = 6         # 淺藍色
        glyph.color = 7         # 藍色
        glyph.color = 8         # 紫色
        glyph.color = 9         # 洋紅色
        glyph.color = 10        # 灰色
        glyph.color = 11        # 深灰色
        glyph.color = None      # 未標記，白色（在版本1235之前，使用-1）
        """
    @color.setter
    def color(self, value: int): ...

    @property
    def colorObject(self) -> 'NSColor':
        """
        -> `NSColor` 顏色物件

        字符的顏色物件，用於插件中的繪製。
        ```            
        # 使用字符顏色繪製輪廓
        glyph.colorObject.set()
        # 獲取RGB（和alpha）值（作為0..1的浮點數，必要時乘以256）
        R, G, B, A = glyph.colorObject.colorUsingColorSpace_(NSColorSpace.genericRGBColorSpace()).getRed_green_blue_alpha_(None, None, None, None)
        print(R, G, B)
        >> 0.617805719376 0.958198726177 0.309286683798
        print(round(R * 256), int(G * 256), int(B * 256))
        >> 158 245 245
        # 繪製圖層
        glyph.layers[0].bezierPath.fill()
        # 設定字符顏色。
        glyph.colorObject = NSColor.colorWithDeviceRed_green_blue_alpha_(247.0 / 255.0, 74.0 / 255.0, 62.9 / 255.0, 1)
        # 或：
        glyph.colorObject = (247.0, 74.0, 62.9) # 最大255.0
        # 或：
        glyph.colorObject = (247.0, 74.0, 62.9, 1) # 帶alpha
        # 或：
        glyph.colorObject = (0.968, 0.29, 0.247, 1) # 最大1.0
        """
    @colorObject.setter
    def colorObject(self, value: NSColor): ...

    @property
    def note(self) -> 'str':
        """
        -> `str` 字串
        
        字符的注釋
        """
    @note.setter
    def note(self, value: str): ...
    @note.deleter
    def note(self): ...

    @property
    def selected(self) -> 'bool':
        """
        -> `bool` 布林值

        如果在字型畫面中選中字符，則回傳True。這與`font.selectedLayers`屬性不同，後者回傳使用中分頁中的選取。
        ```            
        # 取用字型畫面中選中的所有字符
        for glyph in font.glyphs:
            if glyph.selected:
                print(glyph)
        
        """

    @property
    def masterCompatible(self) -> 'bool':
        """
        -> `bool` 布林值

        當此字符中的所有圖層與主板相容（相同組件，錨點，路徑等）時回傳True。
        """

    @property
    def userData(self) -> Dict[str, Union[bool, str, List, Dict, float, bytes]]:
        """
        -> `dict` 字典

        用於儲存用戶資料的字典。使用不重複鍵，僅使用可以儲存在屬性列表中的物件（字符串，列表，字典，數字，NSData），否則資料將無法從儲存的檔案中恢復。
        ```            
        # 設定值
        glyph.userData['rememberToMakeCoffee'] = True
        # 刪除值
        del glyph.userData['rememberToMakeCoffee']
        """
    @userData.setter
    def userData(self, value: Dict[str, Union[bool, str, List, Dict, float, bytes]]): ...
    @userData.deleter
    def userData(self): ...

    @property
    def smartComponentAxes(self) -> List[GSSmartComponentAxis]:
        """
        -> `List[GSSmartComponentAxis]` 智慧組件軸串列

        一個`GSSmartComponentAxis`物件的列表。

        這些是智慧組件內插所發生的軸定義。對應於字符的“顯示智慧字符設定選項”對話框的“屬性”分頁。

        參見 https://glyphsapp.com/tutorials/smart-components 以供參考。
        ```            
        # 向字符新增兩個內插軸
        axis1 = GSSmartComponentAxis()
        axis1.name = 'crotchDepth'
        axis1.topValue = 0
        axis1.bottomValue = -100
        g.smartComponentAxes.append(axis1)
        axis2 = GSSmartComponentAxis()
        axis2.name = 'shoulderWidth'
        axis2.topValue = 100
        axis2.bottomValue = 0
        g.smartComponentAxes.append(axis2)
        # 刪除一個軸
        del g.smartComponentAxes[1]
        """
    @smartComponentAxes.setter
    def smartComponentAxes(self, value: List[GSSmartComponentAxis]): ...
    @smartComponentAxes.deleter
    def smartComponentAxes(self): ...

    @property
    def lastChange(self) -> 'time':
        """
        -> `time` 時間

        字符最後一次更改的日期時間。

        查看Python的time模組以了解如何使用時間戳。
        """
    #endregion
    #region 函數(Funtions)
    
    def beginUndo(self):
        """
        在對字符進行較長時間的更改之前呼叫此函數。在完成後，請確保呼叫`glyph.endUndo()`
        """
    def endUndo(self):
        """
        關閉之前由`glyph.beginUndo()`打開的撤銷組。請確保對每個`beginUndo()`呼叫都呼叫此函數。
        """
    def updateGlyphInfo(self, changeName: bool = True):
        """
        更新此字符的所有訊息，如名稱、Unicode等。

        參數：
        changeName – 如果為True，則將根據字符的名稱自動更改Unicode。
        """
    def duplicate(self, name: str = None) -> str:
        """
        拷貝字符並回傳新字符。

        如果未給出名稱，將附加`.00n`。
        """
    #endregion

class GSLayer(): # 類別
    """
    圖層物件的實作。

    有關如何取用它們的詳細訊息，請查看`GSGlyph.layers`
    """
    def __init__(self):
        self.parent = GSGlyph()
        self.master = GSFontMaster()
        self.colorObject = NSColor()
        self.components = GSComponent()
        self.guides = GSGuide()
        self.annotations = GSAnnotation()
        self.hints = GSHint()
        self.anchors = GSAnchor()
        self.shapes = [GSShape(), GSPath(), GSComponent()]
        self.paths = GSPath()
        self.selection = [GSNode(), GSAnchor(), GSShape(), GSPath()]
        self.selectionBounds = NSRect()
        self.metrics = GSMetricValue()
        self.background = GSLayer()
        self.backgroundImage = GSBackgroundImage()
        self.smartComponentPoleMapping = GSSmartComponentAxis()

    #region 屬性(Properties)
    @property
    def parent(self) -> 'GSGlyph':
        """
        -> `GSGlyph` 字符

        引用此圖層附加到的字符物件。
        """

    @property
    def name(self) -> 'str':
        """
        -> `str` 字串
        
        圖層名稱
        """
    @name.setter
    def name(self, value: str): ...

    @property
    def master(self) -> 'GSFontMaster':
        """
        -> `GSFontMaster` 主板（唯讀）

        此圖層連接的主板
        """
    @property
    def associatedMasterId(self) -> 'str':
        """
        -> `str` 字串

        如果這不是主板圖層，則此屬性為此圖層所屬的字型主板的ID。每個不是主板圖層的圖層都需要附加到一個主板圖層。
        ```
        # 新增新圖層
        newLayer = GSLayer()
        newLayer.name = '{125, 100}' #（字符級中間主板示例）
        # 您可以設定此圖層將關聯的主板ID，否則將使用第一個主板
        newLayer.associatedMasterId = font.masters[-1].id
        font.glyphs['a'].layers.append(newLayer)
        """
    @associatedMasterId.setter
    def associatedMasterId(self, value: str): ...

    @property
    def layerId(self) -> 'str':
        """
        -> `str` 字串
        
        唯一的圖層ID用於在字符的圖層字典中取用圖層。

        對於主板圖層，這應該是`fontMaster`的ID。它可能看起來像這樣：FBCA074D-FCF3-427E-A700-7E318A949AE5
        ```            
        # 查看活動圖層的ID
        id = font.selectedLayers[0].layerId
        print(id)
        >> FBCA074D-FCF3-427E-A700-7E318A949AE5
        # 通過此ID取用圖層
        layer = font.glyphs["a"].layers[id]
        layer = font.glyphs["a"].layers['FBCA074D-FCF3-427E-A700-7E318A949AE5']
        # 對於主板圖層，使用主板的ID
        layer = font.glyphs["a"].layers[font.masters[0].id]
        """
    @property
    def attributes(self) -> 'dict':
        """
        -> `dict` 字典

        圖層屬性，如 axisRules, coordinates, colorPalette, sbixSize, color, svg
        ```            
        axis = font.axes[0]
        layer.attributes["axisRules"] = {axis.axisId: {'min': 100}}
        layer.attributes["coordinates"] = {axis.axisId: 99}
        layer.attributes["colorPalette"] = 2
        """
    @attributes.setter
    def attributes(self, value: dict): ...

    @property
    def color(self) -> 'int':
        """
        -> `int` 整數

        UI中的圖層顏色標籤
        ```            
        layer.color = 0     # 紅色
        layer.color = 1     # 橙色
        layer.color = 2     # 褐色
        layer.color = 3     # 黃色
        layer.color = 4     # 淺綠色
        layer.color = 5     # 深綠色
        layer.color = 6     # 淺藍色
        layer.color = 7     # 藍色
        layer.color = 8     # 紫色
        layer.color = 9     # 洋紅色
        layer.color = 10    # 灰色
        layer.color = 11    # 深灰色
        layer.color = None  # 未標記，白色（在版本1235之前，使用-1）
        """
    @color.setter
    def color(self, value: int): ...

    @property
    def colorObject(self) -> 'NSColor':
        """
        -> `NSColor` 顏色物件

        圖層顏色的NSColor物件，用於插件中的繪製。
        ```            
        # 使用圖層顏色繪製輪廓
        layer.colorObject.set()
        # 獲取RGB（和alpha）值（作為0..1的浮點數，必要時乘以256）
        R, G, B, A = layer.colorObject.colorUsingColorSpace_(NSColorSpace.genericRGBColorSpace()).getRed_green_blue_alpha_(None, None, None, None)
        print(R, G, B)
        >> 0.617805719376 0.958198726177 0.309286683798
        print(round(R * 256), int(G * 256), int(B * 256))
        >> 158 245 245
        # 繪製圖層
        layer.bezierPath.fill()
        # 設定圖層顏色。
        layer.colorObject = NSColor.colorWithDeviceRed_green_blue_alpha_(247.0 / 255.0, 74.0 / 255.0, 62.9 / 255.0, 1)
        """
    @colorObject.setter
    def colorObject(self, value: NSColor): ...

    @property
    def components(self) -> List[GSComponent]:
        """
        -> `List[GSComponent]` 組件串列

        這只是一個幫助代理，用於疊代所有組件（不包括路徑）。要新增/刪除項目，請使用`GSLayer.shapes`。
        ```            
        for component in layer.components:
            print(component)
        """
    @property
    def guides(self) -> List[GSGuide]:
        """
        -> `List[GSGuide]` 參考線串列
        ```            
        # 取用所有參考線
        for guide in layer.guides:
            print(guide)
        # 新增參考線
        newGuide = GSGuide()
        newGuide.position = NSPoint(100, 100)
        newGuide.angle = -10.0
        layer.guides.append(newGuide)
        # 刪除參考線
        del layer.guides[0]
        # 從另一個圖層拷貝參考線
        import copy
        layer.guides = copy.copy(anotherlayer.guides)
        """
    @guides.setter
    def guides(self, value: List[GSGuide]): ...
    @guides.deleter
    def guides(self): ...

    @property
    def annotations(self) -> List[GSAnnotation]:
        """
        -> `List[GSAnnotation]` 註記串列
        ```            
        # 取用所有註記
        for annotation in layer.annotations:
            print(annotation)
        # 新增新註記
        newAnnotation = GSAnnotation()
        newAnnotation.type = TEXT
        newAnnotation.text = '靠，這曲線太醜了！'
        layer.annotations.append(newAnnotation)
        # 刪除註記
        del layer.annotations[0]
        # 從另一個圖層拷貝註記
        import copy
        layer.annotations = copy.copy(anotherlayer.annotations)
        """
    @annotations.setter
    def annotations(self, value: List[GSAnnotation]): ...
    @annotations.deleter
    def annotations(self): ...
    @property
    def hints(self) -> List[GSHint]:
        """
        -> `List[GSHint]` Hint清單
        ```
        # 取用所有Hints
        for hint in layer.hints:
            print(hint)
        # 新增一個新Hint
        newHint = GSHint()
        # 在這裡更改Hint的附加節點等行為
        layer.hints.append(newHint)
        # 刪除Hint
        del layer.hints[0]
        # 從另一個圖層拷貝Hints
        import copy
        layer.hints = copy.copy(anotherlayer.hints)
        # 記得用新圖層的節點重新連接Hints
        """
    @hints.setter
    def hints(self, value: List[GSHint]): ...
    @hints.deleter
    def hints(self): ...

    @property
    def anchors(self) -> Union[List[GSAnchor], 'dict']:
        """
        -> `List[GSAnchor]` 錨點串列或 `dict` 字典
        ```            
        # 取用所有錨點
        for a in layer.anchors:
            print(a)
        # 新增一個新錨點
        layer.anchors['top'] = GSAnchor()
        # 刪除錨點
        del layer.anchors['top']
        # 從另一個圖層拷貝錨點
        import copy
        layer.anchors = copy.copy(anotherlayer.anchors)
        """
    @anchors.setter
    def anchors(self, value: Union[List[GSAnchor], 'dict']): ...
    @anchors.deleter
    def anchors(self): ...

    @property
    def shapes(self) -> List[GSShape | GSPath | GSComponent]:
        """
        -> `List[GSShape | GSPath | GSComponent]` 形狀（路徑、組件）串列
        ```            
        # 取用所有形狀
        for shape in layer.shapes:
            print(shape)
        # 刪除形狀
        del layer.shapes[0]
        # 從另一個圖層拷貝形狀
        import copy
        layer.shapes = copy.copy(anotherlayer.shapes)
        """
    @shapes.setter
    def shapes(self, value: List[GSShape | GSPath | GSComponent]): ...
    @shapes.deleter
    def shapes(self): ...

    @property
    def paths(self) -> List[GSPath]:
        """
        -> `List[GSPath]` 路徑串列

        這只是一個幫助代理，用於疊代所有路徑（不包括組件）。要新增/刪除項目，請使用`GSLayer.shapes`。
        ```            
        # 取用所有路徑
        for path in layer.paths:
            print(path)
        """
    @property
    def selection(self) -> List[GSNode | GSAnchor | GSShape | GSPath]:
        """
        -> `List[GSNode | GSAnchor | GSShape | GSPath]` 選中物件串列

        此串列包含所有選中的項目，包括節點、錨點、參考線等。如果要專門處理節點，則可能需要反覆走訪節點（或錨點等），並檢查它們是否被選中。參見下面的示例。
        ```            
        # 取用所有選中的節點
        for path in layer.paths:
            for node in path.nodes: #（或path.anchors等）
                print(node.selected)
        # 清除選擇
        layer.clearSelection()
        """
    @selection.setter
    def selection(self, value: List[GSNode | GSAnchor | GSShape | GSPath]): ...
    @selection.deleter
    def selection(self): ...

    @property
    def LSB(self) -> 'float':
        """
        -> `float` 浮點數

        左邊距
        """
    @LSB.setter
    def LSB(self, value: float): ...

    @property
    def RSB(self) -> 'float':
        """
        -> `float` 浮點數

        右邊距
        """
    @RSB.setter
    def RSB(self, value: float): 
        ...

    @property
    def TSB(self) -> 'float':
        """
        -> `float` 浮點數

        上邊距
        """
    @TSB.setter
    def TSB(self, value: float): ...

    @property
    def BSB(self) -> 'float':
        """
        -> `float` 浮點數

        下邊距
        """
    @BSB.setter
    def BSB(self, value: float): ...

    @property
    def width(self) -> 'float':
        """
        -> `float` 浮點數

        圖層寬度
        """
    @width.setter
    def width(self, value: float): ...

    @property
    def vertWidth(self) -> Optional[float]:
        """
        -> `float` 浮點數或 `None`

        圖層垂直寬度，
        將其設定為 `None` 以將其重設為預設值

        2.6.2版新增
        """
    @vertWidth.setter
    def vertWidth(self, value: Optional[float]): ...

    @property
    def vertOrigin(self) -> Optional[float]:
        """
        -> `float` 浮點數或 `None`

        圖層垂直原點，
        將其設定為 `None` 以將其重設為預設值

        2.6.2版新增
        """
    @vertOrigin.setter
    def vertOrigin(self, value: Optional[float]): ...

    @property
    def ascenter(self) -> 'float':
        """
        -> `float` 浮點數

        圖層上伸

        3.0.2版新增
        """
    @ascenter.setter
    def ascenter(self, value: float): ...

    @property
    def descender(self) -> 'float':
        """
        -> `float` 浮點數

        圖層下伸

        3.0.2版新增
        """
    @descender.setter
    def descender(self, value: float): ...

    @property
    def leftMetricsKey(self) -> 'str':
        """
        -> `str` 字串

        字符的左側度量鍵。引用自另一個字符的名稱或公式。用於與連結的字符同步度量。
        """
    @leftMetricsKey.setter
    def leftMetricsKey(self, value: str): ...
    @leftMetricsKey.deleter
    def leftMetricsKey(self): ...

    @property
    def rightMetricsKey(self) -> 'str':
        """
        -> `str` 字串

        字符的右側度量鍵。引用自另一個字符的名稱或公式。用於與連結的字符同步度量。
        """
    @rightMetricsKey.setter
    def rightMetricsKey(self, value: str): ...
    @rightMetricsKey.deleter
    def rightMetricsKey(self): ...

    @property
    def widthMetricsKey(self) -> 'str':
        """
        -> `str` 字串

        字符的寬度度量鍵。引用自另一個字符的名稱或公式。用於與連結的字符同步度量。
        """
    @widthMetricsKey.setter
    def widthMetricsKey(self, value: str): ...
    @widthMetricsKey.deleter
    def widthMetricsKey(self): ...

    @property
    def bounds(self) -> 'NSRect':
        """
        -> `NSRect` 矩形（唯讀）

        整個字符的邊界框
        ```            
        # 原點
        print(layer.bounds.origin.x, layer.bounds.origin.y)
        # 尺寸
        print(layer.bounds.size.width, layer.bounds.size.height)
        """
    @property
    def selectionBounds(self) -> 'NSRect':
        """
        -> `NSRect` 矩形（唯讀）

        圖層選擇的邊界框（節點、錨點、組件等）
        """
    @property
    def metrics(self) -> 'GSMetricValue':
        """
        -> `GSMetricValue` 度量值

        度量圖層是一個特定於此圖層的水平度量列表。請使用此屬性，而不是`master.alignmentZones`。
        
        3.0.1版新增
        """
    @metrics.setter
    def metrics(self, value: GSMetricValue): ...
    
    @property
    def background(self) -> 'GSLayer':
        """
        -> `GSLayer` 圖層

        背景圖層
        ```            
        # 將圖層拷貝到其背景
        layer.background = layer.copy()
        # 刪除背景圖層
        layer.background = None
        """
    @background.setter
    def background(self, value: GSLayer): ...
    @background.deleter
    def background(self): ...

    @property
    def backgroundImage(self) -> 'GSBackgroundImage':
        """
        -> `GSBackgroundImage` 背景圖片

        它將被縮放，以至於1 em單位等於圖片的1像素。
        ```            
        # 設定背景圖片
        layer.backgroundImage = GSBackgroundImage('/path/to/file.jpg')
        # 移除背景圖片
        layer.backgroundImage = None
        """
    @backgroundImage.setter
    def backgroundImage(self, value: GSBackgroundImage): ...
    @backgroundImage.deleter
    def backgroundImage(self): ...
    
    @property
    def bezierPath(self) -> 'NSBezierPath':
        """
        -> `NSBezierPath` 貝茲路徑

        作為NSBezierPath物件的圖層。用於在插件中繪製字符。
        ```            
        # 將路徑繪製到編輯畫面中
        NSColor.redColor().set()
        layer.bezierPath.fill()
        """
    @bezierPath.setter
    def bezierPath(self, value: NSBezierPath): ...
    @bezierPath.deleter
    def bezierPath(self): ...

    @property
    def openBezierPath(self) -> 'NSBezierPath':
        """
        -> `NSBezierPath` 貝茲路徑

        作為NSBezierPath物件的圖層的所有開放路徑。用於在插件中繪製字符的輪廓。
        ```            
        # 將路徑繪製到編輯畫面中
        NSColor.redColor().set()
        layer.openBezierPath.stroke()
        """
    @openBezierPath.setter
    def openBezierPath(self, value: NSBezierPath): ...
    @openBezierPath.deleter
    def openBezierPath(self): ...

    @property
    def completeBezierPath(self) -> 'NSBezierPath':
        """
        -> `NSBezierPath` 貝茲路徑

        作為NSBezierPath物件的圖層，包括組件的路徑。用於在插件中繪製字符。
        ```            
        # 將路徑繪製到編輯畫面中
        NSColor.redColor().set()
        layer.completeBezierPath.fill()
        """
    @completeBezierPath.setter
    def completeBezierPath(self, value: NSBezierPath): ...
    @completeBezierPath.deleter
    def completeBezierPath(self): ...

    @property
    def completeOpenBezierPath(self) -> 'NSBezierPath':
        """
        -> `NSBezierPath` 貝茲路徑

        作為NSBezierPath物件的圖層的所有開放路徑，包括組件的路徑。用於在插件中繪製字符的輪廓。
        ```            
        # 將路徑繪製到編輯畫面中
        NSColor.redColor().set()
        layer.completeOpenBezierPath.stroke()
        """
    @completeOpenBezierPath.setter
    def completeOpenBezierPath(self, value: NSBezierPath): ...
    @completeOpenBezierPath.deleter
    def completeOpenBezierPath(self): ...

    @property
    def isAligned(self) -> 'bool':
        """
        -> `bool` 布林值

        指示組件是否自動對齊。
        """
    
    @property
    def isSpecialLayer(self) -> 'bool':
        """
        -> `bool` 布林值

        如果圖層是支架、括號或智慧組件圖層，則回傳True
        """

    @property
    def isMasterLayer(self) -> 'bool':
        """
        -> `bool` 布林值

        如果是主板圖層則回傳True
        """

    @property
    def italicAngle(self) -> 'float':
        """
        -> `float` 浮點數

        適用於此圖層的斜體角度
        """
    @italicAngle.setter
    def italicAngle(self, value: float): ...

    @property
    def visible(self) -> 'bool':
        """
        -> `bool` 布林值

        如果圖層可見（圖層面板中的眼睛圖示）則回傳True
        """
    @visible.setter
    def visible(self, value: bool): ...
    
    @property
    def userData(self) -> Dict[str, Union[bool, str, List, Dict, float, bytes]]:
        """
        -> `dict` 字典

        用於儲存用戶資料的字典。使用不重複鍵，僅使用可以儲存在屬性列表中的物件（字符串，列表，字典，數字，NSData），否則資料將無法從儲存的檔案中恢復。
        ```            
        # 設定值
        layer.userData['rememberToMakeCoffee'] = True
        # 刪除值
        del layer.userData['rememberToMakeCoffee']
        """
    @userData.setter
    def userData(self, value: Dict[str, Union[bool, str, List, Dict, float, bytes]]): ...
    @userData.deleter
    def userData(self): ...

    @property
    def tempData(self) -> 'dict':
        """
        -> `dict` 字典

        用於暫存資料的字典。使用不重複鍵。此資料不會儲存在檔案中。如果需要持續資料，請使用`layer.userData`
        ```            
        # 設定值
        layer.tempData['rememberToMakeCoffee'] = True
        # 刪除值
        del layer.tempData['rememberToMakeCoffee']
        """
    @tempData.setter
    def tempData(self, value: Dict[str, Union[bool, str, List, Dict, float, bytes]]): ...
    @tempData.deleter
    def tempData(self): ...

    @property
    def smartComponentPoleMapping(self) -> Dict[GSSmartComponentAxis, int]: 
        """
        -> `Dict[GSSmartComponentAxis, int]` 智慧組件軸字典

        將此圖層對應到智慧字符的內插軸極。字典鍵是`GSSmartComponentAxis`物件的名稱。值為1表示底部極，值為2表示頂部極。對應於字符的“智慧字符設定選項”對話框的“圖層”分頁。
        參見 https://glyphsapp.com/tutorials/smart-components 。
        ```            
        # 將圖層對應到頂部和底部極
        crotchDepthAxis = glyph.smartComponentAxes['crotchDepth']
        shoulderWidthAxis = glyph.smartComponentAxes['shoulderWidth']
        for layer in glyph.layers:
            # 一般圖層
            if layer.name == 'Regular':
                layer.smartComponentPoleMapping[crotchDepthAxis.id] = 2
                layer.smartComponentPoleMapping[shoulderWidthAxis.id] = 2
            # 窄圖層
            elif layer.name == 'NarrowShoulder':
                layer.smartComponentPoleMapping[crotchDepthAxis.id] = 2
                layer.smartComponentPoleMapping[shoulderWidthAxis.id] = 1
            # 扁圖層
            elif layer.name == 'LowCrotch':
                layer.smartComponentPoleMapping[crotchDepthAxis.id] = 1
                layer.smartComponentPoleMapping[shoulderWidthAxis.id] = 2
        """
    @smartComponentPoleMapping.setter
    def smartComponentPoleMapping(self, value: Dict[GSSmartComponentAxis, int]):...
    #endregion
    #region 函數(Functions)
    
    def decomposeComponents(self):
        """
        一次分解圖層的所有組件。
        """
    def decomposeCorners(self):
        """
        一次分解圖層的所有角。

        2.4版新增
        """
    def compareString(self) -> 'str':
        """
        回傳表示字符輪廓結構的字串，用於相容性比較。
        ```            
        print(layer.compareString())
        >> oocoocoocoocooc_oocoocoocloocoocoocoocoocoocoocoocooc_
        """

    def connectAllOpenPaths(self):
        """
        當端點彼此之間的距離超過1單位時，關閉所有開放路徑。
        """
    def copyDecomposedLayer(self) -> 'GSLayer':
        """
        回傳一個圖層的副本，其中所有的組件都被分解了。
        """

    def syncMetrics(self):
        """
        從連接的字符接管LSB和RSB。
        ```            
        # 同步此字符所有圖層的度量
        for layer in glyph.layers:
            layer.syncMetrics()
        """
    def correctPathDirection(self):
        """
        修正路徑方向。
        """
    def removeOverlap(self, checkSelection: bool = False):
        """
        加入所有輪廓。

        參數：
        - checkSelection – 如果選擇將被考慮。預設值：False
        """
    def roundCoordinates(self):
        """
        將所有坐標的位置四捨五入到格線（在字型資訊中設定的大小）。
        """
    def addNodesAtExtremes(self, force: bool = False, checkSelection: bool = False):
        """
        在路徑的極端位置（例如頂部、底部等）新增節點。

        參數：
        - force – 強制加上極點，即使這可能扭曲形狀
        - checkSelection – 只處理選中的線段
        """
    def applyTransform(self, transform) -> 'list':
        """
        對圖層應用的變形矩陣。

        ```            
        layer.applyTransform([
            0.5, # x 縮放因素向量
            0.0, # x 傾斜因素向量
            0.0, # y 縮放因素向量
            0.5, # y 傾斜因素向量
            0.0, # x 位置
            0.0  # y 位置
        ])
        from Foundation import NSAffineTransform, NSMidX, NSMidY
        bounds = Layer.bounds
        transform = NSAffineTransform.new()
        transform.translateXBy_yBy_(NSMidX(bounds), NSMidY(bounds))
        transform.rotateByDegrees_(-30)
        transform.translateXBy_yBy_(-NSMidX(bounds), -NSMidY(bounds))
        Layer.applyTransform(transform)
        
        參數：
        - transform – 一個包含6個數字的列表，一個 NSAffineTransform 或一個 NSAffineTransformStruct
        """
    def transform(self, 
               tramsform: 'NSAffineTransform',
               selection: bool=False, 
               components: bool=True
               ):
        """
        在圖層應用`NSAffineTransform`。

        參數：
        - transform：一個`NSAffineTransform`
        - selection：是否檢查選擇
        - components：是否對組件進行變換
        ```        
        transformation = NSAffineTransform()
        transformation.rotate(45, (200, 200))
        layer.transform(transformation)
        """
    def beginChanges(self):
        """
        在對圖層進行較大變更之前呼叫此函數。這將提高性能並防止撤銷問題。如果完成了，請確保呼叫`layer.endChanges()`
        """
    def endChanges(self):
        """
        如果之前呼叫了`layer.beginChanges`，請呼叫此函數。確保適當地分組這兩個呼叫。
        """
    def cutBetweenPoints(self, point1: 'NSPoint', point2: 'NSPoint'):
        """
        在點1和點2之間切割所有路徑
        ```            
        # 在y=100處水平切割字符
        layer.cutBetweenPoints(NSPoint(0, 100), NSPoint(layer.width, 100))
        """
    def intersections(self) -> 'list':
        """
        回傳圖層中重疊路徑之間所有交點的清單。
        """

    def intersectionsBetweenPoints(self, 
                                point1: 'NSPoint', 
                                point2: 'NSPoint', 
                                components: bool=False, 
                                ignoreLocked: bool=False
                                ) -> 'NSPoint':
        """
        回傳圖層中測量線和路徑間的所有交點。基本上這與UI中的測量工具相同。

        通常，第一個回傳的點是起點，最後一個回傳的點是終點。因此，第二個點是第一個交點，倒數第二個點是最後一個交點。
        ```            
        # 顯示y=100處的所有交點
        intersections = layer.intersectionsBetweenPoints((-1000, 100), (layer.width+1000, 100))
        print(intersections)
        # 測量線的左側附距
        print(intersections[1].x)
        # 測量線的右側附距
        print(layer.width - intersections[-2].x)
        """

    def addMissingAnchors(self):
        """
        在字符數據庫中新增遺失錨點的定義。
        """
    def clearSelection(self):
        """
        取消選擇圖層中的所有選中項。
        """
    def clear(self):
        """
        從圖層中刪除所有元素。
        """
    def swapForegroundWithBackground(self):
        """
        交換前景與背景圖層。
        """
    def reinterpolate(self):
        """
        根據其他圖層和其內內插重新內插圖層。

        適用於主板圖層和支架圖層，等同於圖層面板中的“重新內插”指令。
        """
    #endregion
        
class GSAnchor(): # 類別
    """
    錨點物件的實作。

    有關如何取用它們的詳細訊息，請查看`GSLayer.anchors`
    """
    def __init__(self, name: str, pt: 'NSPoint'):
        """
        參數：
        - name – 錨點的名稱
        - pt – 錨點的位置
        """
        self.position = NSPoint()

    #region 屬性(Properties)
    @property
    def position(self) -> 'NSPoint':
        """
        -> `NSPoint` 位置

        錨點的位置
        ```            
        # 讀取位置
        print(layer.anchors['top'].position.x, layer.anchors['top'].position.y)
        # 設定位置
        layer.anchors['top'].position = NSPoint(175, 575)
        # 增加50個單位的垂直位置
        layer.anchors['top'].position = NSPoint(layer.anchors['top'].position.x, layer.anchors['top'].position.y + 50)
        """
    @position.setter
    def position(self, value: NSPoint): ...

    @property
    def name(self) -> 'str':
        """
        -> `str` 字串
        
        錨點名稱
        """
    @name.setter
    def name(self, value: str): ...

    @property
    def selected(self) -> 'bool':
        """
        -> `bool` 布林值

        UI中的錨點選擇狀態。
        ```            
        # 選擇錨點
        layer.anchors[0].selected = True
        # 記錄選擇狀態
        print(layer.anchors[0].selected)
        """
    @selected.setter
    def selected(self, value: bool): ...

    @property
    def orientation(self) -> 'int':
        """
        -> `int` 整數

        錨點的相對位置：左邊界（0）、中心（2）或右邊界（1）。
        """
    @orientation.setter
    def orientation(self, value: int): ...

    @property
    def userData(self) -> Dict[str, Union[bool, str, List, Dict, float, bytes]]:
        """
        -> `dict` 字典

        用於儲存用戶資料的字典。使用不重複鍵，僅使用可以儲存在屬性列表中的物件（字符串，列表，字典，數字，NSData），否則資料將無法從儲存的檔案中恢復。
        ```            
        # 設定值
        anchor.userData['rememberToMakeCoffee'] = True
        # 刪除值
        del component.userData['rememberToMakeCoffee']

        3.0版新增
        """
    @userData.setter
    def userData(self, value: Dict[str, Union[bool, str, List, Dict, float, bytes]]): ...
    @userData.deleter
    def userData(self): ...
    #endregion

class GSComponent(): # 類別
    """
    組件物件的實作。

    有關如何取用它們的詳細訊息，請查看`GSLayer.components`
    """
    def __init__(self, glyph: 'GSGlyph', position: 'NSPoint'):
        """
        參數：
        - glyph – 一個`GSGlyph`物件或字符名稱
        - position – 組件的位置為`NSPoint`
        """
        self.position = NSPoint()
        self.component = GSGlyph()
        self.componentLayer = GSLayer()
        self.transform = NSAffineTransformStruct()
        self.bounds = NSRect()
        self.bezierPath = NSBezierPath()
        
    #region 屬性(Properties)
    @property
    def position(self) -> 'NSPoint':
        """
        -> `NSPoint` 位置

        組件的位置
        """
    @position.setter
    def position(self, value: 'NSPoint'): ...

    @property
    def scale(self) -> 'tuple':
        """
        -> `tuple` 元組

        組件的縮放因子。

        包含水平和垂直縮放的元組。
        """
    @scale.setter
    def scale(self, value: 'tuple'): ...

    @property
    def rotation(self) -> 'float':
        """
        -> `float` 浮點數

        組件的旋轉角度
        """
    @rotation.setter
    def rotation(self, value: 'float'): ...

    @property
    def componentName(self) -> 'str':
        """
        -> `str` 字串
        
        組件指向的字符名稱
        """
    @componentName.setter
    def componentName(self, value: 'str'): ...

    @property
    def name(self) -> 'str':
        """
        -> `str` 字串
        
        組件指向的字符名稱

        2.5版新增
        """
    @name.setter
    def name(self, value: 'str'): ...

    @property
    def componentMasterId(self) -> 'str':
        """
        -> `str` 字串
        
        組件指向的主板ID

        3.1版新增
        """
    @componentMasterId.setter
    def componentMasterId(self, value: 'str'): ...

    @property
    def component(self) -> 'GSGlyph':
        """
        -> `GSGlyph` 字符（唯讀）

        要更改引用的基本字符，請將`componentName`設定為新的字符名稱。
        """
    @property
    def componentLayer(self) -> 'GSLayer':
        """
        -> `GSLayer` 圖層（唯讀）
        
        要更改引用的基本字符，請將`componentName`設定為新的字符名稱。
        
        對於智慧組件，`componentLayer`包含內插結果。

        2.5版新增
        """
    @property
    def transform(self) -> 'NSAffineTransformStruct':
        """
        -> `NSAffineTransformStruct` 結構

        組件的變換矩陣。如果是Glyphs 3，則從縮放、旋轉和位置計算。
        ```            
        component.transform = ((
            0.5, # x 縮放因子
            0.0, # x 傾斜因子
            0.0, # y 傾斜因子
            0.5, # y 縮放因子
            0.0, # x 位置
            0.0  # y 位置
        ))
        """
    @transform.setter
    def transform(self, value: 'NSAffineTransformStruct'): ...

    @property
    def bounds(self) -> 'NSRect':
        """
        -> `NSRect` 矩形（唯讀）

        組件的邊界框
        ```            
        component = layer.components[0] # 第一個組件
        # 原點
        print(component.bounds.origin.x, component.bounds.origin.y)
        # 尺寸
        print(component.bounds.size.width, component.bounds.size.height)
        """
    @property
    def automaticAlignment(self) -> 'bool':
        """
        -> `bool` 布林值

        定義組件是否自動對齊。
        """
    @automaticAlignment.setter
    def automaticAlignment(self, value: 'bool'): ...

    @property
    def alignment(self):
        """
        TODO

        2.5版新增
        """
    @alignment.setter
    def alignment(self, value): ...

    @property
    def locked(self) -> 'bool':
        """
        -> `bool` 布林值

        如果組件被鎖定，則回傳True (TODO)

        2.5版新增
        """
    @locked.setter
    def locked(self, value: 'bool'): ...

    @property
    def anchor(self) -> 'str':
        """
        -> `str` 字串

        如果有多個 錨點 / _錨點 配對符合，則可以使用此屬性來設定用於自動對齊的錨點。
        
        這可以從組件資訊框中的錨點按鈕設定。
        """
    @anchor.setter
    def anchor(self, value: 'str'): ...

    @property
    def selected(self) -> 'bool':
        """
        -> `bool` 布林值

        UI中的組件選擇狀態。
        ```            
        # 選擇組件
        layer.components[0].selected = True
        # 記錄選擇狀態
        print(layer.components[0].selected)
        """
    @selected.setter
    def selected(self, value: 'bool'): ...

    @property
    def attributes(self) -> 'dict':
        """
        -> `dict` 字典

        組件的屬性，如`mask`或`reversePaths`。
        ```            
        component.attributes['mask'] = True
        component.attributes['reversePaths'] = True
        """
    @attributes.setter
    def attributes(self, value: 'dict'): ...

    @property
    def smartComponentValues(self) -> Union[Dict[str, int], int, None]:
        """
        -> `dict` 字典

        智慧組件的內插值字典。鍵是軸的ID，值在對應的`GSSmartComponentAxis`物件的頂部和底部值之間。對應於“智慧組件設定選項”對話框的值。如果組件不是智慧組件，則回傳None。

        對於新設定的智慧字符，軸ID是隨機字符串。若儲存並重新打開檔案名稱和ID會維持相同。因此只要不更改名稱，就可以安全地透過智慧字符 > 軸 > ID 使用（如下面的代碼示例所述）。

        參見 https://glyphsapp.com/tutorials/smart-components 以供參考。
        ```            
        component = glyph.layers[0].shapes[1]
        widthAxis = component.component.smartComponentAxes['Width']
        components.smartComponentValues[widthAxis.id] = 45
        # 檢查組件是否是智慧組件
        for component in layer.components:
            if component.smartComponentValues is not None:
                # 做一些事情
        """
    @smartComponentValues.setter
    def smartComponentValues(self, value: Union[Dict[str, int], int, None]): ...
    @smartComponentValues.deleter
    def smartComponentValues(self): ...

    @property
    def bezierPath(self) -> 'NSBezierPath':
        """
        -> `NSBezierPath` 貝茲路徑

        作為NSBezierPath物件的組件。用於在插件中繪製字符。
        ```            
        # 將路徑繪製到編輯畫面中
        NSColor.redColor().set()
        layer.components[0].bezierPath.fill()
        """
    @bezierPath.setter
    def bezierPath(self, value: NSBezierPath): ...
    @bezierPath.deleter
    def bezierPath(self): ...

    @property
    def userData(self) -> Dict[str, Union[bool, str, List, Dict, float, bytes]]:
        """
        -> `dict` 字典

        用於儲存用戶資料的字典。使用不重複鍵，僅使用可以儲存在屬性列表中的物件（字符串，列表，字典，數字，NSData），否則資料將無法從儲存的檔案中恢復。
        ```            
        # 設定值
        component.userData['rememberToMakeCoffee'] = True
        # 刪除值
        del component.userData['rememberToMakeCoffee']

        2.5版新增
        """
    @userData.setter
    def userData(self, value: Dict[str, Union[bool, str, List, Dict, float, bytes]]): ...
    @userData.deleter
    def userData(self): ...

    @property
    def tempData(self) -> 'dict':
        """
        -> `dict` 字典

        用於暫存資料的字典。使用不重複鍵。此資料不會儲存在檔案中。如果需要持續資料，請使用`component.userData`
        ```            
        # 設定值
        component.tempData['rememberToMakeCoffee'] = True
        # 刪除值
        del component.tempData['rememberToMakeCoffee']
        """
    @tempData.setter
    def tempData(self, value: Dict[str, Union[bool, str, List, Dict, float, bytes]]): ...
    @tempData.deleter
    def tempData(self): ...

    #endregion
    #region 函數(Functions)
    def decompose(self, 
               doAnchors: bool = True, 
               doHints: bool = True
               ):
        """
        分解組件。

        參數：
        - doAnchors – 從組件中取得錨點
        - doHints – 從組件中取得Hints
        """
    def applyTransform(self):
        """
        對組件應用變形矩陣。

        ```            
        component.applyTransform((
            0.5, # x 縮放因子
            0.0, # x 傾斜因子
            0.0, # y 傾斜因子
            0.5, # y 縮放因子
            0.0, # x 位置
            0.0  # y 位置
        ))
        """
    #endregion

class GSGlyphReference(): # 類別
    """
    一個小幫手類別用於在userData中儲存對字符的參考，將追踪字符名稱的變化。

    3.0.4版新增
    """
    def __init__(self):
        self.glyph = GSGlyph()

    #region 屬性(Properties)
    @property
    def glyph(self) -> 'GSGlyph':
        """
        -> `GSGlyph` 字符

        要保持追踪的字符物件
        ```
        glyphReference = GSGlyphReference(font.glyphs["A"])
        """
    @glyph.setter
    def glyph(self, value: 'GSGlyph'): ...
    @glyph.deleter
    def glyph(self): ...

    #endregion
        
class GSSmartComponentAxis(): # 類別
    """
    智慧組件內插軸物件的實作。

    有關如何取用它們的詳細訊息，請查看`GSGlyph.smartComponentAxes`

    2.3版新增
    """
    #region 屬性(Properties)
    @property
    def name(self) -> 'str':
        """
        -> `str` 字串

        軸的名稱。名稱僅供顯示目的。
        """
    @property
    def id(self) -> 'str':
        """
        -> `str` 字串
        
        軸的ID。此ID用於將智慧字符的圖層對應到內插的極點。參見`GSLayer.smartComponentPoleMapping`

        2.5版新增
        """

    @property
    def topValue(self) -> Union['int', 'float']:
        """
        -> `int` 整數或 `float` 浮點數

        內插軸上的頂端（極）值。
        """
    @topValue.setter
    def topValue(self, value: Union['int', 'float']): ...

    @property
    def bottomValue(self) -> Union['int', 'float']:
        """
        -> `int` 整數或 `float` 浮點數

        內插軸上的底端（極）值。
        """
    @bottomValue.setter
    def bottomValue(self, value: Union['int', 'float']): ...

    #endregion
        
class GSShape(): # 類別
    """
    形狀物件的實作。

    有關如何取用它們的詳細訊息，請查看`GSLayer.shapes`
    """
    #region 屬性(Properties)
    # @property
    # def position(self) -> 'NSPoint':
    @property
    def locked(self) -> 'bool':
        """
        -> `bool` 布林值

        形狀的鎖定狀態
        """
    @locked.setter
    def locked(self, value: 'bool'): ...

    @property
    def shapeType(self) -> 'int':
        """
        -> `int` 整數

        形狀的類型。可以是路徑或組件的形狀類型。
        """
    #endregion
        
class GSPath(): # 類別
    """
    路徑物件的實作。

    有關如何取用它們的詳細訊息，請查看`GSLayer.paths`

    如果在程式碼中建立路徑，請確保結構是有效的。曲線節點必須由兩個離線節點前置。開放路徑必須以線節點開始。
    """
    def __init__(self):
        self.parent = GSLayer()
        self.bounds = NSRect()
        self.bezierPath = NSBezierPath()

    #region 屬性(Properties)
    @property
    def parent(self) -> 'GSLayer':
        """
        -> `GSLayer` 圖層

        對圖層物件的引用
        """

    @property
    def nodes(self) -> List[GSNode]:
        """
        -> `List[GSNode]` 節點串列
        ```            
        # 取用所有節點
        for path in layer.paths:
            for node in path.nodes:
                print(node)
        """
    @nodes.setter
    def nodes(self, value: List[GSNode]): ...

    @property
    def segments(self) -> List[NSPoint]:
        """
        -> `List[NSPoint]` 節段串列

        兩個物件代表一條線，四個代表一個曲線。包含線段的起點。

        ```            
        # 取用所有段
        for path in layer.paths:
            for segment in path.segments:
                print(segment)
        """
    @segments.setter
    def segments(self, value: List[NSPoint]): ...

    @property
    def closed(self) -> 'bool':
        """
        -> `bool` 布林值

        如果路徑是封閉的則回傳True
        """

    @property
    def direction(self) -> 'int':
        """
        -> `int` 整數

        路徑方向，-1表示逆時針，1表示順時針。
        """
    @direction.setter
    def direction(self, value: 'int'): 
        if value not in (-1, 1):
            raise ValueError('Direction must be -1 or 1')

    @property
    def bounds(self) -> 'NSRect':
        """
        -> `NSRect` 矩形（唯讀）

        路徑的邊界框
        ```            
        path = layer.paths[0] # 第一條路徑
        # 原點
        print(path.bounds.origin.x, path.bounds.origin.y)
        # 尺寸
        print(path.bounds.size.width, path.bounds.size.height)
        """
    @property
    def selected(self) -> 'bool':
        """
        -> `bool` 布林值

        UI 中的路徑選擇狀態。
        ```            
        # 選擇路徑
        layer.paths[0].selected = True
        # 記錄選擇狀態
        print(layer.paths[0].selected)
        """
    @selected.setter
    def selected(self, value: 'bool'): ...

    @property
    def bezierPath(self) -> 'NSBezierPath':
        """
        -> `NSBezierPath` 貝茲路徑

        作為NSBezierPath物件的相同路徑。用於在插件中繪製字符。
        ```            
        # 將路徑繪製到編輯畫面中
        NSColor.redColor().set()
        layer.paths[0].bezierPath.fill()
        """
    @bezierPath.setter
    def bezierPath(self, value: 'NSBezierPath'): ...
    @bezierPath.deleter
    def bezierPath(self): ...

    @property
    def attributes(self) -> 'dict':
        """
        -> `dict` 字典

        路徑屬性，如`fill`、`mask`、`strokeWidth`、`strokeHeight`、`strokeColor`和`strokePos`
        ```            
        # 在黑白圖層中:
        path.attributes['fill'] = True
        path.attributes['mask'] = True
        path.attributes['strokeWidth'] = 100
        path.attributes['strokeHeight'] = 80
        # 在彩色圖層中:
        path.attributes['strokeColor'] = NSColor.redColor()
        path.attributes['fillColor'] = NSColor.blueColor()
        path.attributes['strokePos'] = 1
        """
    @attributes.setter
    def attributes(self, value: 'dict'): ...

    @property
    def tempData(self) -> 'dict':
        """
        -> `dict` 字典

        用於暫存資料的字典。使用不重複鍵。此資料不會儲存在檔案中。如果需要持續資料，請使用`path.userData`
        ```            
        # 設定值
        path.tempData['rememberToMakeCoffee'] = True
        # 刪除值
        del path.tempData['rememberToMakeCoffee']
        """
    @tempData.setter
    def tempData(self, value: Dict[str, Union[bool, str, List, Dict, float, bytes]]): ...
    @tempData.deleter
    def tempData(self): ...
    
    #endregion
    #region 函數(Functions)
    def reverse(self):
        """
        反轉路徑方向
        """
    
    def addNodesAtExtremes(self, 
                        force: bool = False, 
                        checkSelection: bool = False
                        ):
        """
        在路徑的極端位置（例如頂部、底部等）新增節點。

        參數：
        - force – 強制加上極點，即使這可能扭曲形狀
        - checkSelection – 只處理選中的線段
        """
    def applyTransform(self):
        """
        對路徑應用變形矩陣。
        ```            
        path = layer.paths[0]
        path.applyTransform((
            0.5, # x 縮放因子
            0.0, # x 傾斜因子
            0.0, # y 傾斜因子
            0.5, # y 縮放因子
            0.0, # x 位置
            0.0  # y 位置
        ))
        """
    #endregion
        
class GSNode(): # 類別
    """
    節點物件的實作。

    有關如何取用它們的詳細訊息，請查看`GSPath.nodes`
    """
    def __init__(self,
              pt: 'NSPoint',
              type: 'str' = type
              ):
        """
        參數：
        - pt – 節點的位置
        - type – 節點的類型，LINE、CURVE或OFFCURVE
        """
        self.position = NSPoint()
        self.nextNode = GSNode()
        self.prevNode = GSNode()

    #region 屬性(Properties)
    @property
    def position(self) -> 'NSPoint':
        """
        -> `NSPoint` 位置

        節點的位置
        """
    @position.setter
    def position(self, value: 'NSPoint'): ...

    @property
    def type(self) -> 'str':
        """
        -> `str` 字串

        節點的類型：LINE、CURVE 或 OFFCURVE

        始終與常數進行比較，而不是實際值。
        """
    @type.setter
    def type(self, value: 'str'): 
        if value not in ('LINE', 'CURVE', 'OFFCURVE'):
            raise ValueError('Type must be LINE, CURVE or OFFCURVE')

    @property
    def smooth(self) -> 'bool':
        """
        -> `bool` 布林值

        如果是平滑連接則回傳True
        """
    @smooth.setter
    def smooth(self, value: 'bool'): ...

    @property
    def connection(self) -> 'str':
        """
        -> `str` 字串

        自2.3版起已棄用：請改用`smooth`。

        連接的類型，SHARP或SMOOTH
        """
        raise ValueError("Deprecated since 2.3: Use `smooth` instead.")
    @property
    def selected(self) -> 'bool':
        """
        -> `bool` 布林值

        UI 中的節點選擇狀態。
        ```            
        # 選擇節點
        layer.paths[0].nodes[0].selected = True
        # 記錄選擇狀態
        print(layer.paths[0].nodes[0].selected)
        """
    @selected.setter
    def selected(self, value: 'bool'): ...

    @property
    def index(self) -> list | int:
        """
        -> `int` 整數

        節點如果包含在路徑中則回傳索引，否則回傳最大值。
        """

    @property
    def nextNode(self) -> 'GSNode':
        """
        -> `GSNode` 節點

        回傳路徑中的下一個節點。

        請注意，這與節點在路徑中的位置無關，如果目前節點是最後一個節點，則會跳到路徑的開頭。

        如果需要考慮節點在路徑中的位置，請使用節點的索引屬性並將其與路徑長度進行比較。
        ```            
        print(layer.paths[0].nodes[0].nextNode # 回傳路徑中的第二個節點（索引0 + 1))
        print(layer.paths[0].nodes[-1].nextNode # 回傳路徑中的第一個節點（最後一個節點>>跳到路徑開頭))
        # 檢查節點是否是路徑中的最後一個節點（至少有兩個節點）
        print(layer.paths[0].nodes[0].index == (len(layer.paths[0].nodes) - 1)) # 對第一個節點回傳False
        print(layer.paths[0].nodes[-1].index == (len(layer.paths[0].nodes) - 1)) # 對最後一個節點回傳True
        """

    @property
    def prevNode(self) -> 'GSNode':
        """
        -> `GSNode` 節點

        回傳路徑中的上一個節點。

        請注意，這與節點在路徑中的位置無關，如果目前節點是第一個節點，則會跳到路徑的結尾。

        如果需要考慮節點在路徑中的位置，請使用節點的索引屬性並將其與路徑長度進行比較。
        ```            
        print(layer.paths[0].nodes[0].prevNode) # 回傳路徑中的最後一個節點（第一個節點>>跳到路徑結尾))
        print(layer.paths[0].nodes[-1].prevNode) # 回傳路徑中的倒數第二個節點
        # 檢查節點是否是路徑中的第一個節點（至少有兩個節點）
        print(layer.paths[0].nodes[0].index == 0) # 對第一個節點回傳True
        print(layer.paths[0].nodes[-1].index == 0) # 對最後一個節點回傳False
        """

    @property
    def name(self) -> 'str':
        """
        -> `str` 字串

        將一個名稱附加到節點上。
        """
    @name.setter
    def name(self, value: 'str'): ...

    @property
    def orientation(self) -> 'int':
        """
        -> `int` 整數

        節點的相對位置：左邊界（0）、中心（2）或右邊界（1）。
        """
    @orientation.setter
    def orientation(self, value: 'int'): ...

    @property
    def userData(self) -> Dict[str, Union[bool, str, List, Dict, float, bytes]]:
        """
        -> `dict` 字典

        用於儲存用戶資料的字典。使用不重複鍵，僅使用可以儲存在屬性列表中的物件（字符串，列表，字典，數字，NSData），否則資料將無法從儲存的檔案中恢復。
        ```            
        # 設定值
        node.userData['rememberToMakeCoffee'] = True
        # 刪除值
        del node.userData['rememberToMakeCoffee']

        2.4.1版新增
        """
    @userData.setter
    def userData(self, value: Dict[str, Union[bool, str, List, Dict, float, bytes]]): ...
    @userData.deleter
    def userData(self): ...

    #endregion
    #region 函數(Functions)
    def makeNodeFirst(self):
        """
        將此節點變為路徑的起點。
        """
    def toggleConnection(self):
        """
        在銳角和平滑連接之間切換。
        """
    #endregion
        
class GSPathSegment(): # 類別
    """
    線段物件的實作。

    有關如何取用它們的詳細訊息，請查看`GSPath.segments`
    """
    def __init__(self):
        self.bounds = NSRect()
    #region 屬性(Properties)
    @property
    def bounds(self) -> 'NSRect':
        """
        -> `NSRect` 矩形（唯讀）

        線段的邊界框
        ```            
        # 原點
        print(bounds.origin.x, bounds.origin.y)
        # 尺寸
        print(bounds.size.width, bounds.size.height)
        """
    @property
    def type(self) -> 'str':
        """
        -> `str` 字串
        
        節點的類型：LINE、CURVE 或 QCURVE

        始終與常數進行比較，而不是實際值。
        """
    @type.setter
    def type(self, value: 'str'):
        if value not in ('LINE', 'CURVE', 'QCURVE'):
            raise ValueError('Type must be LINE, CURVE or QCURVE')

    #endregion
    #region 函數(Functions)
    def reverse(self):
        """
        反轉線段
        """
    def middlePoint(self):
        """
        t=0.5時的點
        """
    def lastPoint(self):
        """
        線段的結束點
        """
    def inflectionPoints(self):
        """
        線段上反曲點的“t”值列表
        """
    def curvatureAtTime_(self, t: 'float'):
        """
        “t”的曲率
        """
    def pointAtTime_(self, t: 'float'):
        """
        “t”的點
        """
    def normalAtTime_(self, t: 'float'):
        """
        “t”的法向量
        """
    def tangentAtTime_(self, t: 'float'):
        """
        “t”的切線
        """
    def extremePoints(self):
        """
        極值點的列表
        """
    def extremeTimes(self):
        """
        “t”值極值點的列表
        """
    def normalizeHandles(self):
        """
        平衡手柄的長度，同時儘量保持形狀良好
        """
    #endregion

class GSGuide(): # 類別
    """
    參考線物件的實作。

    有關如何取用它們的詳細訊息，請查看`GSLayer.guides`
    """
    #region 屬性(Properties)
    # @property
    # def position(self) -> 'NSPoint':
    @property
    def lockAngle(self) -> 'bool':
        """
        -> `bool` 布林值

        鎖定角度
        """
    @lockAngle.setter
    def lockAngle(self, value: 'bool'): ...

    @property
    def angle(self) -> 'float':
        """
        -> `float` 浮點數

        角度
        """
    @angle.setter
    def angle(self, value: 'float'): ...

    @property
    def name(self) -> 'str':
        """
        -> `str` 字串

        選擇性名稱
        """
    @name.setter
    def name(self, value: 'str'): ...
    @name.deleter
    def name(self): ...

    @property
    def selected(self) -> 'bool':
        """
        -> `bool` 布林值

        UI 中的參考線選取狀態。
        ```            
        # 選取參考線
        layer.guides[0].selected = True
        # 記錄選取狀態
        print(layer.guides[0].selected)
        """
    @selected.setter
    def selected(self, value: 'bool'): ...

    @property
    def locked(self) -> 'bool':
        """
        -> `bool` 布林值

        如果參考線被鎖定，則回傳True
        """
    @locked.setter
    def locked(self, value: 'bool'): ...

    @property
    def filter(self) -> 'NSPredicate':
        """
        -> `NSPredicate` 述詞

        僅在某些字符中顯示參考線的篩選器。僅在全域參考線中才有意義
        """
    @filter.setter
    def filter(self, value: 'NSPredicate'): ...
    @filter.deleter
    def filter(self): ...

    @property
    def showMeasurement(self) -> 'bool':
        """
        -> `bool` 布林值

        如果參考線正在顯示測量則回傳True

        3.1版新增
        """
    @showMeasurement.setter
    def showMeasurement(self, value: 'bool'): ...

    @property
    def userData(self) -> Dict[str, Union[bool, str, List, Dict, float, bytes]]:
        """
        -> `dict` 字典

        用於儲存用戶資料的字典。使用不重複鍵，僅使用可以儲存在屬性列表中的物件（字符串，列表，字典，數字，NSData），否則資料將無法從儲存的檔案中恢復。
        ```            
        # 設定值
        guide.userData['rememberToMakeCoffee'] = True
        # 刪除值
        del guide.userData['rememberToMakeCoffee']
        """
    @userData.setter
    def userData(self, value: Dict[str, Union[bool, str, List, Dict, float, bytes]]): ...
    @userData.deleter
    def userData(self): ...

    #endregion

class GSAnnotation(): # 類別
    """
    註解物件的實作。

    有關如何取用它們的詳細訊息，請查看`GSLayer.annotations`
    """
    def __init__(self): 
        self.position = NSPoint()

    #region 屬性(Properties)
    @property
    def position(self) -> 'NSPoint':
        """
        -> `NSPoint` 位置

        註解的位置。
        """
    @position.setter
    def position(self, value: 'NSPoint'): ...

    @property
    def type(self) -> 'int':
        """
        -> `int` 整數

        註解的類型。

        可用的常數有：`TEXT`、`ARROW`、`CIRCLE`、`PLUS`、`MINUS`
        """
    @type.setter
    def type(self, value: 'int'): 
        if value not in (TEXT, ARROW, CIRCLE, PLUS, MINUS):
            raise ValueError('Type must be TEXT, ARROW, CIRCLE, PLUS or MINUS')

    @property
    def text(self) -> 'str':
        """
        -> `str` 字串

        註解的內容。僅當類型為`TEXT`時才有用
        """
    @text.setter
    def text(self, value: 'str'): 
        if self.type != TEXT:
            raise ValueError('Text can only be set for type TEXT')
    @text.deleter
    def text(self): ...

    @property
    def angle(self) -> 'float':
        """
        -> `float` 浮點數

        註解的角度。
        """
    @angle.setter
    def angle(self, value: 'float'): ...

    @property
    def width(self) -> 'float':
        """
        -> `float` 浮點數

        註解的寬度。
        """
    @width.setter
    def width(self, value: 'float'): ...
    #endregion

class GSHint(): # 類別
    """
    Hint物件的實作。

    有關如何取用它們的詳細訊息，請查看`GSLayer.hints`
    """
    def __init__(self):
        self.parent = GSLayer()
        self.originNode = [GSNode(), GSHandle()]
        self.targetNode = [GSNode(), GSHandle()]
        self.otherNode1 = [GSNode(), GSHandle()]
        self.otherNode2 = [GSNode(), GSHandle()]
        self.originIndex = NSIndexPath()
        self.targetIndex = NSIndexPath()
        self.otherIndex1 = NSIndexPath()
        self.otherIndex2 = NSIndexPath()

    #region 屬性(Properties)
    @property
    def parent(self) -> 'GSLayer':
        """
        -> `GSLayer` 圖層

        Hint的父圖層。
        """

    @property
    def originNode(self) -> GSNode | GSHandle:
        """
        -> `GSNode` 節點或 `GSHandle` 控制桿

        Hint附加到的第一個節點。

        當附加到交叉點時，類型也可為`GSHandle`
        """
    @originNode.setter
    def originNode(self, value: GSNode | GSHandle): ...

    @property
    def targetNode(self) -> Optional[GSNode | GSHandle]:
        """
        -> `GSNode` 節點、 `GSHandle` 控制桿或 `None`

        Hint附加到的第二個節點。對於幽靈Hint，此值將為空。

        當附加到交叉點時，類型也可為`GSHandle`
        """
    @property
    def otherNode1(self) -> GSNode | GSHandle:
        """
        -> `GSNode` 節點或 `GSHandle` 控制桿

        Hint附加到的第三個節點。用於內插或對角線Hint。

        當附加到交叉點時，類型也可為`GSHandle`
        """
    @property
    def otherNode2(self) -> GSNode | GSHandle:
        """
        -> `GSNode` 節點或 `GSHandle` 控制桿

        Hint附加到的第四個節點。用於對角線Hint。

        當附加到交叉點時，類型也可為`GSHandle`
        """
    @property
    def originIndex(self) -> 'NSIndexPath':
        """
        -> `NSIndexPath` 索引路徑

        附加到的第一個節點的索引路徑。
        """
    @property
    def targetIndex(self) -> Optional['NSIndexPath']:
        """
        -> `NSIndexPath` 索引路徑或 `None`

        附加到的第二個節點的索引路徑。對於幽靈Hint，此值將為空。
        """
    @property
    def otherIndex1(self) -> 'NSIndexPath':
        """
        -> `NSIndexPath` 索引路徑

        附加到的第三個節點的索引路徑。用於內插或對角線Hint。
        """
    @property
    def otherIndex2(self) -> 'NSIndexPath':
        """
        -> `NSIndexPath` 索引路徑

        附加到的第四個節點的索引路徑。用於對角線Hint。
        """
    @property
    def type(self) -> 'int':
        """
        -> `int` 整數

        參見`Hint類型`
        """
    @type.setter
    def type(self, value: 'int'):...

    @property
    def options(self) -> 'int':
        """
        -> `int` 整數

        儲存Hint的額外選項。對於TT提示，這可能是四捨五入設定。
        參見`Hint選項`

        對於角落組件，它儲存的對齊設定為：左=0、中=2、右=1、自動（用於筆帽）=對齊|8
        """
    @options.setter
    def options(self, value: 'int'): 
        if value not in (0, 1, 2, 8):
            raise ValueError('Options must be 0, 1, 2 or 8')
        
    @property
    def horizontal(self) -> 'bool':
        """
        -> `bool` 布林值

        Hint是水平則回傳True，垂直則回傳False。
        """
    @horizontal.setter
    def horizontal(self, value: 'bool'): ...

    @property
    def selected(self) -> 'bool':
        """
        -> `bool` 布林值

        UI 中的Hint選取狀態。
        ```            
        # 選取Hint
        layer.hints[0].selected = True
        # 記錄選取狀態
        print(layer.hints[0].selected)
        """
    @selected.setter
    def selected(self, value: 'bool'): ...

    @property
    def name(self) -> 'str':
        """
        -> `str` 字串

        Hint的名稱。這是角落和筆帽組件的參考字符。
        """
    @name.setter
    def name(self, value: 'str'): ...

    @property
    def stem(self) -> 'int':
        """
        -> `int` 整數

        TrueType提示附加到的索引字幹，這些字幹在每個主板的自定義參數“TTFStems”中定義。

        當無字幹時值為-1，
        當自動狀態時值為-2。
        """
    @stem.setter
    def stem(self, value: 'int'): 
        if value not in (-2, -1):
            raise ValueError('Stem must be -2 or -1')
            
    @property
    def isTrueType(self) -> 'bool':
        """
        -> `bool` 布林值

        如果是TrueType指令則回傳True

        3.0版新增
        """

    @property
    def isPostScript(self) -> 'bool':
        """
        -> `bool` 布林值

        如果是PostScript Hint則回傳True

        3.0版新增
        """

    @property
    def isCorner(self) -> 'bool':
        """
        -> `bool` 布林值

        如果是角落（或筆帽、筆刷...）組件則回傳True

        3.0版新增
        """

    @property
    def tempData(self) -> 'dict':
        """
        -> `dict` 字典

        用於暫存資料的字典。使用不重複鍵。此資料不會儲存在檔案中。如果需要持續資料，請使用`hint.userData`
        ```            
        # 設定值
        hint.tempData['rememberToMakeCoffee'] = True
        # 刪除值
        del hint.tempData['rememberToMakeCoffee']
        """
    @tempData.setter
    def tempData(self, value: Dict[str, Union[bool, str, List, Dict, float, bytes]]): ...
    @tempData.deleter
    def tempData(self): ...

    #endregion
        
class GSBackgroundImage(): # 類別
    """
    背景圖片的實作。

    有關如何取用它們的詳細訊息，請查看`GSLayer.backgroundImage`
    """
    def __init__(self,
              path: 'str' = path
              ):
        """
        參數：
        - path – 初始化為圖片檔案（選擇性）
        """
        self.image = NSImage()
        self.crop = NSRect()
        self.position = NSPoint()
        self.transform = NSAffineTransformStruct()

    #region 屬性(Properties)
    @property
    def path(self) -> 'str':
        """
        -> `str` 字串

        圖片檔案的路徑。
        """
    @path.setter
    def path(self, value: 'str'): ...

    @property
    def image(self) -> 'NSImage':
        """
        -> `NSImage` 圖片

        背景圖片的`NSImage`物件，唯讀（即：不可設定）
        """
    @property
    def crop(self) -> 'NSRect':
        """
        -> `NSRect` 矩形

        裁切矩形。這是相對於圖片大小的像素，而不是字型的 em 單位（以防圖片被縮放到 100% 以外的其他尺寸）。
        ```            
        # 更改裁切
        layer.backgroundImage.crop = NSRect(NSPoint(0, 0), NSPoint(1200, 1200))
        """
    @crop.setter
    def crop(self, value: 'NSRect'): ...

    @property
    def locked(self) -> 'bool':
        """
        -> `bool` 布林值

        定義圖片是否被鎖定以在 UI 中取用。
        """
    @locked.setter
    def locked(self, value: 'bool'): ...

    @property
    def alpha(self) -> int:
        """
        -> `int` 整數

        在編輯畫面中圖片的透明度。預設為50%，可能的值為10-100。

        要重設為預設值，請將其設定為除允許的值之外的任何值。
        """
    @alpha.setter
    def alpha(self, value: 'int'): 
        if not 10 <= value <= 100: 
            raise ValueError('The value will reset to default.')
    @property
    def position(self) -> 'NSPoint':
        """
        -> `NSPoint` 位置

        圖片的位置，以字型單位為單位。
        ```            
        # 更改位置
        layer.backgroundImage.position = NSPoint(50, 50)
        """
    @position.setter
    def position(self, value: 'NSPoint'): ...

    @property
    def scale(self) -> 'tuple':
        """
        -> `tuple` 元組

        圖片的縮放因子。

        縮放因子1.0（100%）表示 1 個字型單位等於 1 個點。

        使用整數或浮點值同時設定 x 和 y 縮放因子。對於複數的縮放因子，請使用元組。
        ```            
        # 更改縮放
        layer.backgroundImage.scale = 1.2 # 將 x 和 y 變為 120%
        layer.backgroundImage.scale = (1.1, 1.2) # 將 x 變為110%，y 變為 120%
        """
    @scale.setter
    def scale(self, value: 'tuple'): ...

    @property
    def rotation(self) -> 'float':
        """
        -> `float` 浮點數

        圖片的旋轉角度。
        """
    @rotation.setter
    def rotation(self, value: 'float'): ...

    @property
    def transform(self) -> 'NSAffineTransformStruct':
        """
        -> `NSAffineTransformStruct` 結構

        變形矩陣。
        ```            
        # 變形更動
        layer.backgroundImage.transform = ((
            1.0, # x 縮放因子
            0.0, # x 傾斜因子
            0.0, # y 傾斜因子
            1.0, # y 縮放因子
            0.0, # x 位置
            0.0  # y 位置
        ))
        """
    @transform.setter
    def transform(self, value: 'NSAffineTransformStruct'): ...

    #endregion
    #region 函數(Functions)
    def resetCrop(self):
        """
        重設裁切為圖片的原始尺寸。
        """
    def scaleWidthToEmUnits(self):
        """
        將圖片的裁切寬度縮放到特定的em單位值，保持其長寬比。
        ```            
        # 將圖片適應到圖層的寬度
        layer.backgroundImage.scaleWidthToEmUnits(layer.width)
        """
    def scaleHeightToEmUnits(self):
        """
        將圖片的裁切高度縮放到特定的em單位值，保持其長寬比。
        ```            
        # 將圖片的原點位置設定在下伸線上
        layer.backgroundImage.position = NSPoint(0, font.masters[0].descender)
        # 將圖片縮放到UPM值
        layer.backgroundImage.scaleHeightToEmUnits(font.upm)
        """
    #endregion

class GSGradient(): # 類別
    """
    漸層物件的實作。

    有關如何取用它們的詳細訊息，請查看`GSLayer.gradients`
    """
    def __init__(self):
        self.colors = []
        self.type = 0
        self.start = NSPoint(0, 0)
        self.end = NSPoint(1, 1)

    def addColorStop(self, position: float, color: NSColor):
        """
        新增一個顏色停止點到漸層中。

        參數:
        - position: 0.0 到 1.0 之間的浮點數，表示顏色停止點的位置
        - color: NSColor 物件，表示顏色
        """
        self.colors.append((color, position))

    def removeColorStop(self, index: int):
        """
        移除指定索引的顏色停止點。

        參數:
        - index: 要移除的顏色停止點的索引
        """
        if 0 <= index < len(self.colors):
            del self.colors[index]

    #region 屬性(Properties)
    @property
    def colors(self) -> List[Tuple[NSColor, float]]:
        """
        -> `List[Tuple[NSColor, float]]` 顏色和浮點數的元組串列

        一個顏色列表。每個都是一個列表，包含一個 NSColor 和一個介於 0.0 與 1.0 之間的位置。
        """
    @colors.setter
    def colors(self, value: List[Tuple[NSColor, float]]): 
        if not float(0) <= value[0][1] <= float(1):
            raise ValueError('The value must be between 0.0 and 1.0')
        
    @property
    def type(self) -> 'int':
        """
        -> `int` 整數

        漸層類型。線性=0、放射狀=1
        """
    @type.setter
    def type(self, value: 'int'): 
        if value not in (0, 1):
            raise ValueError('Type must be 0 or 1')
        
    @property
    def start(self) -> 'NSPoint':
        """
        -> `NSPoint` 位置

        以形狀邊界框的相對位置定義的漸層起始點 NSPoint
        """
    @start.setter
    def start(self, value: 'NSPoint'): ...

    @property
    def end(self) -> 'NSPoint':
        """
        -> `NSPoint` 位置

        以形狀邊界框的相對位置定義的漸層結束點 NSPoint
        """
    @end.setter
    def end(self, value: 'NSPoint'): ...

    @property
    def absoluteStart(self) -> 'NSPoint':
        """
        -> `NSPoint` 位置

        漸層的絕對起始點 NSPoint
        """
    @absoluteStart.setter
    def absoluteStart(self, value: 'NSPoint'): ...
    
    @property
    def absoluteEnd(self) -> 'NSPoint':
        """
        -> `NSPoint` 位置

        漸層的絕對結束點 NSPoint
        """
    @absoluteEnd.setter
    def absoluteEnd(self, value: 'NSPoint'): ...

    #endregion

class GSEditViewController(): # 類別
    """
    實作 GSEditViewController 物件，代表 UI 中的編輯分頁。

    有關如何取用它們的詳細訊息，請查看`GSFont.tabs`
    """
    def __init__(self):
        self.parent = GSFont()
        self.viewPort = NSRect()
        self.bounds = NSRect()
        self.selectedLayerOrigin = NSPoint()
        self.previewInstances = GSInstance()
    #region 屬性(Properties)
    @property
    def parent(self) -> 'GSFont':
        """
        -> `GSFont` 字型

        此分頁所屬的`GSFont`物件。
        """
    @property
    def text(self) -> 'str':
        """
        -> `str` 字串

        分頁的文本，可以是文本、斜線跳脫的字符名稱或兩者混合。OpenType 功能將在更改文本後套用。
        ```            
        string = ""
        for l in font.selectedLayers:
            string += "/"+l.parent.name
        tab = font.tabs[-1]
        tab.text = string
        """
    @text.setter
    def text(self, value: 'str'): ...

    @property
    def string(self) -> 'str':
        """
        -> `str` 字串
        
        分頁的基本底層字串
        ```            
        string = ""
        for l in font.selectedLayers:
            char = font.characterForGlyph(l.parent)
            string += chr(char)
        tab = font.tabs[-1]
        tab.text = string

        3.2版新增
        """
    @string.setter
    def string(self, value: 'str'): ...

    @property
    def masterIndex(self) -> 'int':
        """
        -> `int` 整數

        使用中主板的索引（在工具列中選擇）。

        2.6.1版新增
        """
    @masterIndex.setter
    def masterIndex(self, value: 'int'): ...

    @property
    def layers(self) -> 'list':
        """
        -> `list` 列表

        或許，您可以設定（和讀取）一個`GSLayer`物件列表。這些可以是字符的任何圖層。
        ```            
        layers = []
        # 將一個字符的所有圖層顯示在一起
        for layer in font.glyphs['a'].layers:
            layers.append(layer)
        # 附加換行符
        layers.append(GSControlLayer(10)) # 10是換行符的ASCII碼（\n）
        font.tabs[0].layers = layers
        """
    @layers.setter
    def layers(self, value: 'list'): ...

    @property
    def composedLayers(self) -> 'list':
        """
        -> `list` 列表

        已棄用。現在`.layers`就像這樣。
        
        這個列表包含`GSLayer`物件，這些物件在應用 OpenType 功能後（參見`GSEditViewController.features`）。

        2.4版新增
        """
        raise ValueError("Deprecated since 2.4 - Use .layers instead.")
    
    @property
    def scale(self) -> 'float':
        """
        -> `float` 浮點數

        編輯畫面的縮放（縮放因子）。對於 plugin 中的繪製行為很有用。

        隨著編輯畫面的每個縮放步驟變化。因此，如果您想在編輯畫面中以與 UI 相對的恆定大小繪製對象（例如，螢幕上的恆定文本大小），您需要計算對象的大小相對於縮放因子。參見下面的示例。
        ```            
        print(font.currentTab.scale)
        >> 0.414628537193
        # 計算文本大小
        desiredTextSizeOnScreen = 10 #pt
        scaleCorrectedTextSize = desiredTextSizeOnScreen / font.currentTab.scale
        print(scaleCorrectedTextSize)
        >> 24.1179733255
        """
    @scale.setter
    def scale(self, value: 'float'): ...

    @property
    def viewPort(self) -> 'NSRect':
        """
        -> `NSRect` 矩形

        編輯畫面可見區域的螢幕像素座標（畫面座標）。

        NSRect 的原點值描述了組合字符邊界框的左上角（對於 RTL，兩者都在上伸高度），這也是畫面上的原點。

        NSRect 的尺寸值描述了可見區域的寬度和高度。

        當使用繪製方法（例如 Reporter Plugin 中的畫面座標相對方法）時，請使用這些坐標。
        ```            
        # 編輯畫面的四個角：
        # 螢幕左下角
        x = font.currentTab.viewPort.origin.x
        y = font.currentTab.viewPort.origin.y
        # 螢幕左上角
        x = font.currentTab.viewPort.origin.x
        y = font.currentTab.viewPort.origin.y + font.currentTab.viewPort.size.height
        # 螢幕右上角
        x = font.currentTab.viewPort.origin.x + font.currentTab.viewPort.size.width
        y = font.currentTab.viewPort.origin.y + font.currentTab.viewPort.size.height
        # 螢幕右下角
        x = font.currentTab.viewPort.origin.x + font.currentTab.viewPort.size.width
        y = font.currentTab.viewPort.origin.y
        """
    @viewPort.setter
    def viewPort(self, value: 'NSRect'): ...

    @property
    def bounds(self) -> 'NSRect':
        """
        -> `NSRect` 矩形

        編輯畫面中所有字符邊界框的畫面座標值。

        2.4版新增
        """
    @property
    def selectedLayerOrigin(self) -> 'NSPoint':
        """
        -> `NSPoint` 位置

        使用中的圖層原點（0,0）相對於畫面原點的位置（參見`bounds`），以畫面座標表示。
        """
    @property
    def textCursor(self) -> 'int':
        """
        -> `int` 整數

        文本中的游標位置，從 0 開始。
        """
    @textCursor.setter
    def textCursor(self, value: 'int'): ...

    @property
    def textRange(self) -> 'int':
        """
        -> `int` 整數

        從游標位置（參見`textCursor`）開始的選取字符數。
        """
    @textRange.setter
    def textRange(self, value: 'int'): ...

    @property
    def layersCursor(self) -> 'int':
        """
        -> `int` 整數

        游標在圖層列表中的位置，從 0 開始。
        參見`GSEditViewController.layers`

        2.4版新增
        """
    @layersCursor.setter
    def layersCursor(self, value: 'int'): ...

    @property
    def direction(self) -> 'int':
        """
        -> `int` 整數

        書寫方向。
        參見`書寫方向`常數
        ```            
        font.currentTab.direction = GSRTL
        """
    @direction.setter
    def direction(self, value: 'int'): 
        if value not in (GSBIDI, GSLTR, GSRTL, GSVertical, GSVerticalToRight):
            raise ValueError('Direction must be WritingDirections constant')
    @property
    def features(self) -> 'list':
        """
        -> `list` 列表

        套用於編輯畫面中文本的 OpenType 特性列表。
        ```            
        font.currentTab.features = ['locl', 'ss01']
        """
    @features.setter
    def features(self, value: 'list'): ...

    @property
    def tempData(self) -> Dict[str, Union[bool, str, List, Dict, float, bytes]]:
        """
        -> `dict` 字典

        用於暫存資料的字典。使用不重複鍵。這不會儲存在檔案中。如果需要持續資料，請使用`layer.userData`
        ```            
        # 設定值
        layer.tempData['rememberToMakeCoffee'] = True
        # 刪除值
        del layer.tempData['rememberToMakeCoffee']
        """
    @tempData.setter
    def tempData(self, value: Dict[str, Union[bool, str, List, Dict, float, bytes]]): ...
    @tempData.deleter
    def tempData(self): ...

    @property
    def previewInstances(self) -> str | GSInstance:
        """
        -> `str` 字串或 `GSInstance` 實體

        預覽區域中要顯示的實體。

        值為`'live'`表示目前內容的即時預覽，`'all'`表示目前字符所有實體的內插，或個別的`GSInstance`物件。

        ```            
        # 編輯畫面的即時預覽
        font.currentTab.previewInstances = 'live'
        # 在特定實體內插中顯示編輯畫面的文本
        font.currentTab.previewInstances = font.GSInstance[-1]
        # 所有實體的內插
        font.currentTab.previewInstances = 'all'
        """
    @previewInstances.setter
    def previewInstances(self, value: Union[str, GSInstance]):
        if isinstance(value, str) and value not in ['live', 'all']:
            raise ValueError("Invalid value for previewInstances. It should be either 'live', 'all' or a GSInstance object.")
        
    @property
    def previewHeight(self) -> 'float':
        """
        -> `float` 浮點數

        編輯畫面中預覽面板的高度（像素）。

        需要設定為 16 或更高，以使預覽面板可見。當面板關閉時，將回傳 0 或目前大小。
        """
    @previewHeight.setter
    def previewHeight(self, value: 'float'): 
        if value < 16:
            raise ValueError('The value must be 16 or higher.')

    @property
    def bottomToolbarHeight(self) -> 'float':
        """
        -> `float` 浮點數（唯讀）

        最底部的小工具列的高度

        2.4版新增
        """
    #endregion
    #region 函數(Functions)
    def close(self):
        """
        關閉此分頁。
        """
    def saveToPDF(self,
              path: 'str',
              rect: 'NSRect'
              ):
        """
        將畫面儲存為 PDF 檔案。

        參數：
        - path – 檔案路徑
        - rect – 選擇性。定義畫面接口的 NSRect。如果省略，將使用`GSEditViewController.viewPort`。

        2.4版新增
        """
    def redraw(self):
        """
        強制更新編輯畫面
        """
    #endregion
        
class GSGlyphInfo(): # 類別
    """
    字型資訊物件的實作。

    這包含來自字符資料庫的有價值資訊。有關如何建立這些物件的詳細訊息，請查看`GSGlyphsInfo`
    """
    def __init__(self):
        self.components = GSGlyphInfo()

    #region 屬性(Properties)
    @property
    def name(self) -> 'str':
        """
        -> `str` 字串

        字符的人類可讀名稱（“易懂的形式”）。
        """
    @name.setter
    def name(self, value: 'str'): ...

    @property
    def productionName(self) -> Optional['str']:
        """
        -> `str` 字串或    `None`
        
        字符的產品名稱。僅當產品名稱與易懂的形式不同時才會回傳值，否則為 None。
        """
    
    @property
    def category(self) -> 'str':
        """
        -> `str` 字串
        
        類型資料主要來自 unicode.org 的 UnicodeData.txt 檔案。進行了一些更正（例如，重音符號…）例如：“字母”、“數字”、“標點”、“標號”、“分隔符號”、“符號”、“其他”
        """
    @category.setter
    def category(self, value: 'str'): ...

    @property
    def subCategory(self) -> 'str':
        """
        -> `str` 字串
        
        子類型資料主要來自 unicode.org 的 UnicodeData.txt 檔案。進行了一些更正和添加。例如：“修飾子”、“合字”、“基本數字”…
        """
    @subCategory.setter
    def subCategory(self, value: 'str'): ...

    @property
    def case(self) -> 'int':
        """
        -> `int` 整數

        字符大小寫：GSUppercase、GSLowercase、GSSmallcaps
        """

    @property
    def components(self) -> List['GSGlyphInfo']:
        """
        -> `List[GSGlyphInfo]` 字型資訊串列

        這個字符可能由這些字符組成，以`GSGlyphInfo`物件列表的形式回傳。
        """

    @property
    def accents(self) -> List[str]:
        """
        -> `List[str]` 字串串列

        這個字符可能與這些重音符號組合，以字符名稱的列表形式回傳。
        """

    @property
    def anchors(self) -> List[str]:
        """
        -> `List[str]` 字串串列

        為此字符定義的錨點，以錨點名稱的列表形式回傳。
        """

    @property
    def unicode(self) -> 'str':
        """
        -> `str` 字串

        Unicode 值
        """
    @property
    def unicode2(self) -> 'str':
        """
        -> `str` 字串
        
        第二個 Unicode 值，如果存在
        """
    @property
    def script(self) -> 'str':
        """
        -> `str` 字串
        
        字符的語系，例如：“拉丁文字”、“西里爾文字”、“希臘文字”。
        """
    @property
    def index(self) -> 'str':
        """
        -> `str` 字串
        
        字符在資料庫中的索引。用於 UI 中的排序。
        """
    @property
    def sortName(self) -> 'str':
        """
        -> `str` 字串
        
        用於 UI 中排序字符的替代名稱。
        """
    @property
    def sortNameKeep(self) -> 'str':
        """
        -> `str` 字串
        
        用於 UI 中排序字符的替代名稱，當使用“將替代字顯示在基礎字旁邊”時。
        """
    @property
    def desc(self) -> 'str':
        """
        -> `str` 字串
        
        字符的 Unicode 描述。
        """
    @property
    def altNames(self) -> 'str':
        """
        -> `str` 字串
        
        未使用但應該被識別的字符的替代名稱（例如，用於轉換為易懂的形式）。
        """
    
    @property
    def direction(self) -> 'int':
        """
        -> `int` 整數

        書寫方向，
        參見`書寫方向`常數。
        ```            
        glyph.direction = GSRTL

        3.0版新增
        """
    @direction.setter
    def direction(self, value: 'int'): 
        if value not in (GSBIDI, GSLTR, GSRTL, GSVertical, GSVerticalToRight):
            raise ValueError('Direction must be WritingDirections constant')
        
    #endregion
        
class GSFontInfoValueLocalized(): # 類別
    """
    本地化字型資訊值的實作。

    有關如何取用它們的詳細訊息，請查看`GSFont.properties`
    """
    def __init__(self):
        self.values = GSFontInfoValue()

    #region 屬性(Properties)
    @property
    def key(self) -> 'str':
        """
        -> `str` 字串
        
        鍵
        ```            
        # 尋找具有“designers”鍵的 GSFontInfoValueLocalized
        for fontInfo in font.properties:
            if fontInfo.key == "designers":
                print(fontInfo)
        """
    @property
    def values(self) -> List['GSFontInfoValue']:
        """
        -> `List[GSFontInfoValue]` 字型資訊值串列

        一個`GSFontInfoValue`物件列表。
        ```            
        # 列出 GSFontInfoValueLocalized 的值
        for fontInfoValue in fontInfoValueLocalized.values:
            print(fontInfoValue)
        """
    @property
    def defaultValue(self) -> 'str':
        """
        -> `str` 字串

        被視為預設值（dflt 或英文項目）的值
        ```        
        # 列印給定 GSFontInfoValueLocalized 實體的預設值
        print(fontInfoValueLocalized.defaultValue)
        # 下面的列印總是返回 True，因為
        # font.designer 代表相同的值
        fontInfoValueLocalized = None
        for fontInfo in font.properties:
            if fontInfo.key == "designers":
                fontInfoValueLocalized = fontInfo
        print(fontInfoValueLocalized.defaultValue == font.designer)
        """

    #endregion
        
class GSFontInfoValueSingle: # 類別
    """
    GSFontInfoValueSingle 的實作。
    """
    #region 屬性(Properties)
    @property
    def key(self) -> 'str':
        """
        -> `str` 字串
        
        鍵
        ```            
        # GSFontInfoValueSingle 被儲存在 font.properties 這類的屬性中
        # 它與 GSFontInfoValueLocalized 之間的區別之一
        # 是前者沒有 "values" 屬性
        for fontProperty in font.properties:
            if not hasattr(fontProperty, "values"):
                print(fontProperty.key)
        """
    @property
    def value(self) -> 'str':
        """
        -> `str` 字串
        
        值
        ```            
        # GSFontInfoValueSingle 被儲存在 font.properties 這類的屬性中
        # 它與 GSFontInfoValueLocalized 之間的區別之一
        # 是前者沒有 "values" 屬性
        for fontProperty in font.properties:
            if not hasattr(fontProperty, "values"):
                print(fontProperty.value)
        """
    #endregion
        
class GSFontInfoValue: # 類別
    """
    GSFontInfoValue 的實作。
    """
    #region 屬性(Properties)
    @property
    def key(self) -> 'str':
        """
        -> `str` 字串
        
        鍵
        ```            
        # GSFontInfoValue 被儲存在 font.properties 這類的屬性中
        for fontProperty in font.properties:
            # 不是所有的 font.properties 都包含這個屬性
            # 所以我們將尋找那些有它的
            if hasattr(fontProperty, "values"):
                for fontInfoValue in fontProperty.values:
                    # 這行列印出一個鍵屬性
                    # 找到了 GSFontInfoValue 實體
                    print(fontInfoValue.key)
        """
    @property
    def value(self) -> 'str':
        """
        -> `str` 字串
        
        值
        ```            
        # GSFontInfoValue 被儲存在 font.properties 這類的屬性中
        for fontProperty in font.properties:
            # 不是所有的 font.properties 都包含這個屬性
            # 所以我們將尋找那些有它的
            if hasattr(fontProperty, "values"):
                for fontInfoValue in fontProperty.values:
                    # 這行列印出一個值屬性
                    # 找到了 GSFontInfoValue 實體
                    print(fontInfoValue.value)
        """
    @property
    def languageTag(self) -> 'str':
        """
        -> `str` 字串
        
        語言標籤
        ```            
        # GSFontInfoValue 被儲存在 font.properties 這類的屬性中
        for fontProperty in font.properties:
            # 不是所有的 font.properties 都包含這個屬性
            # 所以我們將尋找那些有它的
            if hasattr(fontProperty, "values"):
                for fontInfoValue in fontProperty.values:
                    # 這行列印出語言標籤屬性
                    # 找到了 GSFontInfoValue 實體
                    print(fontInfoValue.languageTag)
        """
    #endregion

class GSMetricValue: # 類別
    """
    GSMetricValue 物件代表垂直度量值及其超出的部分。
    """
    def __init__(self):
        self.filter = NSPredicate()
        self.metric = GSMetric()
    #region 屬性(Properties)
    @property
    def position(self) -> 'float':
        """
        -> `float` 浮點數

        度量的 y 位置。
        """
    @position.setter
    def position(self, value: 'float'): ...

    @property
    def overshoot(self) -> 'float':
        """
        -> `float` 浮點數

        超出的寬度值。
        """
    @overshoot.setter
    def overshoot(self, value: 'float'): ...

    @property
    def name(self) -> 'str':
        """
        -> `str` 字串
        
        度量值的名稱。例如：下伸線、小型大寫、大寫高度等。
        """
    @name.setter
    def name(self, value: 'str'): ...

    @property
    def filter(self) -> 'NSPredicate':
        """
        -> `NSPredicate` 述詞

        限制度量範圍的篩選器。
        """
    @filter.setter
    def filter(self, value: 'NSPredicate'): ...

    @property
    def metric(self) -> 'GSMetric':
        """
        -> `GSMetric` 度量

        對應的 Glyphs 度量物件。參見`GSFont.metrics`。
        """
    @metric.setter
    def metric(self, value: 'GSMetric'): ...

    #endregion

class PreviewTextWindow(): # 類別
    """
    文本預覽視窗
    """
    def __init__(self):
        self.font = GSFont()

    #region 屬性(Properties)
    @property
    def font(self) -> 'GSFont':
        """
        -> `GSFont` 字型
        字型
        """
    @font.setter
    def font(self, value: 'GSFont'): ...

    @property
    def text(self) -> 'str':
        """
        -> `str` 字串
        
        文本
        """
    @text.setter
    def text(self, value: 'str'): ...

    @property
    def instanceIndex(self) -> 'int':
        """
        -> `int` 整數

        選定實體的索引
        """
    @instanceIndex.setter
    def instanceIndex(self, value: 'int'): ...

    @property
    def fontSize(self) -> 'int':
        """
        -> `int` 整數
        
        字型大小
        """
    @fontSize.setter
    def fontSize(self, value: 'int'): ...

    #endregion
    #region 函數(Functions)
    def open(self):
        """
        打開預覽文本視窗
        ```            
        # 打開文本預覽視窗
        PreviewTextWindow.open()
        # 設定在文本預覽視窗中打開實體 "Regular"
        font = PreviewTextWindow.font
        instanceNames = [instance.name for instance in font.instances]
        regularIndex = instanceNames.index("Regular")
        PreviewTextWindow.instanceIndex = regularIndex
        # 設定文本和字型大小值
        PreviewTextWindow.text = 'hamburgefontsiv'
        PreviewTextWindow.fontSize = 200
        """
    def close(self):
        """
        關閉預覽文本視窗
        """
    #endregion

class NSAffineTransform: # 類別
    """
    NSAffineTransform 物件。
    """
    #region 屬性(Properties)
    @property
    def transformStruct(self):
        """
        變形結構
        """
    #endregion
    #region 函數(Functions)
    def shift(self) -> tuple | NSPoint:
        """
        在xy座標上平移
        """
    def scale(self) -> int | float | tuple:
        """
        如果是單一數字則均勻縮放，否則根據x、y縮放，如果給定 center 則使用它作為縮放的原點
        """
    def rotate(self) -> int | float:
        """
        旋轉的角度，以度為單位。如果給定 center 則使用它作為旋轉的原點，正角度為逆時針方向
        """
    def skew(self) -> int | float | tuple:
        """
        如果是單一數字則在x方向上斜切，否則根據x、y斜切，如果給定 center 則使用它作為斜切的原點
        """
    def matrix(self) -> tuple:
        """
        變形矩陣
        """
    #endregion

#region 模組(Methods)
def divideCurve(
        P0: 'NSPoint', 
        P1, 
        P2, 
        P3, 
        t
        ) -> 'list': 
    """
    使用De Casteljau算法將曲線分割。

    參數：
    - P0 - 曲線的起始點（NSPoint）
    - P1 - 第一個離線點
    - P2 - 第二個離線點
    - P3 - 曲線的結束點
    - t - 時間參數

    回傳值：
    一個包含兩個曲線的點列表（Q0、Q1、Q2、Q3、R1、R2、R3）。請注意，“中間”點只回傳一次。
    """

def distance(
        P0: 'NSPoints', 
        P1: 'NSPoints'
        ) -> 'float':
    """
    計算兩個 NSPoints 之間的距離。

    參數：
    - P0 - 一個`NSPoint`
    - P1 - 另一個`NSPoint`

    回傳值：
    距離
    """

def addPoints(
        P1, 
        P2
        ) -> 'NSPoint':
    """
    將兩個點相加。

    參數：
    - P0 - 一個`NSPoint`
    - P1 - 另一個`NSPoint`

    回傳值：
    兩個點的和
    """

def subtractPoints(
        P1, 
        P2
        ) -> 'NSPoint':
    """
    減去點。

    參數：
    - P0 - 一個`NSPoint`
    - P1 - 另一個`NSPoint`

    回傳值：
    減去的點
    """

def scalePoint(
        P: 'NSPoint', 
        scalar: float
        ) -> 'NSPoint':
    """
    縮放一個點。

    參數：
    - P - 一個`NSPoint`
    - scalar - 乘數

    回傳值：
    乘以的點
    """

def removeOverlap(paths: list) -> list:
    """
    從路徑列表中刪除重疊。
    ```    
    paths = [path1, path2, path3]
    mergePaths = removeOverlap(paths)

    參數：
    - paths - 一個路徑列表

    回傳值：
    刪除重疊後的路徑列表
    """

def subtractPaths(paths: list, subtract: list) -> list:
    """
    從路徑列表中刪除重疊。

    參數：
    - paths - 一個路徑列表
    - subtract - 減去的路徑

    回傳值：
    刪除重疊後的路徑列表
    """

def intersectPaths(paths: list, otherPaths: list) -> list:
    """
    從路徑列表中刪除重疊。

    參數：
    - paths - 一個路徑列表
    - otherPaths - 另一個路徑列表

    回傳值：
    刪除重疊後的路徑列表
    """

def GetSaveFile(message=None, 
                ProposedFileName=None, 
                filetypes=None
                ) -> str | None:
    """
    打開一個檔案選取器對話框。

    參數：
    - message - 一個訊息字符串。
    - filetypes - 一個字符串列表，指示檔案類型，例如，['gif'，'pdf']。
    - ProposedFileName - 建議的檔案名。

    回傳值：
    選取的檔案或無
    """

def GetOpenFile(message=None, 
                allowsMultipleSelection=False, 
                filetypes=None, 
                path=None
                ) -> str | list | None:
    """
    打開一個檔案選取器對話框。

    參數：
    - message - 一個訊息字符串。
    - allowsMultipleSelection - 布爾值，如果用戶可以選取多個檔案
    - filetypes - 一個字符串列表，指示檔案類型，例如，['gif'，'pdf']。
    - path - 初始目錄路徑

    回傳值：
    選取的檔案或檔案名列表或無
    """

def GetFolder(message=None, 
              allowsMultipleSelection=False, 
              path=None
              ) -> str | None:
    """
    打開一個檔案夾選取器對話框。

    參數：
    - message - 一個訊息字符串。
    - allowsMultipleSelection - 布爾值，如果用戶可以選取多個檔案
    - path - 初始目錄路徑

    回傳值：
    選取的檔案夾或無
    """

def Message(message: str, title: str='Alert', OKButton=None):
    """
    顯示一個警告面板。

    參數：
    - message - 一個字符串
    - title - 對話框的標題
    - OKButton - 確認按鈕的標籤
    """
def AskString(message: str, 
              value=None, 
              title: str='Glyphs', 
              OKButton=None, 
              placeholder: str=None
              ) -> str:
    """
    顯示一個輸入對話框。

    參數：
    - message - 一個字符串
    - value - 預設值
    - title - 對話框的標題
    - OKButton - 確認按鈕的標籤
    - placeholder - 當文本字段為空時顯示的灰色值

    回傳值：
    字符串
    """

def PickGlyphs(content: list=None, 
               masterID=None, 
               searchString: str=None, 
               defaultsKey=None
               ) -> tuple | list | str:
    """
    顯示一個字符選取器對話框。

    參數：
    - content - 一個字符列表
    - masterID - 用於預覽的主ID
    - searchString - 預先填充搜索
    - defaultsKey - 讀取和儲存搜索鍵的用戶預設值。設定此值將忽略搜尋字符串。

    回傳值：
    選取的字符列表和搜索字符串

    3.2 版新增
    """

def LogToConsole(message: 'str'):
    """
    為除錯向Mac的Console.app寫入訊息。

    參數：
    - message - 一個字符串
    """
def LogError(message: str):
    """
    記錄錯誤訊息並將其寫入巨集視窗的輸出（以紅色顯示）。

    參數：
    - message - 一個字符串
    """
#endregion

#region 常數(Constants)
"""
GlyphsApp中使用的常數。
"""

# 節點類型:
LINE: str
"""
直線節點
"""
CURVE: str
"""
曲線節點。確保每個曲線節點之前至少有兩個離線節點。
"""
QCURVE: str
"""
二次曲線節點。確保每個曲線節點之前至少有一個離線節點。
"""
OFFCURVE: str
"""
離線節點
"""

# 路徑屬性:
FILL: dict
"""
填滿
"""
FILLCOLOR: dict
"""
填滿顏色
"""
FILLPATTERNANGLE: dict
"""
填滿圖案角度
"""
FILLPATTERNBLENDMODE: dict
"""
填滿圖案混合模式
"""
FILLPATTERNFILE: dict
"""
填滿圖案檔案
"""
FILLPATTERNOFFSET: dict
"""
填滿圖案位移
"""
FILLPATTERNSCALE: dict
"""
填滿圖案比例
"""
STROKECOLOR: dict
"""
筆劃顏色
"""
STROKELINECAPEND: dict
"""
筆劃線帽末端
"""
STROKELINECAPSTART: dict
"""
筆劃線帽開始
"""
STROKELINEJOIN: dict
"""
筆劃線連接
"""
STROKEPOSITION: dict
"""
筆劃位置
"""
STROKEWIDTH: dict
"""
筆劃寬度
"""
STROKEHEIGHT: dict
"""
筆劃高度
"""
GRADIENT: dict
"""
漸層
"""
SHADOW: dict
"""
陰影
"""
INNERSHADOW: dict
"""
內陰影
"""
MASK: dict
"""
遮罩
"""

# 檔案格式版本:
"""
用於儲存和讀取.glyphs檔案以及剪貼板時使用的常數。
"""

GSFormatVersion1: Final = int
"""
Glyphs2 使用的格式
"""
GSFormatVersion3: Final = int
"""
Glyphs3 使用的格式
"""
GSFormatVersionCurrent: Final = int
"""
目前使用的格式
"""

# 輸出格式:
OTF: str
"""
寫入基於CFF的字型
"""
TTF: str
"""
寫入基於CFF的字型
"""
VARIABLE: str
"""
寫入可變字型
"""
UFO: str
"""
寫入基於UFO的字型
"""
WOFF: str
"""
寫入WOFF
"""
WOFF2: str
"""
寫入WOFF
"""
PLAIN: str
"""
不打包為webfont
"""
EOT: str
"""
寫入 EOT (Embedded OpenType) 格式。
這是一種用於網頁的壓縮字體格式，主要用於舊版 Internet Explorer 瀏覽器。

2.5 版新增
"""
# 資訊屬性鍵: 
GSPropertyNameFamilyNamesKey: Final = list
"""
家族名稱
"""
GSPropertyNameDesignersKey: Final = list
"""
設計師
"""
GSPropertyNameDesignerURLKey: Final = list
"""
設計師網址
"""
GSPropertyNameManufacturersKey: Final = list
"""
製造商
"""
GSPropertyNameManufacturerURLKey: Final = list
"""
製造商網址
"""
GSPropertyNameCopyrightsKey: Final = list
"""
版權
"""
GSPropertyNameVersionStringKey: Final = list
"""
版本字串
"""
GSPropertyNameVendorIDKey: Final = list
"""
供應商ID
"""
GSPropertyNameUniqueIDKey: Final = list 
"""
唯一ID
"""
GSPropertyNameLicensesKey: Final = list
"""
授權
"""
GSPropertyNameLicenseURLKey: Final = list
"""
授權網址
"""
GSPropertyNameTrademarksKey: Final = list
"""
商標
"""
GSPropertyNameDescriptionsKey: Final = list
"""
描述
"""
GSPropertyNameSampleTextsKey: Final = list
"""
範例文字
"""
GSPropertyNamePostscriptFullNamesKey: Final = list
"""
Postscript全名
"""
GSPropertyNamePostscriptFontNameKey: Final = list
"""
Postscript字型名稱
"""
GSPropertyNameCompatibleFullNamesKey: Final = list
"""
相容用全名
"""
GSPropertyNameStyleNamesKey: Final = list
"""
樣式名稱
"""
GSPropertyNameStyleMapFamilyNamesKey: Final = list
"""
StyleMap家族名稱
"""
GSPropertyNameStyleMapStyleNamesKey: Final = list
"""
StyleMap樣式名稱
"""
GSPropertyNamePreferredFamilyNamesKey: Final = list
"""
建議的家族名稱
"""
GSPropertyNamePreferredSubfamilyNamesKey: Final = list
"""
建議的子家族名稱
"""
GSPropertyNameVariableStyleNamesKey: Final = list
"""
可變樣式名稱
"""
GSPropertyNameWWSFamilyNameKey: Final = list
"""
WWS家族名稱
"""
GSPropertyNameWWSSubfamilyNameKey: Final = list
"""
WWS子家族名稱
"""
GSPropertyNameVariationsPostScriptNamePrefixKey: Final = list
"""
VariationsPostScriptNamePrefix

3.1 版新增
"""

# 實體類型:
INSTANCETYPESINGLE: int
"""
單個內插實體
"""
INSTANCETYPEVARIABLE: int
"""
可變字型設定

3.0.1 版新增
"""
# Hint類型: # GSHint.options
TOPGHOST: int
"""
PSHint的頂部幽靈
"""
STEM: int
"""
PSHint的字幹
"""
BOTTOMGHOST: int
"""
PSHint的底部幽靈
"""
TTSNAP: int
"""
TTHint的捕捉
"""
TTSTEM: int
"""
TTHint的字幹
"""
TTSHIFT: int
"""
TTHint的位移
"""
TTINTERPOLATE: int
"""
TTHint的內插
"""
TTDIAGONAL: int
"""
TTHint的對角線
"""
TTDELTA: int
"""
TTHint的Delta
"""
CORNER: int
"""
角落組件
```            
path = Layer.shapes[0]
brush = GSHint()
brush.name = "_corner.test"
brush.type = CORNER
brush.originNode = path.nodes[1]
Layer.hints.append(brush)
"""
CAP: int
"""
筆帽組件
"""
BRUSH: int
"""
筆刷組件

3.1 版新增
"""
SEGMENT: int
"""
線段組件

3.1 版新增
"""

# Hint選項:
"""
這些是用於GSHint.options的常數。
"""

TTROUND: int
"""
對齊到格線
"""
TTROUNDUP: int
"""
向上取整
"""
TTROUNDDOWN: int
"""
向下取整
"""
TTDONTROUND: int
"""
完全不取整
"""
TRIPLE = 128
"""
表示三重Hint組。需要有三個使用此設定的水平 TTStem Hint才會生效。
"""

# 視窗標籤:
"""
這些是用來存取應用程式主選單中的選單項目的標籤。詳情請參見 GSApplication.menu。
"""

APP_MENU: str
"""
Glyphs 選單
"""
FILE_MENU: str
"""
檔案選單
"""
EDIT_MENU: str
"""
編輯選單
"""
GLYPH_MENU: str
"""
字符選單
"""
PATH_MENU: str
"""
路徑選單
"""
FILTER_MENU: str
"""
濾鏡選單
"""
VIEW_MENU: str
"""
檢視選單
"""
SCRIPT_MENU: str
"""
腳本選單
"""
WINDOW_MENU: str
"""
視窗選單
"""
HELP_MENU: str
"""
說明選單
"""

# 選單狀態:
ONSTATE: str
"""
選單項目將有一個註記框
"""
OFFSTATE: str
"""
選單項目將沒有註記框
"""
MIXEDSTATE: str
"""
選單項目將有水平線
"""

# 回呼鍵:
"""
這些是用於註冊回呼的鍵。詳情請參見 GSApplication.addCallback()。
"""

DRAWFOREGROUND: str
"""
繪製在前景
"""
DRAWBACKGROUND: str
"""
繪製在背景
"""
DRAWINACTIVE: str
"""
繪製非使用中字符
"""
DOCUMENTOPENED: str
"""
當打開新檔案時呼叫
"""
DOCUMENTACTIVATED: str
"""
當文件變為使用中文件時呼叫
"""
DOCUMENTWASSAVED: str
"""
當文件被儲存時呼叫。文件本身將在通知物件中。
"""
DOCUMENTEXPORTED: str
"""
當匯出字型時。對每個實體呼叫此函數，通知物件將包含最終字型文件的路徑。
```    
def exportCallback(info):
    try:
        print(info.object())
    except:
        # 錯誤。打印異常。
        import traceback
        print(traceback.format_exc())
# 將您的函數新增到鉤子
Glyphs.addCallback(exportCallback, DOCUMENTEXPORTED)
"""
DOCUMENTCLOSED: str
"""
當文件被關閉時呼叫
"""
DOCUMENTWILLCLOSE: str
"""
當文件將被關閉時呼叫
訊息物件包含GSWindowController物件
"""
DOCUMENTDIDCLOSE: str
"""
在文件關閉後呼叫
訊息物件包含NSDocument物件
"""
TABDIDOPEN: str
"""
如果打開了新標籤
"""
TABWILLCLOSE: str
"""
如果關閉分頁
"""
UPDATEINTERFACE: str
"""
如果編輯畫面中有變化。也許是選取或字符資料。
"""
MOUSEMOVED: str
"""
如果鼠標移動。如果您需要繪製某些東西，您需要呼叫Glyphs.redraw()，並且還需要註冊一個繪製回呼。  
"""
FILTER_FLAT_KERNING: str
"""
匯出kern表時呼叫

在（通用）外掛中，實作這樣的方法：
```
@objc.typedSelector(b'@@:@o^@')
def filterFlatKerning_error_(self, flattKerning, error):
        newKerning = list()
        for kern in flattKerning:
                name1 = kern[0]
                name2 = kern[1]
                if len(name1) > 1 and len(name2) > 1:   # 這太過於簡化了。
                        continue
                if abs(kern[2]) < 10:   # 忽略小對
                        continue
                newKerning.append(kern)
        return newKerning, None
```
註冊回呼如下：
```
GSCallbackHandler.addCallback_forOperation_(self, FILTER_FLAT_KERNING)   # self需要是NSObject的子類（因為所有外掛都是）
```
3.2 版新增
"""

# 書寫方向:
"""
編輯畫面的書寫方向。
"""
GSBIDI: int
"""
用於遵循主要書寫方向的字符（如標點符號）
"""
GSLTR: int
"""
從左到右（例如拉丁文）
"""
GSRTL: int
"""
從右到左（例如阿拉伯文，希伯來文）
"""
GSVertical: Final = int
"""
從上到下，從右到左（例如中文，日文，韓文）
"""
GSVerticalToRight: Final = int
"""
從上到下，從左到右（例如蒙古文）
"""

# 形狀類型:
GSShapeTypePath: Final = int
"""
路徑
"""
GSShapeTypeComponent: Final = int
"""
組件
"""

# 註記類型:
TEXT: int
ARROW: int
CIRCLE: int
PLUS: int
MINUS: int

# 檢查器尺寸:
GSInspectorSizeSmall: Final = str
GSInspectorSizeRegular: Final = str
GSInspectorSizeLarge: Final = str
GSInspectorSizeXLarge: Final = str

# 度量類型:
"""
這些度量類型用於GSFont.metrics。參見GSMetric.type。
"""
GSMetricsTypeUndefined: Final = int
GSMetricsTypeAscender: Final = int
GSMetricsTypeCapHeight: Final = int
GSMetricsTypeSlantHeight: Final = int
GSMetricsTypexHeight: Final = int
GSMetricsTypeMidHeight: Final = int
GSMetricsTypeBodyHeight: Final = int
GSMetricsTypeDescender: Final = int
GSMetricsTypeBaseline: Final = int
GSMetricsTypeItalicAngle: Final = int
#endregion

# 自定義類別
Glyphs = GSApplication()
glyph = GSGlyph()
layer = GSLayer()
# axis = GSSmartComponentAxis()
# thisLayer = GSLayer()
# Glyphs.font = GSFont
