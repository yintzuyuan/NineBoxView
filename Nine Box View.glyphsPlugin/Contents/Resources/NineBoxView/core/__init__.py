# encoding: utf-8

"""
核心邏輯模組
九宮格預覽的核心功能實作
"""

from __future__ import division, print_function, unicode_literals

# 核心模組可用，但避免在 __init__ 中匯入以防循環依賴
# 使用時請直接從子模組匯入：
# from NineBoxView.core.grid_manager import GridManager
# from NineBoxView.core.event_handler import NineBoxEventHandler

__all__ = [
    'grid_manager',
    'event_handler', 
    'utils',
    'menu_manager',
    'glyphs_service',
    'input_recognition',
    'theme_detector',
    'light_table_support',
    'random_arrangement'
]