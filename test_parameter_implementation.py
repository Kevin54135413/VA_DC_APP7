"""
第3章3.2節參數實作完整性測試
驗證所有參數定義和整合規範是否正確實作
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.ui.parameter_manager import (
    BASIC_PARAMETERS,
    ADVANCED_SETTINGS,
    ParameterManager
)

def test_basic_parameters_specs():
    """測試3.2.1 基本參數實作"""
    print("🔍 測試 3.2.1 基本參數實作...")
    
    # 檢查initial_investment參數
    initial_investment = BASIC_PARAMETERS["initial_investment"]
    assert initial_investment["component"] == "slider_with_input"
    assert initial_investment["label"] == "💰 期初投入金額"
    assert initial_investment["range"] == [100000, 10000000]
    assert initial_investment["default"] == 100000
    assert initial_investment["step"] == 50000
    assert initial_investment["format"] == "currency"
    assert initial_investment["precision"] == 2
    
    # 檢查第1章和第2章整合
    assert "chapter1_integration" in initial_investment
    assert "chapter2_integration" in initial_investment
    assert initial_investment["chapter2_integration"]["va_initial_investment"] == "C0參數"
    assert "calculate_va_target_value" in initial_investment["chapter2_integration"]["formula_references"]
    
    # 檢查investment_years參數
    investment_years = BASIC_PARAMETERS["investment_years"]
    assert investment_years["component"] == "slider"
    assert investment_years["label"] == "⏱️ 投資年數"
    assert investment_years["range"] == [5, 40]
    assert investment_years["default"] == 10
    assert investment_years["step"] == 1
    assert investment_years["format"] == "integer"
    
    # 檢查第1章和第2章整合
    assert investment_years["chapter1_integration"]["timeline_generation"] == True
    assert investment_years["chapter2_integration"]["total_periods_calculation"] == True
    
    # 檢查investment_frequency參數
    investment_frequency = BASIC_PARAMETERS["investment_frequency"]
    assert investment_frequency["component"] == "radio_buttons"
    assert investment_frequency["label"] == "📅 投資頻率"
    assert investment_frequency["default"] == "annually"
    assert investment_frequency["layout"] == "horizontal"
    
    # 檢查四個選項
    options = investment_frequency["options"]
    assert len(options) == 4
    
    monthly_option = next(opt for opt in options if opt["value"] == "monthly")
    assert monthly_option["label"] == "每月"
    assert monthly_option["icon"] == "📅"
    
    quarterly_option = next(opt for opt in options if opt["value"] == "quarterly")
    assert quarterly_option["label"] == "每季"
    assert quarterly_option["icon"] == "📊"
    
    semi_annually_option = next(opt for opt in options if opt["value"] == "semi_annually")
    assert semi_annually_option["label"] == "每半年"
    assert semi_annually_option["icon"] == "📈"
    
    annually_option = next(opt for opt in options if opt["value"] == "annually")
    assert annually_option["label"] == "每年"
    assert annually_option["icon"] == "🗓️"
    
    # 檢查第1章和第2章整合
    assert investment_frequency["chapter1_integration"]["trading_day_rules"] == True
    assert investment_frequency["chapter2_integration"]["parameter_conversion"] == "convert_annual_to_period_parameters"
    
    # 檢查asset_allocation參數
    asset_allocation = BASIC_PARAMETERS["asset_allocation"]
    assert asset_allocation["component"] == "dual_slider"
    assert asset_allocation["label"] == "📊 股債配置"
    assert asset_allocation["visual"] == "interactive_pie_chart"
    
    # 檢查股票配置
    stock_config = asset_allocation["stock_percentage"]
    assert stock_config["range"] == [0, 100]
    assert stock_config["default"] == 80
    assert stock_config["color"] == "#3b82f6"
    
    # 檢查債券配置
    bond_config = asset_allocation["bond_percentage"]
    assert bond_config["range"] == [0, 100]
    assert bond_config["default"] == 20
    assert bond_config["color"] == "#f59e0b"
    assert bond_config["auto_calculate"] == True
    
    # 檢查第1章和第2章整合
    assert asset_allocation["chapter1_integration"]["stock_data_source"] == "Tiingo API (SPY)"
    assert asset_allocation["chapter1_integration"]["bond_data_source"] == "FRED API (DGS1)"
    assert asset_allocation["chapter2_integration"]["portfolio_allocation_module"] == True
    
    print("✅ 基本參數實作正確")

def test_advanced_settings_specs():
    """測試3.2.2 進階設定實作"""
    print("🔍 測試 3.2.2 進階設定實作...")
    
    # 檢查可摺疊區域設定
    expandable_section = ADVANCED_SETTINGS["expandable_section"]
    assert expandable_section["title"] == "⚙️ 進階設定"
    assert expandable_section["expanded"] == False
    assert expandable_section["description"] == "調整策略細節參數"
    
    # 檢查va_growth_rate參數
    va_growth_rate = ADVANCED_SETTINGS["va_growth_rate"]
    assert va_growth_rate["component"] == "slider"
    assert va_growth_rate["label"] == "📈 VA策略目標成長率"
    assert va_growth_rate["range"] == [-20, 50]
    assert va_growth_rate["default"] == 13
    assert va_growth_rate["step"] == 1.0
    assert va_growth_rate["format"] == "percentage"
    assert va_growth_rate["precision"] == 4
    assert va_growth_rate["display_precision"] == 1
    
    # 檢查第2章整合
    chapter2_integration = va_growth_rate["chapter2_integration"]
    assert chapter2_integration["core_formula"] == "calculate_va_target_value"
    assert chapter2_integration["parameter_role"] == "r_period (年化成長率)"
    assert chapter2_integration["extreme_scenarios"] == True
    
    # 檢查inflation_adjustment參數
    inflation_adjustment = ADVANCED_SETTINGS["inflation_adjustment"]
    
    # 檢查開關設定
    enable_toggle = inflation_adjustment["enable_toggle"]
    assert enable_toggle["component"] == "switch"
    assert enable_toggle["label"] == "通膨調整"
    assert enable_toggle["default"] == True
    
    # 檢查通膨率設定
    inflation_rate = inflation_adjustment["inflation_rate"]
    assert inflation_rate["component"] == "slider"
    assert inflation_rate["label"] == "年通膨率"
    assert inflation_rate["range"] == [0, 15]
    assert inflation_rate["default"] == 2
    assert inflation_rate["step"] == 0.5
    assert inflation_rate["format"] == "percentage"
    assert inflation_rate["enabled_when"] == "inflation_adjustment.enable_toggle == True"
    
    # 檢查第2章整合
    chapter2_integration = inflation_rate["chapter2_integration"]
    assert chapter2_integration["formula_impact"] == "calculate_dca_investment中的g_period參數"
    assert chapter2_integration["cumulative_calculation"] == "calculate_dca_cumulative_investment"
    
    # 檢查data_source參數
    data_source = ADVANCED_SETTINGS["data_source"]
    assert data_source["component"] == "smart_auto_selection"
    assert data_source["label"] == "📊 數據來源"
    assert data_source["auto_mode"] == True
    assert data_source["smart_fallback"] == True
    
    # 檢查手動選項
    manual_override = data_source["manual_override"]
    options = manual_override["options"]
    assert len(options) == 2
    
    real_data_option = next(opt for opt in options if opt["value"] == "real_data")
    assert real_data_option["label"] == "真實市場數據"
    assert real_data_option["description"] == "Tiingo API + FRED API"
    assert real_data_option["icon"] == "🌐"
    
    simulation_option = next(opt for opt in options if opt["value"] == "simulation")
    assert simulation_option["label"] == "模擬數據"
    assert simulation_option["description"] == "基於歷史統計的模擬"
    assert simulation_option["icon"] == "🎲"
    
    # 檢查第1章整合
    chapter1_integration = data_source["chapter1_integration"]
    assert chapter1_integration["api_security_mechanisms"] == True
    assert chapter1_integration["fault_tolerance_strategy"] == True
    assert chapter1_integration["data_quality_validation"] == True
    assert chapter1_integration["simulation_model_specs"] == "幾何布朗運動 + Vasicek模型"
    
    print("✅ 進階設定實作正確")

def test_parameter_manager_class():
    """測試ParameterManager類別實作"""
    print("🔍 測試 ParameterManager 類別...")
    
    # 檢查方法存在（不創建實例以避免Streamlit依賴）
    assert hasattr(ParameterManager, 'render_basic_parameters')
    assert hasattr(ParameterManager, 'render_advanced_settings')
    assert hasattr(ParameterManager, 'get_all_parameters')
    assert hasattr(ParameterManager, 'validate_parameters')
    assert hasattr(ParameterManager, 'render_parameter_summary')
    
    # 檢查私有方法
    assert hasattr(ParameterManager, '_render_initial_investment')
    assert hasattr(ParameterManager, '_render_investment_years')
    assert hasattr(ParameterManager, '_render_investment_frequency')
    assert hasattr(ParameterManager, '_render_asset_allocation')
    assert hasattr(ParameterManager, '_render_va_growth_rate')
    assert hasattr(ParameterManager, '_render_inflation_adjustment')
    assert hasattr(ParameterManager, '_render_data_source_selection')
    
    print("✅ ParameterManager 類別實作正確")

def test_parameter_integration_specs():
    """測試參數整合規範"""
    print("🔍 測試參數整合規範...")
    
    # 檢查所有基本參數都有第1章和第2章整合
    for param_name, param_config in BASIC_PARAMETERS.items():
        if param_name != "asset_allocation":  # asset_allocation結構不同
            assert "chapter1_integration" in param_config, f"{param_name} 缺少第1章整合"
            assert "chapter2_integration" in param_config, f"{param_name} 缺少第2章整合"
    
    # 檢查asset_allocation特殊結構
    asset_allocation = BASIC_PARAMETERS["asset_allocation"]
    assert "chapter1_integration" in asset_allocation
    assert "chapter2_integration" in asset_allocation
    
    # 檢查進階設定的整合
    va_growth_rate = ADVANCED_SETTINGS["va_growth_rate"]
    assert "chapter2_integration" in va_growth_rate
    
    inflation_adjustment = ADVANCED_SETTINGS["inflation_adjustment"]
    assert "chapter2_integration" in inflation_adjustment["inflation_rate"]
    
    data_source = ADVANCED_SETTINGS["data_source"]
    assert "chapter1_integration" in data_source
    
    print("✅ 參數整合規範正確")

def test_parameter_ranges_and_defaults():
    """測試參數範圍和預設值"""
    print("🔍 測試參數範圍和預設值...")
    
    # 檢查initial_investment
    initial_investment = BASIC_PARAMETERS["initial_investment"]
    assert initial_investment["range"] == [100000, 10000000]
    assert initial_investment["default"] == 100000
    assert initial_investment["step"] == 50000
    
    # 檢查investment_years
    investment_years = BASIC_PARAMETERS["investment_years"]
    assert investment_years["range"] == [5, 40]
    assert investment_years["default"] == 10
    assert investment_years["step"] == 1
    
    # 檢查va_growth_rate
    va_growth_rate = ADVANCED_SETTINGS["va_growth_rate"]
    assert va_growth_rate["range"] == [-20, 50]
    assert va_growth_rate["default"] == 13
    assert va_growth_rate["step"] == 1.0
    
    # 檢查inflation_rate
    inflation_rate = ADVANCED_SETTINGS["inflation_adjustment"]["inflation_rate"]
    assert inflation_rate["range"] == [0, 15]
    assert inflation_rate["default"] == 2
    assert inflation_rate["step"] == 0.5
    
    print("✅ 參數範圍和預設值正確")

def test_emoji_and_labels():
    """測試emoji圖標和中文標籤"""
    print("🔍 測試emoji圖標和中文標籤...")
    
    # 檢查基本參數標籤
    assert BASIC_PARAMETERS["initial_investment"]["label"] == "💰 期初投入金額"
    assert BASIC_PARAMETERS["investment_years"]["label"] == "⏱️ 投資年數"
    assert BASIC_PARAMETERS["investment_frequency"]["label"] == "📅 投資頻率"
    assert BASIC_PARAMETERS["asset_allocation"]["label"] == "📊 股債配置"
    
    # 檢查進階設定標籤
    assert ADVANCED_SETTINGS["expandable_section"]["title"] == "⚙️ 進階設定"
    assert ADVANCED_SETTINGS["va_growth_rate"]["label"] == "📈 VA策略目標成長率"
    assert ADVANCED_SETTINGS["inflation_adjustment"]["enable_toggle"]["label"] == "通膨調整"
    assert ADVANCED_SETTINGS["data_source"]["label"] == "📊 數據來源"
    
    # 檢查投資頻率選項的emoji
    frequency_options = BASIC_PARAMETERS["investment_frequency"]["options"]
    icons = [opt["icon"] for opt in frequency_options]
    assert "📅" in icons
    assert "📊" in icons
    assert "📈" in icons
    assert "🗓️" in icons
    
    # 檢查數據來源選項的emoji
    data_source_options = ADVANCED_SETTINGS["data_source"]["manual_override"]["options"]
    icons = [opt["icon"] for opt in data_source_options]
    assert "🌐" in icons
    assert "🎲" in icons
    
    print("✅ emoji圖標和中文標籤正確")

def run_all_tests():
    """執行所有測試"""
    print("🚀 開始執行第3章3.2節參數實作完整性測試...\n")
    
    try:
        test_basic_parameters_specs()
        test_advanced_settings_specs()
        test_parameter_manager_class()
        test_parameter_integration_specs()
        test_parameter_ranges_and_defaults()
        test_emoji_and_labels()
        
        print("\n🎉 所有測試通過！第3章3.2節參數實作完全符合需求文件規格")
        print("\n✅ 實作檢查清單:")
        print("   ✅ BASIC_PARAMETERS 字典完整實作")
        print("   ✅ initial_investment: slider_with_input, range[100000,10000000], default=100000")
        print("   ✅ investment_years: slider, range[5,40], default=10")
        print("   ✅ investment_frequency: radio_buttons, 4選項, default=annually")
        print("   ✅ asset_allocation: dual_slider, interactive_pie_chart, auto_calculate")
        print("   ✅ ADVANCED_SETTINGS 字典完整實作")
        print("   ✅ va_growth_rate: range[-20,50], default=13, precision=4")
        print("   ✅ inflation_adjustment: toggle + slider, default=True")
        print("   ✅ data_source: smart_auto_selection, 2選項, auto_mode=True")
        print("   ✅ 所有章節整合規範正確實作")
        print("   ✅ 所有emoji圖標和中文標籤保留")
        print("   ✅ 所有參數範圍和預設值未修改")
        print("   ✅ ParameterManager類別完整實作")
        
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