# NineBoxView 邏輯流程圖

```mermaid
graph TD
    %% Styling for better readability
    classDef decision fill:#e6f3ff,stroke:#5b9bd5,stroke-width:2px;
    classDef process fill:#f8f9fa,stroke:#333,stroke-width:1px;
    classDef result fill:#e2f0d9,stroke:#70ad47,stroke-width:2px,font-weight:bold;

    %% Define Node Classes
    class Q1,Q2,Q3,Q4,Q5,Q6,Q7,Q8,Q9,Q10,Q11 decision;
    class R1,R2,R3,R4,R5,R7,R8,R9,R10,R11,R12,R13 result;

    %% Main Logic Flow
    Start((開始)) --> Q1{有選擇<br>activeGlyph?};

    subgraph "Y: 有選擇 activeGlyph"
        direction TB
        Q1 -- Y --> Q2{鎖定模式?};

        Q2 -- "Y / 上鎖" --> Q3{鎖定框（lockedChars）<br>有有效字符?};
        Q3 -- Y --> Q4{批量輸入框（batchChars）<br>有有效字符?};
        Q4 -- Y --> R1["結果:<br>1. 中心: activeGlyph<br>2. 鎖定格: lockedChars<br>3. 其餘格: 從 batchChars 隨機"];
        Q4 -- N --> R2["結果:<br>1. 中心: activeGlyph<br>2. 鎖定格: lockedChars<br>3. 其餘格: activeGlyph"];

        Q3 -- N --> Q5{批量輸入框（batchChars）<br>有有效字符?};
        Q5 -- Y --> R3["結果:<br>1. 中心: activeGlyph<br>2. 周圍格: 從 batchChars 隨機"];
        Q5 -- N --> R4["結果:<br>1. 中心: activeGlyph<br>2. 其餘格: activeGlyph"];

        Q2 -- "N / 解鎖" --> Q6{批量輸入框（batchChars）<br>有有效字符?};
        Q6 -- Y --> R5["結果:<br>1. 中心: activeGlyph<br>2. 周圍格: 從 batchChars 隨機"];
        Q6 -- N --> R13["結果:<br>1. 中心: activeGlyph<br>2. 其餘格: activeGlyph"];
    end

    subgraph "N: 沒有選擇 activeGlyph"
        direction TB
        Q1 -- N --> Q7{鎖定模式?};

        Q7 -- "Y / 上鎖" --> Q8{鎖定框（lockedChars）<br>有有效字符?};
        Q8 -- Y --> Q9{批量輸入框（batchChars）<br>有有效字符?};
        Q9 -- Y --> R7["結果:<br>1. 鎖定格: lockedChars<br>2. 其餘格(含中心):<br>   從 batchChars 隨機"];
        Q9 -- N --> R8["結果:<br>1. 鎖定格: lockedChars<br>2. 其餘格(含中心): 空白"];

        Q8 -- N --> Q10{批量輸入框（batchChars）<br>有有效字符?};
        Q10 -- Y --> R9["結果:<br>所有九格(含中心）<br>從 batchChars 隨機"];
        Q10 -- N --> R10["結果:<br>所有九格皆為空白"];

        Q7 -- "N / 解鎖" --> Q11{批量輸入框（batchChars）<br>有有效字符?};
        Q11 -- Y --> R11["結果:<br>所有九格(含中心）<br>從 batchChars 隨機"];
        Q11 -- N --> R12["結果:<br>所有九格皆為空白"];
    end

    %% Legend
    subgraph Legend [名詞對照表]
        direction LR
        L1["<b>activeGlyph:</b><br/>在 Glyphs 中當前選擇的字符"]
        L2["<b>batchChars:</b><br/>批量輸入框的有效字符"]
        L3["<b>lockedChars:</b><br/>8 個鎖定框的有效字符"]
    end

    style Legend fill:#fff,stroke:#ccc,stroke-dasharray: 5 5
