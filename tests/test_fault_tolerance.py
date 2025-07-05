"""
容錯機制與品質控制單元測試

測試第1章第1.2節實作的容錯與品質控制功能：
1. APIFaultToleranceManager 測試
2. DataQualityValidator 測試  
3. SimulationDataGenerator 測試
4. IntelligentCacheManager 測試
"""

import unittest
import time
import tempfile
import shutil
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
import logging

# 設定測試日誌級別
logging.basicConfig(level=logging.WARNING)

from src.data_sources.fault_tolerance import (
    APIFaultToleranceManager,
    DataQualityValidator,
    RetryConfig,
    ValidationRules
)

from src.data_sources.simulation import (
    SimulationDataGenerator,
    MarketRegime,
    MarketScenarioConfig,
    YieldCurveConfig
)

from src.data_sources.cache_manager import (
    IntelligentCacheManager,
    CacheConfig,
    CacheEntry
)


class TestAPIFaultToleranceManager(unittest.TestCase):
    """測試API容錯管理器"""
    
    def setUp(self):
        """設置測試環境"""
        self.retry_config = RetryConfig(
            max_retries=3,
            base_delay=0.1,  # 測試時使用較短延遲
            backoff_factor=2.0,
            timeout=5
        )
        self.manager = APIFaultToleranceManager(self.retry_config)
    
    def test_retry_config_initialization(self):
        """測試重試配置初始化"""
        self.assertEqual(self.manager.retry_config.max_retries, 3)
        self.assertEqual(self.manager.retry_config.base_delay, 0.1)
        self.assertEqual(self.manager.retry_config.backoff_factor, 2.0)
    
    def test_successful_api_call(self):
        """測試成功的API調用"""
        def mock_api_function():
            return {"data": "test"}
        
        result = self.manager.fetch_with_retry(mock_api_function)
        self.assertEqual(result, {"data": "test"})
        self.assertEqual(self.manager.error_stats['total_requests'], 1)
        self.assertEqual(self.manager.error_stats['failed_requests'], 0)
    
    def test_retry_mechanism(self):
        """測試重試機制"""
        call_count = 0
        
        def mock_failing_api():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("Network error")
            return {"data": "success"}
        
        result = self.manager.fetch_with_retry(mock_failing_api)
        self.assertEqual(result, {"data": "success"})
        self.assertEqual(call_count, 3)
        self.assertEqual(self.manager.error_stats['retry_attempts'], 2)
    
    def test_complete_failure(self):
        """測試完全失敗的情況"""
        def mock_always_failing_api():
            raise Exception("Persistent error")
        
        with self.assertRaises(Exception):
            self.manager.fetch_with_retry(mock_always_failing_api)
        
        self.assertEqual(self.manager.error_stats['failed_requests'], 3)
    
    def test_fallback_strategy_execution(self):
        """測試備援策略執行"""
        with patch.object(self.manager, '_fetch_yahoo_finance') as mock_yahoo:
            mock_yahoo.return_value = [{"date": "2024-01-01", "adjClose": 400.0}]
            
            data, method = self.manager.execute_fallback_strategy(
                'tiingo', '2024-01-01', '2024-01-31'
            )
            
            self.assertIsNotNone(data)
            self.assertEqual(method, 'yahoo_finance')
            self.assertEqual(len(data), 1)
    
    def test_fallback_strategy_simulation(self):
        """測試模擬數據備援策略"""
        with patch.object(self.manager, '_generate_fallback_simulation') as mock_sim:
            mock_sim.return_value = [{"date": "2024-01-01", "adjClose": 400.0}]
            
            data, method = self.manager.execute_fallback_strategy(
                'tiingo', '2024-01-01', '2024-01-31'
            )
            
            self.assertIsNotNone(data)
            self.assertEqual(method, 'simulation')
    
    def test_backoff_delay_calculation(self):
        """測試退避延遲計算"""
        delay1 = self.manager._calculate_backoff_delay(0)
        delay2 = self.manager._calculate_backoff_delay(1)
        delay3 = self.manager._calculate_backoff_delay(2)
        
        # 檢查延遲遞增
        self.assertLess(delay1, delay2)
        self.assertLess(delay2, delay3)
        
        # 檢查包含抖動
        self.assertGreater(delay1, self.retry_config.base_delay)
    
    def test_stats_tracking(self):
        """測試統計追蹤"""
        initial_stats = self.manager.get_stats()
        
        # 執行一些操作
        def mock_api():
            return "success"
        
        self.manager.fetch_with_retry(mock_api)
        
        updated_stats = self.manager.get_stats()
        self.assertEqual(updated_stats['total_requests'], 1)
        self.assertGreater(updated_stats['success_rate'], 0)


class TestDataQualityValidator(unittest.TestCase):
    """測試數據品質驗證器"""
    
    def setUp(self):
        """設置測試環境"""
        self.validator = DataQualityValidator()
    
    def test_valid_price_data(self):
        """測試有效價格數據驗證"""
        valid_data = [
            {"date": "2024-01-01", "adjClose": 400.0},
            {"date": "2024-01-02", "adjClose": 402.0},
            {"date": "2024-01-03", "adjClose": 399.5}
        ]
        
        result = self.validator.validate_market_data(valid_data, 'price_data')
        
        self.assertTrue(result['is_valid'])
        self.assertEqual(len(result['errors']), 0)
        self.assertGreater(result['data_quality_score'], 80)
    
    def test_invalid_price_data(self):
        """測試無效價格數據"""
        invalid_data = [
            {"date": "2024-01-01", "adjClose": -100.0},  # 負價格
            {"date": "invalid-date", "adjClose": 400.0},  # 無效日期
            {"date": "2024-01-03", "adjClose": "invalid"}  # 無效數值
        ]
        
        result = self.validator.validate_market_data(invalid_data, 'price_data')
        
        self.assertFalse(result['is_valid'])
        self.assertGreater(len(result['errors']), 0)
        self.assertLess(result['data_quality_score'], 50)
    
    def test_yield_data_validation(self):
        """測試殖利率數據驗證"""
        yield_data = [
            {"date": "2024-01-01", "value": "4.5"},
            {"date": "2024-01-02", "value": "4.6"},
            {"date": "2024-01-03", "value": "."}  # FRED缺失值
        ]
        
        result = self.validator.validate_market_data(yield_data, 'yield_data')
        
        self.assertTrue(result['is_valid'])
        self.assertIn('missing_values', result['statistics'])
    
    def test_extreme_daily_changes(self):
        """測試極端日間變化檢測"""
        volatile_data = [
            {"date": "2024-01-01", "adjClose": 400.0},
            {"date": "2024-01-02", "adjClose": 500.0},  # 25%漲幅
            {"date": "2024-01-03", "adjClose": 350.0}   # 30%跌幅
        ]
        
        result = self.validator.validate_market_data(volatile_data, 'price_data')
        
        self.assertGreater(len(result['warnings']), 0)
        self.assertIn('max_daily_change', result['statistics'])
    
    def test_empty_data_handling(self):
        """測試空數據處理"""
        result = self.validator.validate_market_data([], 'price_data')
        
        self.assertFalse(result['is_valid'])
        self.assertIn("數據為空", result['errors'])
        self.assertEqual(result['data_quality_score'], 0.0)
    
    def test_date_continuity_check(self):
        """測試日期連續性檢查"""
        gapped_data = [
            {"date": "2024-01-01", "adjClose": 400.0},
            {"date": "2024-01-15", "adjClose": 410.0},  # 大缺口
            {"date": "2024-01-16", "adjClose": 412.0}
        ]
        
        result = self.validator.validate_market_data(gapped_data, 'price_data')
        
        self.assertIn('date_continuity', result['statistics'])
        continuity = result['statistics']['date_continuity']
        self.assertIn('gaps', continuity)
    
    def test_quality_score_calculation(self):
        """測試品質分數計算"""
        # 高品質數據
        high_quality_data = [
            {"date": f"2024-01-{str(i).zfill(2)}", "adjClose": 400.0 + i} 
            for i in range(1, 31)
        ]
        
        result = self.validator.validate_market_data(high_quality_data, 'price_data')
        high_score = result['data_quality_score']
        
        # 低品質數據
        low_quality_data = [
            {"date": "2024-01-01", "adjClose": 400.0},
            {"date": "invalid", "adjClose": "bad"}
        ]
        
        result = self.validator.validate_market_data(low_quality_data, 'price_data')
        low_score = result['data_quality_score']
        
        self.assertGreater(high_score, low_score)
    
    def test_statistics_generation(self):
        """測試統計信息生成"""
        stats = self.validator.get_quality_stats()
        
        self.assertIn('total_validations', stats)
        self.assertIn('passed_validations', stats)
        self.assertIn('average_quality_score', stats)


class TestSimulationDataGenerator(unittest.TestCase):
    """測試模擬數據生成器"""
    
    def setUp(self):
        """設置測試環境"""
        self.generator = SimulationDataGenerator(random_seed=42)
    
    def test_stock_data_generation(self):
        """測試股票數據生成"""
        start_date = "2024-01-01"
        end_date = "2024-01-10"
        
        data = self.generator.generate_stock_data(
            start_date, end_date, initial_price=400.0
        )
        
        self.assertGreater(len(data), 0)
        self.assertEqual(data[0]['date'], start_date)
        self.assertEqual(data[0]['adjClose'], 400.0)
        self.assertEqual(data[0]['data_source'], 'simulation')
    
    def test_different_market_scenarios(self):
        """測試不同市場情境"""
        start_date = "2024-01-01"
        end_date = "2024-01-31"
        
        # 牛市
        bull_data = self.generator.generate_stock_data(
            start_date, end_date, scenario=MarketRegime.BULL
        )
        
        # 熊市
        bear_data = self.generator.generate_stock_data(
            start_date, end_date, scenario=MarketRegime.BEAR
        )
        
        self.assertEqual(len(bull_data), len(bear_data))
        self.assertNotEqual(bull_data[-1]['adjClose'], bear_data[-1]['adjClose'])
    
    def test_yield_data_generation(self):
        """測試殖利率數據生成"""
        start_date = "2024-01-01"
        end_date = "2024-01-10"
        
        data = self.generator.generate_yield_data(start_date, end_date)
        
        self.assertGreater(len(data), 0)
        self.assertEqual(data[0]['date'], start_date)
        self.assertEqual(data[0]['data_source'], 'simulation')
        
        # 檢查殖利率格式
        yield_val = float(data[0]['value'])
        self.assertGreater(yield_val, 0)
        self.assertLess(yield_val, 15)
    
    def test_mixed_scenario_generation(self):
        """測試混合情境生成"""
        start_date = "2024-01-01"
        end_date = "2024-01-31"
        
        scenario_sequence = [
            (MarketRegime.BULL, 10),
            (MarketRegime.BEAR, 10),
            (MarketRegime.SIDEWAYS, 11)
        ]
        
        data = self.generator.generate_mixed_scenario_data(
            start_date, end_date, scenario_sequence=scenario_sequence
        )
        
        self.assertGreater(len(data), 20)
        self.assertEqual(data[0]['data_source'], 'simulation_mixed')
    
    def test_stress_test_generation(self):
        """測試壓力測試數據生成"""
        start_date = "2024-01-01"
        end_date = "2024-01-31"
        
        # 黑天鵝事件
        black_swan_data = self.generator.generate_stress_test_data(
            start_date, end_date, stress_type='black_swan'
        )
        
        # 高波動率
        high_vol_data = self.generator.generate_stress_test_data(
            start_date, end_date, stress_type='high_volatility'
        )
        
        self.assertGreater(len(black_swan_data), 0)
        self.assertGreater(len(high_vol_data), 0)
    
    def test_market_summary_calculation(self):
        """測試市場摘要計算"""
        data = [
            {"adjClose": 100.0},
            {"adjClose": 110.0},
            {"adjClose": 105.0},
            {"adjClose": 120.0}
        ]
        
        summary = self.generator.get_market_summary(data)
        
        self.assertIn('total_return', summary)
        self.assertIn('volatility', summary)
        self.assertIn('max_drawdown', summary)
        self.assertIn('sharpe_ratio', summary)
        
        # 檢查總報酬率計算
        expected_return = (120.0 / 100.0) - 1
        self.assertAlmostEqual(summary['total_return'], expected_return, places=4)
    
    def test_custom_config_usage(self):
        """測試自定義配置使用"""
        custom_config = MarketScenarioConfig(
            annual_return=0.15,
            annual_volatility=0.25,
            duration_years=1.0,
            regime=MarketRegime.BULL
        )
        
        data = self.generator.generate_stock_data(
            "2024-01-01", "2024-01-31", 
            custom_config=custom_config
        )
        
        self.assertGreater(len(data), 0)
        self.assertEqual(data[0]['annual_return'], 0.15)
        self.assertEqual(data[0]['annual_volatility'], 0.25)


class TestIntelligentCacheManager(unittest.TestCase):
    """測試智能快取管理器"""
    
    def setUp(self):
        """設置測試環境"""
        self.temp_dir = tempfile.mkdtemp()
        
        self.config = CacheConfig(
            local_cache_dir=self.temp_dir,
            max_cache_size_mb=1,  # 測試用小容量
            max_entries=10
        )
        
        self.cache_manager = IntelligentCacheManager(self.config)
    
    def tearDown(self):
        """清理測試環境"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_basic_cache_operations(self):
        """測試基本快取操作"""
        # 設置快取
        self.cache_manager.set("test_key", {"data": "test_value"})
        
        # 獲取快取
        result = self.cache_manager.get("test_key")
        self.assertEqual(result, {"data": "test_value"})
        
        # 刪除快取
        deleted = self.cache_manager.delete("test_key")
        self.assertTrue(deleted)
        
        # 驗證已刪除
        result = self.cache_manager.get("test_key", "default")
        self.assertEqual(result, "default")
    
    def test_ttl_expiration(self):
        """測試TTL過期機制"""
        # 設置短TTL
        self.cache_manager.set("ttl_key", "ttl_value", ttl=1)
        
        # 立即獲取應該成功
        result = self.cache_manager.get("ttl_key")
        self.assertEqual(result, "ttl_value")
        
        # 等待過期
        time.sleep(1.1)
        
        # 過期後應該返回預設值
        result = self.cache_manager.get("ttl_key", "expired")
        self.assertEqual(result, "expired")
    
    def test_cache_key_generation(self):
        """測試快取鍵生成"""
        params = {
            "start_date": "2024-01-01",
            "end_date": "2024-01-31",
            "scenario": "bull_market"
        }
        
        key1 = self.cache_manager.generate_cache_key("test", params)
        key2 = self.cache_manager.generate_cache_key("test", params)
        
        # 相同參數應該生成相同鍵
        self.assertEqual(key1, key2)
        
        # 不同參數應該生成不同鍵
        params2 = params.copy()
        params2["scenario"] = "bear_market"
        key3 = self.cache_manager.generate_cache_key("test", params2)
        
        self.assertNotEqual(key1, key3)
    
    def test_cache_statistics(self):
        """測試快取統計"""
        initial_stats = self.cache_manager.get_cache_stats()
        
        # 執行一些快取操作
        self.cache_manager.set("stat_key1", "value1")
        self.cache_manager.get("stat_key1")  # 命中
        self.cache_manager.get("nonexistent", "default")  # 未命中
        
        updated_stats = self.cache_manager.get_cache_stats()
        
        self.assertEqual(updated_stats['hits'], 1)
        self.assertEqual(updated_stats['misses'], 1)
        self.assertGreater(updated_stats['hit_rate'], 0)
    
    def test_cache_cleanup(self):
        """測試快取清理"""
        # 填充快取至接近容量限制
        for i in range(15):  # 超過max_entries
            self.cache_manager.set(f"cleanup_key_{i}", f"value_{i}")
        
        stats = self.cache_manager.get_cache_stats()
        
        # 驗證清理已執行
        self.assertLess(stats['memory_entries'], 15)
        self.assertGreater(stats['evictions'], 0)
    
    def test_pattern_based_clearing(self):
        """測試基於模式的清除"""
        # 設置多個快取
        self.cache_manager.set("api_test_1", "value1")
        self.cache_manager.set("api_test_2", "value2")
        self.cache_manager.set("historical_data_1", "value3")
        
        # 清除特定模式的快取
        self.cache_manager.clear("api_test")
        
        # 驗證清除結果
        self.assertEqual(self.cache_manager.get("api_test_1", "cleared"), "cleared")
        self.assertEqual(self.cache_manager.get("api_test_2", "cleared"), "cleared")
        self.assertNotEqual(self.cache_manager.get("historical_data_1", "cleared"), "cleared")
    
    def test_memory_usage_tracking(self):
        """測試記憶體使用量追蹤"""
        large_data = {"large_list": list(range(1000))}
        
        initial_usage = self.cache_manager.get_cache_stats()['memory_usage_mb']
        
        self.cache_manager.set("large_key", large_data)
        
        after_usage = self.cache_manager.get_cache_stats()['memory_usage_mb']
        
        self.assertGreater(after_usage, initial_usage)


if __name__ == '__main__':
    # 創建測試套件
    test_suite = unittest.TestSuite()
    
    # 添加測試類別
    test_suite.addTest(unittest.makeSuite(TestAPIFaultToleranceManager))
    test_suite.addTest(unittest.makeSuite(TestDataQualityValidator))
    test_suite.addTest(unittest.makeSuite(TestSimulationDataGenerator))
    test_suite.addTest(unittest.makeSuite(TestIntelligentCacheManager))
    
    # 運行測試
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # 輸出測試總結
    print(f"\n測試總結:")
    print(f"運行測試: {result.testsRun}")
    print(f"失敗: {len(result.failures)}")
    print(f"錯誤: {len(result.errors)}")
    print(f"成功率: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%") 