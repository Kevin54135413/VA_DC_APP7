"""
Tiingo客戶端模組 - 第1章數據源規格實現

實現多層級API金鑰獲取、容錯機制和精確的數據處理。
嚴格按照第1章需求規格：
- 多層級金鑰獲取：Streamlit Secrets → 環境變數 → .env檔案
- APIFaultToleranceManager 容錯機制
- 重試機制：max_retries=3, base_delay=1.0, backoff_factor=2.0
- API端點：https://api.tiingo.com/tiingo/daily/SPY/prices
- 價格精度：小數點後2位
"""

import requests
import logging
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
import pandas as pd

from ..utils.api_security import get_api_key, validate_api_key_format
from ..models.data_models import MarketDataPoint, DataModelFactory
from .fault_tolerance import APIFaultToleranceManager

logger = logging.getLogger(__name__)

# 第1章規格：數據精度規則
PRICE_PRECISION = 2  # 價格精度：小數點後2位
PERCENTAGE_PRECISION_RULES = {
    'price_precision': 2,
    'yield_precision': 4,
    'percentage_precision': 2
}

class TiingoDataFetcher:
    """
    Tiingo數據獲取器 - 第1章規格實現
    
    功能：
    - 多層級API金鑰獲取
    - 容錯機制與重試
    - 精確的數據處理
    - 批次獲取優化
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        初始化Tiingo數據獲取器
        
        Args:
            api_key: API金鑰，如果未提供則使用多層級獲取
        """
        # 多層級API金鑰獲取：Streamlit Secrets → 環境變數 → .env檔案
        if api_key is None:
            api_key = get_api_key('TIINGO_API_KEY')
        
        if not api_key:
            raise ValueError("無法獲取Tiingo API金鑰")
        
        if not validate_api_key_format('TIINGO_API_KEY', api_key):
            raise ValueError("Tiingo API金鑰格式無效")
        
        self.api_key = api_key
        self.base_url = "https://api.tiingo.com/tiingo/daily"
        
        # 第1章規格：APIFaultToleranceManager 容錯機制
        from .fault_tolerance import RetryConfig
        retry_config = RetryConfig(
            max_retries=3,
            base_delay=1.0,
            backoff_factor=2.0
        )
        self.fault_tolerance = APIFaultToleranceManager(retry_config)
        
        logger.info("Tiingo數據獲取器已初始化")
    
    def get_spy_prices(self, start_date: str, end_date: str) -> List[MarketDataPoint]:
        """
        獲取SPY股票價格數據
        
        Args:
            start_date: 起始日期 (YYYY-MM-DD)
            end_date: 結束日期 (YYYY-MM-DD)
            
        Returns:
            List[MarketDataPoint]: 市場數據點列表
        """
        # 第1章規格：API端點
        url = f"{self.base_url}/SPY/prices"
        
        params = {
            'startDate': start_date,
            'endDate': end_date,
            'columns': 'date,adjClose',
            'token': self.api_key
        }
        
        logger.info(f"正在獲取SPY數據: {start_date} 至 {end_date}")
        
        try:
            # 使用容錯機制執行API請求
            response_data = self.fault_tolerance.execute_with_retry(
                self._make_api_request,
                url,
                params
            )
            
            if not response_data:
                logger.error("Tiingo API請求失敗")
                return []
            
            # 轉換為MarketDataPoint對象，確保價格精度
            market_data = self._convert_to_market_data(response_data)
            
            logger.info(f"成功獲取 {len(market_data)} 筆SPY數據")
            return market_data
            
        except Exception as e:
            logger.error(f"獲取SPY數據失敗: {str(e)}")
            return []
    
    def _make_api_request(self, url: str, params: Dict[str, Any]) -> Optional[List[Dict]]:
        """
        執行API請求
        
        Args:
            url: API端點URL
            params: 請求參數
            
        Returns:
            API回應數據
        """
        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            if not isinstance(data, list):
                raise ValueError("API回應格式錯誤")
            
            return data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"API請求失敗: {str(e)}")
            raise e
        except Exception as e:
            logger.error(f"處理API回應失敗: {str(e)}")
            raise e
    
    def _convert_to_market_data(self, api_data: List[Dict]) -> List[MarketDataPoint]:
        """
        轉換API數據為MarketDataPoint對象
        
        Args:
            api_data: API回應數據
            
        Returns:
            List[MarketDataPoint]: 市場數據點列表
        """
        market_data = []
        
        for item in api_data:
            try:
                # 確保價格精度：小數點後2位
                price = round(float(item['adjClose']), PRICE_PRECISION)
                
                # 提取日期（取YYYY-MM-DD部分）
                date_str = item['date'][:10]
                
                data_point = MarketDataPoint(
                    date=date_str,
                    spy_price=price,
                    bond_yield=None,
                    bond_price=None,
                    data_source='tiingo'
                )
                
                market_data.append(data_point)
                
            except (KeyError, ValueError, TypeError) as e:
                logger.warning(f"跳過無效數據點: {str(e)}")
                continue
        
        return market_data
    
    def test_connectivity(self) -> Dict[str, Any]:
        """
        測試API連通性
        
        Returns:
            Dict[str, Any]: 連通性測試結果
        """
        test_url = "https://api.tiingo.com/api/test"
        params = {'token': self.api_key}
        
        start_time = time.time()
        
        try:
            response = requests.get(test_url, params=params, timeout=10)
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                result_data = response.json()
                if result_data.get('message') == 'You successfully sent a request':
                    return {
                        'is_connected': True,
                        'response_time_ms': round(response_time, 2),
                        'status_code': 200,
                        'error_message': None
                    }
            
            return {
                'is_connected': False,
                'response_time_ms': round(response_time, 2),
                'status_code': response.status_code,
                'error_message': f'API測試失敗: {response.text[:100]}'
            }
            
        except requests.exceptions.Timeout:
            return {
                'is_connected': False,
                'response_time_ms': (time.time() - start_time) * 1000,
                'status_code': 0,
                'error_message': 'API請求逾時'
            }
        except requests.exceptions.ConnectionError:
            return {
                'is_connected': False,
                'response_time_ms': (time.time() - start_time) * 1000,
                'status_code': 0,
                'error_message': 'API連線失敗'
            }
        except Exception as e:
            return {
                'is_connected': False,
                'response_time_ms': (time.time() - start_time) * 1000,
                'status_code': 0,
                'error_message': f'API測試異常: {str(e)}'
            }
    
    def get_optimized_spy_data(self, target_dates: List[str]) -> List[MarketDataPoint]:
        """
        獲取優化的SPY數據（針對特定日期）
        
        Args:
            target_dates: 目標日期列表
            
        Returns:
            List[MarketDataPoint]: 市場數據點列表
        """
        if not target_dates:
            return []
        
        # 確定日期範圍
        start_date = min(target_dates)
        end_date = max(target_dates)
        
        # 獲取完整日期範圍的數據
        all_data = self.get_spy_prices(start_date, end_date)
        
        # 篩選目標日期的數據
        target_data = []
        target_date_set = set(target_dates)
        
        for data_point in all_data:
            if data_point.date in target_date_set:
                target_data.append(data_point)
        
        return target_data


# 向後兼容性別名
TiingoAPIClient = TiingoDataFetcher 