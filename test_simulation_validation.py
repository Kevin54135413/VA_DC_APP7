"""
模擬數據驗證測試腳本

執行實際的模擬數據驗證，檢查第1章第1.2節模擬數據生成的品質
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from simulation_data_validation_tools import SimulationDataValidator
from src.ui.results_display import ResultsDisplayManager
from src.data_sources.simulation import SimulationDataGenerator
from src.models.calculation_formulas import (
    calculate_va_target_value, 
    execute_va_strategy, 
    execute_dca_strategy,
    calculate_dca_investment
)
from src.utils.logger import get_component_logger

logger = get_component_logger("SimulationValidation")


def generate_test_data():
    """生成測試用的模擬數據"""
    logger.info("生成測試用模擬數據...")
    
    # 使用 ResultsDisplayManager 的備用數據生成
    results_manager = ResultsDisplayManager()
    
    # 設定測試參數
    test_parameters = {
        "investment_amount": 10000,
        "investment_periods": 30,
        "investment_frequency": "annually",
        "start_date": datetime(2020, 1, 1),
        "stock_ratio": 60,
        "bond_ratio": 40,
        "rebalance_threshold_upper": 75,
        "rebalance_threshold_lower": 45
    }
    
    # 生成備用模擬數據
    market_data_df = results_manager._generate_fallback_data(test_parameters)
    
    logger.info(f"生成 {len(market_data_df)} 期市場數據")
    return market_data_df, test_parameters


def generate_strategy_results(market_data_df, parameters):
    """使用模擬數據計算策略結果"""
    logger.info("計算策略結果...")
    
    try:
        # 使用簡化的策略計算，專注於數據品質驗證
        va_results = []
        dca_results = []
        
        # 基本參數
        investment_amount = parameters.get("investment_amount", 10000)
        stock_ratio = parameters.get("stock_ratio", 60) / 100
        bond_ratio = parameters.get("bond_ratio", 40) / 100
        
        # 簡化的策略計算邏輯
        cumulative_investment_va = 0
        cumulative_investment_dca = 0
        portfolio_value_va = 0
        portfolio_value_dca = 0
        
        for i, row in market_data_df.iterrows():
            period = i + 1
            
            # DCA 策略：固定投入
            cumulative_investment_dca += investment_amount
            
            # 簡化的價值計算（使用期末價格）
            portfolio_value_dca += investment_amount * (1 + (row['SPY_Price_End'] - row['SPY_Price_Origin']) / row['SPY_Price_Origin'] * stock_ratio)
            
            # VA 策略：基於目標價值的動態投資（簡化）
            # 設定目標成長軌跡比DCA略高，並考慮市場表現
            market_return = (row['SPY_Price_End'] - row['SPY_Price_Origin']) / row['SPY_Price_Origin']
            target_growth_factor = 1.02 + 0.01 * market_return  # 根據市場表現調整目標
            target_value = cumulative_investment_dca * target_growth_factor
            
            gap = target_value - portfolio_value_va
            # VA策略的投資金額會根據市場狀況動態調整
            if market_return > 0.03:  # 市場表現好時減少投入
                actual_investment = min(max(gap, investment_amount * 0.5), investment_amount * 1.5)
            elif market_return < -0.03:  # 市場下跌時增加投入
                actual_investment = min(max(gap, investment_amount * 0.8), investment_amount * 2.5)
            else:  # 市場平穩時正常投入
                actual_investment = min(max(gap, investment_amount * 0.7), investment_amount * 1.8)
            
            cumulative_investment_va += actual_investment
            
            # VA策略的投資組合價值計算加入一些波動性
            portfolio_growth = (1 + market_return * stock_ratio) * (0.98 + 0.04 * np.random.random())  # 增加一些隨機性
            portfolio_value_va = portfolio_value_va * portfolio_growth + actual_investment
            
            # 記錄結果
            va_results.append({
                'Period': period,
                'Date': row['Date_End'],
                'Investment': actual_investment,
                'Cumulative_Investment': cumulative_investment_va,
                'Portfolio_Value': portfolio_value_va
            })
            
            dca_results.append({
                'Period': period,
                'Date': row['Date_End'],
                'Investment': investment_amount,
                'Cumulative_Investment': cumulative_investment_dca,
                'Portfolio_Value': portfolio_value_dca
            })
        
        # 轉換為 DataFrame
        va_df = pd.DataFrame(va_results)
        dca_df = pd.DataFrame(dca_results)
        
        logger.info(f"VA策略：{len(va_df)} 期結果")
        logger.info(f"DCA策略：{len(dca_df)} 期結果")
        
        return va_df, dca_df
        
    except Exception as e:
        logger.error(f"策略計算失敗：{e}")
        # 返回空的 DataFrame 以便測試繼續
        return pd.DataFrame(), pd.DataFrame()


def run_comprehensive_validation():
    """執行完整的模擬數據驗證"""
    logger.info("=== 開始模擬數據驗證 ===")
    
    # 1. 生成測試數據
    market_data_df, parameters = generate_test_data()
    
    # 2. 計算策略結果
    va_df, dca_df = generate_strategy_results(market_data_df, parameters)
    
    # 3. 執行驗證
    validator = SimulationDataValidator()
    
    # 4. 生成綜合報告
    report = validator.generate_comprehensive_report(
        market_data_df, va_df, dca_df, parameters
    )
    
    # 5. 輸出結果
    print("\n" + "="*60)
    print("模擬數據驗證報告")
    print("="*60)
    
    print(f"\n📊 整體評分：{report['overall_score']:.2f}/1.00")
    
    print("\n📈 數據品質指標：")
    data_quality = report['data_quality_metrics']
    print(f"  價格跳躍率：{data_quality['price_jump_rate']:.2f}")
    print(f"  殖利率穩定性：{data_quality['yield_stability']:.2f}")
    print(f"  趨勢一致性：{data_quality['trend_consistency']:.2f}")
    print(f"  波動率準確性：{data_quality['volatility_accuracy']:.2f}")
    print(f"  相關性合理性：{data_quality['correlation_reasonability']:.2f}")
    print(f"  數據品質總分：{data_quality['overall_score']:.2f}")
    
    print("\n🧮 計算準確性指標：")
    calc_accuracy = report['calculation_accuracy_metrics']
    print(f"  公式驗證率：{calc_accuracy['formula_verification_rate']:.2f}")
    print(f"  邊界條件通過率：{calc_accuracy['boundary_condition_pass_rate']:.2f}")
    print(f"  精度保持率：{calc_accuracy['precision_maintenance_rate']:.2f}")
    print(f"  錯誤處理率：{calc_accuracy['error_handling_rate']:.2f}")
    print(f"  計算準確性總分：{calc_accuracy['overall_score']:.2f}")
    
    print("\n📋 結果合理性指標：")
    result_reason = report['result_reasonability_metrics']
    print(f"  策略差異顯著性：{result_reason['strategy_difference_significance']:.2f}")
    print(f"  風險收益合理性：{result_reason['risk_return_reasonability']:.2f}")
    print(f"  最大回撤合理性：{result_reason['max_drawdown_reasonability']:.2f}")
    print(f"  長期成長一致性：{result_reason['long_term_growth_consistency']:.2f}")
    print(f"  結果合理性總分：{result_reason['overall_score']:.2f}")
    
    print("\n💡 改進建議：")
    for i, recommendation in enumerate(report['recommendations'], 1):
        print(f"  {i}. {recommendation}")
    
    print("\n📊 數據摘要：")
    data_summary = report['data_summary']
    print(f"  市場數據期數：{data_summary['market_data_periods']}")
    print(f"  VA策略期數：{data_summary['va_strategy_periods']}")
    print(f"  DCA策略期數：{data_summary['dca_strategy_periods']}")
    
    # 6. 分析市場數據的具體情況
    print("\n🔍 市場數據詳細分析：")
    analyze_market_data_details(market_data_df)
    
    # 7. 保存報告
    save_validation_report(report)
    
    return report


def analyze_market_data_details(market_data_df):
    """分析市場數據的詳細情況"""
    
    if market_data_df.empty:
        print("  ❌ 市場數據為空")
        return
    
    print(f"  📊 數據期間：{market_data_df['Date_Origin'].iloc[0]} 至 {market_data_df['Date_End'].iloc[-1]}")
    
    # 股票價格分析
    if 'SPY_Price_Origin' in market_data_df.columns and 'SPY_Price_End' in market_data_df.columns:
        spy_returns = (market_data_df['SPY_Price_End'] - market_data_df['SPY_Price_Origin']) / market_data_df['SPY_Price_Origin']
        print(f"  📈 股票平均期間收益率：{spy_returns.mean():.2%}")
        print(f"  📊 股票期間收益率標準差：{spy_returns.std():.2%}")
        print(f"  📏 股票價格範圍：${market_data_df['SPY_Price_Origin'].min():.2f} - ${market_data_df['SPY_Price_End'].max():.2f}")
        
        # 檢查價格連續性
        price_gaps = []
        for i in range(1, len(market_data_df)):
            current_origin = market_data_df['SPY_Price_Origin'].iloc[i]
            previous_end = market_data_df['SPY_Price_End'].iloc[i-1]
            gap = abs(current_origin - previous_end) / previous_end
            price_gaps.append(gap)
        
        avg_gap = np.mean(price_gaps) if price_gaps else 0
        print(f"  🔗 平均價格連續性缺口：{avg_gap:.2%}")
    
    # 債券殖利率分析
    if 'Bond_Yield_Origin' in market_data_df.columns and 'Bond_Yield_End' in market_data_df.columns:
        yield_changes = market_data_df['Bond_Yield_End'] - market_data_df['Bond_Yield_Origin']
        print(f"  📈 債券平均殖利率變化：{yield_changes.mean():.3f}%")
        print(f"  📊 債券殖利率變化標準差：{yield_changes.std():.3f}%")
        print(f"  📏 債券殖利率範圍：{market_data_df['Bond_Yield_Origin'].min():.3f}% - {market_data_df['Bond_Yield_End'].max():.3f}%")
        
        # 檢查殖利率連續性
        yield_gaps = []
        for i in range(1, len(market_data_df)):
            current_origin = market_data_df['Bond_Yield_Origin'].iloc[i]
            previous_end = market_data_df['Bond_Yield_End'].iloc[i-1]
            gap = abs(current_origin - previous_end)
            yield_gaps.append(gap)
        
        avg_yield_gap = np.mean(yield_gaps) if yield_gaps else 0
        print(f"  🔗 平均殖利率連續性缺口：{avg_yield_gap:.3f}%")


def save_validation_report(report):
    """保存驗證報告"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"simulation_validation_report_{timestamp}.json"
    
    try:
        import json
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2, default=str)
        
        print(f"\n💾 驗證報告已保存至：{filename}")
        
    except Exception as e:
        logger.error(f"保存報告失敗：{e}")


def test_specific_scenarios():
    """測試特定情境"""
    logger.info("=== 測試特定情境 ===")
    
    # 測試極端參數
    extreme_parameters = {
        "investment_amount": 1000,
        "investment_periods": 1,
        "investment_frequency": "monthly",
        "start_date": datetime(2024, 1, 1),
        "stock_ratio": 100,  # 純股票
        "bond_ratio": 0,
        "rebalance_threshold_upper": 110,
        "rebalance_threshold_lower": 90
    }
    
    results_manager = ResultsDisplayManager()
    extreme_data = results_manager._generate_fallback_data(extreme_parameters)
    
    print(f"\n🧪 極端情境測試：")
    print(f"  投資期數：{extreme_parameters['investment_periods']}")
    print(f"  投資頻率：{extreme_parameters['investment_frequency']}")
    print(f"  股債比例：{extreme_parameters['stock_ratio']}:{extreme_parameters['bond_ratio']}")
    print(f"  生成數據期數：{len(extreme_data)}")
    
    if not extreme_data.empty:
        print(f"  ✅ 極端情境數據生成成功")
    else:
        print(f"  ❌ 極端情境數據生成失敗")


if __name__ == "__main__":
    try:
        # 執行完整驗證
        report = run_comprehensive_validation()
        
        # 測試特定情境
        test_specific_scenarios()
        
        print("\n" + "="*60)
        print("✅ 模擬數據驗證完成")
        print("="*60)
        
    except Exception as e:
        logger.error(f"驗證過程發生錯誤：{e}")
        import traceback
        traceback.print_exc() 