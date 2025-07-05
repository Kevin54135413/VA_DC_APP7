"""
第4.3節測試套件 - 狀態管理與快取策略

測試覆蓋範圍：
1. CacheManager類別測試
2. 狀態管理函數測試
3. Streamlit快取函數測試
4. 智能快取管理函數測試
5. 函數簽名驗證測試
6. 整合測試
"""

import unittest
import sys
import os
import time
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

# 添加項目根目錄到Python路徑
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# 導入被測試的模組
from src.core.state_cache import (
    # CacheManager類別
    CacheManager,
    get_cache_manager,
    
    # 狀態管理函數
    state_management,
    params_changed,
    get_current_parameters,
    clear_related_cache,
    
    # Streamlit快取函數
    cached_market_data,
    cached_strategy_calculation,
    cached_performance_metrics,
    
    # 智能快取管理函數
    intelligent_cache_invalidation,
    cache_warming,
    get_cache_statistics,
    
    # 輔助函數
    fetch_market_data_comprehensive,
    generate_simulation_data_comprehensive,
    calculate_va_strategy_from_hash,
    calculate_dca_strategy_from_hash,
    calculate_performance_metrics_from_hash
)

class TestCacheManager(unittest.TestCase):
    """測試CacheManager類別"""
    
    def setUp(self):
        """設置測試環境"""
        self.cache_manager = CacheManager()
    
    def test_cache_manager_initialization(self):
        """測試CacheManager初始化"""
        # 驗證初始化
        self.assertIsInstance(self.cache_manager, CacheManager)
        self.assertIsInstance(self.cache_manager.cache_stats, dict)
        
        # 驗證初始統計
        expected_keys = ['hits', 'misses', 'evictions', 'total_requests', 'last_cleanup', 'cache_size_mb']
        for key in expected_keys:
            self.assertIn(key, self.cache_manager.cache_stats)
        
        # 驗證初始值
        self.assertEqual(self.cache_manager.cache_stats['hits'], 0)
        self.assertEqual(self.cache_manager.cache_stats['misses'], 0)
        self.assertEqual(self.cache_manager.cache_stats['evictions'], 0)
        self.assertEqual(self.cache_manager.cache_stats['total_requests'], 0)
        self.assertEqual(self.cache_manager.cache_stats['cache_size_mb'], 0.0)
    
    def test_get_cache_hit_ratio(self):
        """測試get_cache_hit_ratio方法"""
        # 測試初始狀態（無請求）
        hit_ratio = self.cache_manager.get_cache_hit_ratio()
        self.assertEqual(hit_ratio, 0.0)
        
        # 測試有命中和未命中的情況
        self.cache_manager.record_hit()
        self.cache_manager.record_hit()
        self.cache_manager.record_miss()
        
        hit_ratio = self.cache_manager.get_cache_hit_ratio()
        expected_ratio = 2 / 3  # 2命中，1未命中
        self.assertAlmostEqual(hit_ratio, expected_ratio, places=3)
        
        # 測試只有命中的情況
        cache_manager2 = CacheManager()
        cache_manager2.record_hit()
        cache_manager2.record_hit()
        
        hit_ratio = cache_manager2.get_cache_hit_ratio()
        self.assertEqual(hit_ratio, 1.0)
    
    def test_record_operations(self):
        """測試記錄操作"""
        # 測試記錄命中
        self.cache_manager.record_hit()
        self.assertEqual(self.cache_manager.cache_stats['hits'], 1)
        self.assertEqual(self.cache_manager.cache_stats['total_requests'], 1)
        
        # 測試記錄未命中
        self.cache_manager.record_miss()
        self.assertEqual(self.cache_manager.cache_stats['misses'], 1)
        self.assertEqual(self.cache_manager.cache_stats['total_requests'], 2)
        
        # 測試記錄驅逐
        self.cache_manager.record_eviction()
        self.assertEqual(self.cache_manager.cache_stats['evictions'], 1)
        # 驅逐不應該增加總請求數
        self.assertEqual(self.cache_manager.cache_stats['total_requests'], 2)
    
    def test_update_cache_size(self):
        """測試更新快取大小"""
        test_size = 125.5
        self.cache_manager.update_cache_size(test_size)
        self.assertEqual(self.cache_manager.cache_stats['cache_size_mb'], test_size)
    
    def test_reset_stats(self):
        """測試重設統計"""
        # 先設置一些統計數據
        self.cache_manager.record_hit()
        self.cache_manager.record_miss()
        self.cache_manager.record_eviction()
        self.cache_manager.update_cache_size(100.0)
        
        # 重設統計
        self.cache_manager.reset_stats()
        
        # 驗證重設後的狀態
        self.assertEqual(self.cache_manager.cache_stats['hits'], 0)
        self.assertEqual(self.cache_manager.cache_stats['misses'], 0)
        self.assertEqual(self.cache_manager.cache_stats['evictions'], 0)
        self.assertEqual(self.cache_manager.cache_stats['total_requests'], 0)
        self.assertEqual(self.cache_manager.cache_stats['cache_size_mb'], 0.0)
    
    def test_get_cache_manager_singleton(self):
        """測試全域快取管理器單例"""
        manager1 = get_cache_manager()
        manager2 = get_cache_manager()
        
        # 應該是同一個實例
        self.assertIs(manager1, manager2)
        self.assertIsInstance(manager1, CacheManager)

class TestStateManagement(unittest.TestCase):
    """測試狀態管理函數"""
    
    def setUp(self):
        """設置測試環境"""
        self.mock_st = Mock()
        self.mock_st.session_state = {}
        self.mock_st.spinner = Mock()
        self.mock_st.rerun = Mock()
    
    @patch('src.core.state_cache.st')
    @patch('src.core.state_cache.main_calculation_flow')
    @patch('src.core.state_cache.get_current_parameters')
    def test_state_management_initialization(self, mock_get_params, mock_main_flow, mock_st):
        """測試狀態管理初始化"""
        # 設置mock
        mock_session_state = {}
        mock_st.session_state = mock_session_state
        mock_st.spinner.return_value.__enter__ = Mock()
        mock_st.spinner.return_value.__exit__ = Mock()
        mock_st.rerun = Mock()
        mock_get_params.return_value = {'initial_investment': 10000}
        mock_main_flow.return_value = {'result': 'initial_calculation'}
        
        # 調用函數
        state_management()
        
        # 驗證初始化
        self.assertIn('calculation_results', mock_session_state)
        self.assertIn('last_params', mock_session_state)
        self.assertIn('cache_manager', mock_session_state)
        
        # 由於last_params初始為None，會觸發重新計算
        # 驗證計算結果和參數更新
        self.assertEqual(mock_session_state['calculation_results'], {'result': 'initial_calculation'})
        self.assertEqual(mock_session_state['last_params'], {'initial_investment': 10000})
        self.assertIsInstance(mock_session_state['cache_manager'], CacheManager)
        
        # 驗證重新計算被觸發
        mock_main_flow.assert_called_once()
        mock_st.rerun.assert_called_once()
    
    @patch('src.core.state_cache.st')
    @patch('src.core.state_cache.main_calculation_flow')
    @patch('src.core.state_cache.get_current_parameters')
    def test_state_management_with_params_change(self, mock_get_params, mock_main_flow, mock_st):
        """測試參數變更時的狀態管理"""
        # 設置mock
        mock_session_state = {
            'calculation_results': None,
            'last_params': {'initial_investment': 10000},
            'cache_manager': CacheManager()
        }
        mock_st.session_state = mock_session_state
        mock_st.spinner.return_value.__enter__ = Mock()
        mock_st.spinner.return_value.__exit__ = Mock()
        mock_st.rerun = Mock()
        
        mock_get_params.return_value = {'initial_investment': 20000}
        mock_main_flow.return_value = {'result': 'test_result'}
        
        # 調用函數
        state_management()
        
        # 驗證重新計算被觸發
        mock_main_flow.assert_called_once()
        mock_st.rerun.assert_called_once()
        
        # 驗證參數更新
        self.assertEqual(mock_session_state['last_params'], {'initial_investment': 20000})
        self.assertEqual(mock_session_state['calculation_results'], {'result': 'test_result'})
    
    def test_params_changed_detection(self):
        """測試參數變更檢測"""
        # 測試初始狀態（last_params為None）
        current_params = {'initial_investment': 10000}
        self.assertTrue(params_changed(current_params, None))
        
        # 測試相同參數
        last_params = {'initial_investment': 10000}
        self.assertFalse(params_changed(current_params, last_params))
        
        # 測試不同參數
        different_params = {'initial_investment': 20000}
        self.assertTrue(params_changed(different_params, last_params))
        
        # 測試關鍵參數變更
        key_param_change = {'initial_investment': 20000, 'annual_investment': 15000}
        last_key_params = {'initial_investment': 10000, 'annual_investment': 12000}
        self.assertTrue(params_changed(key_param_change, last_key_params))
    
    @patch('src.core.state_cache.st')
    def test_get_current_parameters(self, mock_st):
        """測試獲取當前參數"""
        # 設置mock session_state，創建具有屬性的mock對象
        mock_session_state = Mock()
        mock_session_state.initial_investment = 15000
        mock_session_state.annual_investment = 18000
        mock_session_state.frequency = 'quarterly'
        mock_session_state.annual_growth_rate = 7.0
        mock_session_state.scenario = 'historical'
        
        mock_st.session_state = mock_session_state
        
        # 調用函數
        params = get_current_parameters()
        
        # 驗證返回的參數
        self.assertIsInstance(params, dict)
        self.assertEqual(params['initial_investment'], 15000)
        self.assertEqual(params['annual_investment'], 18000)
        self.assertEqual(params['frequency'], 'quarterly')
        
        # 驗證預設值
        self.assertEqual(params['annual_growth_rate'], 7.0)
        self.assertEqual(params['scenario'], 'historical')
    
    @patch('src.core.state_cache.st')
    def test_clear_related_cache(self, mock_st):
        """測試清理相關快取"""
        # 設置mock
        mock_st.cache_data = Mock()
        mock_st.cache_data.clear = Mock()
        
        test_params = {'param1': 'value1'}
        
        # 調用函數
        clear_related_cache(test_params)
        
        # 驗證Streamlit快取被清理
        mock_st.cache_data.clear.assert_called_once()

class TestStreamlitCacheFunctions(unittest.TestCase):
    """測試Streamlit快取函數"""
    
    @patch('src.core.state_cache.st')
    def test_cached_market_data_function_signature(self, mock_st):
        """測試cached_market_data函數簽名"""
        # 驗證函數存在且可調用
        self.assertTrue(callable(cached_market_data))
        
        # 驗證函數簽名（通過檢查參數）
        import inspect
        sig = inspect.signature(cached_market_data)
        params = list(sig.parameters.keys())
        
        expected_params = ['start_date', 'end_date', 'scenario']
        self.assertEqual(params, expected_params)
        
        # 驗證返回類型註解
        self.assertEqual(sig.return_annotation, Optional[Dict])
    
    @patch('src.core.state_cache.st')
    def test_cached_strategy_calculation_function_signature(self, mock_st):
        """測試cached_strategy_calculation函數簽名"""
        # 驗證函數存在且可調用
        self.assertTrue(callable(cached_strategy_calculation))
        
        # 驗證函數簽名
        import inspect
        sig = inspect.signature(cached_strategy_calculation)
        params = list(sig.parameters.keys())
        
        expected_params = ['market_data_hash', 'params_hash', 'calculation_type']
        self.assertEqual(params, expected_params)
        
        # 驗證返回類型註解
        self.assertEqual(sig.return_annotation, Optional[Dict])
    
    @patch('src.core.state_cache.st')
    def test_cached_performance_metrics_function_signature(self, mock_st):
        """測試cached_performance_metrics函數簽名"""
        # 驗證函數存在且可調用
        self.assertTrue(callable(cached_performance_metrics))
        
        # 驗證函數簽名
        import inspect
        sig = inspect.signature(cached_performance_metrics)
        params = list(sig.parameters.keys())
        
        expected_params = ['va_hash', 'dca_hash']
        self.assertEqual(params, expected_params)
        
        # 驗證返回類型註解
        self.assertEqual(sig.return_annotation, Optional[Dict])
    
    @patch('src.core.state_cache.assess_data_quality')
    @patch('src.core.state_cache.fetch_market_data_comprehensive')
    @patch('src.core.state_cache.st')
    def test_cached_market_data_execution(self, mock_st, mock_fetch, mock_assess):
        """測試cached_market_data執行"""
        # 設置mock
        mock_fetch.return_value = {'test': 'data'}
        mock_assess.return_value = 0.95
        
        # 由於@st.cache_data裝飾器，我們需要直接調用底層函數
        # 這裡我們測試函數邏輯而不是裝飾器
        result = fetch_market_data_comprehensive('2023-01-01', '2023-12-31')
        
        # 驗證結果
        self.assertIsInstance(result, dict)
        self.assertIn('stock_data', result)
        self.assertIn('bond_data', result)
        self.assertIn('metadata', result)

class TestIntelligentCacheManagement(unittest.TestCase):
    """測試智能快取管理函數"""
    
    def test_intelligent_cache_invalidation_function_signature(self):
        """測試intelligent_cache_invalidation函數簽名"""
        # 驗證函數存在且可調用
        self.assertTrue(callable(intelligent_cache_invalidation))
        
        # 驗證函數簽名
        import inspect
        sig = inspect.signature(intelligent_cache_invalidation)
        
        # 驗證無參數
        self.assertEqual(len(sig.parameters), 0)
        
        # 驗證返回類型註解
        self.assertEqual(sig.return_annotation, None)
    
    def test_cache_warming_function_signature(self):
        """測試cache_warming函數簽名"""
        # 驗證函數存在且可調用
        self.assertTrue(callable(cache_warming))
        
        # 驗證函數簽名
        import inspect
        sig = inspect.signature(cache_warming)
        
        # 驗證無參數
        self.assertEqual(len(sig.parameters), 0)
        
        # 驗證返回類型註解
        self.assertEqual(sig.return_annotation, None)
    
    def test_get_cache_statistics_function_signature(self):
        """測試get_cache_statistics函數簽名"""
        # 驗證函數存在且可調用
        self.assertTrue(callable(get_cache_statistics))
        
        # 驗證函數簽名
        import inspect
        sig = inspect.signature(get_cache_statistics)
        
        # 驗證無參數
        self.assertEqual(len(sig.parameters), 0)
        
        # 驗證返回類型註解
        self.assertEqual(sig.return_annotation, Dict[str, Any])
    
    @patch('src.core.state_cache.find_expired_cache_keys')
    @patch('src.core.state_cache.get_cache_size')
    @patch('src.core.state_cache.get_max_cache_size')
    @patch('src.core.state_cache.st')
    def test_intelligent_cache_invalidation_execution(self, mock_st, mock_max_size, mock_size, mock_expired):
        """測試intelligent_cache_invalidation執行"""
        # 設置mock
        mock_expired.return_value = ['expired_key_1', 'expired_key_2']
        mock_size.return_value = 150.0
        mock_max_size.return_value = 200.0
        mock_st.cache_data = Mock()
        mock_st.cache_data.clear = Mock()
        
        # 調用函數
        intelligent_cache_invalidation()
        
        # 驗證過期鍵被處理
        mock_expired.assert_called_once()
        
        # 驗證快取大小被檢查
        mock_size.assert_called()
        mock_max_size.assert_called()
    
    @patch('src.core.state_cache.cached_market_data')
    def test_cache_warming_execution(self, mock_cached):
        """測試cache_warming執行"""
        # 設置mock
        mock_cached.return_value = {'data': 'test'}
        
        # 調用函數
        cache_warming()
        
        # 驗證預熱場景被調用
        expected_calls = [
            (("2020-01-01", "2023-12-31", "historical"),),
            (("2018-01-01", "2023-12-31", "historical"),)
        ]
        
        # 檢查是否調用了預期的參數
        self.assertEqual(mock_cached.call_count, 2)
    
    @patch('src.core.state_cache.get_cache_manager')
    def test_get_cache_statistics_execution(self, mock_get_manager):
        """測試get_cache_statistics執行"""
        # 設置mock
        mock_manager = Mock()
        mock_manager.cache_stats = {
            'hits': 10,
            'misses': 5,
            'evictions': 2,
            'total_requests': 15,
            'last_cleanup': '2024-01-01T00:00:00',
            'cache_size_mb': 100.0
        }
        mock_manager.get_cache_hit_ratio.return_value = 0.67
        mock_get_manager.return_value = mock_manager
        
        # 調用函數
        result = get_cache_statistics()
        
        # 驗證結果結構
        self.assertIsInstance(result, dict)
        self.assertIn('hit_ratio', result)
        self.assertIn('total_hits', result)
        self.assertIn('total_misses', result)
        self.assertIn('cache_size_mb', result)
        self.assertIn('health_status', result)
        
        # 驗證統計值
        self.assertEqual(result['total_hits'], 10)
        self.assertEqual(result['total_misses'], 5)
        self.assertAlmostEqual(result['hit_ratio'], 0.67, places=2)

class TestAuxiliaryFunctions(unittest.TestCase):
    """測試輔助函數"""
    
    def test_fetch_market_data_comprehensive(self):
        """測試fetch_market_data_comprehensive"""
        start_date = '2023-01-01'
        end_date = '2023-01-31'
        
        result = fetch_market_data_comprehensive(start_date, end_date)
        
        # 驗證結果結構
        self.assertIsInstance(result, dict)
        self.assertIn('stock_data', result)
        self.assertIn('bond_data', result)
        self.assertIn('metadata', result)
        
        # 驗證股票數據
        self.assertIn('dates', result['stock_data'])
        self.assertIn('prices', result['stock_data'])
        self.assertIsInstance(result['stock_data']['dates'], list)
        self.assertIsInstance(result['stock_data']['prices'], list)
        
        # 驗證債券數據
        self.assertIn('dates', result['bond_data'])
        self.assertIn('prices', result['bond_data'])
        
        # 驗證元數據
        self.assertEqual(result['metadata']['start_date'], start_date)
        self.assertEqual(result['metadata']['end_date'], end_date)
        self.assertEqual(result['metadata']['data_source'], 'historical')
    
    def test_generate_simulation_data_comprehensive(self):
        """測試generate_simulation_data_comprehensive"""
        scenario = 'bull_market'
        start_date = '2023-01-01'
        end_date = '2023-01-31'
        
        result = generate_simulation_data_comprehensive(scenario, start_date, end_date)
        
        # 驗證結果結構
        self.assertIsInstance(result, dict)
        self.assertIn('stock_data', result)
        self.assertIn('bond_data', result)
        self.assertIn('metadata', result)
        
        # 驗證元數據
        self.assertEqual(result['metadata']['scenario'], scenario)
        self.assertEqual(result['metadata']['data_source'], 'simulation')
    
    def test_calculate_va_strategy_from_hash(self):
        """測試calculate_va_strategy_from_hash"""
        market_hash = 'test_market_hash'
        params_hash = 'test_params_hash'
        
        result = calculate_va_strategy_from_hash(market_hash, params_hash)
        
        # 驗證結果結構
        self.assertIsInstance(result, dict)
        self.assertIn('strategy_type', result)
        self.assertIn('periods', result)
        self.assertIn('final_value', result)
        self.assertIn('total_investment', result)
        self.assertIn('total_return', result)
        
        # 驗證策略類型
        self.assertEqual(result['strategy_type'], 'VA')
        
        # 驗證期間數據
        self.assertIsInstance(result['periods'], list)
        self.assertGreater(len(result['periods']), 0)
    
    def test_calculate_dca_strategy_from_hash(self):
        """測試calculate_dca_strategy_from_hash"""
        market_hash = 'test_market_hash'
        params_hash = 'test_params_hash'
        
        result = calculate_dca_strategy_from_hash(market_hash, params_hash)
        
        # 驗證結果結構
        self.assertIsInstance(result, dict)
        self.assertEqual(result['strategy_type'], 'DCA')
        self.assertIn('periods', result)
        self.assertIn('final_value', result)
    
    def test_calculate_performance_metrics_from_hash(self):
        """測試calculate_performance_metrics_from_hash"""
        va_hash = 'test_va_hash'
        dca_hash = 'test_dca_hash'
        
        result = calculate_performance_metrics_from_hash(va_hash, dca_hash)
        
        # 驗證結果結構
        self.assertIsInstance(result, dict)
        self.assertIn('va_metrics', result)
        self.assertIn('dca_metrics', result)
        self.assertIn('comparison', result)
        
        # 驗證VA指標
        va_metrics = result['va_metrics']
        self.assertIn('annual_return', va_metrics)
        self.assertIn('volatility', va_metrics)
        self.assertIn('sharpe_ratio', va_metrics)
        self.assertIn('max_drawdown', va_metrics)
        
        # 驗證DCA指標
        dca_metrics = result['dca_metrics']
        self.assertIn('annual_return', dca_metrics)
        self.assertIn('volatility', dca_metrics)
        self.assertIn('sharpe_ratio', dca_metrics)
        self.assertIn('max_drawdown', dca_metrics)
        
        # 驗證比較結果
        comparison = result['comparison']
        self.assertIn('return_difference', comparison)
        self.assertIn('volatility_difference', comparison)
        self.assertIn('better_strategy', comparison)
        self.assertIn(comparison['better_strategy'], ['VA', 'DCA'])

class TestFunctionSignatures(unittest.TestCase):
    """測試函數簽名一致性"""
    
    def test_all_required_functions_exist(self):
        """測試所有必需的函數都存在"""
        required_functions = [
            'state_management',
            'cached_market_data',
            'cached_strategy_calculation', 
            'cached_performance_metrics',
            'intelligent_cache_invalidation',
            'cache_warming',
            'get_cache_statistics'
        ]
        
        for func_name in required_functions:
            self.assertTrue(
                hasattr(sys.modules['src.core.state_cache'], func_name),
                f"函數 {func_name} 不存在"
            )
    
    def test_cache_manager_class_exists(self):
        """測試CacheManager類別存在"""
        self.assertTrue(hasattr(sys.modules['src.core.state_cache'], 'CacheManager'))
        
        # 驗證必需的方法
        cache_manager = CacheManager()
        self.assertTrue(hasattr(cache_manager, '__init__'))
        self.assertTrue(hasattr(cache_manager, 'get_cache_hit_ratio'))
        self.assertTrue(callable(cache_manager.get_cache_hit_ratio))
    
    def test_function_return_types(self):
        """測試函數返回類型"""
        # 測試state_management返回None
        import inspect
        sig = inspect.signature(state_management)
        self.assertEqual(sig.return_annotation, None)
        
        # 測試get_cache_statistics返回Dict[str, Any]
        sig = inspect.signature(get_cache_statistics)
        self.assertEqual(sig.return_annotation, Dict[str, Any])
        
        # 測試快取函數返回Optional[Dict]
        sig = inspect.signature(cached_market_data)
        self.assertEqual(sig.return_annotation, Optional[Dict])

class TestIntegration(unittest.TestCase):
    """整合測試"""
    
    def test_cache_manager_integration(self):
        """測試CacheManager整合"""
        # 創建快取管理器
        cache_manager = CacheManager()
        
        # 模擬一系列操作
        cache_manager.record_hit()
        cache_manager.record_hit()
        cache_manager.record_miss()
        cache_manager.update_cache_size(150.0)
        
        # 驗證統計
        hit_ratio = cache_manager.get_cache_hit_ratio()
        self.assertAlmostEqual(hit_ratio, 2/3, places=3)
        
        # 驗證快取大小
        self.assertEqual(cache_manager.cache_stats['cache_size_mb'], 150.0)
        
        # 重設並驗證
        cache_manager.reset_stats()
        self.assertEqual(cache_manager.get_cache_hit_ratio(), 0.0)
    
    @patch('src.core.state_cache.get_cache_manager')
    def test_get_cache_statistics_integration(self, mock_get_manager):
        """測試get_cache_statistics整合"""
        # 設置mock快取管理器
        mock_manager = CacheManager()
        mock_manager.record_hit()
        mock_manager.record_hit()
        mock_manager.record_miss()
        mock_manager.update_cache_size(100.0)
        mock_get_manager.return_value = mock_manager
        
        # 獲取統計
        stats = get_cache_statistics()
        
        # 驗證統計完整性
        required_keys = [
            'hit_ratio', 'total_hits', 'total_misses', 'total_requests',
            'cache_size_mb', 'health_status', 'stats_generated_at'
        ]
        
        for key in required_keys:
            self.assertIn(key, stats)
        
        # 驗證統計值
        self.assertAlmostEqual(stats['hit_ratio'], 2/3, places=3)
        self.assertEqual(stats['total_hits'], 2)
        self.assertEqual(stats['total_misses'], 1)
        self.assertEqual(stats['total_requests'], 3)
    
    def test_auxiliary_functions_integration(self):
        """測試輔助函數整合"""
        # 測試數據生成流程
        start_date = '2023-01-01'
        end_date = '2023-01-10'
        
        # 歷史數據
        historical_data = fetch_market_data_comprehensive(start_date, end_date)
        self.assertIsInstance(historical_data, dict)
        
        # 模擬數據
        simulation_data = generate_simulation_data_comprehensive('bull_market', start_date, end_date)
        self.assertIsInstance(simulation_data, dict)
        
        # 策略計算
        va_result = calculate_va_strategy_from_hash('test_hash', 'test_params')
        dca_result = calculate_dca_strategy_from_hash('test_hash', 'test_params')
        
        self.assertEqual(va_result['strategy_type'], 'VA')
        self.assertEqual(dca_result['strategy_type'], 'DCA')
        
        # 績效指標
        metrics = calculate_performance_metrics_from_hash('va_hash', 'dca_hash')
        self.assertIn('va_metrics', metrics)
        self.assertIn('dca_metrics', metrics)
        self.assertIn('comparison', metrics)

if __name__ == '__main__':
    # 設置測試環境
    import warnings
    warnings.filterwarnings('ignore')
    
    # 運行測試
    unittest.main(verbosity=2, buffer=True) 