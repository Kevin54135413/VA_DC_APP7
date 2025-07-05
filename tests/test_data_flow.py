"""
第4.4節 - 簡化資料流整合測試套件

測試所有核心函數和資料流程管道的功能
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os

# 添加src目錄到Python路徑
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from core.data_flow import (
    basic_error_recovery,
    fetch_historical_data_simple,
    generate_simulation_data_simple,
    SimpleDataFlowPipeline,
    DataFlowConfig,
    create_simple_data_flow_pipeline,
    validate_basic_parameters,
    get_market_data_simple
)

class TestBasicErrorRecovery(unittest.TestCase):
    """測試基本錯誤恢復機制"""
    
    def setUp(self):
        """設置測試環境"""
        self.mock_streamlit_patcher = patch('core.data_flow.st')
        self.mock_st = self.mock_streamlit_patcher.start()
        
    def tearDown(self):
        """清理測試環境"""
        self.mock_streamlit_patcher.stop()
    
    def test_basic_error_recovery_function_exists(self):
        """測試basic_error_recovery函數是否存在"""
        self.assertTrue(callable(basic_error_recovery))
    
    def test_basic_error_recovery_success_with_historical_data(self):
        """測試使用歷史數據成功恢復"""
        mock_data = {
            'stock_data': [{'date': '2024-01-01', 'adjClose': 400.0}],
            'bond_data': [{'date': '2024-01-01', 'value': '4.0'}],
            'metadata': {'data_source': 'historical_api'}
        }
        
        with patch('core.data_flow.fetch_historical_data_simple', return_value=mock_data):
            result = basic_error_recovery()
            
            self.assertIsNotNone(result)
            self.assertEqual(result['metadata']['data_source'], 'historical_api')
            self.mock_st.info.assert_called()
            self.mock_st.success.assert_called()
    
    def test_basic_error_recovery_fallback_to_simulation(self):
        """測試回退到模擬數據"""
        mock_simulation_data = {
            'stock_data': [{'date': '2024-01-01', 'adjClose': 400.0}],
            'bond_data': [{'date': '2024-01-01', 'value': '4.0'}],
            'metadata': {'data_source': 'simulation'}
        }
        
        with patch('core.data_flow.fetch_historical_data_simple', return_value=None), \
             patch('core.data_flow.generate_simulation_data_simple', return_value=mock_simulation_data):
            
            result = basic_error_recovery()
            
            self.assertIsNotNone(result)
            self.assertEqual(result['metadata']['data_source'], 'simulation')
            # 檢查是否有info和success被調用
            self.assertTrue(self.mock_st.info.called)
            self.assertTrue(self.mock_st.success.called)
    
    def test_basic_error_recovery_all_methods_fail(self):
        """測試所有方法都失敗的情況"""
        with patch('core.data_flow.fetch_historical_data_simple', return_value=None), \
             patch('core.data_flow.generate_simulation_data_simple', return_value=None):
            
            result = basic_error_recovery()
            
            self.assertIsNone(result)
            self.mock_st.error.assert_called()
    
    def test_basic_error_recovery_exception_handling(self):
        """測試異常處理"""
        with patch('core.data_flow.fetch_historical_data_simple', side_effect=Exception("API Error")), \
             patch('core.data_flow.generate_simulation_data_simple', return_value=None):
            
            result = basic_error_recovery()
            
            self.assertIsNone(result)
            self.mock_st.warning.assert_called()
            self.mock_st.error.assert_called()

class TestDataFetchingFunctions(unittest.TestCase):
    """測試數據獲取函數"""
    
    def test_fetch_historical_data_simple_function_exists(self):
        """測試fetch_historical_data_simple函數是否存在"""
        self.assertTrue(callable(fetch_historical_data_simple))
    
    def test_fetch_historical_data_simple_success(self):
        """測試歷史數據獲取成功"""
        mock_stock_data = [{'date': '2024-01-01', 'adjClose': 400.0}]
        mock_bond_data = [{'date': '2024-01-01', 'value': '4.0'}]
        
        with patch('core.data_flow.TiingoDataFetcher') as mock_tiingo, \
             patch('core.data_flow.FREDDataFetcher') as mock_fred:
            
            mock_tiingo.return_value.fetch_stock_data.return_value = mock_stock_data
            mock_fred.return_value.fetch_yield_data.return_value = mock_bond_data
            
            result = fetch_historical_data_simple()
            
            self.assertIsNotNone(result)
            self.assertEqual(result['stock_data'], mock_stock_data)
            self.assertEqual(result['bond_data'], mock_bond_data)
            self.assertEqual(result['metadata']['data_source'], 'historical_api')
    
    def test_fetch_historical_data_simple_failure(self):
        """測試歷史數據獲取失敗"""
        with patch('core.data_flow.TiingoDataFetcher', side_effect=Exception("API Error")):
            result = fetch_historical_data_simple()
            self.assertIsNone(result)
    
    def test_generate_simulation_data_simple_function_exists(self):
        """測試generate_simulation_data_simple函數是否存在"""
        self.assertTrue(callable(generate_simulation_data_simple))
    
    def test_generate_simulation_data_simple_success(self):
        """測試模擬數據生成成功"""
        mock_stock_data = [{'date': '2024-01-01', 'adjClose': 400.0}]
        mock_bond_data = [{'date': '2024-01-01', 'value': '4.0'}]
        
        with patch('core.data_flow.SimulationDataGenerator') as mock_simulator:
            mock_instance = mock_simulator.return_value
            mock_instance.generate_stock_data.return_value = mock_stock_data
            mock_instance.generate_yield_data.return_value = mock_bond_data
            
            result = generate_simulation_data_simple()
            
            self.assertIsNotNone(result)
            self.assertEqual(result['stock_data'], mock_stock_data)
            self.assertEqual(result['bond_data'], mock_bond_data)
            self.assertEqual(result['metadata']['data_source'], 'simulation')
    
    def test_generate_simulation_data_simple_failure(self):
        """測試模擬數據生成失敗"""
        with patch('core.data_flow.SimulationDataGenerator', side_effect=Exception("Simulation Error")):
            result = generate_simulation_data_simple()
            self.assertIsNone(result)

class TestDataFlowConfig(unittest.TestCase):
    """測試資料流程配置"""
    
    def test_data_flow_config_default_values(self):
        """測試預設配置值"""
        config = DataFlowConfig()
        
        self.assertTrue(config.enable_api_fallback)
        self.assertTrue(config.enable_simulation_fallback)
        self.assertEqual(config.max_retry_attempts, 2)
        self.assertTrue(config.data_validation_enabled)
        self.assertTrue(config.streamlit_progress_enabled)
    
    def test_data_flow_config_custom_values(self):
        """測試自定義配置值"""
        config = DataFlowConfig(
            enable_api_fallback=False,
            enable_simulation_fallback=False,
            max_retry_attempts=5,
            data_validation_enabled=False,
            streamlit_progress_enabled=False
        )
        
        self.assertFalse(config.enable_api_fallback)
        self.assertFalse(config.enable_simulation_fallback)
        self.assertEqual(config.max_retry_attempts, 5)
        self.assertFalse(config.data_validation_enabled)
        self.assertFalse(config.streamlit_progress_enabled)

class TestSimpleDataFlowPipeline(unittest.TestCase):
    """測試簡化資料流程管道"""
    
    def setUp(self):
        """設置測試環境"""
        self.mock_streamlit_patcher = patch('core.data_flow.st')
        self.mock_st = self.mock_streamlit_patcher.start()
        
        # 創建管道實例
        self.pipeline = SimpleDataFlowPipeline()
        
        # 模擬用戶參數
        self.valid_parameters = {
            'initial_investment': 100000,
            'annual_investment': 120000,
            'investment_years': 10,
            'stock_ratio': 80,
            'annual_growth_rate': 8.0,
            'annual_inflation_rate': 3.0,
            'frequency': 'Monthly'
        }
    
    def tearDown(self):
        """清理測試環境"""
        self.mock_streamlit_patcher.stop()
    
    def test_pipeline_initialization(self):
        """測試管道初始化"""
        self.assertIsNotNone(self.pipeline)
        self.assertIsNotNone(self.pipeline.config)
        self.assertIsNotNone(self.pipeline.results_manager)
    
    def test_pipeline_initialization_with_config(self):
        """測試帶配置的管道初始化"""
        config = DataFlowConfig(streamlit_progress_enabled=False)
        pipeline = SimpleDataFlowPipeline(config)
        
        self.assertFalse(pipeline.config.streamlit_progress_enabled)
    
    def test_validate_user_input_success(self):
        """測試用戶輸入驗證成功"""
        result = self.pipeline._validate_user_input(self.valid_parameters)
        self.assertTrue(result)
    
    def test_validate_user_input_missing_field(self):
        """測試缺少必要欄位"""
        invalid_params = self.valid_parameters.copy()
        del invalid_params['initial_investment']
        
        result = self.pipeline._validate_user_input(invalid_params)
        self.assertFalse(result)
    
    def test_validate_user_input_invalid_values(self):
        """測試無效數值"""
        test_cases = [
            {'initial_investment': -1000},  # 負數
            {'annual_investment': 0},       # 零
            {'investment_years': 0},        # 零
            {'investment_years': 51},       # 超出範圍
            {'stock_ratio': -10},           # 負數
            {'stock_ratio': 110}            # 超出範圍
        ]
        
        for invalid_update in test_cases:
            invalid_params = self.valid_parameters.copy()
            invalid_params.update(invalid_update)
            
            result = self.pipeline._validate_user_input(invalid_params)
            self.assertFalse(result, f"驗證應該失敗: {invalid_update}")
    
    def test_fetch_market_data_success(self):
        """測試市場數據獲取成功"""
        mock_data = {
            'stock_data': [{'date': '2024-01-01', 'adjClose': 400.0}],
            'bond_data': [{'date': '2024-01-01', 'value': '4.0'}],
            'metadata': {'data_source': 'simulation'}
        }
        
        with patch('core.data_flow.basic_error_recovery', return_value=mock_data):
            result = self.pipeline._fetch_market_data()
            
            self.assertIsNotNone(result)
            self.assertEqual(result['metadata']['data_source'], 'simulation')
    
    def test_fetch_market_data_failure(self):
        """測試市場數據獲取失敗"""
        with patch('core.data_flow.basic_error_recovery', return_value=None):
            result = self.pipeline._fetch_market_data()
            self.assertIsNone(result)
    
    def test_convert_market_data_to_dataframe_list_format(self):
        """測試市場數據轉換（列表格式）"""
        market_data = {
            'stock_data': [
                {'date': '2024-01-01', 'adjClose': 400.0},
                {'date': '2024-01-02', 'adjClose': 405.0}
            ],
            'bond_data': [
                {'date': '2024-01-01', 'value': '4.0'},
                {'date': '2024-01-02', 'value': '4.1'}
            ]
        }
        
        result = self.pipeline._convert_market_data_to_dataframe(market_data)
        
        self.assertIsInstance(result, pd.DataFrame)
        self.assertTrue(len(result) > 0)
        self.assertIn('SPY_Price_Origin', result.columns)
        self.assertIn('Bond_Price_Origin', result.columns)
    
    def test_convert_market_data_to_dataframe_dict_format(self):
        """測試市場數據轉換（字典格式）"""
        market_data = {
            'stock_data': {
                'dates': ['2024-01-01', '2024-01-02'],
                'prices': [400.0, 405.0]
            },
            'bond_data': {
                'dates': ['2024-01-01', '2024-01-02'],
                'prices': [4.0, 4.1]
            }
        }
        
        result = self.pipeline._convert_market_data_to_dataframe(market_data)
        
        self.assertIsInstance(result, pd.DataFrame)
        self.assertTrue(len(result) > 0)
    
    def test_convert_market_data_to_dataframe_error_handling(self):
        """測試市場數據轉換錯誤處理"""
        invalid_data = {'invalid': 'data'}
        
        result = self.pipeline._convert_market_data_to_dataframe(invalid_data)
        
        self.assertIsInstance(result, pd.DataFrame)
        self.assertTrue(len(result) > 0)  # 應該返回預設數據
    
    def test_create_default_market_data(self):
        """測試創建預設市場數據"""
        result = self.pipeline._create_default_market_data()
        
        self.assertIsInstance(result, pd.DataFrame)
        self.assertTrue(len(result) > 0)
        self.assertIn('SPY_Price_Origin', result.columns)
        self.assertIn('Bond_Price_Origin', result.columns)
    
    def test_calculate_strategies_success(self):
        """測試策略計算成功"""
        mock_market_data = {
            'stock_data': [{'date': '2024-01-01', 'adjClose': 400.0}],
            'bond_data': [{'date': '2024-01-01', 'value': '4.0'}],
            'metadata': {'data_source': 'simulation'}
        }
        
        mock_va_results = pd.DataFrame({
            'Cum_Value': [100000, 110000, 120000],
            'Period': [1, 2, 3]
        })
        
        mock_dca_results = pd.DataFrame({
            'Cum_Value': [100000, 108000, 115000],
            'Period': [1, 2, 3]
        })
        
        mock_summary = pd.DataFrame({
            'Metric': ['Final Value', 'Total Return'],
            'VA': [120000, 20.0],
            'DCA': [115000, 15.0]
        })
        
        with patch('core.data_flow.calculate_va_strategy', return_value=mock_va_results), \
             patch('core.data_flow.calculate_dca_strategy', return_value=mock_dca_results), \
             patch('core.data_flow.calculate_summary_metrics', return_value=mock_summary):
            
            result = self.pipeline._calculate_strategies(self.valid_parameters, mock_market_data)
            
            self.assertIsNotNone(result)
            self.assertIn('va_results', result)
            self.assertIn('dca_results', result)
            self.assertIn('summary_metrics', result)
    
    def test_calculate_strategies_failure(self):
        """測試策略計算失敗"""
        mock_market_data = {
            'stock_data': [{'date': '2024-01-01', 'adjClose': 400.0}],
            'bond_data': [{'date': '2024-01-01', 'value': '4.0'}]
        }
        
        with patch('core.data_flow.calculate_va_strategy', side_effect=Exception("Calculation Error")):
            result = self.pipeline._calculate_strategies(self.valid_parameters, mock_market_data)
            self.assertIsNone(result)
    
    def test_prepare_display_data(self):
        """測試準備顯示數據"""
        mock_results = {
            'va_results': pd.DataFrame({'Cum_Value': [100000, 110000, 120000]}),
            'dca_results': pd.DataFrame({'Cum_Value': [100000, 108000, 115000]}),
            'summary_metrics': pd.DataFrame({'Metric': ['Test'], 'Value': [100]})
        }
        
        result = self.pipeline._prepare_display_data(mock_results)
        
        self.assertIn('va_final_value', result)
        self.assertIn('dca_final_value', result)
        self.assertIn('difference', result)
        self.assertIn('difference_percentage', result)
        self.assertEqual(result['va_final_value'], 120000)
        self.assertEqual(result['dca_final_value'], 115000)
    
    def test_display_basic_metrics(self):
        """測試顯示基本指標"""
        mock_results = {
            'va_results': pd.DataFrame({'Cum_Value': [100000, 110000, 120000]}),
            'dca_results': pd.DataFrame({'Cum_Value': [100000, 108000, 115000]})
        }
        
        # 模擬streamlit的columns方法，支持context manager
        mock_col1 = Mock()
        mock_col1.__enter__ = Mock(return_value=mock_col1)
        mock_col1.__exit__ = Mock(return_value=None)
        mock_col2 = Mock()
        mock_col2.__enter__ = Mock(return_value=mock_col2)
        mock_col2.__exit__ = Mock(return_value=None)
        mock_col3 = Mock()
        mock_col3.__enter__ = Mock(return_value=mock_col3)
        mock_col3.__exit__ = Mock(return_value=None)
        self.mock_st.columns.return_value = [mock_col1, mock_col2, mock_col3]
        
        # 測試不應該拋出異常
        try:
            self.pipeline._display_basic_metrics(mock_results)
        except Exception as e:
            self.fail(f"_display_basic_metrics raised {e} unexpectedly!")
    
    def test_display_charts(self):
        """測試顯示圖表"""
        mock_results = {
            'va_results': pd.DataFrame({'Cum_Value': [100000, 110000, 120000]}),
            'dca_results': pd.DataFrame({'Cum_Value': [100000, 108000, 115000]})
        }
        
        # 測試不應該拋出異常
        try:
            self.pipeline._display_charts(mock_results)
        except Exception as e:
            self.fail(f"_display_charts raised {e} unexpectedly!")
    
    def test_display_detailed_tables(self):
        """測試顯示詳細表格"""
        mock_results = {
            'va_results': pd.DataFrame({'Cum_Value': [100000, 110000, 120000]}),
            'dca_results': pd.DataFrame({'Cum_Value': [100000, 108000, 115000]}),
            'summary_metrics': pd.DataFrame({'Metric': ['Test'], 'Value': [100]})
        }
        
        # 模擬streamlit的tabs方法，支持context manager
        mock_tab1 = Mock()
        mock_tab1.__enter__ = Mock(return_value=mock_tab1)
        mock_tab1.__exit__ = Mock(return_value=None)
        mock_tab2 = Mock()
        mock_tab2.__enter__ = Mock(return_value=mock_tab2)
        mock_tab2.__exit__ = Mock(return_value=None)
        mock_tab3 = Mock()
        mock_tab3.__enter__ = Mock(return_value=mock_tab3)
        mock_tab3.__exit__ = Mock(return_value=None)
        self.mock_st.tabs.return_value = [mock_tab1, mock_tab2, mock_tab3]
        
        # 測試不應該拋出異常
        try:
            self.pipeline._display_detailed_tables(mock_results)
        except Exception as e:
            self.fail(f"_display_detailed_tables raised {e} unexpectedly!")
    
    def test_execute_pipeline_success(self):
        """測試完整管道執行成功"""
        mock_market_data = {
            'stock_data': [{'date': '2024-01-01', 'adjClose': 400.0}],
            'bond_data': [{'date': '2024-01-01', 'value': '4.0'}],
            'metadata': {'data_source': 'simulation'}
        }
        
        mock_va_results = pd.DataFrame({
            'Cum_Value': [100000, 110000, 120000],
            'Period': [1, 2, 3]
        })
        
        mock_dca_results = pd.DataFrame({
            'Cum_Value': [100000, 108000, 115000],
            'Period': [1, 2, 3]
        })
        
        mock_summary = pd.DataFrame({
            'Metric': ['Final Value'],
            'VA': [120000],
            'DCA': [115000]
        })
        
        with patch.object(self.pipeline, '_fetch_market_data', return_value=mock_market_data), \
             patch('core.data_flow.calculate_va_strategy', return_value=mock_va_results), \
             patch('core.data_flow.calculate_dca_strategy', return_value=mock_dca_results), \
             patch('core.data_flow.calculate_summary_metrics', return_value=mock_summary):
            
            result = self.pipeline.execute_pipeline(self.valid_parameters)
            
            self.assertIsNotNone(result)
    
    def test_execute_pipeline_validation_failure(self):
        """測試管道執行驗證失敗"""
        invalid_params = {'invalid': 'params'}
        
        result = self.pipeline.execute_pipeline(invalid_params)
        self.assertIsNone(result)
    
    def test_execute_pipeline_data_fetch_failure(self):
        """測試管道執行數據獲取失敗"""
        with patch.object(self.pipeline, '_fetch_market_data', return_value=None):
            result = self.pipeline.execute_pipeline(self.valid_parameters)
            self.assertIsNone(result)
    
    def test_execute_pipeline_calculation_failure(self):
        """測試管道執行計算失敗"""
        mock_market_data = {
            'stock_data': [{'date': '2024-01-01', 'adjClose': 400.0}],
            'bond_data': [{'date': '2024-01-01', 'value': '4.0'}]
        }
        
        with patch.object(self.pipeline, '_fetch_market_data', return_value=mock_market_data), \
             patch.object(self.pipeline, '_calculate_strategies', return_value=None):
            
            result = self.pipeline.execute_pipeline(self.valid_parameters)
            self.assertIsNone(result)

class TestUtilityFunctions(unittest.TestCase):
    """測試便利函數"""
    
    def test_create_simple_data_flow_pipeline(self):
        """測試創建簡化資料流程管道"""
        pipeline = create_simple_data_flow_pipeline()
        
        self.assertIsInstance(pipeline, SimpleDataFlowPipeline)
        self.assertIsNotNone(pipeline.config)
    
    def test_create_simple_data_flow_pipeline_with_config(self):
        """測試帶配置創建管道"""
        config = DataFlowConfig(streamlit_progress_enabled=False)
        pipeline = create_simple_data_flow_pipeline(config)
        
        self.assertFalse(pipeline.config.streamlit_progress_enabled)
    
    def test_validate_basic_parameters(self):
        """測試基本參數驗證函數"""
        valid_params = {
            'initial_investment': 100000,
            'annual_investment': 120000,
            'investment_years': 10,
            'stock_ratio': 80,
            'annual_growth_rate': 8.0,
            'annual_inflation_rate': 3.0
        }
        
        with patch('core.data_flow.st'):
            result = validate_basic_parameters(valid_params)
            self.assertTrue(result)
    
    def test_get_market_data_simple(self):
        """測試簡化市場數據獲取函數"""
        mock_data = {
            'stock_data': [{'date': '2024-01-01', 'adjClose': 400.0}],
            'bond_data': [{'date': '2024-01-01', 'value': '4.0'}],
            'metadata': {'data_source': 'simulation'}
        }
        
        with patch('core.data_flow.basic_error_recovery', return_value=mock_data):
            result = get_market_data_simple({})
            
            self.assertIsNotNone(result)
            self.assertEqual(result['metadata']['data_source'], 'simulation')

class TestFunctionSignatures(unittest.TestCase):
    """測試函數簽名符合需求文件規格"""
    
    def test_basic_error_recovery_signature(self):
        """測試basic_error_recovery函數簽名"""
        import inspect
        
        sig = inspect.signature(basic_error_recovery)
        
        # 檢查返回類型註解
        self.assertTrue(hasattr(basic_error_recovery, '__annotations__'))
        
        # 檢查無參數（按照需求文件）
        self.assertEqual(len(sig.parameters), 0)
    
    def test_fetch_historical_data_simple_signature(self):
        """測試fetch_historical_data_simple函數簽名"""
        import inspect
        
        sig = inspect.signature(fetch_historical_data_simple)
        
        # 檢查返回類型註解
        self.assertTrue(hasattr(fetch_historical_data_simple, '__annotations__'))
        
        # 檢查無參數
        self.assertEqual(len(sig.parameters), 0)
    
    def test_generate_simulation_data_simple_signature(self):
        """測試generate_simulation_data_simple函數簽名"""
        import inspect
        
        sig = inspect.signature(generate_simulation_data_simple)
        
        # 檢查返回類型註解
        self.assertTrue(hasattr(generate_simulation_data_simple, '__annotations__'))
        
        # 檢查無參數
        self.assertEqual(len(sig.parameters), 0)

class TestIntegrationWithOtherChapters(unittest.TestCase):
    """測試與其他章節的整合"""
    
    def test_integration_with_chapter1_data_sources(self):
        """測試與第1章數據源的整合"""
        # 檢查是否可以正確導入第1章模組
        try:
            from core.data_flow import SimulationDataGenerator, TiingoDataFetcher, FREDDataFetcher
            self.assertTrue(True)
        except ImportError as e:
            self.fail(f"無法導入第1章模組: {e}")
    
    def test_integration_with_chapter2_calculations(self):
        """測試與第2章計算引擎的整合"""
        # 檢查是否可以正確導入第2章模組
        try:
            from core.data_flow import calculate_va_strategy, calculate_dca_strategy, calculate_summary_metrics
            self.assertTrue(True)
        except ImportError as e:
            self.fail(f"無法導入第2章模組: {e}")
    
    def test_integration_with_chapter3_ui(self):
        """測試與第3章UI組件的整合"""
        # 檢查是否可以正確導入第3章模組
        try:
            from core.data_flow import ResultsDisplayManager
            self.assertTrue(True)
        except ImportError as e:
            self.fail(f"無法導入第3章模組: {e}")
    
    def test_data_flow_pipeline_integration(self):
        """測試資料流程管道的整合功能"""
        pipeline = SimpleDataFlowPipeline()
        
        # 檢查管道是否正確初始化所有組件
        self.assertIsNotNone(pipeline.config)
        self.assertIsNotNone(pipeline.results_manager)
        
        # 檢查管道是否具有所有必要的方法
        required_methods = [
            '_validate_user_input',
            '_fetch_market_data',
            '_calculate_strategies',
            '_display_results',
            'execute_pipeline'
        ]
        
        for method in required_methods:
            self.assertTrue(hasattr(pipeline, method), f"管道缺少方法: {method}")
            self.assertTrue(callable(getattr(pipeline, method)), f"方法不可調用: {method}")

if __name__ == '__main__':
    # 創建測試套件
    test_suite = unittest.TestSuite()
    
    # 添加所有測試類別
    test_classes = [
        TestBasicErrorRecovery,
        TestDataFetchingFunctions,
        TestDataFlowConfig,
        TestSimpleDataFlowPipeline,
        TestUtilityFunctions,
        TestFunctionSignatures,
        TestIntegrationWithOtherChapters
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # 運行測試
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # 顯示測試結果摘要
    print(f"\n{'='*50}")
    print(f"測試總結")
    print(f"{'='*50}")
    print(f"執行測試: {result.testsRun}")
    print(f"失敗: {len(result.failures)}")
    print(f"錯誤: {len(result.errors)}")
    print(f"跳過: {len(result.skipped) if hasattr(result, 'skipped') else 0}")
    
    if result.failures:
        print(f"\n失敗的測試:")
        for test, traceback in result.failures:
            print(f"  - {test}: {traceback.split('AssertionError: ')[-1].split('\\n')[0]}")
    
    if result.errors:
        print(f"\n錯誤的測試:")
        for test, traceback in result.errors:
            print(f"  - {test}: {traceback.split('\\n')[-2]}")
    
    success_rate = (result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100
    print(f"\n測試成功率: {success_rate:.1f}%") 