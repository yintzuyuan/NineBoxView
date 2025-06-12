@startuml
!theme plain
skinparam activity {
  BorderColor #5B9BD5
  BackgroundColor #E6F3FF
  ArrowColor #333
  FontName "sans-serif"
}
skinparam diamond {
  BorderColor #5B9BD5
  BackgroundColor #FFFFFF
  ArrowColor #333
  FontName "sans-serif"
}
skinparam partition {
  BorderColor #333
  BackgroundColor #F8F9FA
  FontName "sans-serif"
}
title 九宮格預覽繪製邏輯 - UML 活動圖

start

:1. 使用者選擇字符 (activeGlyph);

partition "選擇字符邏輯判斷" {
    if (有選擇 activeGlyph?) then (Y)
        if (批量輸入框 (batchChars) 有效?) then (Y)
            :結果:
            中心格: activeGlyph;
        else (N)
            :結果:
            中心格: activeGlyph
            其餘格: activeGlyph;
        endif
    else (N)
        if (批量輸入框 (batchChars) 有效?) then (Y)
            :結果:
            中心格: 從 batchChars 隨機;
        else (N)
            :結果:
            中心格: 空白
            其餘格: 空白;
        endif
    endif
}

:2. 使用者編輯鎖定模式;

partition "鎖定模式邏輯判斷" {
    if (鎖定模式?) then (Y / 上鎖)
        if (鎖定框 (lockedChars) 有效?) then (Y)
            :結果:
            鎖定格: lockedChars;
        else (N)
            :結果:
            鎖定格: 不填入;
        endif
    else (N / 解鎖)
        :結果:
        鎖定格: 不填入;
    endif
}

:3. 使用者編輯鎖定框 (lockedChars);

partition "鎖定框邏輯判斷" {
    if (鎖定框 (lockedChars) 有效?) then (Y)
        :結果:
        鎖定格: lockedChars;
    else (N)
        :結果:
        鎖定格: 不填入;
    endif
}

:4. 使用者編輯批量輸入框 (batchChars);

partition "批量輸入框邏輯判斷" {
    if (批量輸入框 (batchChars) 有效?) then (Y)
        :結果:
        其餘格: 從 batchChars 隨機;
    else (N)
        :結果:
        其餘格: 不填入;
    endif
}

stop
@enduml

優先順序:
- 中心格 > 鎖定格 > 其餘格

詞彙:
- 中心格: 九宮格的中心格 (格子 4)
- 鎖定格: 鎖定框對應的有效鎖定格 (格子 0,1,2,3,5,6,7,8)
- 其餘格: 鎖定框未對應的其他格 (格子 0,1,2,3,5,6,7,8)
- 不填入: 不執行填入動作，由其他邏輯按照優先順序決定填入的內容
- 空白: 填入空白字符