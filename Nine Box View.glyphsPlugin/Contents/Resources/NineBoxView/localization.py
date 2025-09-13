# encoding: utf-8

"""
NineBoxView 本地化管理模組

集中管理所有使用者介面文字的多語言翻譯，支援 5 種語言：
- 英文 (en): 預設語言
- 繁體中文 (zh-Hant): 主要目標語言
- 簡體中文 (zh-Hans): 簡體版本  
- 日文 (ja): 日文版本
- 韓文 (ko): 韓文版本

使用方式：
    from .localization import localize, localize_with_params
    
    # 簡單文字本地化
    text = localize('menu_glyph_picker')
    
    # 帶參數的文字本地化（示例）
    message = localize_with_params('error_glyph_not_exist_in_master', 
                                   glyph_name='A', master_name='Regular')
"""

from __future__ import division, print_function, unicode_literals
from GlyphsApp import Glyphs

# 翻譯字典：所有使用者可見文字的多語言版本
STRINGS = {
    # 右鍵選單項目
    'menu_glyph_picker': {
        'en': u'Glyph Picker...',
        'zh-Hant': u'字符選擇器...',
        'zh-Hans': u'字符选择器...',
        'ja': u'グリフ選択器...',
        'ko': u'글리프 선택기...'
    },
    
    'menu_insert_to_current_tab': {
        'en': u'Insert to Current Tab',
        'zh-Hant': u'插入到目前分頁',
        'zh-Hans': u'插入到当前分页',
        'ja': u'現在のタブに挿入',
        'ko': u'현재 탭에 삽입'
    },
    
    'menu_open_in_new_tab': {
        'en': u'Open in New Tab',
        'zh-Hant': u'在新分頁開啟',
        'zh-Hans': u'在新分页打开',
        'ja': u'新しいタブで開く',
        'ko': u'새 탭에서 열기'
    },
    
    'menu_copy_glyph_name': {
        'en': u'Copy Glyph Name',
        'zh-Hant': u'複製字符名稱',
        'zh-Hans': u'复制字符名称',
        'ja': u'グリフ名をコピー',
        'ko': u'글리프 이름 복사'
    },
    
    
    
    # 前台錯誤訊息（使用者可見的 UI 訊息）
    'error_glyph_not_exist': {
        'en': u'Glyph does not exist',
        'zh-Hant': u'字符不存在',
        'zh-Hans': u'字符不存在',
        'ja': u'グリフが存在しません',
        'ko': u'글리프가 존재하지 않습니다'
    },
    
    
    # 視窗標題
    'window_control_panel_suffix': {
        'en': u' - Control Panel',
        'zh-Hant': u' - 控制面板',
        'zh-Hans': u' - 控制面板',
        'ja': u' - コントロールパネル',
        'ko': u' - 제어판'
    },
    
    # UI 元件文字
    'clear_all_locks': {
        'en': u'Clear All Locks',
        'zh-Hant': u'清空鎖定',
        'zh-Hans': u'清空锁定',
        'ja': u'ロッククリア',
        'ko': u'잠금 해제'
    },
    
    'menu_lock_field_title': {
        'en': u'Lock Field Menu',
        'zh-Hant': u'鎖定輸入框選單',
        'zh-Hans': u'锁定输入框菜单',
        'ja': u'ロックフィールドメニュー',
        'ko': u'잠금 필드 메뉴'
    },
    
    # Tooltip 文字
    'tooltip_clear_all_locks': {
        'en': u'Clear all lock input fields',
        'zh-Hant': u'清除所有鎖定輸入框',
        'zh-Hans': u'清除所有锁定输入框',
        'ja': u'すべてのロック入力フィールドをクリア',
        'ko': u'모든 잠금 입력 필드 지우기'
    },
    
    'tooltip_toggle_to_unlock': {
        'en': u'Toggle to unlock mode',
        'zh-Hant': u'切換為解鎖模式',
        'zh-Hans': u'切换为解锁模式',
        'ja': u'アンロックモードに切り替え',
        'ko': u'잠금 해제 모드로 전환'
    },
    
    'tooltip_toggle_to_lock': {
        'en': u'Toggle to lock mode',
        'zh-Hant': u'切換為鎖定模式',
        'zh-Hans': u'切换为锁定模式',
        'ja': u'ロックモードに切り替え',
        'ko': u'잠금 모드로 전환'
    },
    
    
    
    'tooltip_search_input': {
        'en': u'Enter reference characters...',
        'zh-Hant': u'輸入參考字符...',
        'zh-Hans': u'输入参考字符...',
        'ja': u'参考文字を入力...',
        'ko': u'참고 문자를 입력하세요...'
    }
}


def localize(key):
    """
    本地化指定鍵值的文字
    
    Args:
        key (str): 翻譯鍵值
        
    Returns:
        str: 本地化後的文字，如果鍵值不存在則返回鍵值本身
    """
    translations = STRINGS.get(key)
    if not translations:
        return key
    
    return Glyphs.localize(translations)


def localize_with_params(key, **params):
    """
    本地化指定鍵值的文字並替換參數
    
    Args:
        key (str): 翻譯鍵值
        **params: 要替換的參數
        
    Returns:
        str: 本地化並替換參數後的文字
    """
    localized_text = localize(key)
    try:
        return localized_text.format(**params)
    except (KeyError, ValueError):
        # 如果參數替換失敗，返回原始本地化文字
        return localized_text


def get_available_languages():
    """
    取得支援的語言清單
    
    Returns:
        list: 支援的語言代碼清單
    """
    return ['en', 'zh-Hant', 'zh-Hans', 'ja', 'ko']


def validate_translations():
    """
    驗證所有翻譯鍵值是否完整
    
    Returns:
        dict: 驗證結果，包含缺失的翻譯
    """
    missing_translations = {}
    supported_languages = get_available_languages()
    
    for key, translations in STRINGS.items():
        missing_langs = []
        for lang in supported_languages:
            if lang not in translations or not translations[lang].strip():
                missing_langs.append(lang)
        
        if missing_langs:
            missing_translations[key] = missing_langs
    
    return missing_translations