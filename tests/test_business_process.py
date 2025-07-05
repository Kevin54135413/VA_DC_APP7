"""
第4.2節業務流程測試套件

測試覆蓋所有核心函數：
- performance_monitor
- main_calculation_flow
- calculate_strategies_parallel
- calculate_va_strategy_safe, calculate_dca_strategy_safe
- data_acquisition_flow
- fetch_historical_data_optimized
- calculate_target_dates, adjust_to_trading_days
- fetch_tiingo_data_batch, fetch_fred_data_batch
- extract_target_date_data, get_closest_price
- generate_cache_key_enhanced, assess_data_quality
"""

import pytest
import time
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
import concurrent.futures
from contextlib import contextmanager
import json
import hashlib

# 導入待測試的模組
from src.core.business_process import (
    performance_monitor,
    main_calculation_flow,
    calculate_strategies_parallel,
    calculate_va_strategy_safe,
    calculate_dca_strategy_safe,
    data_acquisition_flow,
    fetch_historical_data_optimized,
    calculate_target_dates,
    adjust_to_trading_days,
    fetch_tiingo_data_batch,
    fetch_fred_data_batch,
    extract_target_date_data,
    get_closest_price,
    generate_cache_key_enhanced,
    assess_data_quality,
    calculate_period_start_date,
    calculate_period_end_date,
    check_date_continuity,
    detect_outliers,
    record_performance_metric
)

class TestPerformanceMonitor:
    """測試效能監控系統"""
    
    def test_performance_monitor_success(self):
        """測試效能監控成功情況"""
        with patch('src.core.business_process.record_performance_metric') as mock_record:
            start_time = time.time()
            
            with performance_monitor("test_operation"):
                time.sleep(0.1)  # 模擬操作耗時
            
            # 驗證記錄函數被調用
            mock_record.assert_called_once()
            args = mock_record.call_args[0]
            assert args[0] == "test_operation"
            assert args[1] >= 0.1  # 耗時至少0.1秒
            assert args[2] == "success"
    
    def test_performance_monitor_exception(self):
        """測試效能監控異常情況"""
        with patch('src.core.business_process.record_performance_metric') as mock_record:
            with pytest.raises(ValueError):
                with performance_monitor("test_operation"):
                    raise ValueError("Test error")
            
            # 驗證異常情況下的記錄
            mock_record.assert_called_once()
            args = mock_record.call_args[0]
            assert args[0] == "test_operation"
            assert args[2] == "failed"
            assert args[3] == "Test error"
    
    def test_record_performance_metric(self):
        """測試效能指標記錄"""
        with patch('src.core.business_process.logger') as mock_logger:
            record_performance_metric("test_op", 1.5, "success")
            
            # 驗證日誌記錄
            mock_logger.info.assert_called_once()
            log_call = mock_logger.info.call_args[0][0]
            assert "test_op" in log_call
            assert "1.5" in log_call
            assert "success" in log_call

class TestMainCalculationFlow:
    """測試主要計算流程"""
    
    @patch('src.core.business_process.collect_user_parameters')
    @patch('src.core.business_process.validate_parameters_comprehensive')
    @patch('src.core.business_process.data_acquisition_flow')
    @patch('src.core.business_process.calculate_strategies_parallel')
    @patch('src.core.business_process.calculate_performance_metrics_enhanced')
    @patch('src.core.business_process.validate_calculation_results')
    @patch('src.core.business_process.assess_data_quality')
    @patch('src.core.business_process.generate_params_hash')
    def test_main_calculation_flow_success(self, mock_hash, mock_quality, mock_validate,
                                         mock_metrics, mock_parallel, mock_data,
                                         mock_params_validation, mock_collect):
        """測試主要計算流程成功情況"""
        # 設置mock返回值
        mock_collect.return_value = {'test': 'params'}
        
        mock_validation_result = Mock()
        mock_validation_result.is_valid = True
        mock_params_validation.return_value = mock_validation_result
        
        mock_data.return_value = {'test': 'data'}
        mock_parallel.return_value = ({'va': 'result'}, {'dca': 'result'})
        mock_metrics.return_value = {'test': 'metrics'}
        mock_validate.return_value = True
        mock_quality.return_value = 0.9
        mock_hash.return_value = 'test_hash'
        
        # 執行測試
        result = main_calculation_flow()
        
        # 驗證結果
        assert result is not None
        assert 'va_results' in result
        assert 'dca_results' in result
        assert 'metrics' in result
        assert 'metadata' in result
        
        # 驗證所有步驟都被調用
        mock_collect.assert_called_once()
        mock_params_validation.assert_called_once()
        mock_data.assert_called_once()
        mock_parallel.assert_called_once()
        mock_metrics.assert_called_once()
        mock_validate.assert_called_once()
    
    @patch('src.core.business_process.collect_user_parameters')
    @patch('src.core.business_process.validate_parameters_comprehensive')
    @patch('src.core.business_process.display_validation_errors_with_suggestions')
    def test_main_calculation_flow_validation_failure(self, mock_display, mock_validate, mock_collect):
        """測試參數驗證失敗情況"""
        mock_collect.return_value = {'test': 'params'}
        
        mock_validation_result = Mock()
        mock_validation_result.is_valid = False
        mock_validation_result.errors = ['Error 1', 'Error 2']
        mock_validate.return_value = mock_validation_result
        
        result = main_calculation_flow()
        
        assert result is None
        mock_display.assert_called_once()
    
    @patch('src.core.business_process.collect_user_parameters')
    @patch('src.core.business_process.validate_parameters_comprehensive')
    @patch('src.core.business_process.data_acquisition_flow')
    @patch('src.core.business_process.display_data_error_message')
    def test_main_calculation_flow_data_failure(self, mock_display, mock_data, mock_validate, mock_collect):
        """測試數據獲取失敗情況"""
        mock_collect.return_value = {'test': 'params'}
        
        mock_validation_result = Mock()
        mock_validation_result.is_valid = True
        mock_validate.return_value = mock_validation_result
        
        mock_data.return_value = None
        
        result = main_calculation_flow()
        
        assert result is None
        mock_display.assert_called_once()

class TestParallelCalculation:
    """測試並行計算"""
    
    @patch('src.core.business_process.calculate_va_strategy_safe')
    @patch('src.core.business_process.calculate_dca_strategy_safe')
    def test_calculate_strategies_parallel_success(self, mock_dca, mock_va):
        """測試並行策略計算成功情況"""
        mock_va.return_value = {'va': 'result'}
        mock_dca.return_value = {'dca': 'result'}
        
        market_data = {'test': 'data'}
        user_params = {'test': 'params'}
        
        va_result, dca_result = calculate_strategies_parallel(market_data, user_params)
        
        assert va_result == {'va': 'result'}
        assert dca_result == {'dca': 'result'}
        mock_va.assert_called_once_with(market_data, user_params)
        mock_dca.assert_called_once_with(market_data, user_params)
    
    @patch('src.core.business_process.calculate_va_strategy_safe')
    @patch('src.core.business_process.calculate_dca_strategy_safe')
    def test_calculate_strategies_parallel_timeout(self, mock_dca, mock_va):
        """測試並行策略計算超時情況"""
        # 模擬超時
        mock_va.side_effect = lambda *args: time.sleep(35)  # 超過30秒超時
        mock_dca.return_value = {'dca': 'result'}
        
        market_data = {'test': 'data'}
        user_params = {'test': 'params'}
        
        va_result, dca_result = calculate_strategies_parallel(market_data, user_params)
        
        assert va_result is None
        assert dca_result is None
    
    @patch('src.core.business_process.calculate_va_strategy')
    def test_calculate_va_strategy_safe_success(self, mock_calculate):
        """測試安全VA策略計算成功情況"""
        mock_calculate.return_value = {'va': 'result'}
        
        market_data = {'test': 'data'}
        user_params = {
            'initial_investment': 10000,
            'annual_investment': 12000,
            'annual_growth_rate': 7.0,
            'annual_inflation_rate': 2.0,
            'investment_years': 10,
            'frequency': 'monthly',
            'stock_ratio': 80.0,
            'va_strategy_type': 'Rebalance'
        }
        
        result = calculate_va_strategy_safe(market_data, user_params)
        
        assert result == {'va': 'result'}
        mock_calculate.assert_called_once()
    
    @patch('src.core.business_process.calculate_va_strategy')
    def test_calculate_va_strategy_safe_exception(self, mock_calculate):
        """測試安全VA策略計算異常情況"""
        mock_calculate.side_effect = Exception("Calculation error")
        
        market_data = {'test': 'data'}
        user_params = {}
        
        result = calculate_va_strategy_safe(market_data, user_params)
        
        assert result is None
    
    @patch('src.core.business_process.calculate_dca_strategy')
    def test_calculate_dca_strategy_safe_success(self, mock_calculate):
        """測試安全DCA策略計算成功情況"""
        mock_calculate.return_value = {'dca': 'result'}
        
        market_data = {'test': 'data'}
        user_params = {
            'initial_investment': 10000,
            'annual_investment': 12000,
            'annual_growth_rate': 7.0,
            'annual_inflation_rate': 2.0,
            'investment_years': 10,
            'frequency': 'monthly',
            'stock_ratio': 80.0
        }
        
        result = calculate_dca_strategy_safe(market_data, user_params)
        
        assert result == {'dca': 'result'}
        mock_calculate.assert_called_once()

class TestDataAcquisition:
    """測試數據獲取流程"""
    
    @patch('src.core.business_process.generate_cache_key_enhanced')
    @patch('src.core.business_process.get_from_cache_with_validation')
    @patch('src.core.business_process.is_cache_expired')
    @patch('src.core.business_process.update_cache_hit_metrics')
    def test_data_acquisition_flow_cache_hit(self, mock_update, mock_expired, mock_cache, mock_key):
        """測試數據獲取流程快取命中情況"""
        mock_key.return_value = 'test_cache_key'
        mock_cache.return_value = {'cached': 'data'}
        mock_expired.return_value = False
        
        params = Mock()
        result = data_acquisition_flow(params)
        
        assert result == {'cached': 'data'}
        mock_update.assert_called_once_with('test_cache_key')
    
    @patch('src.core.business_process.generate_cache_key_enhanced')
    @patch('src.core.business_process.get_from_cache_with_validation')
    @patch('src.core.business_process.is_cache_expired')
    @patch('src.core.business_process.fetch_historical_data_optimized')
    @patch('src.core.business_process.assess_data_quality')
    @patch('src.core.business_process.update_cache_with_metadata')
    @patch('src.core.business_process.generate_params_hash')
    def test_data_acquisition_flow_cache_miss(self, mock_hash, mock_update_cache, mock_quality,
                                            mock_fetch, mock_expired, mock_cache, mock_key):
        """測試數據獲取流程快取未命中情況"""
        mock_key.return_value = 'test_cache_key'
        mock_cache.return_value = None
        mock_fetch.return_value = {'new': 'data'}
        mock_quality.return_value = 0.8
        mock_hash.return_value = 'params_hash'
        
        params = Mock()
        params.scenario = 'historical'
        
        result = data_acquisition_flow(params)
        
        assert result == {'new': 'data'}
        mock_fetch.assert_called_once_with(params)
        mock_update_cache.assert_called_once()
    
    @patch('src.core.business_process.calculate_target_dates')
    @patch('src.core.business_process.adjust_to_trading_days')
    @patch('src.core.business_process.fetch_tiingo_data_batch')
    @patch('src.core.business_process.fetch_fred_data_batch')
    @patch('src.core.business_process.extract_target_date_data')
    def test_fetch_historical_data_optimized_success(self, mock_extract, mock_fred, mock_tiingo,
                                                   mock_adjust, mock_calculate):
        """測試優化版歷史數據獲取成功情況"""
        # 設置mock返回值
        mock_calculate.return_value = {
            'period_starts': [datetime(2020, 1, 1)],
            'period_ends': [datetime(2020, 1, 31)]
        }
        mock_adjust.return_value = {
            'period_starts': [datetime(2020, 1, 1)],
            'period_ends': [datetime(2020, 1, 31)]
        }
        
        mock_stock_data = pd.DataFrame({'date': ['2020-01-01'], 'price': [100.0]})
        mock_bond_data = pd.DataFrame({'date': ['2020-01-01'], 'price': [98.0]})
        
        mock_tiingo.return_value = mock_stock_data
        mock_fred.return_value = mock_bond_data
        mock_extract.return_value = {'extracted': 'data'}
        
        params = Mock()
        params.start_date = datetime(2020, 1, 1)
        params.frequency = 'monthly'
        params.periods = 1
        
        result = fetch_historical_data_optimized(params)
        
        assert result == {'extracted': 'data'}
        mock_calculate.assert_called_once()
        mock_adjust.assert_called_once()
        mock_tiingo.assert_called_once()
        mock_fred.assert_called_once()
        mock_extract.assert_called_once()

class TestTargetDateCalculation:
    """測試目標日期計算"""
    
    def test_calculate_target_dates_monthly(self):
        """測試月度目標日期計算"""
        start_date = datetime(2020, 1, 1)
        result = calculate_target_dates(start_date, 'monthly', 3)
        
        assert len(result['period_starts']) == 3
        assert len(result['period_ends']) == 3
        assert result['period_starts'][0] == datetime(2020, 1, 1)
        assert result['period_starts'][1] == datetime(2020, 2, 1)
        assert result['period_starts'][2] == datetime(2020, 3, 1)
    
    def test_calculate_target_dates_quarterly(self):
        """測試季度目標日期計算"""
        start_date = datetime(2020, 1, 1)
        result = calculate_target_dates(start_date, 'quarterly', 2)
        
        assert len(result['period_starts']) == 2
        assert result['period_starts'][0] == datetime(2020, 1, 1)
        assert result['period_starts'][1] == datetime(2020, 4, 1)
    
    def test_calculate_target_dates_annually(self):
        """測試年度目標日期計算"""
        start_date = datetime(2020, 1, 1)
        result = calculate_target_dates(start_date, 'annually', 2)
        
        assert len(result['period_starts']) == 2
        assert result['period_starts'][0] == datetime(2020, 1, 1)
        assert result['period_starts'][1] == datetime(2021, 1, 1)
    
    def test_calculate_period_start_date(self):
        """測試期初日期計算"""
        base_date = datetime(2020, 1, 1)
        
        # 測試月度
        result = calculate_period_start_date(base_date, 'monthly', 3)
        assert result == datetime(2020, 3, 1)
        
        # 測試季度
        result = calculate_period_start_date(base_date, 'quarterly', 2)
        assert result == datetime(2020, 4, 1)
        
        # 測試年度
        result = calculate_period_start_date(base_date, 'annually', 2)
        assert result == datetime(2021, 1, 1)
    
    def test_calculate_period_end_date(self):
        """測試期末日期計算"""
        base_date = datetime(2020, 1, 1)
        
        # 測試月度
        result = calculate_period_end_date(base_date, 'monthly', 1)
        assert result == datetime(2020, 1, 31)
        
        # 測試季度
        result = calculate_period_end_date(base_date, 'quarterly', 1)
        assert result == datetime(2020, 3, 31)
    
    @patch('pandas.tseries.offsets.CustomBusinessDay')
    def test_adjust_to_trading_days(self, mock_business_day):
        """測試交易日調整"""
        # 設置mock
        mock_bd = Mock()
        mock_bd.is_on_offset.return_value = True
        mock_business_day.return_value = mock_bd
        
        target_dates = {
            'period_starts': [datetime(2020, 1, 1)],
            'period_ends': [datetime(2020, 1, 31)]
        }
        
        result = adjust_to_trading_days(target_dates)
        
        assert len(result['period_starts']) == 1
        assert len(result['period_ends']) == 1

class TestBatchDataFetch:
    """測試批次數據獲取"""
    
    @patch('src.core.business_process.TiingoAPIClient')
    def test_fetch_tiingo_data_batch_success(self, mock_client_class):
        """測試Tiingo批次數據獲取成功情況"""
        # 設置mock
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        mock_data = [
            Mock(date='2020-01-01', spy_price=100.0),
            Mock(date='2020-01-02', spy_price=101.0)
        ]
        mock_client.get_spy_prices.return_value = mock_data
        
        start_date = datetime(2020, 1, 1)
        end_date = datetime(2020, 1, 2)
        
        result = fetch_tiingo_data_batch(start_date, end_date)
        
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 2
        assert 'date' in result.columns
        assert 'price' in result.columns
    
    @patch('src.core.business_process.TiingoAPIClient')
    def test_fetch_tiingo_data_batch_retry(self, mock_client_class):
        """測試Tiingo批次數據獲取重試機制"""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        # 前兩次失敗，第三次成功
        mock_client.get_spy_prices.side_effect = [
            Exception("API Error"),
            Exception("API Error"),
            [Mock(date='2020-01-01', spy_price=100.0)]
        ]
        
        start_date = datetime(2020, 1, 1)
        end_date = datetime(2020, 1, 2)
        
        result = fetch_tiingo_data_batch(start_date, end_date)
        
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 1
        assert mock_client.get_spy_prices.call_count == 3
    
    @patch('src.core.business_process.FREDAPIClient')
    def test_fetch_fred_data_batch_success(self, mock_client_class):
        """測試FRED批次數據獲取成功情況"""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        mock_data = [
            Mock(date='2020-01-01', bond_yield=2.0, bond_price=98.0),
            Mock(date='2020-01-02', bond_yield=2.1, bond_price=97.9)
        ]
        mock_client.get_bond_yields.return_value = mock_data
        
        start_date = datetime(2020, 1, 1)
        end_date = datetime(2020, 1, 2)
        
        result = fetch_fred_data_batch(start_date, end_date)
        
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 2
        assert 'date' in result.columns
        assert 'price' in result.columns

class TestDataExtraction:
    """測試數據提取"""
    
    def test_extract_target_date_data(self):
        """測試目標日期數據提取"""
        # 準備測試數據
        stock_data = pd.DataFrame({
            'date': pd.to_datetime(['2020-01-01', '2020-01-02', '2020-01-31']),
            'price': [100.0, 101.0, 102.0]
        })
        
        bond_data = pd.DataFrame({
            'date': pd.to_datetime(['2020-01-01', '2020-01-02', '2020-01-31']),
            'price': [98.0, 98.1, 98.2]
        })
        
        adjusted_dates = {
            'period_starts': [datetime(2020, 1, 1)],
            'period_ends': [datetime(2020, 1, 31)]
        }
        
        result = extract_target_date_data(stock_data, bond_data, adjusted_dates)
        
        assert 'periods_data' in result
        assert len(result['periods_data']) == 1
        assert result['periods_data'][0]['period'] == 1
        assert result['periods_data'][0]['start_stock_price'] == 100.0
        assert result['periods_data'][0]['end_stock_price'] == 102.0
        assert result['total_periods'] == 1
    
    def test_get_closest_price_exact_match(self):
        """測試獲取最接近價格 - 精確匹配"""
        data = pd.DataFrame({
            'date': pd.to_datetime(['2020-01-01', '2020-01-02', '2020-01-03']),
            'price': [100.0, 101.0, 102.0]
        })
        
        target_date = datetime(2020, 1, 2)
        result = get_closest_price(data, target_date)
        
        assert result == 101.0
    
    def test_get_closest_price_closest_match(self):
        """測試獲取最接近價格 - 最接近匹配"""
        data = pd.DataFrame({
            'date': pd.to_datetime(['2020-01-01', '2020-01-03', '2020-01-05']),
            'price': [100.0, 102.0, 104.0]
        })
        
        target_date = datetime(2020, 1, 2)
        result = get_closest_price(data, target_date)
        
        assert result == 100.0  # 2020-01-01 更接近 2020-01-02
    
    def test_get_closest_price_empty_data(self):
        """測試獲取最接近價格 - 空數據"""
        data = pd.DataFrame(columns=['date', 'price'])
        target_date = datetime(2020, 1, 1)
        
        result = get_closest_price(data, target_date)
        
        assert result == 100.0  # 預設值

class TestCacheAndQuality:
    """測試快取和品質管理"""
    
    def test_generate_cache_key_enhanced(self):
        """測試增強版快取鍵生成"""
        params = Mock()
        params.scenario = 'historical'
        params.start_date = datetime(2020, 1, 1)
        params.frequency = 'monthly'
        params.periods = 12
        params.stock_ratio = 80.0
        
        result = generate_cache_key_enhanced(params)
        
        assert isinstance(result, str)
        assert len(result) == 32  # MD5 hash length
    
    def test_generate_cache_key_enhanced_with_none_values(self):
        """測試快取鍵生成 - 包含None值"""
        params = Mock()
        params.scenario = 'historical'
        params.start_date = None
        params.frequency = 'monthly'
        
        result = generate_cache_key_enhanced(params)
        
        assert isinstance(result, str)
        assert len(result) == 32
    
    def test_assess_data_quality_none_data(self):
        """測試數據品質評估 - None數據"""
        result = assess_data_quality(None)
        assert result == 0.0
    
    def test_assess_data_quality_dict_data(self):
        """測試數據品質評估 - 字典數據"""
        data = {
            'periods_data': [
                {
                    'start_stock_price': 100.0,
                    'start_bond_price': 98.0,
                    'end_stock_price': 102.0,
                    'end_bond_price': 98.5
                }
            ]
        }
        
        result = assess_data_quality(data)
        
        assert 0.0 <= result <= 1.0
        assert result > 0.8  # 完整數據應該有高品質分數
    
    def test_assess_data_quality_dataframe_data(self):
        """測試數據品質評估 - DataFrame數據"""
        data = pd.DataFrame({
            'date': pd.to_datetime(['2020-01-01', '2020-01-02', '2020-01-03']),
            'price': [100.0, 101.0, 102.0],
            'volume': [1000, 1100, 1200]
        })
        
        result = assess_data_quality(data)
        
        assert 0.0 <= result <= 1.0
        assert result > 0.8  # 完整數據應該有高品質分數
    
    def test_assess_data_quality_empty_dataframe(self):
        """測試數據品質評估 - 空DataFrame"""
        data = pd.DataFrame()
        
        result = assess_data_quality(data)
        
        assert result == 0.0
    
    def test_check_date_continuity(self):
        """測試日期連續性檢查"""
        # 正常連續數據
        data = pd.DataFrame({
            'date': pd.to_datetime(['2020-01-01', '2020-01-02', '2020-01-03']),
            'price': [100.0, 101.0, 102.0]
        })
        
        result = check_date_continuity(data)
        
        assert result == 0.0  # 沒有異常間隔
        
        # 有間隔的數據
        data_with_gap = pd.DataFrame({
            'date': pd.to_datetime(['2020-01-01', '2020-01-15', '2020-01-16']),
            'price': [100.0, 101.0, 102.0]
        })
        
        result_gap = check_date_continuity(data_with_gap)
        
        assert result_gap > 0.0  # 有異常間隔
    
    def test_detect_outliers(self):
        """測試異常值檢測"""
        # 正常數據
        data = pd.DataFrame({
            'price': [100.0, 101.0, 102.0, 103.0, 104.0]
        })
        
        result = detect_outliers(data)
        
        assert result == 0.0  # 沒有異常值
        
        # 包含異常值的數據
        data_with_outliers = pd.DataFrame({
            'price': [100.0, 101.0, 102.0, 103.0, 1000.0]  # 1000是異常值
        })
        
        result_outliers = detect_outliers(data_with_outliers)
        
        assert result_outliers > 0.0  # 有異常值

class TestFunctionSignatures:
    """測試函數簽名一致性"""
    
    def test_performance_monitor_signature(self):
        """測試performance_monitor函數簽名"""
        import inspect
        sig = inspect.signature(performance_monitor)
        
        # 檢查參數
        params = list(sig.parameters.keys())
        assert 'operation_name' in params
        assert sig.parameters['operation_name'].annotation == str
        
        # 檢查返回值類型
        from typing import get_origin, get_args
        return_annotation = sig.return_annotation
        assert get_origin(return_annotation) is not None  # 應該是ContextManager類型
    
    def test_main_calculation_flow_signature(self):
        """測試main_calculation_flow函數簽名"""
        import inspect
        sig = inspect.signature(main_calculation_flow)
        
        # 檢查無參數
        assert len(sig.parameters) == 0
        
        # 檢查返回值類型
        from typing import get_origin
        return_annotation = sig.return_annotation
        assert get_origin(return_annotation) is not None  # Optional[Dict[str, Any]]
    
    def test_calculate_strategies_parallel_signature(self):
        """測試calculate_strategies_parallel函數簽名"""
        import inspect
        sig = inspect.signature(calculate_strategies_parallel)
        
        # 檢查參數
        params = list(sig.parameters.keys())
        assert 'market_data' in params
        assert 'user_params' in params
        
        # 檢查返回值類型
        from typing import get_origin
        return_annotation = sig.return_annotation
        assert get_origin(return_annotation) is not None  # Tuple[Optional, Optional]
    
    def test_calculate_target_dates_signature(self):
        """測試calculate_target_dates函數簽名"""
        import inspect
        sig = inspect.signature(calculate_target_dates)
        
        # 檢查參數
        params = list(sig.parameters.keys())
        assert 'start_date' in params
        assert 'frequency' in params
        assert 'periods' in params
        
        # 檢查參數類型
        assert sig.parameters['start_date'].annotation == datetime
        assert sig.parameters['frequency'].annotation == str
        assert sig.parameters['periods'].annotation == int
    
    def test_get_closest_price_signature(self):
        """測試get_closest_price函數簽名"""
        import inspect
        sig = inspect.signature(get_closest_price)
        
        # 檢查參數
        params = list(sig.parameters.keys())
        assert 'data' in params
        assert 'target_date' in params
        
        # 檢查參數類型
        assert sig.parameters['data'].annotation == pd.DataFrame
        assert sig.parameters['target_date'].annotation == datetime
        
        # 檢查返回值類型
        assert sig.return_annotation == float
    
    def test_assess_data_quality_signature(self):
        """測試assess_data_quality函數簽名"""
        import inspect
        sig = inspect.signature(assess_data_quality)
        
        # 檢查參數
        params = list(sig.parameters.keys())
        assert 'data' in params
        
        # 檢查返回值類型
        assert sig.return_annotation == float

if __name__ == '__main__':
    pytest.main([__file__, '-v']) 