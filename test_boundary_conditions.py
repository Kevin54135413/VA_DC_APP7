"""
邊界條件測試腳本

測試模擬數據生成和策略計算在極端參數情況下的穩定性和合理性
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Any
from src.ui.results_display import ResultsDisplayManager
from src.utils.logger import get_component_logger

logger = get_component_logger("BoundaryConditionTest")


class BoundaryConditionTester:
    """邊界條件測試器"""
    
    def __init__(self):
        self.results_manager = ResultsDisplayManager()
        self.test_results = []
        
    def run_all_boundary_tests(self) -> Dict[str, Any]:
        """執行所有邊界條件測試"""
        logger.info("=== 開始邊界條件測試 ===")
        
        test_cases = [
            self.test_minimum_values(),
            self.test_maximum_values(),
            self.test_extreme_ratios(),
            self.test_short_periods(),
            self.test_long_periods(),
            self.test_high_frequency(),
            self.test_edge_dates(),
            self.test_zero_amounts()
        ]
        
        passed_tests = sum(1 for result in test_cases if result['passed'])
        total_tests = len(test_cases)
        
        summary = {
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'pass_rate': passed_tests / total_tests,
            'test_details': test_cases,
            'overall_status': 'PASS' if passed_tests == total_tests else 'PARTIAL_PASS'
        }
        
        logger.info(f"邊界條件測試完成：{passed_tests}/{total_tests} 通過")
        return summary
    
    def test_minimum_values(self) -> Dict[str, Any]:
        """測試最小值邊界條件"""
        logger.info("測試最小值邊界條件...")
        
        try:
            parameters = {
                "investment_amount": 1,  # 最小投資金額
                "investment_periods": 1,  # 最小投資期數
                "investment_frequency": "annually",
                "start_date": datetime(2024, 1, 1),
                "stock_ratio": 1,  # 最小股票比例（非零）
                "bond_ratio": 99,  # 相應債券比例
                "rebalance_threshold_upper": 51,  # 最小閾值差異
                "rebalance_threshold_lower": 49
            }
            
            market_data = self.results_manager._generate_fallback_data(parameters)
            
            # 驗證結果
            if len(market_data) == 1 and not market_data.empty:
                return {'test_name': 'minimum_values', 'passed': True, 'message': '最小值測試通過'}
            else:
                return {'test_name': 'minimum_values', 'passed': False, 'message': f'數據生成異常：期數{len(market_data)}'}
                
        except Exception as e:
            return {'test_name': 'minimum_values', 'passed': False, 'message': f'最小值測試失敗：{e}'}
    
    def test_maximum_values(self) -> Dict[str, Any]:
        """測試最大值邊界條件"""
        logger.info("測試最大值邊界條件...")
        
        try:
            parameters = {
                "investment_amount": 1000000,  # 大投資金額
                "investment_periods": 50,  # 大投資期數
                "investment_frequency": "annually",
                "start_date": datetime(2000, 1, 1),
                "stock_ratio": 95,  # 高股票比例
                "bond_ratio": 5,   # 低債券比例
                "rebalance_threshold_upper": 95,  # 大閾值範圍
                "rebalance_threshold_lower": 5
            }
            
            market_data = self.results_manager._generate_fallback_data(parameters)
            
            # 驗證結果
            if len(market_data) == 50 and not market_data.empty:
                # 檢查數據範圍合理性
                max_price = market_data['SPY_Price_End'].max()
                min_price = market_data['SPY_Price_Origin'].min()
                
                if 100 <= min_price <= 10000 and 100 <= max_price <= 50000:  # 合理的價格範圍
                    return {'test_name': 'maximum_values', 'passed': True, 'message': '最大值測試通過'}
                else:
                    return {'test_name': 'maximum_values', 'passed': False, 'message': f'價格範圍異常：{min_price}-{max_price}'}
            else:
                return {'test_name': 'maximum_values', 'passed': False, 'message': f'數據生成異常：期數{len(market_data)}'}
                
        except Exception as e:
            return {'test_name': 'maximum_values', 'passed': False, 'message': f'最大值測試失敗：{e}'}
    
    def test_extreme_ratios(self) -> Dict[str, Any]:
        """測試極端配置比例"""
        logger.info("測試極端配置比例...")
        
        test_results = []
        
        extreme_ratios = [
            {"stock_ratio": 100, "bond_ratio": 0},  # 純股票
            {"stock_ratio": 0, "bond_ratio": 100},  # 純債券
            {"stock_ratio": 99, "bond_ratio": 1},   # 接近純股票
            {"stock_ratio": 1, "bond_ratio": 99}    # 接近純債券
        ]
        
        for i, ratio in enumerate(extreme_ratios):
            try:
                parameters = {
                    "investment_amount": 10000,
                    "investment_periods": 5,
                    "investment_frequency": "annually",
                    "start_date": datetime(2020, 1, 1),
                    **ratio,
                    "rebalance_threshold_upper": 75,
                    "rebalance_threshold_lower": 25
                }
                
                market_data = self.results_manager._generate_fallback_data(parameters)
                
                if len(market_data) == 5 and not market_data.empty:
                    test_results.append(True)
                else:
                    test_results.append(False)
                    
            except Exception as e:
                logger.warning(f"極端比例測試{i}失敗：{e}")
                test_results.append(False)
        
        passed = sum(test_results)
        total = len(test_results)
        
        if passed == total:
            return {'test_name': 'extreme_ratios', 'passed': True, 'message': f'極端比例測試通過：{passed}/{total}'}
        else:
            return {'test_name': 'extreme_ratios', 'passed': False, 'message': f'極端比例測試部分失敗：{passed}/{total}'}
    
    def test_short_periods(self) -> Dict[str, Any]:
        """測試短期投資期間"""
        logger.info("測試短期投資期間...")
        
        try:
            parameters = {
                "investment_amount": 5000,
                "investment_periods": 1,  # 僅1期
                "investment_frequency": "monthly",
                "start_date": datetime(2024, 6, 1),
                "stock_ratio": 60,
                "bond_ratio": 40,
                "rebalance_threshold_upper": 70,
                "rebalance_threshold_lower": 50
            }
            
            market_data = self.results_manager._generate_fallback_data(parameters)
            
            # 對於月度頻率，1年投資期間應該生成12期數據
            expected_periods = 1 * 12  # 1年 * 12個月
            
            if len(market_data) == expected_periods and not market_data.empty:
                return {'test_name': 'short_periods', 'passed': True, 'message': f'短期測試通過：生成{len(market_data)}期'}
            else:
                return {'test_name': 'short_periods', 'passed': False, 'message': f'期數不符：預期{expected_periods}，實際{len(market_data)}'}
                
        except Exception as e:
            return {'test_name': 'short_periods', 'passed': False, 'message': f'短期測試失敗：{e}'}
    
    def test_long_periods(self) -> Dict[str, Any]:
        """測試長期投資期間"""
        logger.info("測試長期投資期間...")
        
        try:
            parameters = {
                "investment_amount": 10000,
                "investment_periods": 40,  # 40年長期投資
                "investment_frequency": "annually",
                "start_date": datetime(1980, 1, 1),
                "stock_ratio": 70,
                "bond_ratio": 30,
                "rebalance_threshold_upper": 80,
                "rebalance_threshold_lower": 60
            }
            
            market_data = self.results_manager._generate_fallback_data(parameters)
            
            if len(market_data) == 40 and not market_data.empty:
                # 檢查長期數據的合理性
                final_price = market_data['SPY_Price_End'].iloc[-1]
                initial_price = market_data['SPY_Price_Origin'].iloc[0]
                
                # 40年1.5%年成長應該有約1.8倍成長
                growth_ratio = final_price / initial_price
                if 1.5 <= growth_ratio <= 5.0:  # 合理的長期成長範圍
                    return {'test_name': 'long_periods', 'passed': True, 'message': f'長期測試通過：成長{growth_ratio:.2f}倍'}
                else:
                    return {'test_name': 'long_periods', 'passed': False, 'message': f'長期成長異常：{growth_ratio:.2f}倍'}
            else:
                return {'test_name': 'long_periods', 'passed': False, 'message': f'數據生成異常：期數{len(market_data)}'}
                
        except Exception as e:
            return {'test_name': 'long_periods', 'passed': False, 'message': f'長期測試失敗：{e}'}
    
    def test_high_frequency(self) -> Dict[str, Any]:
        """測試高頻率投資"""
        logger.info("測試高頻率投資...")
        
        try:
            parameters = {
                "investment_amount": 10000,
                "investment_periods": 2,  # 2年
                "investment_frequency": "monthly",  # 月度投資
                "start_date": datetime(2022, 1, 1),
                "stock_ratio": 50,
                "bond_ratio": 50,
                "rebalance_threshold_upper": 60,
                "rebalance_threshold_lower": 40
            }
            
            market_data = self.results_manager._generate_fallback_data(parameters)
            
            # 2年月度投資應該有24期
            expected_periods = 2 * 12
            
            if len(market_data) == expected_periods and not market_data.empty:
                # 檢查日期連續性
                dates = pd.to_datetime(market_data['Date_Origin'])
                date_diffs = dates.diff().dropna()
                
                # 月度投資的日期差應該大致為30天
                avg_diff = date_diffs.dt.days.mean()
                if 25 <= avg_diff <= 35:  # 允許一定範圍
                    return {'test_name': 'high_frequency', 'passed': True, 'message': f'高頻測試通過：平均間隔{avg_diff:.1f}天'}
                else:
                    return {'test_name': 'high_frequency', 'passed': False, 'message': f'日期間隔異常：{avg_diff:.1f}天'}
            else:
                return {'test_name': 'high_frequency', 'passed': False, 'message': f'期數不符：預期{expected_periods}，實際{len(market_data)}'}
                
        except Exception as e:
            return {'test_name': 'high_frequency', 'passed': False, 'message': f'高頻測試失敗：{e}'}
    
    def test_edge_dates(self) -> Dict[str, Any]:
        """測試邊緣日期情況"""
        logger.info("測試邊緣日期情況...")
        
        try:
            # 測試年底開始日期
            parameters = {
                "investment_amount": 10000,
                "investment_periods": 3,
                "investment_frequency": "quarterly",
                "start_date": datetime(2023, 12, 31),  # 年底開始
                "stock_ratio": 60,
                "bond_ratio": 40,
                "rebalance_threshold_upper": 70,
                "rebalance_threshold_lower": 50
            }
            
            market_data = self.results_manager._generate_fallback_data(parameters)
            
            # 3年季度投資應該有12期
            expected_periods = 3 * 4
            
            if len(market_data) == expected_periods and not market_data.empty:
                # 檢查第一個日期
                first_date = market_data['Date_Origin'].iloc[0]
                if '2023-12-31' in first_date or '2024-01-01' in first_date:
                    return {'test_name': 'edge_dates', 'passed': True, 'message': f'邊緣日期測試通過：首期{first_date}'}
                else:
                    return {'test_name': 'edge_dates', 'passed': False, 'message': f'首期日期異常：{first_date}'}
            else:
                return {'test_name': 'edge_dates', 'passed': False, 'message': f'期數不符：預期{expected_periods}，實際{len(market_data)}'}
                
        except Exception as e:
            return {'test_name': 'edge_dates', 'passed': False, 'message': f'邊緣日期測試失敗：{e}'}
    
    def test_zero_amounts(self) -> Dict[str, Any]:
        """測試零值邊界情況"""
        logger.info("測試零值邊界情況...")
        
        try:
            # 測試接近零但非零的投資金額
            parameters = {
                "investment_amount": 0.01,  # 極小投資金額
                "investment_periods": 2,
                "investment_frequency": "annually",
                "start_date": datetime(2024, 1, 1),
                "stock_ratio": 50,
                "bond_ratio": 50,
                "rebalance_threshold_upper": 55,
                "rebalance_threshold_lower": 45
            }
            
            market_data = self.results_manager._generate_fallback_data(parameters)
            
            if len(market_data) == 2 and not market_data.empty:
                # 檢查數據的有效性
                if all(market_data['SPY_Price_Origin'] > 0) and all(market_data['Bond_Yield_Origin'] > 0):
                    return {'test_name': 'zero_amounts', 'passed': True, 'message': '零值邊界測試通過'}
                else:
                    return {'test_name': 'zero_amounts', 'passed': False, 'message': '數據包含無效值'}
            else:
                return {'test_name': 'zero_amounts', 'passed': False, 'message': f'數據生成異常：期數{len(market_data)}'}
                
        except Exception as e:
            return {'test_name': 'zero_amounts', 'passed': False, 'message': f'零值邊界測試失敗：{e}'}


def main():
    """主函數"""
    tester = BoundaryConditionTester()
    summary = tester.run_all_boundary_tests()
    
    print("\n" + "="*60)
    print("邊界條件測試報告")
    print("="*60)
    
    print(f"\n📊 整體結果：{summary['overall_status']}")
    print(f"通過率：{summary['pass_rate']:.1%} ({summary['passed_tests']}/{summary['total_tests']})")
    
    print("\n📋 詳細結果：")
    for test in summary['test_details']:
        status = "✅" if test['passed'] else "❌"
        print(f"  {status} {test['test_name']}: {test['message']}")
    
    # 保存結果
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"boundary_condition_test_report_{timestamp}.json"
    
    try:
        import json
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2, default=str)
        print(f"\n💾 測試報告已保存至：{filename}")
    except Exception as e:
        logger.error(f"保存報告失敗：{e}")
    
    return summary


if __name__ == "__main__":
    main() 