"""
核心計算公式模組演示腳本

展示所有15個函數的使用方式和實際計算結果，包括：
1. 參數頻率轉換模組 (2個函數)
2. VA策略公式模組 (2個函數)  
3. DCA策略公式模組 (3個函數)
4. 股債混合組合計算模組 (2個函數)
5. 績效指標計算模組 (6個函數)
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from src.models.calculation_formulas import *
import logging

# 設置日誌級別
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def demo_parameter_conversion():
    """演示參數頻率轉換模組"""
    print("\n" + "="*60)
    print("📊 參數頻率轉換模組演示")
    print("="*60)
    
    # 1. validate_conversion_parameters
    print("\n1️⃣ validate_conversion_parameters() - 參數驗證")
    try:
        is_limit_case = validate_conversion_parameters(8.0, 3.0)
        print(f"   年化成長率8%, 通膨率3% → 需要極限公式: {is_limit_case}")
        
        is_limit_case_equal = validate_conversion_parameters(5.0, 5.0)
        print(f"   年化成長率5%, 通膨率5% → 需要極限公式: {is_limit_case_equal}")
        
        print("   ✅ 參數驗證正常")
    except ValueError as e:
        print(f"   ❌ 參數驗證失敗: {e}")
    
    # 2. convert_annual_to_period_parameters
    print("\n2️⃣ convert_annual_to_period_parameters() - 年度參數轉換")
    annual_params = {
        "annual_investment": 12000,    # 年投12萬
        "annual_growth_rate": 8.0,     # 年化8%報酬
        "annual_inflation_rate": 3.0,  # 年化3%通膨
        "investment_years": 10,        # 投資10年
        "frequency": "Monthly"         # 每月投資
    }
    
    period_params = convert_annual_to_period_parameters(**annual_params)
    print(f"   輸入參數: 年投{annual_params['annual_investment']:,}元, 成長率{annual_params['annual_growth_rate']}%, 通膨率{annual_params['annual_inflation_rate']}%")
    print(f"   轉換結果:")
    print(f"   - 每期投入: ${period_params['C_period']:,.2f}")
    print(f"   - 每期成長率: {period_params['r_period']:.4%}")
    print(f"   - 每期通膨率: {period_params['g_period']:.4%}")
    print(f"   - 總期數: {period_params['total_periods']}期")
    print(f"   - 每年期數: {period_params['periods_per_year']}期")
    
    return period_params

def demo_va_strategy(period_params):
    """演示VA策略公式模組"""
    print("\n" + "="*60)
    print("💰 VA策略公式模組演示")
    print("="*60)
    
    C0 = 1000  # 期初投入
    C_period = period_params['C_period']
    r_period = period_params['r_period']
    g_period = period_params['g_period']
    
    # 3. calculate_va_target_value
    print("\n3️⃣ calculate_va_target_value() - VA目標價值計算")
    for period in [1, 6, 12, 24]:
        target_value = calculate_va_target_value(C0, C_period, r_period, g_period, period)
        print(f"   第{period:2d}期目標價值: ${target_value:,.2f}")
    
    # 4. execute_va_strategy
    print("\n4️⃣ execute_va_strategy() - VA策略執行")
    scenarios = [
        {"desc": "需要買入", "target": 15000, "current": 14000, "strategy": "Rebalance"},
        {"desc": "需要賣出(Rebalance)", "target": 14000, "current": 15000, "strategy": "Rebalance"},
        {"desc": "需要賣出(No Sell)", "target": 14000, "current": 15000, "strategy": "No Sell"}
    ]
    
    for scenario in scenarios:
        result = execute_va_strategy(
            target_value=scenario["target"],
            current_value=scenario["current"],
            stock_ratio=0.7, bond_ratio=0.3,
            spy_price=400, bond_price=95,
            strategy_type=scenario["strategy"]
        )
        print(f"   {scenario['desc']}:")
        print(f"     投資缺口: ${result['investment_gap']:,.2f}")
        print(f"     股票交易: {result['stock_trade_units']:+.4f}單位")
        print(f"     債券交易: {result['bond_trade_units']:+.4f}單位")
        print(f"     實際投入: ${result['actual_investment']:,.2f}")

def demo_dca_strategy(period_params):
    """演示DCA策略公式模組"""
    print("\n" + "="*60)
    print("📈 DCA策略公式模組演示")
    print("="*60)
    
    C0 = 1000
    C_period = period_params['C_period']
    g_period = period_params['g_period']
    
    # 5. calculate_dca_investment
    print("\n5️⃣ calculate_dca_investment() - DCA投入金額計算")
    for period in [1, 6, 12, 24]:
        investment = calculate_dca_investment(C_period, g_period, period)
        inflation_factor = ((1 + g_period) ** (period - 1))
        print(f"   第{period:2d}期投入: ${investment:,.2f} (通膨係數: {inflation_factor:.4f})")
    
    # 6. calculate_dca_cumulative_investment
    print("\n6️⃣ calculate_dca_cumulative_investment() - DCA累積投入計算")
    for period in [6, 12, 24, 36]:
        cumulative = calculate_dca_cumulative_investment(C0, C_period, g_period, period)
        print(f"   截至第{period:2d}期累積投入: ${cumulative:,.2f}")
    
    # 7. execute_dca_strategy
    print("\n7️⃣ execute_dca_strategy() - DCA策略執行")
    periods_to_test = [1, 6, 12]
    for period in periods_to_test:
        fixed_investment = calculate_dca_investment(C_period, g_period, period)
        result = execute_dca_strategy(
            fixed_investment=fixed_investment,
            stock_ratio=0.7, bond_ratio=0.3,
            spy_price=400, bond_price=95
        )
        print(f"   第{period}期投資執行:")
        print(f"     總投入: ${fixed_investment:,.2f}")
        print(f"     股票投資: ${result['stock_investment']:,.2f} ({result['stock_trade_units']:.4f}單位)")
        print(f"     債券投資: ${result['bond_investment']:,.2f} ({result['bond_trade_units']:.4f}單位)")

def demo_portfolio_calculation():
    """演示股債混合組合計算模組"""
    print("\n" + "="*60)
    print("⚖️ 股債混合組合計算模組演示")
    print("="*60)
    
    # 8. calculate_portfolio_allocation
    print("\n8️⃣ calculate_portfolio_allocation() - 資產配置計算")
    stock_ratios = [100, 80, 70, 60, 30, 0]
    for stock_pct in stock_ratios:
        stock_ratio, bond_ratio = calculate_portfolio_allocation(stock_pct)
        print(f"   股票{stock_pct:3d}% → 標準化: 股票{stock_ratio:.1%}, 債券{bond_ratio:.1%}")
    
    # 9. calculate_bond_price
    print("\n9️⃣ calculate_bond_price() - 債券價格計算")
    yield_rates = [1.0, 2.5, 5.0, 7.5, 10.0]
    for yield_rate in yield_rates:
        bond_price = calculate_bond_price(yield_rate)
        print(f"   殖利率{yield_rate:4.1f}% → 債券價格: ${bond_price:.2f}")

def demo_performance_metrics():
    """演示績效指標計算模組"""
    print("\n" + "="*60)
    print("📊 績效指標計算模組演示")
    print("="*60)
    
    # 10. calculate_annualized_return
    print("\n🔟 calculate_annualized_return() - 年化報酬率計算")
    scenarios = [
        {"final": 15000, "investment": 12000, "years": 2},
        {"final": 20000, "investment": 15000, "years": 3},
        {"final": 8000, "investment": 10000, "years": 1}
    ]
    for scenario in scenarios:
        annual_return = calculate_annualized_return(
            scenario["final"], scenario["investment"], scenario["years"]
        )
        print(f"   期末${scenario['final']:,} / 投入${scenario['investment']:,} / {scenario['years']}年 → 年化報酬: {annual_return:+.2f}%")
    
    # 11. calculate_irr
    print("\n1️⃣1️⃣ calculate_irr() - 內部報酬率計算")
    cash_flow_scenarios = [
        {"desc": "簡單投資", "flows": [-1000, 1200]},
        {"desc": "定期投資", "flows": [-1000, -500, -500, 2500]},
        {"desc": "複雜投資", "flows": [-2000, -1000, 500, 1000, 2000]}
    ]
    for scenario in cash_flow_scenarios:
        irr = calculate_irr(scenario["flows"])
        flows_str = " → ".join([f"${f:+,}" for f in scenario["flows"]])
        print(f"   {scenario['desc']}: {flows_str}")
        print(f"     IRR: {irr:.2f}%" if irr else "     IRR: 無法收斂")
    
    # 12. build_va_cash_flows
    print("\n1️⃣2️⃣ build_va_cash_flows() - VA現金流構建")
    va_cash_flows = build_va_cash_flows(
        C0=1000,
        investment_history=[500, -200, 300, 100],
        final_value=15000,
        final_investment=100
    )
    flows_str = " → ".join([f"${f:+,}" for f in va_cash_flows])
    print(f"   VA現金流: {flows_str}")
    
    # 13. build_dca_cash_flows  
    print("\n1️⃣3️⃣ build_dca_cash_flows() - DCA現金流構建")
    dca_cash_flows = build_dca_cash_flows(
        C0=1000,
        fixed_investment=500,
        periods=5,
        final_value=15000
    )
    flows_str = " → ".join([f"${f:+,}" for f in dca_cash_flows])
    print(f"   DCA現金流: {flows_str}")
    
    # 14. calculate_volatility_and_sharpe
    print("\n1️⃣4️⃣ calculate_volatility_and_sharpe() - 波動率與夏普比率計算")
    period_returns = [0.02, -0.01, 0.03, 0.00, -0.02, 0.04, 0.01, -0.01, 0.02, 0.00, 0.01, 0.02]
    volatility, sharpe = calculate_volatility_and_sharpe(period_returns, 12)
    avg_return = sum(period_returns) / len(period_returns)
    print(f"   月度報酬率: {period_returns}")
    print(f"   平均月度報酬: {avg_return:.2%}")
    print(f"   年化波動率: {volatility:.2f}%")
    print(f"   夏普比率: {sharpe:.3f}")
    
    # 15. calculate_max_drawdown
    print("\n1️⃣5️⃣ calculate_max_drawdown() - 最大回撤計算")
    asset_values = [10000, 11000, 12500, 11800, 10200, 9500, 11000, 13000, 12800, 14500]
    max_dd, (peak_idx, trough_idx) = calculate_max_drawdown(asset_values)
    print(f"   資產價值序列: {asset_values}")
    print(f"   最大回撤: {max_dd:.2f}%")
    print(f"   回撤期間: 第{peak_idx}期(峰值${asset_values[peak_idx]:,}) → 第{trough_idx}期(谷值${asset_values[trough_idx]:,})")

def demo_comprehensive_calculation():
    """演示完整的投資策略計算流程"""
    print("\n" + "="*60)
    print("🎯 完整投資策略計算流程演示")
    print("="*60)
    
    # 設定投資參數
    investment_params = {
        "annual_investment": 60000,
        "annual_growth_rate": 10.0,
        "annual_inflation_rate": 2.5,
        "investment_years": 5,
        "frequency": "Quarterly"
    }
    
    print(f"\n投資設定:")
    print(f"- 年度投入: ${investment_params['annual_investment']:,}")
    print(f"- 預期年化報酬: {investment_params['annual_growth_rate']}%")
    print(f"- 預期年化通膨: {investment_params['annual_inflation_rate']}%")
    print(f"- 投資年數: {investment_params['investment_years']}年")
    print(f"- 投資頻率: {investment_params['frequency']}")
    print(f"- 股債配置: 80% / 20%")
    
    # 轉換參數
    params = convert_annual_to_period_parameters(**investment_params)
    stock_ratio, bond_ratio = calculate_portfolio_allocation(80)
    
    print(f"\n期間參數:")
    print(f"- 每期投入: ${params['C_period']:,}")
    print(f"- 每期成長率: {params['r_period']:.4%}")
    print(f"- 每期通膨率: {params['g_period']:.4%}")
    print(f"- 總期數: {params['total_periods']}期")
    
    # 模擬投資過程
    C0 = 5000  # 期初投入
    periods_to_simulate = min(8, params['total_periods'])
    
    print(f"\n模擬前{periods_to_simulate}期投資:")
    print("-" * 100)
    print(f"{'期數':>4} {'VA目標':>12} {'DCA投入':>12} {'累積投入':>12} {'股票價格':>10} {'債券殖利率':>10}")
    print("-" * 100)
    
    # 模擬市場價格
    initial_spy = 400
    initial_yield = 4.0
    
    for period in range(1, periods_to_simulate + 1):
        # 計算VA目標價值
        va_target = calculate_va_target_value(C0, params['C_period'], params['r_period'], params['g_period'], period)
        
        # 計算DCA投入
        dca_investment = calculate_dca_investment(params['C_period'], params['g_period'], period)
        dca_cumulative = calculate_dca_cumulative_investment(C0, params['C_period'], params['g_period'], period)
        
        # 模擬市場價格變動
        spy_price = initial_spy * (1 + params['r_period']) ** period
        bond_yield = initial_yield + (period - 1) * 0.1
        
        print(f"{period:4d} ${va_target:11,.0f} ${dca_investment:11,.0f} ${dca_cumulative:11,.0f} ${spy_price:9.2f} {bond_yield:9.1f}%")
    
    print("-" * 100)
    
    # 計算最終績效指標
    final_period = periods_to_simulate
    final_va_target = calculate_va_target_value(C0, params['C_period'], params['r_period'], params['g_period'], final_period)
    final_dca_cumulative = calculate_dca_cumulative_investment(C0, params['C_period'], params['g_period'], final_period)
    
    print(f"\n第{final_period}期預期結果:")
    print(f"- VA策略目標價值: ${final_va_target:,.0f}")
    print(f"- DCA策略累積投入: ${final_dca_cumulative:,.0f}")
    
    # 計算績效指標
    investment_years = final_period / params['periods_per_year']
    va_annual_return = calculate_annualized_return(final_va_target, final_dca_cumulative, investment_years)
    print(f"- 預期年化報酬率: {va_annual_return:.2f}%")

def main():
    """主演示函數"""
    print("🚀 核心計算公式模組完整演示")
    print("實作了需求文件第2章第2.1節中定義的15個核心函數")
    
    try:
        # 執行各模組演示
        period_params = demo_parameter_conversion()
        demo_va_strategy(period_params)
        demo_dca_strategy(period_params)
        demo_portfolio_calculation()
        demo_performance_metrics()
        demo_comprehensive_calculation()
        
        print("\n" + "="*60)
        print("✅ 核心計算公式模組演示完成！")
        print("📋 已實作的15個函數清單:")
        print("   1. validate_conversion_parameters() - 參數驗證")
        print("   2. convert_annual_to_period_parameters() - 年度參數轉換")
        print("   3. calculate_va_target_value() - VA目標價值計算")
        print("   4. execute_va_strategy() - VA策略執行")
        print("   5. calculate_dca_investment() - DCA投入金額計算")
        print("   6. calculate_dca_cumulative_investment() - DCA累積投入計算")
        print("   7. execute_dca_strategy() - DCA策略執行")
        print("   8. calculate_portfolio_allocation() - 資產配置計算")
        print("   9. calculate_bond_price() - 債券價格計算")
        print("  10. calculate_annualized_return() - 年化報酬率計算")
        print("  11. calculate_irr() - 內部報酬率計算")
        print("  12. build_va_cash_flows() - VA現金流構建")
        print("  13. build_dca_cash_flows() - DCA現金流構建")
        print("  14. calculate_volatility_and_sharpe() - 波動率與夏普比率計算")
        print("  15. calculate_max_drawdown() - 最大回撤計算")
        print("\n🎯 所有函數均嚴格遵循數學公式，包含完整的邊界條件處理！")
        
    except Exception as e:
        print(f"\n❌ 演示過程中發生錯誤: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 