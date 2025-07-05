"""
第3章3.5節響應式設計實作測試
驗證所有設備適配和移動端優化功能
"""

import pytest
import sys
import os
from unittest.mock import Mock, patch, MagicMock

# 添加src目錄到Python路徑
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def test_responsive_design_imports():
    """測試響應式設計模組導入"""
    try:
        from src.ui.responsive_design import (
            ResponsiveDesignManager,
            DEVICE_BREAKPOINTS,
            MOBILE_OPTIMIZED_COMPONENTS,
            RESPONSIVE_CSS
        )
        print("✅ 響應式設計模組導入成功")
        return True
    except ImportError as e:
        print(f"❌ 響應式設計模組導入失敗: {e}")
        return False

def test_device_breakpoints_structure():
    """測試設備斷點結構 - 3.5.1節規格"""
    from src.ui.responsive_design import DEVICE_BREAKPOINTS
    
    # 檢查斷點數值
    assert DEVICE_BREAKPOINTS["desktop"] == 1024, "桌面斷點必須是1024px"
    assert DEVICE_BREAKPOINTS["tablet"] == 768, "平板斷點必須是768px"
    assert DEVICE_BREAKPOINTS["mobile"] == 0, "移動端斷點必須是0px"
    
    print("✅ 設備斷點結構符合3.5.1節規格")
    return True

def test_mobile_optimized_components_structure():
    """測試移動端優化組件結構 - 3.5.2節規格"""
    from src.ui.responsive_design import MOBILE_OPTIMIZED_COMPONENTS
    
    # 檢查touch_friendly_controls
    touch_controls = MOBILE_OPTIMIZED_COMPONENTS["touch_friendly_controls"]
    assert touch_controls["min_touch_target"] == "44px", "最小觸控目標必須是44px"
    assert touch_controls["slider_thumb_size"] == "24px", "滑桿拇指大小必須是24px"
    assert touch_controls["button_min_height"] == "48px", "按鈕最小高度必須是48px"
    assert touch_controls["tap_feedback"] == True, "必須啟用觸控反饋"
    
    # 檢查readable_typography
    typography = MOBILE_OPTIMIZED_COMPONENTS["readable_typography"]
    assert typography["min_font_size"] == "16px", "最小字體大小必須是16px"
    assert typography["line_height"] == "1.6", "行高必須是1.6"
    assert typography["contrast_ratio"] == "4.5:1", "對比度必須是4.5:1"
    assert typography["readable_color_scheme"] == True, "必須使用可讀色彩方案"
    
    # 檢查simplified_interactions
    interactions = MOBILE_OPTIMIZED_COMPONENTS["simplified_interactions"]
    assert interactions["reduce_decimal_precision"] == True, "必須減少小數精度"
    assert interactions["larger_step_sizes"] == True, "必須使用較大步長"
    assert interactions["preset_value_shortcuts"] == True, "必須提供預設值快捷鍵"
    assert interactions["swipe_gestures"] == True, "必須支援滑動手勢"
    
    # 檢查performance_optimization
    performance = MOBILE_OPTIMIZED_COMPONENTS["performance_optimization"]
    assert performance["lazy_loading"] == True, "必須啟用延遲載入"
    assert performance["image_compression"] == True, "必須啟用圖片壓縮"
    assert performance["minimal_animations"] == True, "必須使用最小動畫"
    assert performance["efficient_rendering"] == True, "必須啟用高效渲染"
    
    print("✅ 移動端優化組件結構符合3.5.2節規格")
    return True

def test_responsive_css_structure():
    """測試響應式CSS結構"""
    from src.ui.responsive_design import RESPONSIVE_CSS
    
    # 檢查CSS是否包含必要的媒體查詢
    assert "@media (max-width: 767px)" in RESPONSIVE_CSS, "必須包含移動端媒體查詢"
    assert "@media (min-width: 768px)" in RESPONSIVE_CSS, "必須包含平板端媒體查詢"
    assert "@media (min-width: 1024px)" in RESPONSIVE_CSS, "必須包含桌面端媒體查詢"
    
    # 檢查移動端字體大小調整
    assert "font-size: 1.75rem" in RESPONSIVE_CSS, "必須包含移動端h1字體調整"
    assert "font-size: 1.5rem" in RESPONSIVE_CSS, "必須包含移動端h2字體調整"
    assert "font-size: 1.25rem" in RESPONSIVE_CSS, "必須包含移動端h3字體調整"
    
    # 檢查觸控友善控件
    assert "min-height: 48px" in RESPONSIVE_CSS, "必須包含最小觸控高度"
    assert "font-size: 16px" in RESPONSIVE_CSS, "必須包含最小字體大小"
    
    print("✅ 響應式CSS結構符合規格")
    return True

@patch('streamlit.session_state', {})
def test_responsive_design_manager_initialization():
    """測試響應式設計管理器初始化"""
    from src.ui.responsive_design import ResponsiveDesignManager
    
    # 創建管理器實例
    manager = ResponsiveDesignManager()
    
    # 檢查基本屬性
    assert hasattr(manager, 'device_breakpoints'), "必須有設備斷點屬性"
    assert hasattr(manager, 'mobile_components'), "必須有移動端組件屬性"
    assert hasattr(manager, 'current_device'), "必須有當前設備屬性"
    assert hasattr(manager, 'screen_width'), "必須有螢幕寬度屬性"
    
    print("✅ 響應式設計管理器初始化成功")
    return True

def test_device_detection_logic():
    """測試設備檢測邏輯 - 3.5.1節規格"""
    from src.ui.responsive_design import ResponsiveDesignManager
    
    manager = ResponsiveDesignManager()
    
    # 模擬不同螢幕寬度
    test_cases = [
        (1920, "desktop"),  # >= 1024px
        (1024, "desktop"),  # = 1024px
        (768, "tablet"),    # >= 768px
        (800, "tablet"),    # 768px < width < 1024px
        (480, "mobile"),    # < 768px
        (320, "mobile")     # 小螢幕
    ]
    
    for width, expected_device in test_cases:
        # 模擬螢幕寬度
        manager.screen_width = width
        manager.current_device = manager._detect_device_type()
        
        # 檢查設備類型檢測
        detected_device = manager._detect_device_type()
        assert detected_device == expected_device, f"螢幕寬度{width}px應該檢測為{expected_device}，但檢測為{detected_device}"
    
    print("✅ 設備檢測邏輯符合3.5.1節規格")
    return True

def test_mobile_layout_methods():
    """測試移動端布局方法 - 3.5.1節規格"""
    from src.ui.responsive_design import ResponsiveDesignManager
    
    manager = ResponsiveDesignManager()
    
    # 檢查必要方法存在
    assert hasattr(manager, 'render_mobile_layout'), "必須有render_mobile_layout方法"
    assert hasattr(manager, 'render_simplified_parameters'), "必須有render_simplified_parameters方法"
    assert hasattr(manager, 'render_mobile_optimized_results'), "必須有render_mobile_optimized_results方法"
    assert hasattr(manager, 'render_compact_recommendations'), "必須有render_compact_recommendations方法"
    
    print("✅ 移動端布局方法符合3.5.1節規格")
    return True

def test_desktop_layout_methods():
    """測試桌面端布局方法 - 3.5.1節規格"""
    from src.ui.responsive_design import ResponsiveDesignManager
    
    manager = ResponsiveDesignManager()
    
    # 檢查必要方法存在
    assert hasattr(manager, 'render_desktop_layout'), "必須有render_desktop_layout方法"
    assert hasattr(manager, 'render_full_parameter_panel'), "必須有render_full_parameter_panel方法"
    assert hasattr(manager, 'render_main_results_area'), "必須有render_main_results_area方法"
    assert hasattr(manager, 'render_smart_suggestions_panel'), "必須有render_smart_suggestions_panel方法"
    
    print("✅ 桌面端布局方法符合3.5.1節規格")
    return True

def test_device_optimization_parameters():
    """測試設備優化參數"""
    from src.ui.responsive_design import ResponsiveDesignManager
    
    manager = ResponsiveDesignManager()
    
    # 測試移動端優化參數
    manager.current_device = "mobile"
    mobile_params = manager.get_optimized_parameters()
    
    assert mobile_params["decimal_places"] == 0, "移動端小數位數必須是0"
    assert mobile_params["step_size"] == 1000, "移動端步長必須是1000"
    assert mobile_params["show_advanced"] == False, "移動端不應顯示進階選項"
    assert mobile_params["use_presets"] == True, "移動端必須使用預設值"
    
    # 測試平板端優化參數
    manager.current_device = "tablet"
    tablet_params = manager.get_optimized_parameters()
    
    assert tablet_params["decimal_places"] == 1, "平板端小數位數必須是1"
    assert tablet_params["step_size"] == 500, "平板端步長必須是500"
    
    # 測試桌面端優化參數
    manager.current_device = "desktop"
    desktop_params = manager.get_optimized_parameters()
    
    assert desktop_params["decimal_places"] == 2, "桌面端小數位數必須是2"
    assert desktop_params["step_size"] == 100, "桌面端步長必須是100"
    assert desktop_params["show_advanced"] == True, "桌面端應顯示進階選項"
    
    print("✅ 設備優化參數符合規格")
    return True

def test_parameter_manager_mobile_methods():
    """測試參數管理器移動端方法"""
    try:
        from src.ui.parameter_manager import ParameterManager
        
        manager = ParameterManager()
        
        # 檢查移動端方法存在
        assert hasattr(manager, 'render_mobile_optimized_parameters'), "必須有render_mobile_optimized_parameters方法"
        assert hasattr(manager, 'render_complete_parameter_panel'), "必須有render_complete_parameter_panel方法"
        assert hasattr(manager, '_render_mobile_initial_investment'), "必須有_render_mobile_initial_investment方法"
        assert hasattr(manager, '_render_mobile_investment_years'), "必須有_render_mobile_investment_years方法"
        assert hasattr(manager, '_render_mobile_investment_frequency'), "必須有_render_mobile_investment_frequency方法"
        assert hasattr(manager, '_render_mobile_asset_allocation'), "必須有_render_mobile_asset_allocation方法"
        
        print("✅ 參數管理器移動端方法完整")
        return True
    except ImportError as e:
        print(f"❌ 參數管理器導入失敗: {e}")
        return False

def test_results_display_mobile_methods():
    """測試結果展示管理器移動端方法"""
    try:
        from src.ui.results_display import ResultsDisplayManager
        
        manager = ResultsDisplayManager()
        
        # 檢查移動端方法存在
        assert hasattr(manager, 'render_mobile_optimized_results'), "必須有render_mobile_optimized_results方法"
        assert hasattr(manager, '_render_mobile_summary_cards'), "必須有_render_mobile_summary_cards方法"
        assert hasattr(manager, '_render_mobile_metric_card'), "必須有_render_mobile_metric_card方法"
        assert hasattr(manager, '_render_mobile_chart'), "必須有_render_mobile_chart方法"
        assert hasattr(manager, '_render_mobile_comparison_table'), "必須有_render_mobile_comparison_table方法"
        
        print("✅ 結果展示管理器移動端方法完整")
        return True
    except ImportError as e:
        print(f"❌ 結果展示管理器導入失敗: {e}")
        return False

def test_smart_recommendations_compact_methods():
    """測試智能建議管理器緊湊方法"""
    try:
        from src.ui.smart_recommendations import SmartRecommendationsManager
        
        manager = SmartRecommendationsManager()
        
        # 檢查緊湊版方法存在
        assert hasattr(manager, 'render_compact_recommendations'), "必須有render_compact_recommendations方法"
        assert hasattr(manager, '_render_compact_knowledge_cards'), "必須有_render_compact_knowledge_cards方法"
        
        print("✅ 智能建議管理器緊湊方法完整")
        return True
    except ImportError as e:
        print(f"❌ 智能建議管理器導入失敗: {e}")
        return False

def test_layout_manager_responsive_integration():
    """測試布局管理器響應式整合"""
    try:
        from src.ui.layout_manager import LayoutManager
        
        manager = LayoutManager()
        
        # 檢查初始化方法
        assert hasattr(manager, 'initialize_layout'), "必須有initialize_layout方法"
        
        print("✅ 布局管理器響應式整合完成")
        return True
    except ImportError as e:
        print(f"❌ 布局管理器導入失敗: {e}")
        return False

def run_all_tests():
    """運行所有測試"""
    print("🚀 開始第3章3.5節響應式設計實作測試")
    print("=" * 60)
    
    test_results = []
    
    # 基礎結構測試
    test_results.append(("響應式設計模組導入", test_responsive_design_imports()))
    test_results.append(("設備斷點結構", test_device_breakpoints_structure()))
    test_results.append(("移動端優化組件結構", test_mobile_optimized_components_structure()))
    test_results.append(("響應式CSS結構", test_responsive_css_structure()))
    
    # 功能測試
    test_results.append(("響應式設計管理器初始化", test_responsive_design_manager_initialization()))
    test_results.append(("設備檢測邏輯", test_device_detection_logic()))
    test_results.append(("移動端布局方法", test_mobile_layout_methods()))
    test_results.append(("桌面端布局方法", test_desktop_layout_methods()))
    test_results.append(("設備優化參數", test_device_optimization_parameters()))
    
    # 整合測試
    test_results.append(("參數管理器移動端方法", test_parameter_manager_mobile_methods()))
    test_results.append(("結果展示管理器移動端方法", test_results_display_mobile_methods()))
    test_results.append(("智能建議管理器緊湊方法", test_smart_recommendations_compact_methods()))
    test_results.append(("布局管理器響應式整合", test_layout_manager_responsive_integration()))
    
    # 統計結果
    passed = sum(1 for _, result in test_results if result)
    total = len(test_results)
    
    print("=" * 60)
    print(f"📊 測試結果摘要:")
    print(f"總測試數: {total}")
    print(f"通過: {passed}")
    print(f"失敗: {total - passed}")
    print(f"成功率: {passed/total*100:.1f}%")
    
    if passed == total:
        print("🎉 所有測試通過！第3章3.5節響應式設計實作完成")
    else:
        print("⚠️  部分測試失敗，請檢查實作")
    
    return passed == total

if __name__ == "__main__":
    run_all_tests() 