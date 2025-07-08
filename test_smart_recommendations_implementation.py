"""
第3章3.4節智能建議區域實作測試
驗證所有規格要求和功能完整性
"""

import unittest
import sys
import os
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock

# 添加src目錄到Python路徑
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.ui.smart_recommendations import (
    SmartRecommendationsManager,
    SMART_RECOMMENDATIONS,
    EDUCATIONAL_CONTENT
)

class TestSmartRecommendationsImplementation(unittest.TestCase):
    """測試智能建議區域實作"""
    
    def setUp(self):
        """設置測試環境"""
        self.manager = SmartRecommendationsManager()
        
        # 模擬參數
        self.test_parameters = {
            "initial_investment": 100000,
            "investment_years": 10,
            "stock_ratio": 80,
            "bond_ratio": 20,
            "monthly_investment": 10000,
            "rebalance_frequency": "monthly"
        }
        
        # 模擬計算結果 - VA策略明顯優於DCA策略
        self.test_calculation_results = {
            "summary_df": pd.DataFrame({
                "Strategy": ["VA_Rebalance", "DCA"],
                "Final_Value": [2500000, 2300000],
                "Annualized_Return": [15.5, 10.2],  # 差異5.3%，超過5%閾值
                "Volatility": [15.3, 14.8],
                "Sharpe_Ratio": [0.82, 0.76]
            })
        }
    
    def test_3_4_1_smart_recommendations_structure(self):
        """測試3.4.1節個人化建議系統結構"""
        # 測試SMART_RECOMMENDATIONS結構
        self.assertIn("recommendation_templates", SMART_RECOMMENDATIONS)
        self.assertIn("risk_assessment", SMART_RECOMMENDATIONS)
        
        # 測試recommendation_templates規格
        templates = SMART_RECOMMENDATIONS["recommendation_templates"]
        self.assertIn("va_recommended", templates)
        self.assertIn("dca_recommended", templates)
        self.assertIn("neutral_analysis", templates)
        
        # 測試va_recommended範本
        va_template = templates["va_recommended"]
        self.assertEqual(va_template["title"], "🎯 建議您使用定期定值策略")
        self.assertEqual(va_template["style"], "success_card")
        self.assertIn("reasoning", va_template)
        
        # 測試dca_recommended範本
        dca_template = templates["dca_recommended"]
        self.assertEqual(dca_template["title"], "💰 建議您使用定期定額策略")
        self.assertEqual(dca_template["style"], "success_card")
        self.assertIn("reasoning", dca_template)
        
        # 測試neutral_analysis範本
        neutral_template = templates["neutral_analysis"]
        self.assertEqual(neutral_template["title"], "📊 兩種策略表現相近")
        self.assertEqual(neutral_template["style"], "info_card")
        self.assertIn("reasoning", neutral_template)
        
        # 測試risk_assessment結構
        risk_assessment = SMART_RECOMMENDATIONS["risk_assessment"]
        self.assertIn("high_risk", risk_assessment)
        self.assertIn("moderate_risk", risk_assessment)
        self.assertIn("low_risk", risk_assessment)
        
        print("✅ 3.4.1節個人化建議系統結構測試通過")
    
    def test_3_4_2_educational_content_structure(self):
        """測試3.4.2節投資知識卡片結構"""
        # 測試EDUCATIONAL_CONTENT結構
        self.assertIn("knowledge_cards", EDUCATIONAL_CONTENT)
        self.assertIn("help_section", EDUCATIONAL_CONTENT)
        
        # 測試knowledge_cards規格
        cards = EDUCATIONAL_CONTENT["knowledge_cards"]
        required_cards = ["what_is_va", "what_is_dca", "risk_explanation"]
        
        for card_name in required_cards:
            self.assertIn(card_name, cards)
        
        # 測試what_is_va卡片
        va_card = cards["what_is_va"]
        self.assertEqual(va_card["title"], "💡 什麼是定期定值？")
        self.assertEqual(va_card["content"], "就像設定目標存款，不夠就多存，超過就少存。當市場下跌時自動加碼，上漲時減少投入，追求平穩的成長軌跡。")
        self.assertTrue(va_card["expandable"])
        self.assertTrue(va_card["beginner_friendly"])
        self.assertEqual(va_card["icon"], "🎯")
        
        # 測試what_is_dca卡片
        dca_card = cards["what_is_dca"]
        self.assertEqual(dca_card["title"], "💡 什麼是定期定額？")
        self.assertEqual(dca_card["content"], "每月固定投入相同金額，就像定期定額存款。不管市場漲跌都持續投入，用時間來分散成本。")
        self.assertTrue(dca_card["expandable"])
        self.assertTrue(dca_card["beginner_friendly"])
        self.assertEqual(dca_card["icon"], "💰")
        
        # 測試risk_explanation卡片
        risk_card = cards["risk_explanation"]
        self.assertEqual(risk_card["title"], "⚠️ 投資風險說明")
        self.assertEqual(risk_card["content"], "所有投資都有風險，過去績效不代表未來表現。請根據自身風險承受能力謹慎投資。")
        self.assertEqual(risk_card["importance"], "high")
        self.assertTrue(risk_card["always_visible"])
        
        # 測試help_section規格
        help_section = EDUCATIONAL_CONTENT["help_section"]
        self.assertEqual(help_section["title"], "🙋‍♀️ 需要幫助？")
        
        required_quick_links = ["📖 新手指南", "❓ 常見問題"]
        actual_quick_links = [link["text"] for link in help_section["quick_links"]]
        
        for required_link in required_quick_links:
            self.assertIn(required_link, actual_quick_links)
        
        # 驗證總共只有2個快速連結
        self.assertEqual(len(help_section["quick_links"]), 2)
        
        # 測試tutorial_button規格
        tutorial_btn = help_section["tutorial_button"]
        self.assertEqual(tutorial_btn["text"], "🚀 5分鐘快速上手")
        self.assertEqual(tutorial_btn["style"], "primary")
        
        print("✅ 3.4.2節投資知識卡片結構測試通過")
    
    def test_smart_recommendations_manager_initialization(self):
        """測試SmartRecommendationsManager初始化"""
        # 測試初始化
        self.assertIsNotNone(self.manager.recommendations_config)
        self.assertIsNotNone(self.manager.educational_config)
        self.assertIsNone(self.manager.current_recommendation)
        self.assertEqual(self.manager.user_profile, {})
        
        print("✅ SmartRecommendationsManager初始化測試通過")
    
    def test_risk_tolerance_derivation(self):
        """測試風險承受度推導邏輯"""
        # 測試高風險承受度
        high_risk_params = {
            "initial_investment": 600000,
            "investment_years": 15,
            "stock_ratio": 85
        }
        risk_tolerance = self.manager._derive_risk_tolerance(high_risk_params)
        self.assertEqual(risk_tolerance, "high")
        
        # 測試中等風險承受度
        moderate_risk_params = {
            "initial_investment": 300000,
            "investment_years": 7,
            "stock_ratio": 70
        }
        risk_tolerance = self.manager._derive_risk_tolerance(moderate_risk_params)
        self.assertEqual(risk_tolerance, "moderate")
        
        # 測試保守風險承受度
        conservative_risk_params = {
            "initial_investment": 100000,
            "investment_years": 3,
            "stock_ratio": 50
        }
        risk_tolerance = self.manager._derive_risk_tolerance(conservative_risk_params)
        self.assertEqual(risk_tolerance, "conservative")
        
        print("✅ 風險承受度推導邏輯測試通過")
    
    def test_strategy_performance_comparison(self):
        """測試策略績效比較邏輯"""
        # 測試有效的計算結果
        comparison = self.manager._compare_strategy_performance(self.test_calculation_results)
        
        self.assertIn("performance_difference", comparison)
        self.assertIn("better_strategy", comparison)
        self.assertIn("va_final_value", comparison)
        self.assertIn("dca_final_value", comparison)
        self.assertIn("amount_difference", comparison)
        
        # 驗證計算邏輯
        self.assertEqual(comparison["better_strategy"], "VA")  # VA報酬率更高
        self.assertEqual(comparison["amount_difference"], 200000)  # 2500000 - 2300000
        self.assertAlmostEqual(comparison["performance_difference"], 5.3, places=1)  # 15.5 - 10.2
        
        # 測試無效的計算結果
        empty_results = {}
        comparison_empty = self.manager._compare_strategy_performance(empty_results)
        self.assertEqual(comparison_empty["performance_difference"], 0)
        self.assertEqual(comparison_empty["better_strategy"], "neutral")
        
        print("✅ 策略績效比較邏輯測試通過")
    
    def test_user_profile_analysis(self):
        """測試用戶檔案分析"""
        # 分析用戶檔案
        self.manager._analyze_user_profile(self.test_parameters, self.test_calculation_results)
        
        # 驗證用戶檔案結構
        profile = self.manager.user_profile
        self.assertIn("investment_amount", profile)
        self.assertIn("time_horizon", profile)
        self.assertIn("risk_tolerance_derived", profile)
        self.assertIn("strategy_performance_comparison", profile)
        
        # 驗證具體值
        self.assertEqual(profile["investment_amount"], 100000)
        self.assertEqual(profile["time_horizon"], 10)
        self.assertEqual(profile["risk_tolerance_derived"], "moderate")
        
        print("✅ 用戶檔案分析測試通過")
    
    def test_recommendation_generation(self):
        """測試建議生成邏輯"""
        # 設置用戶檔案
        self.manager._analyze_user_profile(self.test_parameters, self.test_calculation_results)
        
        # 驗證建議生成
        self.assertIsNotNone(self.manager.current_recommendation)
        
        recommendation = self.manager.current_recommendation
        self.assertIn("title", recommendation)
        self.assertIn("style", recommendation)
        self.assertIn("content", recommendation)
        self.assertIn("recommendation_type", recommendation)
        
        # 根據測試數據，應該推薦VA策略
        self.assertEqual(recommendation["recommendation_type"], "va_recommended")
        self.assertEqual(recommendation["title"], "🎯 建議您使用定期定值策略")
        
        print("✅ 建議生成邏輯測試通過")
    
    def test_va_recommendation_preparation(self):
        """測試VA策略推薦準備"""
        # 設置測試環境
        self.manager.user_profile = {
            "time_horizon": 10,
            "strategy_performance_comparison": {
                "amount_difference": 200000,
                "better_strategy": "VA"
            }
        }
        
        # 準備VA推薦
        va_recommendation = self.manager._prepare_va_recommendation()
        
        # 驗證推薦結構
        self.assertEqual(va_recommendation["title"], "🎯 建議您使用定期定值策略")
        self.assertEqual(va_recommendation["style"], "success_card")
        self.assertEqual(va_recommendation["recommendation_type"], "va_recommended")
        
        # 驗證動態變數替換
        self.assertIn("200,000", va_recommendation["content"])
        self.assertIn("10 年", va_recommendation["content"])
        
        print("✅ VA策略推薦準備測試通過")
    
    def test_dca_recommendation_preparation(self):
        """測試DCA策略推薦準備"""
        # 設置測試環境
        self.manager.user_profile = {
            "strategy_performance_comparison": {
                "dca_final_value": 2300000,
                "dca_return": 11.2,
                "better_strategy": "DCA"
            }
        }
        
        # 準備DCA推薦
        dca_recommendation = self.manager._prepare_dca_recommendation()
        
        # 驗證推薦結構
        self.assertEqual(dca_recommendation["title"], "💰 建議您使用定期定額策略")
        self.assertEqual(dca_recommendation["style"], "success_card")
        self.assertEqual(dca_recommendation["recommendation_type"], "dca_recommended")
        
        # 驗證動態變數替換
        self.assertIn("2,300,000", dca_recommendation["content"])
        self.assertIn("11.20", dca_recommendation["content"])
        
        print("✅ DCA策略推薦準備測試通過")
    
    def test_neutral_recommendation_preparation(self):
        """測試中性分析準備"""
        # 準備中性推薦
        neutral_recommendation = self.manager._prepare_neutral_recommendation()
        
        # 驗證推薦結構
        self.assertEqual(neutral_recommendation["title"], "📊 兩種策略表現相近")
        self.assertEqual(neutral_recommendation["style"], "info_card")
        self.assertEqual(neutral_recommendation["recommendation_type"], "neutral_analysis")
        
        # 驗證內容包含兩種策略優勢
        self.assertIn("定期定值的優勢", neutral_recommendation["content"])
        self.assertIn("定期定額的優勢", neutral_recommendation["content"])
        
        print("✅ 中性分析準備測試通過")
    
    def test_recommendation_summary(self):
        """測試建議摘要功能"""
        # 測試無建議狀態
        summary = self.manager.get_recommendation_summary()
        self.assertEqual(summary["status"], "no_recommendation")
        
        # 設置建議並測試
        self.manager._analyze_user_profile(self.test_parameters, self.test_calculation_results)
        summary = self.manager.get_recommendation_summary()
        
        self.assertEqual(summary["status"], "active")
        self.assertIn("recommendation_type", summary)
        self.assertIn("title", summary)
        self.assertIn("user_profile", summary)
        
        print("✅ 建議摘要功能測試通過")
    
    def test_comprehensive_functionality(self):
        """測試綜合功能"""
        # 模擬完整的建議生成流程
        self.manager._analyze_user_profile(self.test_parameters, self.test_calculation_results)
        
        # 驗證所有組件都正常工作
        self.assertIsNotNone(self.manager.current_recommendation)
        self.assertIsNotNone(self.manager.user_profile)
        
        # 驗證建議內容包含必要資訊
        recommendation = self.manager.current_recommendation
        self.assertTrue(len(recommendation["content"]) > 50)  # 內容不能太短
        
        # 驗證用戶檔案完整性
        profile = self.manager.user_profile
        self.assertTrue(profile["investment_amount"] > 0)
        self.assertTrue(profile["time_horizon"] > 0)
        self.assertIn(profile["risk_tolerance_derived"], ["high", "moderate", "conservative"])
        
        print("✅ 綜合功能測試通過")

def run_all_tests():
    """運行所有測試"""
    print("🚀 開始第3章3.4節智能建議區域實作測試")
    print("=" * 60)
    
    # 創建測試套件
    test_suite = unittest.TestLoader().loadTestsFromTestCase(TestSmartRecommendationsImplementation)
    
    # 運行測試
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # 輸出總結
    print("\n" + "=" * 60)
    print("📊 測試結果總結")
    print(f"總測試數: {result.testsRun}")
    print(f"成功: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"失敗: {len(result.failures)}")
    print(f"錯誤: {len(result.errors)}")
    
    if result.failures:
        print("\n❌ 失敗的測試:")
        for test, traceback in result.failures:
            print(f"  - {test}: {traceback}")
    
    if result.errors:
        print("\n💥 錯誤的測試:")
        for test, traceback in result.errors:
            print(f"  - {test}: {traceback}")
    
    if result.wasSuccessful():
        print("\n🎉 所有測試通過！第3章3.4節智能建議區域實作完成")
        return True
    else:
        print("\n⚠️ 部分測試未通過，請檢查實作")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1) 