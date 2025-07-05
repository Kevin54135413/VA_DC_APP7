"""
第3章3.1節實作完整性測試
驗證所有需求文件規格是否正確實作
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.ui.layout_manager import (
    APP_HEADER_SPECS, 
    RESPONSIVE_LAYOUT_CONFIG, 
    MODERN_HEADER_SPECS,
    LayoutManager
)

def test_app_header_specs():
    """測試3.1.1 APP_HEADER_SPECS字典實作"""
    print("🔍 測試 3.1.1 APP_HEADER_SPECS 字典...")
    
    # 檢查main_title規格
    assert APP_HEADER_SPECS["main_title"]["text"] == "投資策略績效比較分析系統"
    assert APP_HEADER_SPECS["main_title"]["font_size"] == "2.5rem"
    assert APP_HEADER_SPECS["main_title"]["font_weight"] == "bold"
    assert APP_HEADER_SPECS["main_title"]["color"] == "#1f2937"
    assert APP_HEADER_SPECS["main_title"]["text_align"] == "center"
    assert APP_HEADER_SPECS["main_title"]["margin_bottom"] == "0.5rem"
    
    # 檢查subtitle規格
    assert APP_HEADER_SPECS["subtitle"]["text"] == "VA(定期定值) vs DCA(定期定額) 策略比較"
    assert APP_HEADER_SPECS["subtitle"]["font_size"] == "1.2rem"
    assert APP_HEADER_SPECS["subtitle"]["color"] == "#6b7280"
    assert APP_HEADER_SPECS["subtitle"]["text_align"] == "center"
    assert APP_HEADER_SPECS["subtitle"]["margin_bottom"] == "1rem"
    
    # 檢查visual_simplicity三個原則
    assert APP_HEADER_SPECS["visual_simplicity"]["clean_interface"] == "移除非必要視覺元素"
    assert APP_HEADER_SPECS["visual_simplicity"]["intuitive_navigation"] == "符合用戶心理模型的操作流程"
    assert APP_HEADER_SPECS["visual_simplicity"]["friendly_guidance"] == "使用emoji和簡潔文案提升親和力"
    
    print("✅ APP_HEADER_SPECS 字典實作正確")

def test_responsive_layout_config():
    """測試3.1.2 RESPONSIVE_LAYOUT_CONFIG實作"""
    print("🔍 測試 3.1.2 RESPONSIVE_LAYOUT_CONFIG...")
    
    # 檢查desktop_layout規格
    desktop = RESPONSIVE_LAYOUT_CONFIG["desktop_layout"]["implementation"]
    
    # left_panel規格
    assert desktop["left_panel"]["width"] == 350
    assert desktop["left_panel"]["content"] == "simplified_parameter_inputs"
    assert desktop["left_panel"]["collapsible"] == False
    
    # center_panel規格
    assert desktop["center_panel"]["width"] == "auto"
    assert desktop["center_panel"]["content"] == "results_visualization"
    assert desktop["center_panel"]["responsive"] == True
    
    # right_panel規格
    assert desktop["right_panel"]["width"] == 300
    assert desktop["right_panel"]["content"] == "smart_recommendations"
    assert desktop["right_panel"]["hide_on_tablet"] == True
    
    # breakpoint規格
    assert RESPONSIVE_LAYOUT_CONFIG["desktop_layout"]["breakpoint"] == ">=1024px"
    
    # 檢查mobile_layout規格
    mobile = RESPONSIVE_LAYOUT_CONFIG["mobile_layout"]
    assert mobile["structure"] == "tab_navigation"
    assert mobile["navigation_position"] == "bottom"
    assert mobile["breakpoint"] == "<1024px"
    
    # 檢查三個tabs
    tabs = mobile["tabs"]
    assert len(tabs) == 3
    
    # 檢查第一個tab (🎯設定)
    tab1 = next(t for t in tabs if t["priority"] == 1)
    assert tab1["name"] == "🎯 設定"
    assert tab1["icon"] == "⚙️"
    assert tab1["content"] == "parameter_inputs"
    
    # 檢查第二個tab (📊結果)
    tab2 = next(t for t in tabs if t["priority"] == 2)
    assert tab2["name"] == "📊 結果"
    assert tab2["icon"] == "📈"
    assert tab2["content"] == "results_display"
    
    # 檢查第三個tab (💡建議)
    tab3 = next(t for t in tabs if t["priority"] == 3)
    assert tab3["name"] == "💡 建議"
    assert tab3["icon"] == "🎯"
    assert tab3["content"] == "recommendations"
    
    print("✅ RESPONSIVE_LAYOUT_CONFIG 實作正確")

def test_modern_header_specs():
    """測試3.1.3 MODERN_HEADER_SPECS實作"""
    print("🔍 測試 3.1.3 MODERN_HEADER_SPECS...")
    
    # 檢查main_header規格
    main_header = MODERN_HEADER_SPECS["main_header"]
    assert main_header["title"] == "🏠 投資策略比較分析"
    assert main_header["subtitle"] == "輕鬆比較兩種投資方法"
    assert main_header["style"] == "minimal_centered"
    assert main_header["mobile_optimized"] == True
    
    # 檢查smart_status_indicator規格
    status_indicator = MODERN_HEADER_SPECS["smart_status_indicator"]
    
    # 檢查data_source_status
    data_source = status_indicator["data_source_status"]
    assert data_source["display_mode"] == "icon_with_tooltip"
    assert data_source["auto_fallback"] == True
    assert data_source["user_notification"] == "minimal"
    
    # 檢查三種狀態
    states = data_source["states"]
    assert states["real_data"]["icon"] == "🟢"
    assert states["real_data"]["tooltip"] == "使用真實市場數據"
    assert states["simulation"]["icon"] == "🟡"
    assert states["simulation"]["tooltip"] == "使用模擬數據"
    assert states["offline"]["icon"] == "🔴"
    assert states["offline"]["tooltip"] == "離線模式"
    
    # 檢查chapter1_integration
    chapter1 = status_indicator["chapter1_integration"]
    assert chapter1["multilevel_api_security"] == "background_processing"
    assert chapter1["fault_tolerance"] == "automatic"
    assert chapter1["data_quality_monitoring"] == "silent"
    assert chapter1["backup_strategy"] == "seamless_switching"
    
    print("✅ MODERN_HEADER_SPECS 實作正確")

def test_layout_manager_class():
    """測試LayoutManager類別實作"""
    print("🔍 測試 LayoutManager 類別...")
    
    # 創建LayoutManager實例
    layout_manager = LayoutManager()
    
    # 檢查屬性初始化
    assert hasattr(layout_manager, 'device_type')
    assert hasattr(layout_manager, 'layout_config')
    assert hasattr(layout_manager, 'header_specs')
    assert hasattr(layout_manager, 'modern_header_specs')
    
    # 檢查配置正確性
    assert layout_manager.layout_config == RESPONSIVE_LAYOUT_CONFIG
    assert layout_manager.header_specs == APP_HEADER_SPECS
    assert layout_manager.modern_header_specs == MODERN_HEADER_SPECS
    
    # 檢查方法存在
    assert hasattr(layout_manager, 'apply_modern_styling')
    assert hasattr(layout_manager, 'render_modern_header')
    assert hasattr(layout_manager, 'render_layout')
    assert hasattr(layout_manager, 'render_desktop_layout')
    assert hasattr(layout_manager, 'render_mobile_layout')
    assert hasattr(layout_manager, 'initialize_layout')
    
    print("✅ LayoutManager 類別實作正確")

def run_all_tests():
    """執行所有測試"""
    print("🚀 開始執行第3章3.1節實作完整性測試...\n")
    
    try:
        test_app_header_specs()
        test_responsive_layout_config()
        test_modern_header_specs()
        test_layout_manager_class()
        
        print("\n🎉 所有測試通過！第3章3.1節實作完全符合需求文件規格")
        print("\n✅ 實作檢查清單:")
        print("   ✅ APP_HEADER_SPECS 字典完整實作")
        print("   ✅ main_title: 字體大小2.5rem, 粗體, 顏色#1f2937")
        print("   ✅ subtitle: 字體大小1.2rem, 顏色#6b7280")
        print("   ✅ visual_simplicity 三個原則完整")
        print("   ✅ desktop_layout: left_panel 350px, center_panel auto, right_panel 300px")
        print("   ✅ mobile_layout: tab_navigation, 三個tabs按priority排序")
        print("   ✅ smart_status_indicator: 三種狀態🟢🟡🔴")
        print("   ✅ chapter1_integration: API狀態整合")
        print("   ✅ LayoutManager類別完整實作")
        print("   ✅ 響應式斷點: >=1024px (桌面), <1024px (移動)")
        
    except AssertionError as e:
        print(f"❌ 測試失敗: {e}")
        return False
    except Exception as e:
        print(f"❌ 測試過程中發生錯誤: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = run_all_tests()
    if not success:
        exit(1) 