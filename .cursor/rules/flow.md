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

if (有選擇 activeGlyph?) then (Y)
    partition "情境: 有選擇 activeGlyph" {
        if (鎖定模式?) then (Y / 上鎖)
            if (鎖定框 (lockedChars) 有效?) then (Y)
                if (批量輸入框 (batchChars) 有效?) then (Y)
                    :結果:
                    1. 中心: activeGlyph
                    2. 鎖定格: lockedChars
                    3. 其餘格: 從 batchChars 隨機;
                else (N)
                    :結果:
                    1. 中心: activeGlyph
                    2. 鎖定格: lockedChars
                    3. 其餘格: activeGlyph;
                endif
            else (N)
                if (批量輸入框 (batchChars) 有效?) then (Y)
                    :結果:
                    1. 中心: activeGlyph
                    2. 周圍格: 從 batchChars 隨機;
                else (N)
                    :結果:
                    1. 中心: activeGlyph
                    2. 周圍格: activeGlyph;
                endif
            endif
        else (N / 解鎖)
            if (批量輸入框 (batchChars) 有效?) then (Y)
                :結果:
                1. 中心: activeGlyph
                2. 周圍格: 從 batchChars 隨機;
            else (N)
                :結果:
                1. 中心: activeGlyph
                2. 周圍格: activeGlyph;
            endif
        endif
    }
else (N)
    partition "情境: 沒有選擇 activeGlyph" {
        if (鎖定模式?) then (Y / 上鎖)
            if (鎖定框 (lockedChars) 有效?) then (Y)
                if (批量輸入框 (batchChars) 有效?) then (Y)
                    :結果:
                    1. 中心: 從 batchChars 隨機
                    2. 鎖定格: lockedChars
                    3. 其餘格: 從 batchChars 隨機;
                else (N)
                    :結果:
                    1. 中心: 空白
                    2. 鎖定格: lockedChars
                    3. 其餘格: 空白;
                endif
            else (N)
                if (批量輸入框 (batchChars) 有效?) then (Y)
                    :結果:
                    1. 中心: 從 batchChars 隨機
                    2. 周圍格: 從 batchChars 隨機;
                else (N)
                    :結果:
                    1. 中心: 空白
                    2. 周圍格: 空白;
                endif
            endif
        else (N / 解鎖)
            if (批量輸入框 (batchChars) 有效?) then (Y)
                :結果:
                1. 中心: 從 batchChars 隨機
                2. 周圍格: 從 batchChars 隨機;
            else (N)
                :結果:
                1. 中心: 空白
                2. 周圍格: 空白;
            endif
        endif
    }
endif

stop
@enduml
