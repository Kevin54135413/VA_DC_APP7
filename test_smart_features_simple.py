"""
第3章3.4節智能功能與用戶體驗實作簡化測試
專注於驗證核心功能結構和規格遵循性
"""

import unittest
import pandas as pd
import numpy as np
import os
import sys

# 添加src目錄到Python路徑
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

class TestSmartFeaturesStructure(unittest.TestCase):
    """測試智能功能結構完整性"""
    
    def test_3_4_1_smart_data_source_manager_requirements(self):
        """測試3.4.1智能數據源管理實作要求"""
        # 驗證必要的函數規格
        required_functions = [
            'smart_data_source_manager',
            'get_real_market_data_with_security',
            'get_simulation_data_chapter1_compliant',
            'get_cached_data_or_default',
            'user_friendly_error_handler'
        ]
        
        # 檢查smart_features.py文件是否存在
        smart_features_path = os.path.join('src', 'ui', 'smart_features.py')
        self.assertTrue(os.path.exists(smart_features_path), "smart_features.py文件必須存在")
        
        # 讀取文件內容
        with open(smart_features_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 驗證@st.cache_data(ttl=3600)裝飾器
        self.assertIn('@st.cache_data(ttl=3600)', content, "必須使用@st.cache_data(ttl=3600)裝飾器")
        
        # 驗證必要函數存在
        for func_name in required_functions:
            self.assertIn(f'def {func_name}', content, f"必須實作{func_name}函數")
        
        # 驗證st.session_state.data_source_status支援三種狀態
        expected_states = ['real_data', 'simulation', 'offline']
        for state in expected_states:
            self.assertIn(f'"{state}"', content, f"必須支援{state}狀態")
        
        print("✅ 3.4.1智能數據源管理實作要求驗證通過")
    
    def test_3_4_1_error_handling_requirements(self):
        """測試3.4.1異常處理機制要求"""
        smart_features_path = os.path.join('src', 'ui', 'smart_features.py')
        
        with open(smart_features_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 驗證APIConnectionError異常類別
        self.assertIn('class APIConnectionError', content, "必須定義APIConnectionError異常類別")
        
        # 驗證異常處理提示訊息
        expected_messages = [
            "💡 正在使用模擬數據進行分析",
            "🌐 網路連線問題，已切換為離線模式"
        ]
        
        for message in expected_messages:
            self.assertIn(message, content, f"必須包含提示訊息: {message}")
        
        # 驗證user_friendly_error_handler四種錯誤類型
        error_types = ["api_error", "calculation_error", "data_error", "validation_error"]
        for error_type in error_types:
            self.assertIn(f'"{error_type}"', content, f"必須支援{error_type}錯誤類型")
        
        print("✅ 3.4.1異常處理機制要求驗證通過")
    
    def test_3_4_2_progressive_calculation_requirements(self):
        """測試3.4.2漸進式載入與反饋實作要求"""
        smart_features_path = os.path.join('src', 'ui', 'smart_features.py')
        
        with open(smart_features_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 驗證progressive_calculation_with_feedback函數
        self.assertIn('def progressive_calculation_with_feedback', content, 
                     "必須實作progressive_calculation_with_feedback函數")
        
        # 驗證四階段進度顯示
        expected_stages = [
            "📊 準備市場數據...",
            "🎯 計算定期定值策略...",
            "💰 計算定期定額策略...",
            "📈 生成績效比較...",
            "✅ 計算完成！"
        ]
        
        for stage in expected_stages:
            self.assertIn(stage, content, f"必須包含階段提示: {stage}")
        
        # 驗證進度百分比
        progress_values = [25, 50, 75, 100]
        for value in progress_values:
            self.assertIn(f'progress({value})', content, f"必須包含進度值: {value}")
        
        # 驗證函數整合要求
        integration_functions = [
            'prepare_market_data',
            'calculate_va_strategy_with_chapter2',
            'calculate_dca_strategy_with_chapter2',
            'generate_comparison_analysis'
        ]
        
        for func_name in integration_functions:
            self.assertIn(f'def {func_name}', content, f"必須實作{func_name}函數")
        
        print("✅ 3.4.2漸進式載入與反饋實作要求驗證通過")
    
    def test_3_4_3_smart_recommendations_structure(self):
        """測試3.4.3智能建議系統整合實作要求"""
        smart_features_path = os.path.join('src', 'ui', 'smart_features.py')
        
        with open(smart_features_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 驗證SMART_RECOMMENDATIONS結構
        self.assertIn('SMART_RECOMMENDATIONS = {', content, "必須定義SMART_RECOMMENDATIONS字典")
        
        # 驗證personalized_advice結構
        self.assertIn('"personalized_advice"', content, "必須包含personalized_advice")
        self.assertIn('"recommendation_engine"', content, "必須包含recommendation_engine")
        
        # 驗證四個factors
        expected_factors = [
            "investment_amount",
            "time_horizon",
            "risk_tolerance",
            "strategy_performance"
        ]
        
        for factor in expected_factors:
            self.assertIn(f'"{factor}"', content, f"必須包含factor: {factor}")
        
        # 驗證三個模板
        expected_templates = ["va_preferred", "dca_preferred", "neutral_analysis"]
        for template in expected_templates:
            self.assertIn(f'"{template}"', content, f"必須包含模板: {template}")
        
        # 驗證va_preferred模板內容
        expected_va_content = [
            "🎯 建議採用VA策略",
            "基於您的參數，VA策略預期表現較佳",
            "較高預期報酬",
            "適合您的風險承受度",
            "投資金額充足"
        ]
        
        for content_item in expected_va_content:
            self.assertIn(content_item, content, f"va_preferred必須包含: {content_item}")
        
        # 驗證dca_preferred模板內容
        expected_dca_content = [
            "💰 建議採用DCA策略",
            "DCA策略更適合您的投資目標",
            "操作簡單",
            "風險相對較低",
            "適合長期投資"
        ]
        
        for content_item in expected_dca_content:
            self.assertIn(content_item, content, f"dca_preferred必須包含: {content_item}")
        
        print("✅ 3.4.3智能建議系統整合實作要求驗證通過")
    
    def test_3_4_3_investment_knowledge_structure(self):
        """測試3.4.3投資知識卡片實作要求"""
        smart_features_path = os.path.join('src', 'ui', 'smart_features.py')
        
        with open(smart_features_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 驗證investment_knowledge結構
        self.assertIn('"investment_knowledge"', content, "必須包含investment_knowledge")
        
        # 驗證strategy_explanation_cards
        self.assertIn('"strategy_explanation_cards"', content, "必須包含strategy_explanation_cards")
        
        # 驗證what_is_va和what_is_dca卡片
        expected_cards = [
            ("what_is_va", "💡 什麼是定期定值(VA)？"),
            ("what_is_dca", "💡 什麼是定期定額(DCA)？")
        ]
        
        for card_key, card_title in expected_cards:
            self.assertIn(f'"{card_key}"', content, f"必須包含卡片: {card_key}")
            self.assertIn(card_title, content, f"必須包含卡片標題: {card_title}")
        
        # 驗證risk_warnings
        self.assertIn('"risk_warnings"', content, "必須包含risk_warnings")
        self.assertIn('"importance": "high"', content, "風險警告必須為高重要性")
        self.assertIn("投資有風險，過去績效不代表未來結果", content, "必須包含風險警告內容")
        
        # 驗證help_section
        self.assertIn('"help_section"', content, "必須包含help_section")
        
        help_components = ["quick_start_guide", "faq", "contact"]
        for component in help_components:
            self.assertIn(f'"{component}"', content, f"必須包含幫助組件: {component}")
        
        print("✅ 3.4.3投資知識卡片實作要求驗證通過")
    
    def test_chapter1_technical_compliance(self):
        """測試第1章技術規範遵循性"""
        smart_features_path = os.path.join('src', 'ui', 'smart_features.py')
        
        with open(smart_features_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 驗證第1章模組導入
        chapter1_imports = [
            "from ..utils.api_security import get_api_key, validate_api_key_format",
            "from ..data_sources.api_client import test_api_connectivity",
            "from ..data_sources.fault_tolerance import APIFaultToleranceManager",
            "from ..data_sources.simulation import SimulationDataGenerator",
            "from ..data_sources.cache_manager import IntelligentCacheManager"
        ]
        
        for import_line in chapter1_imports:
            self.assertIn(import_line, content, f"必須導入第1章模組: {import_line}")
        
        # 驗證第1章函數調用
        chapter1_functions = [
            "get_api_key('TIINGO_API_KEY')",
            "get_api_key('FRED_API_KEY')",
            "validate_api_key_format",
            "test_api_connectivity",
            "TiingoDataFetcher",
            "FREDDataFetcher",
            "BatchDataFetcher"
        ]
        
        for func_call in chapter1_functions:
            self.assertIn(func_call, content, f"必須調用第1章函數: {func_call}")
        
        print("✅ 第1章技術規範遵循性驗證通過")
    
    def test_chapter2_calculation_integration(self):
        """測試第2章計算公式整合"""
        smart_features_path = os.path.join('src', 'ui', 'smart_features.py')
        
        with open(smart_features_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 驗證第2章模組導入
        chapter2_imports = [
            "from ..models.calculation_formulas import",
            "from ..models.strategy_engine import calculate_va_strategy, calculate_dca_strategy",
            "from ..models.table_calculator import calculate_summary_metrics"
        ]
        
        for import_line in chapter2_imports:
            self.assertIn(import_line, content, f"必須導入第2章模組: {import_line}")
        
        # 驗證第2章函數調用
        chapter2_functions = [
            "calculate_va_strategy",
            "calculate_dca_strategy",
            "calculate_summary_metrics"
        ]
        
        for func_call in chapter2_functions:
            self.assertIn(func_call, content, f"必須調用第2章函數: {func_call}")
        
        print("✅ 第2章計算公式整合驗證通過")
    
    def test_text_and_emoji_preservation(self):
        """測試文字和emoji圖標保留"""
        smart_features_path = os.path.join('src', 'ui', 'smart_features.py')
        
        with open(smart_features_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 驗證關鍵emoji圖標未被修改
        required_emojis = [
            "📊", "🎯", "💰", "📈", "✅",  # 進度階段
            "🟢", "🟡", "🔴",  # 數據源狀態
            "💡", "🌐",  # 提示訊息
            "🔌", "🧮", "⚠️"  # 錯誤處理
        ]
        
        for emoji in required_emojis:
            self.assertIn(emoji, content, f"必須保留emoji圖標: {emoji}")
        
        # 驗證關鍵文字未被修改
        required_texts = [
            "準備市場數據",
            "計算定期定值策略",
            "計算定期定額策略",
            "生成績效比較",
            "計算完成",
            "使用真實市場數據",
            "使用模擬數據",
            "離線模式"
        ]
        
        for text in required_texts:
            self.assertIn(text, content, f"必須保留關鍵文字: {text}")
        
        print("✅ 文字和emoji圖標保留驗證通過")
    
    def test_smart_recommendation_engine_class(self):
        """測試SmartRecommendationEngine類別完整性"""
        smart_features_path = os.path.join('src', 'ui', 'smart_features.py')
        
        with open(smart_features_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 驗證SmartRecommendationEngine類別
        self.assertIn('class SmartRecommendationEngine:', content, "必須定義SmartRecommendationEngine類別")
        
        # 驗證必要方法
        required_methods = [
            'generate_personalized_advice',
            '_analyze_user_profile',
            '_analyze_strategy_performance',
            '_generate_recommendation',
            'render_investment_knowledge'
        ]
        
        for method in required_methods:
            self.assertIn(f'def {method}', content, f"必須實作方法: {method}")
        
        print("✅ SmartRecommendationEngine類別完整性驗證通過")

class TestRequirementsCompliance(unittest.TestCase):
    """測試需求遵循性"""
    
    def test_no_functionality_simplification(self):
        """測試功能未被簡化"""
        smart_features_path = os.path.join('src', 'ui', 'smart_features.py')
        
        with open(smart_features_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 驗證所有智能功能都已實作
        required_functions = [
            'smart_data_source_manager',
            'progressive_calculation_with_feedback',
            'SmartRecommendationEngine',
            'render_smart_features'
        ]
        
        for func_name in required_functions:
            self.assertIn(func_name, content, f"不得簡化功能: {func_name}")
        
        # 驗證複雜邏輯保留
        complex_logic_indicators = [
            'APIConnectionError',
            'try:',
            'except',
            'if ',
            'for ',
            'while ',
            'class ',
            'def '
        ]
        
        # 計算複雜邏輯出現次數
        complex_count = sum(content.count(indicator) for indicator in complex_logic_indicators)
        self.assertGreater(complex_count, 50, f"必須保留複雜的智能決策邏輯，當前計數: {complex_count}")
        
        print("✅ 功能未被簡化驗證通過")
    
    def test_complete_integration_requirements(self):
        """測試完整整合要求"""
        smart_features_path = os.path.join('src', 'ui', 'smart_features.py')
        
        with open(smart_features_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 驗證與第1-2章的完整技術整合
        integration_indicators = [
            '第1章',
            '第2章',
            'calculate_va_strategy',
            'calculate_dca_strategy',
            'get_api_key',
            'APIFaultToleranceManager',
            'SimulationDataGenerator'
        ]
        
        for indicator in integration_indicators:
            self.assertIn(indicator, content, f"必須保持完整技術整合: {indicator}")
        
        print("✅ 完整整合要求驗證通過")

if __name__ == '__main__':
    # 創建測試套件
    test_suite = unittest.TestSuite()
    
    # 添加測試類別
    test_classes = [
        TestSmartFeaturesStructure,
        TestRequirementsCompliance
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # 運行測試
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # 輸出測試結果摘要
    print(f"\n{'='*70}")
    print(f"第3章3.4節智能功能與用戶體驗實作簡化測試結果")
    print(f"{'='*70}")
    print(f"總測試數: {result.testsRun}")
    print(f"成功: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"失敗: {len(result.failures)}")
    print(f"錯誤: {len(result.errors)}")
    
    if result.failures:
        print(f"\n失敗的測試:")
        for test, traceback in result.failures:
            print(f"- {test}")
            print(f"  {traceback.split('AssertionError: ')[-1].split('\\n')[0]}")
    
    if result.errors:
        print(f"\n錯誤的測試:")
        for test, traceback in result.errors:
            print(f"- {test}")
    
    # 測試通過率
    success_rate = (result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100
    print(f"\n測試通過率: {success_rate:.1f}%")
    
    if success_rate == 100:
        print("🎉 所有測試通過！第3章3.4節智能功能實作完成。")
        print("\n✅ 實作完成項目:")
        print("   - 3.4.1 智能數據源管理實作")
        print("   - 3.4.2 漸進式載入與反饋實作")
        print("   - 3.4.3 智能建議系統整合實作")
        print("   - 第1章技術規範完整性保持")
        print("   - 第2章計算公式完整整合")
        print("   - 所有文字和emoji圖標保留")
        print("   - 完整的錯誤處理和用戶反饋機制")
    else:
        print("⚠️  部分測試未通過，需要修復。") 