"""
最終驗證報告生成器

整合所有模擬數據驗證測試結果，生成完整的驗證報告和改進建議
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import json
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Any
from pathlib import Path
import glob

from src.utils.logger import get_component_logger

logger = get_component_logger("FinalValidationReport")


class FinalValidationReportGenerator:
    """最終驗證報告生成器"""
    
    def __init__(self):
        self.report_data = {}
        self.recommendations = []
        
    def load_all_test_reports(self) -> Dict[str, Any]:
        """載入所有測試報告"""
        logger.info("載入所有測試報告...")
        
        reports = {}
        
        # 查找所有報告文件
        report_files = {
            'simulation_validation': glob.glob('simulation_validation_report_*.json'),
            'boundary_condition': glob.glob('boundary_condition_test_report_*.json'),
            'consistency_verification': glob.glob('consistency_verification_report_*.json')
        }
        
        for report_type, files in report_files.items():
            if files:
                # 選擇最新的報告
                latest_file = max(files, key=os.path.getctime)
                try:
                    with open(latest_file, 'r', encoding='utf-8') as f:
                        reports[report_type] = json.load(f)
                    logger.info(f"載入 {report_type} 報告：{latest_file}")
                except Exception as e:
                    logger.error(f"載入 {report_type} 報告失敗：{e}")
                    reports[report_type] = None
            else:
                logger.warning(f"未找到 {report_type} 報告")
                reports[report_type] = None
        
        return reports
    
    def analyze_overall_performance(self, reports: Dict[str, Any]) -> Dict[str, Any]:
        """分析整體性能"""
        logger.info("分析整體性能...")
        
        performance_summary = {
            'overall_score': 0.0,
            'category_scores': {},
            'critical_issues': [],
            'warnings': [],
            'strengths': []
        }
        
        # 數據品質分析
        if reports['simulation_validation']:
            data_quality = reports['simulation_validation']['data_quality_metrics']
            performance_summary['category_scores']['data_quality'] = data_quality['overall_score']
            
            # 識別關鍵問題
            if data_quality['price_jump_rate'] < 0.8:
                performance_summary['critical_issues'].append('價格跳躍率過高，需要調整價格生成邏輯')
            
            if data_quality['volatility_accuracy'] < 0.5:
                performance_summary['critical_issues'].append('波動率偏差過大，需要校正波動率參數')
            
            if data_quality['correlation_reasonability'] > 0.8:
                performance_summary['strengths'].append('股債相關性合理')
            
            if data_quality['yield_stability'] > 0.9:
                performance_summary['strengths'].append('債券殖利率穩定性良好')
        
        # 計算準確性分析
        if reports['simulation_validation']:
            calc_accuracy = reports['simulation_validation']['calculation_accuracy_metrics']
            performance_summary['category_scores']['calculation_accuracy'] = calc_accuracy['overall_score']
            
            if calc_accuracy['formula_verification_rate'] > 0.95:
                performance_summary['strengths'].append('公式驗證率優秀')
            
            if calc_accuracy['precision_maintenance_rate'] < 0.7:
                performance_summary['warnings'].append('精度保持需要改進')
        
        # 邊界條件測試分析
        if reports['boundary_condition']:
            boundary_score = reports['boundary_condition']['pass_rate']
            performance_summary['category_scores']['boundary_conditions'] = boundary_score
            
            if boundary_score == 1.0:
                performance_summary['strengths'].append('邊界條件測試全部通過')
            elif boundary_score < 0.8:
                performance_summary['critical_issues'].append('邊界條件測試存在失敗項目')
        
        # 一致性驗證分析
        if reports['consistency_verification']:
            consistency_details = reports['consistency_verification']['test_details']
            avg_consistency = np.mean([test['score'] for test in consistency_details.values() if 'score' in test])
            performance_summary['category_scores']['consistency'] = avg_consistency
            
            if avg_consistency < 0.6:
                performance_summary['warnings'].append('一致性驗證需要改進')
            
            # 檢查特定一致性問題
            if 'parameter_sensitivity' in consistency_details:
                if not consistency_details['parameter_sensitivity']['passed']:
                    performance_summary['warnings'].append('參數敏感性測試未通過，需要檢查參數影響')
        
        # 計算整體評分
        scores = list(performance_summary['category_scores'].values())
        if scores:
            performance_summary['overall_score'] = np.mean(scores)
        
        return performance_summary
    
    def generate_improvement_recommendations(self, reports: Dict[str, Any], performance: Dict[str, Any]) -> List[Dict[str, Any]]:
        """生成改進建議"""
        logger.info("生成改進建議...")
        
        recommendations = []
        
        # 基於數據品質的建議
        if reports['simulation_validation']:
            data_quality = reports['simulation_validation']['data_quality_metrics']
            
            if data_quality['volatility_accuracy'] < 0.5:
                recommendations.append({
                    'priority': 'HIGH',
                    'category': '數據品質',
                    'issue': '波動率偏差過大',
                    'current_value': f"{data_quality['volatility_accuracy']:.2f}",
                    'target_value': '> 0.8',
                    'specific_action': '調整 stock_volatility 參數從 0.20 到 0.23，使實際波動率更接近設定的 25%',
                    'implementation': 'src/ui/results_display.py 第 868 行',
                    'expected_impact': '提高波動率匹配度至 80% 以上'
                })
            
            if data_quality['price_jump_rate'] < 1.0:
                recommendations.append({
                    'priority': 'MEDIUM',
                    'category': '數據品質',
                    'issue': '價格跳躍控制',
                    'current_value': f"{data_quality['price_jump_rate']:.2f}",
                    'target_value': '1.0',
                    'specific_action': '優化價格變化限制邏輯，確保極端變化控制在 8% 以內',
                    'implementation': 'src/ui/results_display.py 第 925-930 行',
                    'expected_impact': '完全消除異常價格跳躍'
                })
        
        # 基於結果合理性的建議
        if reports['simulation_validation']:
            result_reason = reports['simulation_validation']['result_reasonability_metrics']
            
            if result_reason['max_drawdown_reasonability'] < 0.3:
                recommendations.append({
                    'priority': 'HIGH',
                    'category': '策略合理性',
                    'issue': '最大回撤不足',
                    'current_value': f"{result_reason['max_drawdown_reasonability']:.2f}",
                    'target_value': '> 0.7',
                    'specific_action': '增加市場下跌情境，確保策略有 5%-15% 的真實回撤風險',
                    'implementation': '在模擬數據中加入週期性下跌階段',
                    'expected_impact': '使策略表現更符合真實市場風險'
                })
            
            if result_reason['long_term_growth_consistency'] < 0.2:
                recommendations.append({
                    'priority': 'HIGH',
                    'category': '長期一致性',
                    'issue': '成長率偏差過大',
                    'current_value': f"{result_reason['long_term_growth_consistency']:.2f}",
                    'target_value': '> 0.7',
                    'specific_action': '調整 stock_growth_rate 從 0.015 到 0.006，使年化成長率接近設定的 2.4%',
                    'implementation': 'src/ui/results_display.py 第 867 行',
                    'expected_impact': '長期成長軌跡符合預期，偏差控制在 20% 以內'
                })
        
        # 基於一致性驗證的建議
        if reports['consistency_verification']:
            consistency_details = reports['consistency_verification']['test_details']
            
            if 'frequency_consistency' in consistency_details and not consistency_details['frequency_consistency']['passed']:
                recommendations.append({
                    'priority': 'MEDIUM',
                    'category': '跨頻率一致性',
                    'issue': '不同投資頻率結果不一致',
                    'current_value': f"{consistency_details['frequency_consistency']['score']:.2f}",
                    'target_value': '> 0.8',
                    'specific_action': '確保年化收益率計算在不同頻率下保持一致性',
                    'implementation': '檢查並統一各頻率的複利計算邏輯',
                    'expected_impact': '跨頻率投資結果具有可比性'
                })
        
        # 通用改進建議
        recommendations.append({
            'priority': 'LOW',
            'category': '系統優化',
            'issue': '精度保持',
            'current_value': '0.5-0.6',
            'target_value': '> 0.9',
            'specific_action': '統一數值精度格式，限制小數位數在 4 位以內',
            'implementation': '在所有計算結果輸出前進行格式化',
            'expected_impact': '提高數據呈現的專業性和一致性'
        })
        
        # 按優先級排序
        priority_order = {'HIGH': 1, 'MEDIUM': 2, 'LOW': 3}
        recommendations.sort(key=lambda x: priority_order[x['priority']])
        
        return recommendations
    
    def generate_comprehensive_report(self) -> Dict[str, Any]:
        """生成綜合報告"""
        logger.info("生成綜合驗證報告...")
        
        # 載入所有測試報告
        reports = self.load_all_test_reports()
        
        # 分析整體性能
        performance = self.analyze_overall_performance(reports)
        
        # 生成改進建議
        recommendations = self.generate_improvement_recommendations(reports, performance)
        
        # 構建綜合報告
        comprehensive_report = {
            'report_metadata': {
                'generated_at': datetime.now().isoformat(),
                'validation_plan_version': '1.0',
                'total_test_categories': 3,
                'report_generator': 'FinalValidationReportGenerator'
            },
            'executive_summary': {
                'overall_score': performance['overall_score'],
                'overall_status': self._determine_overall_status(performance['overall_score']),
                'critical_issues_count': len(performance['critical_issues']),
                'warnings_count': len(performance['warnings']),
                'strengths_count': len(performance['strengths']),
                'high_priority_recommendations': len([r for r in recommendations if r['priority'] == 'HIGH'])
            },
            'detailed_performance': performance,
            'test_results_summary': self._summarize_test_results(reports),
            'improvement_recommendations': recommendations,
            'implementation_roadmap': self._create_implementation_roadmap(recommendations),
            'quality_metrics': self._calculate_quality_metrics(reports),
            'raw_reports': reports
        }
        
        return comprehensive_report
    
    def _determine_overall_status(self, score: float) -> str:
        """判斷整體狀態"""
        if score >= 0.8:
            return 'EXCELLENT'
        elif score >= 0.7:
            return 'GOOD'
        elif score >= 0.6:
            return 'ACCEPTABLE'
        elif score >= 0.5:
            return 'NEEDS_IMPROVEMENT'
        else:
            return 'CRITICAL'
    
    def _summarize_test_results(self, reports: Dict[str, Any]) -> Dict[str, Any]:
        """總結測試結果"""
        summary = {}
        
        if reports['simulation_validation']:
            summary['simulation_validation'] = {
                'overall_score': reports['simulation_validation']['overall_score'],
                'data_quality_score': reports['simulation_validation']['data_quality_metrics']['overall_score'],
                'calculation_accuracy_score': reports['simulation_validation']['calculation_accuracy_metrics']['overall_score'],
                'result_reasonability_score': reports['simulation_validation']['result_reasonability_metrics']['overall_score']
            }
        
        if reports['boundary_condition']:
            summary['boundary_condition'] = {
                'pass_rate': reports['boundary_condition']['pass_rate'],
                'total_tests': reports['boundary_condition']['total_tests'],
                'passed_tests': reports['boundary_condition']['passed_tests']
            }
        
        if reports['consistency_verification']:
            summary['consistency_verification'] = {
                'pass_rate': reports['consistency_verification']['pass_rate'],
                'total_tests': reports['consistency_verification']['total_tests'],
                'passed_tests': reports['consistency_verification']['passed_tests']
            }
        
        return summary
    
    def _create_implementation_roadmap(self, recommendations: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """創建實施路線圖"""
        roadmap = {
            'immediate_actions': [],  # 高優先級，1週內
            'short_term_goals': [],   # 中優先級，1個月內
            'long_term_improvements': []  # 低優先級，3個月內
        }
        
        for rec in recommendations:
            if rec['priority'] == 'HIGH':
                roadmap['immediate_actions'].append({
                    'action': rec['specific_action'],
                    'implementation': rec['implementation'],
                    'expected_impact': rec['expected_impact']
                })
            elif rec['priority'] == 'MEDIUM':
                roadmap['short_term_goals'].append({
                    'action': rec['specific_action'],
                    'implementation': rec['implementation'],
                    'expected_impact': rec['expected_impact']
                })
            else:
                roadmap['long_term_improvements'].append({
                    'action': rec['specific_action'],
                    'implementation': rec['implementation'],
                    'expected_impact': rec['expected_impact']
                })
        
        return roadmap
    
    def _calculate_quality_metrics(self, reports: Dict[str, Any]) -> Dict[str, float]:
        """計算品質指標"""
        metrics = {}
        
        if reports['simulation_validation']:
            sv = reports['simulation_validation']
            metrics.update({
                'data_completeness': 1.0 if sv['data_summary']['market_data_periods'] > 0 else 0.0,
                'calculation_reliability': sv['calculation_accuracy_metrics']['overall_score'],
                'result_credibility': sv['result_reasonability_metrics']['overall_score'],
                'data_consistency': sv['data_quality_metrics']['overall_score']
            })
        
        if reports['boundary_condition']:
            metrics['robustness'] = reports['boundary_condition']['pass_rate']
        
        if reports['consistency_verification']:
            metrics['stability'] = reports['consistency_verification']['pass_rate']
        
        return metrics
    
    def save_report(self, report: Dict[str, Any], filename: str = None) -> str:
        """保存報告"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"final_validation_report_{timestamp}.json"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2, default=str)
            
            logger.info(f"最終驗證報告已保存至：{filename}")
            return filename
        except Exception as e:
            logger.error(f"保存報告失敗：{e}")
            return ""
    
    def print_executive_summary(self, report: Dict[str, Any]):
        """列印執行摘要"""
        summary = report['executive_summary']
        performance = report['detailed_performance']
        
        print("\n" + "="*80)
        print("模擬資料查核 - 最終驗證報告")
        print("="*80)
        
        print(f"\n📊 整體評估")
        print(f"  總體評分：{summary['overall_score']:.2f}/1.00")
        print(f"  整體狀態：{summary['overall_status']}")
        
        print(f"\n🎯 問題統計")
        print(f"  關鍵問題：{summary['critical_issues_count']} 項")
        print(f"  警告事項：{summary['warnings_count']} 項")
        print(f"  優勢項目：{summary['strengths_count']} 項")
        print(f"  高優先級建議：{summary['high_priority_recommendations']} 項")
        
        print(f"\n📈 分類評分")
        for category, score in performance['category_scores'].items():
            print(f"  {category}: {score:.2f}")
        
        if performance['critical_issues']:
            print(f"\n🚨 關鍵問題")
            for issue in performance['critical_issues']:
                print(f"  • {issue}")
        
        if performance['strengths']:
            print(f"\n✅ 優勢項目")
            for strength in performance['strengths']:
                print(f"  • {strength}")
        
        print(f"\n📋 改進建議摘要")
        recommendations = report['improvement_recommendations']
        for priority in ['HIGH', 'MEDIUM', 'LOW']:
            priority_recs = [r for r in recommendations if r['priority'] == priority]
            if priority_recs:
                print(f"  {priority} 優先級：{len(priority_recs)} 項")
                for rec in priority_recs[:2]:  # 只顯示前2項
                    print(f"    - {rec['issue']}: {rec['specific_action']}")


def main():
    """主函數"""
    generator = FinalValidationReportGenerator()
    
    # 生成綜合報告
    comprehensive_report = generator.generate_comprehensive_report()
    
    # 列印執行摘要
    generator.print_executive_summary(comprehensive_report)
    
    # 保存報告
    filename = generator.save_report(comprehensive_report)
    
    print(f"\n💾 完整報告已保存至：{filename}")
    print("\n" + "="*80)
    print("✅ 模擬資料查核完成")
    print("="*80)
    
    return comprehensive_report


if __name__ == "__main__":
    main() 