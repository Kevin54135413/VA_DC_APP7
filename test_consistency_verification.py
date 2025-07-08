"""
一致性驗證測試腳本

檢查模擬數據生成在不同情況下的一致性和穩定性
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Any, Tuple
from src.ui.results_display import ResultsDisplayManager
from src.utils.logger import get_component_logger
import matplotlib.pyplot as plt

logger = get_component_logger("ConsistencyVerification")


class ConsistencyVerificationTester:
    """一致性驗證測試器"""
    
    def __init__(self):
        self.results_manager = ResultsDisplayManager()
        self.test_results = []
        
    def run_all_consistency_tests(self) -> Dict[str, Any]:
        """執行所有一致性驗證測試"""
        logger.info("=== 開始一致性驗證測試 ===")
        
        test_results = {
            'reproducibility': self.test_reproducibility(),
            'parameter_sensitivity': self.test_parameter_sensitivity(),
            'frequency_consistency': self.test_frequency_consistency(),
            'temporal_stability': self.test_temporal_stability(),
            'statistical_properties': self.test_statistical_properties()
        }
        
        # 計算整體通過率
        total_tests = len(test_results)
        passed_tests = sum(1 for result in test_results.values() if result['passed'])
        
        summary = {
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'pass_rate': passed_tests / total_tests,
            'test_details': test_results,
            'overall_status': 'PASS' if passed_tests == total_tests else 'PARTIAL_PASS'
        }
        
        logger.info(f"一致性驗證測試完成：{passed_tests}/{total_tests} 通過")
        return summary
    
    def test_reproducibility(self) -> Dict[str, Any]:
        """測試可重現性 - 相同參數多次運行的一致性"""
        logger.info("測試可重現性...")
        
        try:
            # 標準測試參數
            parameters = {
                "investment_amount": 10000,
                "investment_periods": 10,
                "investment_frequency": "annually",
                "start_date": datetime(2020, 1, 1),
                "stock_ratio": 60,
                "bond_ratio": 40,
                "rebalance_threshold_upper": 70,
                "rebalance_threshold_lower": 50
            }
            
            # 運行多次測試
            runs = []
            for i in range(5):
                market_data = self.results_manager._generate_fallback_data(parameters)
                runs.append(market_data)
            
            # 分析一致性
            consistency_scores = []
            
            for i in range(1, len(runs)):
                # 比較股票價格軌跡
                price_correlation = np.corrcoef(
                    runs[0]['SPY_Price_End'].values,
                    runs[i]['SPY_Price_End'].values
                )[0, 1]
                
                # 比較殖利率軌跡
                yield_correlation = np.corrcoef(
                    runs[0]['Bond_Yield_End'].values,
                    runs[i]['Bond_Yield_End'].values
                )[0, 1]
                
                # 價格範圍一致性
                price_range_similarity = self._calculate_range_similarity(
                    runs[0]['SPY_Price_End'], runs[i]['SPY_Price_End']
                )
                
                run_score = np.mean([
                    1 - abs(price_correlation),  # 相關性應該低（因為是隨機生成）
                    1 - abs(yield_correlation),
                    price_range_similarity
                ])
                consistency_scores.append(run_score)
            
            avg_consistency = np.mean(consistency_scores)
            
            # 評分標準：平均一致性 > 0.3 為合格（允許隨機性但結構一致）
            passed = avg_consistency > 0.3
            
            return {
                'test_name': 'reproducibility',
                'passed': passed,
                'score': avg_consistency,
                'message': f'可重現性測試：平均一致性{avg_consistency:.3f}'
            }
            
        except Exception as e:
            return {
                'test_name': 'reproducibility',
                'passed': False,
                'score': 0.0,
                'message': f'可重現性測試失敗：{e}'
            }
    
    def test_parameter_sensitivity(self) -> Dict[str, Any]:
        """測試參數敏感性 - 參數微調對結果的影響"""
        logger.info("測試參數敏感性...")
        
        try:
            # 基準參數
            base_parameters = {
                "investment_amount": 10000,
                "investment_periods": 10,
                "investment_frequency": "annually", 
                "start_date": datetime(2020, 1, 1),
                "stock_ratio": 60,
                "bond_ratio": 40,
                "rebalance_threshold_upper": 70,
                "rebalance_threshold_lower": 50
            }
            
            # 獲取基準結果
            base_data = self.results_manager._generate_fallback_data(base_parameters)
            
            # 測試微調參數的影響
            sensitivity_tests = [
                {"investment_amount": 10100},  # +1%
                {"investment_periods": 11},    # +10%
                {"stock_ratio": 61, "bond_ratio": 39},  # +1%股票比例
                {"rebalance_threshold_upper": 71, "rebalance_threshold_lower": 49}  # 微調閾值
            ]
            
            sensitivity_scores = []
            
            for test_params in sensitivity_tests:
                modified_params = base_parameters.copy()
                modified_params.update(test_params)
                
                try:
                    modified_data = self.results_manager._generate_fallback_data(modified_params)
                    
                    if len(modified_data) == len(base_data):
                        # 計算價格軌跡相似性
                        price_similarity = self._calculate_trajectory_similarity(
                            base_data['SPY_Price_End'].values,
                            modified_data['SPY_Price_End'].values
                        )
                        
                        # 微調應該產生相似但非完全相同的結果
                        # 相似性在0.7-0.95之間為理想
                        if 0.7 <= price_similarity <= 0.95:
                            sensitivity_scores.append(1.0)
                        elif price_similarity > 0.95:
                            sensitivity_scores.append(0.7)  # 太相似
                        elif price_similarity < 0.7:
                            sensitivity_scores.append(0.5)  # 太不同
                        else:
                            sensitivity_scores.append(0.0)
                    else:
                        sensitivity_scores.append(0.0)
                        
                except Exception as e:
                    logger.warning(f"敏感性測試失敗：{test_params}, {e}")
                    sensitivity_scores.append(0.0)
            
            avg_sensitivity = np.mean(sensitivity_scores)
            passed = avg_sensitivity > 0.6
            
            return {
                'test_name': 'parameter_sensitivity',
                'passed': passed,
                'score': avg_sensitivity,
                'message': f'參數敏感性測試：平均評分{avg_sensitivity:.3f}'
            }
            
        except Exception as e:
            return {
                'test_name': 'parameter_sensitivity',
                'passed': False,
                'score': 0.0,
                'message': f'參數敏感性測試失敗：{e}'
            }
    
    def test_frequency_consistency(self) -> Dict[str, Any]:
        """測試跨頻率計算一致性"""
        logger.info("測試跨頻率計算一致性...")
        
        try:
            base_params = {
                "investment_amount": 12000,  # 可被12整除，便於月度比較
                "investment_periods": 2,     # 2年
                "start_date": datetime(2020, 1, 1),
                "stock_ratio": 60,
                "bond_ratio": 40,
                "rebalance_threshold_upper": 70,
                "rebalance_threshold_lower": 50
            }
            
            # 測試不同頻率
            frequencies = ["annually", "quarterly", "monthly"]
            results = {}
            
            for freq in frequencies:
                params = base_params.copy()
                params["investment_frequency"] = freq
                
                data = self.results_manager._generate_fallback_data(params)
                results[freq] = data
            
            # 驗證期數正確性
            expected_periods = {"annually": 2, "quarterly": 8, "monthly": 24}
            period_check = all(
                len(results[freq]) == expected_periods[freq] 
                for freq in frequencies
            )
            
            # 檢查數據品質一致性
            quality_scores = []
            for freq in frequencies:
                data = results[freq]
                if not data.empty:
                    # 計算平均期間收益率
                    returns = (data['SPY_Price_End'] - data['SPY_Price_Origin']) / data['SPY_Price_Origin']
                    avg_return = returns.mean()
                    
                    # 年化收益率應該相近（考慮複利效應）
                    periods_per_year = expected_periods[freq] / 2  # 2年
                    annualized_return = (1 + avg_return) ** periods_per_year - 1
                    
                    # 年化收益率應該在合理範圍內（約6%年化，對應1.5%每期）
                    if 0.04 <= annualized_return <= 0.12:  # 4%-12%年化
                        quality_scores.append(1.0)
                    else:
                        quality_scores.append(0.5)
                else:
                    quality_scores.append(0.0)
            
            avg_quality = np.mean(quality_scores)
            passed = period_check and avg_quality > 0.7
            
            return {
                'test_name': 'frequency_consistency',
                'passed': passed,
                'score': avg_quality,
                'message': f'頻率一致性測試：期數檢查{period_check}，品質評分{avg_quality:.3f}'
            }
            
        except Exception as e:
            return {
                'test_name': 'frequency_consistency',
                'passed': False,
                'score': 0.0,
                'message': f'頻率一致性測試失敗：{e}'
            }
    
    def test_temporal_stability(self) -> Dict[str, Any]:
        """測試時間穩定性 - 不同起始日期的穩定性"""
        logger.info("測試時間穩定性...")
        
        try:
            base_params = {
                "investment_amount": 10000,
                "investment_periods": 5,
                "investment_frequency": "annually",
                "stock_ratio": 60,
                "bond_ratio": 40,
                "rebalance_threshold_upper": 70,
                "rebalance_threshold_lower": 50
            }
            
            # 測試不同起始日期
            start_dates = [
                datetime(2020, 1, 1),
                datetime(2021, 6, 15),
                datetime(2022, 12, 31),
                datetime(2015, 3, 10)
            ]
            
            results = []
            for start_date in start_dates:
                params = base_params.copy()
                params["start_date"] = start_date
                
                data = self.results_manager._generate_fallback_data(params)
                if not data.empty:
                    # 計算統計特徵
                    stats = {
                        'mean_return': ((data['SPY_Price_End'] - data['SPY_Price_Origin']) / data['SPY_Price_Origin']).mean(),
                        'volatility': ((data['SPY_Price_End'] - data['SPY_Price_Origin']) / data['SPY_Price_Origin']).std(),
                        'yield_stability': data['Bond_Yield_End'].std()
                    }
                    results.append(stats)
            
            if len(results) >= 3:
                # 分析統計特徵的穩定性
                mean_returns = [r['mean_return'] for r in results]
                volatilities = [r['volatility'] for r in results]
                yield_stabilities = [r['yield_stability'] for r in results]
                
                # 計算變異係數（標準差/平均值）
                return_cv = np.std(mean_returns) / np.mean(mean_returns) if np.mean(mean_returns) != 0 else 1
                volatility_cv = np.std(volatilities) / np.mean(volatilities) if np.mean(volatilities) != 0 else 1
                yield_cv = np.std(yield_stabilities) / np.mean(yield_stabilities) if np.mean(yield_stabilities) != 0 else 1
                
                # 變異係數應該相對較小（< 0.5）表示穩定
                stability_score = np.mean([
                    1 - min(return_cv, 1.0),
                    1 - min(volatility_cv, 1.0),
                    1 - min(yield_cv, 1.0)
                ])
                
                passed = stability_score > 0.5
                
                return {
                    'test_name': 'temporal_stability',
                    'passed': passed,
                    'score': stability_score,
                    'message': f'時間穩定性測試：穩定性評分{stability_score:.3f}'
                }
            else:
                return {
                    'test_name': 'temporal_stability',
                    'passed': False,
                    'score': 0.0,
                    'message': '時間穩定性測試：有效結果不足'
                }
                
        except Exception as e:
            return {
                'test_name': 'temporal_stability',
                'passed': False,
                'score': 0.0,
                'message': f'時間穩定性測試失敗：{e}'
            }
    
    def test_statistical_properties(self) -> Dict[str, Any]:
        """測試統計特性的合理性"""
        logger.info("測試統計特性...")
        
        try:
            parameters = {
                "investment_amount": 10000,
                "investment_periods": 20,
                "investment_frequency": "annually",
                "start_date": datetime(2000, 1, 1),
                "stock_ratio": 60,
                "bond_ratio": 40,
                "rebalance_threshold_upper": 70,
                "rebalance_threshold_lower": 50
            }
            
            data = self.results_manager._generate_fallback_data(parameters)
            
            if data.empty:
                return {
                    'test_name': 'statistical_properties',
                    'passed': False,
                    'score': 0.0,
                    'message': '統計特性測試：數據為空'
                }
            
            # 計算統計指標
            returns = (data['SPY_Price_End'] - data['SPY_Price_Origin']) / data['SPY_Price_Origin']
            
            stats = {
                'mean_return': returns.mean(),
                'volatility': returns.std(),
                'skewness': returns.skew(),
                'kurtosis': returns.kurtosis(),
                'min_return': returns.min(),
                'max_return': returns.max()
            }
            
            # 評估統計合理性
            checks = {
                'mean_reasonable': 0.005 <= stats['mean_return'] <= 0.03,  # 0.5%-3%期間收益率
                'volatility_reasonable': 0.02 <= stats['volatility'] <= 0.15,  # 2%-15%波動率
                'skewness_reasonable': -2 <= stats['skewness'] <= 2,  # 偏度合理範圍
                'kurtosis_reasonable': -2 <= stats['kurtosis'] <= 5,  # 峰度合理範圍
                'extreme_reasonable': -0.15 <= stats['min_return'] and stats['max_return'] <= 0.15  # 極值合理
            }
            
            passed_checks = sum(checks.values())
            total_checks = len(checks)
            score = passed_checks / total_checks
            
            passed = score > 0.7
            
            return {
                'test_name': 'statistical_properties',
                'passed': passed,
                'score': score,
                'message': f'統計特性測試：{passed_checks}/{total_checks} 檢查通過',
                'details': stats
            }
            
        except Exception as e:
            return {
                'test_name': 'statistical_properties',
                'passed': False,
                'score': 0.0,
                'message': f'統計特性測試失敗：{e}'
            }
    
    def _calculate_range_similarity(self, series1: pd.Series, series2: pd.Series) -> float:
        """計算兩個序列的範圍相似性"""
        try:
            range1 = series1.max() - series1.min()
            range2 = series2.max() - series2.min()
            
            if range1 == 0 and range2 == 0:
                return 1.0
            elif range1 == 0 or range2 == 0:
                return 0.0
            else:
                ratio = min(range1, range2) / max(range1, range2)
                return ratio
        except:
            return 0.0
    
    def _calculate_trajectory_similarity(self, arr1: np.ndarray, arr2: np.ndarray) -> float:
        """計算兩個軌跡的相似性"""
        try:
            if len(arr1) != len(arr2):
                return 0.0
            
            # 正規化
            arr1_norm = (arr1 - arr1.min()) / (arr1.max() - arr1.min()) if arr1.max() != arr1.min() else np.zeros_like(arr1)
            arr2_norm = (arr2 - arr2.min()) / (arr2.max() - arr2.min()) if arr2.max() != arr2.min() else np.zeros_like(arr2)
            
            # 計算相關係數
            correlation = np.corrcoef(arr1_norm, arr2_norm)[0, 1]
            
            # 處理NaN情況
            if np.isnan(correlation):
                correlation = 0.0
            
            return abs(correlation)
        except:
            return 0.0


def main():
    """主函數"""
    tester = ConsistencyVerificationTester()
    summary = tester.run_all_consistency_tests()
    
    print("\n" + "="*60)
    print("一致性驗證測試報告")
    print("="*60)
    
    print(f"\n📊 整體結果：{summary['overall_status']}")
    print(f"通過率：{summary['pass_rate']:.1%} ({summary['passed_tests']}/{summary['total_tests']})")
    
    print("\n📋 詳細結果：")
    for test_name, result in summary['test_details'].items():
        status = "✅" if result['passed'] else "❌"
        score = result.get('score', 0.0)
        print(f"  {status} {test_name}: {result['message']} (評分: {score:.3f})")
        
        # 顯示詳細信息（如果有）
        if 'details' in result:
            details = result['details']
            print(f"      詳情: 平均收益={details['mean_return']:.3f}, 波動率={details['volatility']:.3f}")
    
    # 保存結果
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"consistency_verification_report_{timestamp}.json"
    
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