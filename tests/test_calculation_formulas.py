"""
核心計算公式模組詳細測試腳本

測試所有15個函數的功能完整性、數學正確性、邊界條件處理
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import unittest
import numpy as np
from src.models.calculation_formulas import *

class TestCalculationFormulas(unittest.TestCase):
    """核心計算公式模組測試類"""
    
    def setUp(self):
        """測試前準備"""
        self.sample_params = {
            "annual_investment": 12000,
            "annual_growth_rate": 8.0,
            "annual_inflation_rate": 3.0,
            "investment_years": 10,
            "frequency": "Monthly"
        }
        
        # 轉換後的期間參數
        self.period_params = convert_annual_to_period_parameters(**self.sample_params)
        
    # ========================================================================
    # 2.1.1 參數頻率轉換模組測試
    # ========================================================================
    
    def test_validate_conversion_parameters(self):
        """測試參數驗證函數"""
        # 正常參數
        self.assertFalse(validate_conversion_parameters(8.0, 3.0))
        
        # 極限情況：成長率等於通膨率
        self.assertTrue(validate_conversion_parameters(5.0, 5.0))
        
        # 邊界條件測試
        with self.assertRaises(ValueError):
            validate_conversion_parameters(-25.0, 3.0)  # 成長率過低
        
        with self.assertRaises(ValueError):
            validate_conversion_parameters(8.0, 20.0)  # 通膨率過高
    
    def test_convert_annual_to_period_parameters(self):
        """測試年度參數轉換函數"""
        result = convert_annual_to_period_parameters(**self.sample_params)
        
        # 檢查返回值結構
        expected_keys = {"C_period", "r_period", "g_period", "total_periods", "periods_per_year"}
        self.assertEqual(set(result.keys()), expected_keys)
        
        # 檢查計算結果
        self.assertEqual(result["C_period"], 1000.0)  # 12000/12
        self.assertEqual(result["total_periods"], 120)  # 10*12
        self.assertEqual(result["periods_per_year"], 12)
        
        # 檢查複利轉換
        expected_r = (1.08 ** (1/12)) - 1
        expected_g = (1.03 ** (1/12)) - 1
        self.assertAlmostEqual(result["r_period"], expected_r, places=6)
        self.assertAlmostEqual(result["g_period"], expected_g, places=6)
        
        # 測試不同頻率
        quarterly_result = convert_annual_to_period_parameters(
            12000, 8.0, 3.0, 10, "Quarterly"
        )
        self.assertEqual(quarterly_result["C_period"], 3000.0)  # 12000/4
        self.assertEqual(quarterly_result["total_periods"], 40)  # 10*4
        
        # 邊界條件測試
        with self.assertRaises(ValueError):
            convert_annual_to_period_parameters(-1000, 8.0, 3.0, 10, "Monthly")  # 負投資額
        
        with self.assertRaises(ValueError):
            convert_annual_to_period_parameters(12000, 8.0, 3.0, 0, "Monthly")  # 零投資年數
    
    # ========================================================================
    # 2.1.2 VA策略公式模組測試
    # ========================================================================
    
    def test_calculate_va_target_value(self):
        """測試VA目標價值計算函數"""
        C0 = 1000
        C_period = self.period_params["C_period"]
        r_period = self.period_params["r_period"]
        g_period = self.period_params["g_period"]
        
        # 測試一般情況
        target_value = calculate_va_target_value(C0, C_period, r_period, g_period, 12)
        self.assertGreater(target_value, C0)  # 目標價值應大於期初投入
        
        # 測試極限情況（r_period = g_period）
        target_value_limit = calculate_va_target_value(C0, C_period, 0.005, 0.005, 12)
        expected_limit = C0 * (1.005**12) + C_period * 12 * (1.005**11)
        self.assertAlmostEqual(target_value_limit, expected_limit, places=2)
        
        # 邊界條件測試
        with self.assertRaises(ValueError):
            calculate_va_target_value(-100, C_period, r_period, g_period, 12)  # 負C0
        
        with self.assertRaises(ValueError):
            calculate_va_target_value(C0, C_period, r_period, g_period, 0)  # 零期數
    
    def test_execute_va_strategy(self):
        """測試VA策略執行函數"""
        # 買入情況
        buy_result = execute_va_strategy(
            target_value=15000, current_value=14000, 
            stock_ratio=0.7, bond_ratio=0.3,
            spy_price=400, bond_price=95,
            strategy_type="Rebalance"
        )
        
        self.assertEqual(buy_result["investment_gap"], 1000)
        self.assertGreater(buy_result["stock_trade_units"], 0)
        self.assertGreater(buy_result["bond_trade_units"], 0)
        self.assertEqual(buy_result["actual_investment"], 1000)
        
        # 賣出情況 (Rebalance)
        sell_result = execute_va_strategy(
            target_value=14000, current_value=15000,
            stock_ratio=0.7, bond_ratio=0.3,
            spy_price=400, bond_price=95,
            strategy_type="Rebalance"
        )
        
        self.assertEqual(sell_result["investment_gap"], -1000)
        self.assertLess(sell_result["stock_trade_units"], 0)
        self.assertLess(sell_result["bond_trade_units"], 0)
        self.assertEqual(sell_result["actual_investment"], -1000)
        
        # No Sell策略測試
        no_sell_result = execute_va_strategy(
            target_value=14000, current_value=15000,
            stock_ratio=0.7, bond_ratio=0.3,
            spy_price=400, bond_price=95,
            strategy_type="No Sell"
        )
        
        self.assertEqual(no_sell_result["stock_trade_units"], 0)
        self.assertEqual(no_sell_result["bond_trade_units"], 0)
        self.assertEqual(no_sell_result["actual_investment"], 0)
        
        # 邊界條件測試
        with self.assertRaises(ValueError):
            execute_va_strategy(-1000, 14000, 0.7, 0.3, 400, 95, "Rebalance")  # 負目標價值
        
        with self.assertRaises(ValueError):
            execute_va_strategy(15000, 14000, 1.5, 0.3, 400, 95, "Rebalance")  # 超過1的比例
    
    # ========================================================================
    # 2.1.3 DCA策略公式模組測試
    # ========================================================================
    
    def test_calculate_dca_investment(self):
        """測試DCA投入金額計算函數"""
        C_period = self.period_params["C_period"]
        g_period = self.period_params["g_period"]
        
        # 第1期投入（無通膨調整）
        period1_investment = calculate_dca_investment(C_period, g_period, 1)
        self.assertAlmostEqual(period1_investment, C_period, places=2)
        
        # 第12期投入（含通膨調整）
        period12_investment = calculate_dca_investment(C_period, g_period, 12)
        expected = C_period * ((1 + g_period) ** 11)
        self.assertAlmostEqual(period12_investment, expected, places=2)
        
        # 邊界條件測試
        with self.assertRaises(ValueError):
            calculate_dca_investment(-1000, g_period, 1)  # 負投入金額
        
        with self.assertRaises(ValueError):
            calculate_dca_investment(C_period, g_period, 0)  # 零期數
    
    def test_calculate_dca_cumulative_investment(self):
        """測試DCA累積投入計算函數"""
        C0 = 1000
        C_period = self.period_params["C_period"]
        g_period = self.period_params["g_period"]
        
        # 測試一般情況
        cumulative = calculate_dca_cumulative_investment(C0, C_period, g_period, 12)
        self.assertGreater(cumulative, C0 + C_period * 12)  # 應大於無通膨調整的總額
        
        # 測試零通膨情況
        cumulative_zero_inflation = calculate_dca_cumulative_investment(C0, C_period, 0, 12)
        expected_zero = C0 + C_period * 12
        self.assertAlmostEqual(cumulative_zero_inflation, expected_zero, places=2)
        
        # 邊界條件測試
        with self.assertRaises(ValueError):
            calculate_dca_cumulative_investment(-100, C_period, g_period, 12)  # 負C0
    
    def test_execute_dca_strategy(self):
        """測試DCA策略執行函數"""
        result = execute_dca_strategy(
            fixed_investment=1000,
            stock_ratio=0.7, bond_ratio=0.3,
            spy_price=400, bond_price=95
        )
        
        # 檢查返回值結構
        expected_keys = {"stock_trade_units", "bond_trade_units", "stock_investment", "bond_investment"}
        self.assertEqual(set(result.keys()), expected_keys)
        
        # 檢查投資分配
        self.assertEqual(result["stock_investment"], 700)  # 1000 * 0.7
        self.assertEqual(result["bond_investment"], 300)   # 1000 * 0.3
        
        # 檢查單位數計算
        self.assertAlmostEqual(result["stock_trade_units"], 700/400, places=4)
        self.assertAlmostEqual(result["bond_trade_units"], 300/95, places=4)
        
        # 邊界條件測試
        with self.assertRaises(ValueError):
            execute_dca_strategy(-1000, 0.7, 0.3, 400, 95)  # 負投入金額
    
    # ========================================================================
    # 2.1.4 股債混合組合計算模組測試
    # ========================================================================
    
    def test_calculate_portfolio_allocation(self):
        """測試資產配置計算函數"""
        stock_ratio, bond_ratio = calculate_portfolio_allocation(70)
        
        self.assertEqual(stock_ratio, 0.7)
        self.assertEqual(bond_ratio, 0.3)
        self.assertAlmostEqual(stock_ratio + bond_ratio, 1.0, places=6)
        
        # 測試邊界值
        stock_100, bond_0 = calculate_portfolio_allocation(100)
        self.assertEqual(stock_100, 1.0)
        self.assertEqual(bond_0, 0.0)
        
        stock_0, bond_100 = calculate_portfolio_allocation(0)
        self.assertEqual(stock_0, 0.0)
        self.assertEqual(bond_100, 1.0)
        
        # 邊界條件測試
        with self.assertRaises(ValueError):
            calculate_portfolio_allocation(-10)  # 負比例
        
        with self.assertRaises(ValueError):
            calculate_portfolio_allocation(150)  # 超過100%
    
    def test_calculate_bond_price(self):
        """測試債券價格計算函數"""
        # 5%殖利率，面值100，1年期
        price = calculate_bond_price(5.0)
        expected = 100 / (1.05)
        self.assertAlmostEqual(price, expected, places=2)
        
        # 測試不同參數
        price_2year = calculate_bond_price(5.0, 100, 2)
        expected_2year = 100 / (1.05 ** 2)
        self.assertAlmostEqual(price_2year, expected_2year, places=2)
        
        # 邊界條件測試
        with self.assertRaises(ValueError):
            calculate_bond_price(-1.0)  # 負殖利率
        
        with self.assertRaises(ValueError):
            calculate_bond_price(5.0, 0)  # 零面值
    
    # ========================================================================
    # 2.1.5 績效指標計算模組測試
    # ========================================================================
    
    def test_calculate_annualized_return(self):
        """測試年化報酬率計算函數"""
        # 2年期間，15000期末價值，12000總投入
        annual_return = calculate_annualized_return(15000, 12000, 2)
        expected = ((15000 / 12000) ** (1/2) - 1) * 100
        self.assertAlmostEqual(annual_return, expected, places=2)
        
        # 測試零報酬情況
        zero_return = calculate_annualized_return(12000, 12000, 2)
        self.assertAlmostEqual(zero_return, 0, places=2)
        
        # 邊界條件測試
        with self.assertRaises(ValueError):
            calculate_annualized_return(-1000, 12000, 2)  # 負期末價值
        
        with self.assertRaises(ValueError):
            calculate_annualized_return(15000, 0, 2)  # 零投入
    
    def test_calculate_irr(self):
        """測試IRR計算函數"""
        # 簡單現金流：-1000期初，+1200期末
        cash_flows = [-1000, 1200]
        irr = calculate_irr(cash_flows)
        expected = 20.0  # 20%報酬率
        self.assertAlmostEqual(irr, expected, places=1)
        
        # 複雜現金流
        complex_flows = [-1000, -500, -500, 2500]
        irr_complex = calculate_irr(complex_flows)
        self.assertIsNotNone(irr_complex)
        
        # 邊界條件測試
        with self.assertRaises(ValueError):
            calculate_irr([])  # 空現金流
        
        with self.assertRaises(ValueError):
            calculate_irr([-1000])  # 只有一個現金流
    
    def test_build_va_cash_flows(self):
        """測試VA現金流構建函數"""
        C0 = 1000
        investment_history = [500, -200, 300, 100]
        final_value = 15000
        final_investment = 100
        
        cash_flows = build_va_cash_flows(C0, investment_history, final_value, final_investment)
        
        # 檢查結構
        self.assertEqual(len(cash_flows), 5)  # C0 + 3個中間期 + 1個最終期
        self.assertEqual(cash_flows[0], -1000)  # 期初投入為負
        self.assertEqual(cash_flows[-1], 15000 - 100)  # 最終回收
        
        # 邊界條件測試
        with self.assertRaises(ValueError):
            build_va_cash_flows(-100, investment_history, final_value, final_investment)  # 負C0
    
    def test_build_dca_cash_flows(self):
        """測試DCA現金流構建函數"""
        C0 = 1000
        fixed_investment = 500
        periods = 5
        final_value = 15000
        
        cash_flows = build_dca_cash_flows(C0, fixed_investment, periods, final_value)
        
        # 檢查結構
        self.assertEqual(len(cash_flows), 5)
        self.assertEqual(cash_flows[0], -1000)  # 期初投入
        self.assertEqual(cash_flows[-1], 15000 - 500)  # 最終回收
        
        # 中間期應該都是-500
        for i in range(1, periods-1):
            self.assertEqual(cash_flows[i], -500)
    
    def test_calculate_volatility_and_sharpe(self):
        """測試波動率和夏普比率計算函數"""
        # 模擬月度報酬率 (小數形式)
        period_returns = [0.01, -0.02, 0.03, 0.005, -0.01, 0.02]
        periods_per_year = 12
        
        volatility, sharpe = calculate_volatility_and_sharpe(period_returns, periods_per_year)
        
        self.assertGreater(volatility, 0)  # 波動率應為正
        self.assertIsInstance(sharpe, float)  # 夏普比率應為數值
        
        # 測試空列表
        vol_empty, sharpe_empty = calculate_volatility_and_sharpe([], 12)
        self.assertEqual(vol_empty, 0.0)
        self.assertEqual(sharpe_empty, 0.0)
    
    def test_calculate_max_drawdown(self):
        """測試最大回撤計算函數"""
        # 模擬資產價值序列（包含回撤）
        cumulative_values = [1000, 1100, 1200, 1000, 900, 1300, 1400]
        
        max_dd, (peak_idx, trough_idx) = calculate_max_drawdown(cumulative_values)
        
        self.assertGreater(max_dd, 0)  # 最大回撤應為正值
        self.assertIsInstance(peak_idx, int)
        self.assertIsInstance(trough_idx, int)
        self.assertLessEqual(peak_idx, trough_idx)  # 峰值應在谷值之前
        
        # 測試單調遞增序列（無回撤）
        increasing_values = [1000, 1100, 1200, 1300]
        max_dd_zero, _ = calculate_max_drawdown(increasing_values)
        self.assertAlmostEqual(max_dd_zero, 0.0, places=2)
        
        # 邊界條件測試
        with self.assertRaises(ValueError):
            calculate_max_drawdown([1000, -100])  # 包含負值
    
    # ========================================================================
    # 輔助函數測試
    # ========================================================================
    
    def test_validate_strategy_parameters(self):
        """測試策略參數驗證函數"""
        # 正常參數
        validate_strategy_parameters(1000, 500, 0.7, 0.3)  # 應該不拋出異常
        
        # 邊界條件測試
        with self.assertRaises(ValueError):
            validate_strategy_parameters(-100, 500, 0.7, 0.3)  # 負C0
        
        with self.assertRaises(ValueError):
            validate_strategy_parameters(1000, 500, 1.5, 0.3)  # 超過1的比例
        
        with self.assertRaises(ValueError):
            validate_strategy_parameters(1000, 500, 0.6, 0.3)  # 比例總和不為1
    
    def test_format_calculation_result(self):
        """測試結果格式化函數"""
        # 測試浮點數格式化
        formatted_float = format_calculation_result(3.14159, 2)
        self.assertEqual(formatted_float, 3.14)
        
        # 測試字典格式化
        input_dict = {"a": 3.14159, "b": "text", "c": 2.71828}
        formatted_dict = format_calculation_result(input_dict, 2)
        self.assertEqual(formatted_dict["a"], 3.14)
        self.assertEqual(formatted_dict["b"], "text")
        self.assertEqual(formatted_dict["c"], 2.72)
        
        # 測試列表格式化
        input_list = [3.14159, 2.71828, "text"]
        formatted_list = format_calculation_result(input_list, 2)
        self.assertEqual(formatted_list[0], 3.14)
        self.assertEqual(formatted_list[1], 2.72)
        self.assertEqual(formatted_list[2], "text")

def run_comprehensive_tests():
    """執行全面的測試套件"""
    print("🧪 開始執行核心計算公式模組全面測試...")
    print("=" * 60)
    
    # 創建測試套件
    test_loader = unittest.TestLoader()
    test_suite = test_loader.loadTestsFromTestCase(TestCalculationFormulas)
    
    # 執行測試
    test_runner = unittest.TextTestRunner(verbosity=2)
    test_result = test_runner.run(test_suite)
    
    print("=" * 60)
    if test_result.wasSuccessful():
        print("✅ 所有測試通過！")
        print(f"📊 執行了 {test_result.testsRun} 個測試")
    else:
        print("❌ 測試失敗!")
        print(f"失敗: {len(test_result.failures)}")
        print(f"錯誤: {len(test_result.errors)}")
    
    return test_result.wasSuccessful()

if __name__ == "__main__":
    success = run_comprehensive_tests()
    exit(0 if success else 1) 