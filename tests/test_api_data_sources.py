# tests/test_api_data_sources.py

"""
API數據源測試模組

測試Tiingo和FRED API的數據獲取功能、API安全機制和容錯處理。
"""

import unittest
import unittest.mock
from datetime import datetime, timedelta
import sys
import os

# 添加src到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.data_sources.fault_tolerance import APIFaultToleranceManager
from src.data_sources.data_fetcher import TiingoDataFetcher, FREDDataFetcher, BatchDataFetcher
from src.data_sources.trading_calendar import calculate_period_start_date
from src.models.data_models import MarketDataPoint, DataModelFactory
from src.data_sources.api_client import (
    get_api_key, validate_api_key_format, test_api_connectivity
)
from src.data_sources.trading_calendar import (
    calculate_period_end_dates,
    adjust_for_trading_days, generate_trading_days, is_trading_day,
    generate_investment_timeline, get_target_dates_for_data_fetching
)


class TestAPIKeyManagement(unittest.TestCase):
    """測試API金鑰管理功能"""
    
    def setUp(self):
        """測試前準備"""
        self.valid_tiingo_key = "abcdefghijklmnopqrstuvwxyz123456"
        self.valid_fred_key = "abcdefghijklmnopqrstuvwxyz123456"
        self.invalid_short_key = "short"
        
    def test_get_api_key_from_environment(self):
        """測試從環境變數獲取API金鑰"""
        with unittest.mock.patch.dict('os.environ', {'TEST_API_KEY': self.valid_tiingo_key}):
            with unittest.mock.patch('src.data_sources.api_client.validate_api_key_format', return_value=True):
                result = get_api_key('TEST_API_KEY')
                self.assertEqual(result, self.valid_tiingo_key)
    
    def test_get_api_key_required_not_found(self):
        """測試必要金鑰未找到時拋出異常"""
        with unittest.mock.patch.dict('os.environ', {}, clear=True):
            with self.assertRaises(ValueError) as context:
                get_api_key('NONEXISTENT_KEY', required=True)
            self.assertIn("未設定或格式無效", str(context.exception))
    
    def test_get_api_key_optional_not_found(self):
        """測試選用金鑰未找到時返回None"""
        with unittest.mock.patch.dict('os.environ', {}, clear=True):
            result = get_api_key('NONEXISTENT_KEY', required=False)
            self.assertIsNone(result)
    
    def test_validate_tiingo_api_key_format_valid(self):
        """測試有效的Tiingo API金鑰格式"""
        self.assertTrue(validate_api_key_format('TIINGO_API_KEY', self.valid_tiingo_key))
    
    def test_validate_tiingo_api_key_format_invalid(self):
        """測試無效的Tiingo API金鑰格式"""
        self.assertFalse(validate_api_key_format('TIINGO_API_KEY', self.invalid_short_key))
        self.assertFalse(validate_api_key_format('TIINGO_API_KEY', ''))
        self.assertFalse(validate_api_key_format('TIINGO_API_KEY', None))
    
    def test_validate_fred_api_key_format_valid(self):
        """測試有效的FRED API金鑰格式"""
        self.assertTrue(validate_api_key_format('FRED_API_KEY', self.valid_fred_key))
    
    def test_validate_fred_api_key_format_invalid(self):
        """測試無效的FRED API金鑰格式"""
        # FRED金鑰必須是32字符
        self.assertFalse(validate_api_key_format('FRED_API_KEY', 'abcdefghijklmnopqrstuvwxyz12345'))  # 31字符
        self.assertFalse(validate_api_key_format('FRED_API_KEY', 'abcdefghijklmnopqrstuvwxyz1234567'))  # 33字符


class TestAPIConnectivity(unittest.TestCase):
    """測試API連通性功能"""
    
    def setUp(self):
        """測試前準備"""
        self.valid_key = "test_api_key_123456789012345678"
        
    @unittest.mock.patch('src.data_sources.api_client.requests.get')
    def test_tiingo_api_connectivity_success(self, mock_get):
        """測試Tiingo API連通性成功"""
        # 模擬成功的API回應
        mock_response = unittest.mock.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {'date': '2024-01-01T00:00:00.000Z', 'adjClose': 476.28}
        ]
        mock_get.return_value = mock_response
        
        result = test_api_connectivity('tiingo', self.valid_key)
        
        self.assertEqual(result['service'], 'tiingo')
        self.assertTrue(result['is_connected'])
        self.assertEqual(result['status_code'], 200)
        self.assertIsNone(result['error_message'])
        self.assertIsNotNone(result['response_time'])
    
    @unittest.mock.patch('src.data_sources.api_client.requests.get')
    def test_tiingo_api_connectivity_failure(self, mock_get):
        """測試Tiingo API連通性失敗"""
        # 模擬失敗的API回應
        mock_response = unittest.mock.Mock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"
        mock_get.return_value = mock_response
        
        result = test_api_connectivity('tiingo', 'invalid_key')
        
        self.assertEqual(result['service'], 'tiingo')
        self.assertFalse(result['is_connected'])
        self.assertEqual(result['status_code'], 401)
        self.assertEqual(result['error_message'], "API金鑰無效或已過期")
    
    @unittest.mock.patch('src.data_sources.api_client.requests.get')
    def test_fred_api_connectivity_success(self, mock_get):
        """測試FRED API連通性成功"""
        mock_response = unittest.mock.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'observations': [
                {'date': '2024-01-01', 'value': '5.02'}
            ]
        }
        mock_get.return_value = mock_response
        
        result = test_api_connectivity('fred', self.valid_key)
        
        self.assertEqual(result['service'], 'fred')
        self.assertTrue(result['is_connected'])
        self.assertEqual(result['status_code'], 200)
        self.assertIsNone(result['error_message'])
    
    def test_unsupported_api_service(self):
        """測試不支援的API服務"""
        result = test_api_connectivity('unsupported', self.valid_key)
        
        self.assertEqual(result['service'], 'unsupported')
        self.assertFalse(result['is_connected'])
        self.assertIn("不支援的API服務", result['error_message'])


class TestAPIFaultTolerance(unittest.TestCase):
    """測試API容錯機制"""
    
    def setUp(self):
        """測試前準備"""
        self.fault_manager = APIFaultToleranceManager()
    
    def test_fetch_with_retry_success_first_attempt(self):
        """測試第一次嘗試就成功的情況"""
        mock_function = unittest.mock.Mock(return_value="success")
        
        result = self.fault_manager.fetch_with_retry(mock_function, "arg1", "arg2")
        
        self.assertEqual(result, "success")
        mock_function.assert_called_once_with("arg1", "arg2")
    
    def test_fetch_with_retry_success_after_retries(self):
        """測試重試後成功的情況"""
        mock_function = unittest.mock.Mock(side_effect=[
            requests.exceptions.Timeout("Timeout"),
            requests.exceptions.ConnectionError("Connection failed"),
            "success"
        ])
        
        with unittest.mock.patch('time.sleep'):  # 跳過實際的延遲
            result = self.fault_manager.fetch_with_retry(mock_function)
        
        self.assertEqual(result, "success")
        self.assertEqual(mock_function.call_count, 3)
    
    def test_fetch_with_retry_all_attempts_fail(self):
        """測試所有重試都失敗的情況"""
        mock_function = unittest.mock.Mock(side_effect=requests.exceptions.Timeout("Persistent timeout"))
        
        with unittest.mock.patch('time.sleep'):
            with self.assertRaises(requests.exceptions.Timeout):
                self.fault_manager.fetch_with_retry(mock_function)
        
        self.assertEqual(mock_function.call_count, 3)  # 預設最大重試次數
    
    def test_execute_fallback_strategy_simulation(self):
        """測試備援策略執行 - 模擬數據"""
        with unittest.mock.patch.object(self.fault_manager, '_generate_simulation_data') as mock_sim:
            mock_sim.return_value = [{'date': '2024-01-01', 'adjClose': 400.0}]
            
            data, method = self.fault_manager.execute_fallback_strategy(
                'tiingo', '2024-01-01', '2024-01-02'
            )
            
            self.assertEqual(method, 'simulation')
            self.assertIsNotNone(data)
            self.assertEqual(len(data), 1)


class TestTradingCalendar(unittest.TestCase):
    """測試交易日曆功能"""
    
    def setUp(self):
        """測試前準備"""
        self.base_date = datetime(2025, 1, 1)
    
    def test_calculate_period_start_date_monthly(self):
        """測試每月期初日期計算"""
        # 第1期：2025-01-01
        result = calculate_period_start_date(self.base_date, 'monthly', 1)
        self.assertEqual(result, datetime(2025, 1, 1))
        
        # 第2期：2025-02-01
        result = calculate_period_start_date(self.base_date, 'monthly', 2)
        self.assertEqual(result, datetime(2025, 2, 1))
        
        # 第13期：2026-01-01
        result = calculate_period_start_date(self.base_date, 'monthly', 13)
        self.assertEqual(result, datetime(2026, 1, 1))
    
    def test_calculate_period_start_date_quarterly(self):
        """測試每季期初日期計算"""
        # 第1期：2025-01-01
        result = calculate_period_start_date(self.base_date, 'quarterly', 1)
        self.assertEqual(result, datetime(2025, 1, 1))
        
        # 第2期：2025-04-01
        result = calculate_period_start_date(self.base_date, 'quarterly', 2)
        self.assertEqual(result, datetime(2025, 4, 1))
        
        # 第5期：2026-01-01
        result = calculate_period_start_date(self.base_date, 'quarterly', 5)
        self.assertEqual(result, datetime(2026, 1, 1))
    
    def test_calculate_period_end_dates_monthly(self):
        """測試每月期末日期計算"""
        # 第1期：2025-01-31
        result = calculate_period_end_dates(self.base_date, 'monthly', 1)
        self.assertEqual(result, datetime(2025, 1, 31))
        
        # 第2期：2025-02-28 (非閏年)
        result = calculate_period_end_dates(self.base_date, 'monthly', 2)
        self.assertEqual(result, datetime(2025, 2, 28))
    
    def test_calculate_period_end_dates_quarterly(self):
        """測試每季期末日期計算"""
        # 第1期：2025-03-31
        result = calculate_period_end_dates(self.base_date, 'quarterly', 1)
        self.assertEqual(result, datetime(2025, 3, 31))
        
        # 第2期：2025-06-30
        result = calculate_period_end_dates(self.base_date, 'quarterly', 2)
        self.assertEqual(result, datetime(2025, 6, 30))
    
    def test_calculate_dates_invalid_frequency(self):
        """測試無效頻率的錯誤處理"""
        with self.assertRaises(ValueError):
            calculate_period_start_date(self.base_date, 'invalid', 1)
        
        with self.assertRaises(ValueError):
            calculate_period_end_dates(self.base_date, 'invalid', 1)
    
    def test_calculate_dates_invalid_period_number(self):
        """測試無效期數的錯誤處理"""
        with self.assertRaises(ValueError):
            calculate_period_start_date(self.base_date, 'monthly', 0)
        
        with self.assertRaises(ValueError):
            calculate_period_end_dates(self.base_date, 'monthly', -1)
    
    def test_is_trading_day_weekdays(self):
        """測試工作日是否為交易日"""
        # 2025-01-02 是週四，應該是交易日
        thursday = datetime(2025, 1, 2)
        self.assertTrue(is_trading_day(thursday))
        
        # 2025-01-03 是週五，應該是交易日
        friday = datetime(2025, 1, 3)
        self.assertTrue(is_trading_day(friday))
    
    def test_is_trading_day_weekends(self):
        """測試週末不是交易日"""
        # 2025-01-04 是週六
        saturday = datetime(2025, 1, 4)
        self.assertFalse(is_trading_day(saturday))
        
        # 2025-01-05 是週日
        sunday = datetime(2025, 1, 5)
        self.assertFalse(is_trading_day(sunday))
    
    def test_is_trading_day_holidays(self):
        """測試假期不是交易日"""
        # 2025-01-01 是元旦
        new_year = datetime(2025, 1, 1)
        self.assertFalse(is_trading_day(new_year))
        
        # 2025-12-25 是聖誕節
        christmas = datetime(2025, 12, 25)
        self.assertFalse(is_trading_day(christmas))
    
    def test_adjust_for_trading_days_next(self):
        """測試向後調整到交易日"""
        # 2025-01-01 (元旦, 週三) -> 2025-01-02 (週四)
        new_year = datetime(2025, 1, 1)
        adjusted = adjust_for_trading_days(new_year, 'next')
        self.assertEqual(adjusted, datetime(2025, 1, 2))
    
    def test_adjust_for_trading_days_previous(self):
        """測試向前調整到交易日"""
        # 2025-01-01 (元旦, 週三) -> 2024-12-31 (週二)
        new_year = datetime(2025, 1, 1)
        adjusted = adjust_for_trading_days(new_year, 'previous')
        self.assertEqual(adjusted, datetime(2024, 12, 31))
    
    def test_adjust_for_trading_days_invalid_type(self):
        """測試無效調整類型"""
        with self.assertRaises(ValueError):
            adjust_for_trading_days(datetime.now(), 'invalid')
    
    def test_generate_trading_days(self):
        """測試生成交易日列表"""
        # 2025-01-01 到 2025-01-05 (包含元旦假期和週末)
        start = datetime(2025, 1, 1)
        end = datetime(2025, 1, 5)
        
        trading_days = generate_trading_days(start, end)
        
        # 應該只有 01-02 (週四) 和 01-03 (週五) 是交易日
        expected = [datetime(2025, 1, 2), datetime(2025, 1, 3)]
        self.assertEqual(trading_days, expected)
    
    def test_generate_trading_days_invalid_range(self):
        """測試無效日期範圍"""
        start = datetime(2025, 1, 5)
        end = datetime(2025, 1, 1)
        
        with self.assertRaises(ValueError):
            generate_trading_days(start, end)
    
    def test_generate_investment_timeline_monthly(self):
        """測試生成每月投資時間軸"""
        timeline = generate_investment_timeline(1, 'monthly', 2025)
        
        self.assertEqual(len(timeline), 12)  # 12個月
        
        # 檢查第1期
        first_period = timeline[0]
        self.assertEqual(first_period['period'], 1)
        self.assertEqual(first_period['raw_start_date'], datetime(2025, 1, 1))
        self.assertEqual(first_period['raw_end_date'], datetime(2025, 1, 31))
        
        # 檢查最後一期
        last_period = timeline[-1]
        self.assertEqual(last_period['period'], 12)
        self.assertEqual(last_period['raw_start_date'], datetime(2025, 12, 1))
        self.assertEqual(last_period['raw_end_date'], datetime(2025, 12, 31))
    
    def test_generate_investment_timeline_quarterly(self):
        """測試生成每季投資時間軸"""
        timeline = generate_investment_timeline(1, 'quarterly', 2025)
        
        self.assertEqual(len(timeline), 4)  # 4個季度
        
        # 檢查各季度的起始月份
        expected_start_months = [1, 4, 7, 10]
        expected_end_months = [3, 6, 9, 12]
        
        for i, period in enumerate(timeline):
            self.assertEqual(period['raw_start_date'].month, expected_start_months[i])
            self.assertEqual(period['raw_end_date'].month, expected_end_months[i])
    
    def test_generate_investment_timeline_invalid_parameters(self):
        """測試無效參數的錯誤處理"""
        with self.assertRaises(ValueError):
            generate_investment_timeline(0, 'monthly')  # 無效年數
        
        with self.assertRaises(ValueError):
            generate_investment_timeline(1, 'invalid')  # 無效頻率
    
    def test_get_target_dates_for_data_fetching(self):
        """測試提取數據獲取目標日期"""
        timeline = generate_investment_timeline(1, 'quarterly', 2025)
        
        overall_start, overall_end, key_dates = get_target_dates_for_data_fetching(timeline)
        
        # 檢查整體範圍
        self.assertEqual(overall_start.year, 2025)
        self.assertEqual(overall_start.month, 1)
        self.assertEqual(overall_end.year, 2025)
        self.assertEqual(overall_end.month, 12)
        
        # 檢查關鍵日期數量 (4個季度 × 2個日期 = 8個，但可能有重複)
        self.assertGreaterEqual(len(key_dates), 4)
        self.assertLessEqual(len(key_dates), 8)
    
    def test_get_target_dates_empty_timeline(self):
        """測試空時間軸的錯誤處理"""
        with self.assertRaises(ValueError):
            get_target_dates_for_data_fetching([])


class TestDataFetchers(unittest.TestCase):
    """測試數據獲取器"""
    
    def setUp(self):
        """測試前準備"""
        self.tiingo_key = "test_tiingo_key_123456789012345"
        self.fred_key = "test_fred_key_abcdefghijklmnopqrs"
        
    @unittest.mock.patch('src.data_sources.data_fetcher.requests.get')
    def test_tiingo_fetch_spy_data_success(self, mock_get):
        """測試Tiingo獲取SPY數據成功"""
        # 模擬API回應
        mock_response = unittest.mock.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {'date': '2024-01-01T00:00:00.000Z', 'adjClose': 476.28},
            {'date': '2024-01-02T00:00:00.000Z', 'adjClose': 478.50}
        ]
        mock_get.return_value = mock_response
        
        fetcher = TiingoDataFetcher(self.tiingo_key)
        
        with unittest.mock.patch.object(fetcher.fault_tolerance, 'fetch_with_retry') as mock_retry:
            mock_retry.return_value = mock_response.json.return_value
            
            result = fetcher.fetch_spy_data('2024-01-01', '2024-01-02')
            
            self.assertEqual(len(result), 2)
            self.assertEqual(result[0]['date'], '2024-01-01')
            self.assertEqual(result[0]['adjClose'], 476.28)
            self.assertEqual(result[1]['date'], '2024-01-02')
            self.assertEqual(result[1]['adjClose'], 478.50)
    
    @unittest.mock.patch('src.data_sources.data_fetcher.requests.get')
    def test_fred_fetch_yield_data_success(self, mock_get):
        """測試FRED獲取殖利率數據成功"""
        # 模擬API回應
        mock_response = unittest.mock.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'observations': [
                {'date': '2024-01-01', 'value': '5.02'},
                {'date': '2024-01-02', 'value': '5.05'},
                {'date': '2024-01-03', 'value': '.'}  # 缺失數據
            ]
        }
        mock_get.return_value = mock_response
        
        fetcher = FREDDataFetcher(self.fred_key)
        
        with unittest.mock.patch.object(fetcher.fault_tolerance, 'fetch_with_retry') as mock_retry:
            mock_retry.return_value = mock_response.json.return_value
            
            result = fetcher.fetch_yield_data('2024-01-01', '2024-01-03')
            
            # 應該只有2筆有效數據（排除缺失值）
            self.assertEqual(len(result), 2)
            self.assertEqual(result[0]['date'], '2024-01-01')
            self.assertEqual(result[0]['value'], '5.02')
    
    def test_fred_calculate_bond_prices(self):
        """測試債券價格計算"""
        fetcher = FREDDataFetcher(self.fred_key)
        
        yields = {
            '2024-01-01': 5.0,   # 5% -> 債券價格約 95.24
            '2024-01-02': 3.0,   # 3% -> 債券價格約 97.09
            '2024-01-03': 0.0    # 0% -> 債券價格 100.00
        }
        
        prices = fetcher.calculate_bond_prices(yields)
        
        self.assertEqual(len(prices), 3)
        self.assertAlmostEqual(prices['2024-01-01'], 95.24, places=2)
        self.assertAlmostEqual(prices['2024-01-02'], 97.09, places=2)
        self.assertAlmostEqual(prices['2024-01-03'], 100.0, places=2)
    
    def test_tiingo_get_target_prices(self):
        """測試獲取目標日期價格"""
        fetcher = TiingoDataFetcher(self.tiingo_key)
        
        # 模擬fetch_spy_data回應
        with unittest.mock.patch.object(fetcher, 'fetch_spy_data') as mock_fetch:
            mock_fetch.return_value = [
                {'date': '2024-01-01', 'adjClose': 476.28},
                {'date': '2024-01-02', 'adjClose': 478.50},
                {'date': '2024-01-03', 'adjClose': 480.75}
            ]
            
            target_dates = [
                datetime(2024, 1, 1),
                datetime(2024, 1, 3)
            ]
            
            result = fetcher.get_target_prices(target_dates)
            
            self.assertEqual(len(result), 2)
            self.assertEqual(result['2024-01-01'], 476.28)
            self.assertEqual(result['2024-01-03'], 480.75)
    
    def test_batch_fetcher_initialization(self):
        """測試批次獲取器初始化"""
        batch_fetcher = BatchDataFetcher(self.tiingo_key, self.fred_key)
        
        self.assertIsNotNone(batch_fetcher.tiingo_fetcher)
        self.assertIsNotNone(batch_fetcher.fred_fetcher)
        self.assertIsNotNone(batch_fetcher.data_factory)


if __name__ == '__main__':
    # 設定測試日誌層級
    import logging
    logging.basicConfig(level=logging.WARNING)
    
    unittest.main() 