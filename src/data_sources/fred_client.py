"""
FRED客戶端模組 - 第1章數據源規格實現

實現多層級API金鑰獲取、容錯機制和精確的數據處理。
嚴格按照第1章需求規格：
- 多層級金鑰獲取：Streamlit Secrets → 環境變數 → .env檔案
- APIFaultToleranceManager 容錯機制
- 重試機制：max_retries=3, base_delay=1.0, backoff_factor=2.0
- API端點：https://api.stlouisfed.org/fred/series/observations
- 殖利率精度：小數點後4位
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
YIELD_PRECISION = 4  # 殖利率精度：小數點後4位
PERCENTAGE_PRECISION_RULES = {
    'price_precision': 2,
    'yield_precision': 4,
    'percentage_precision': 2
}

class FREDDataFetcher:
    """
    FRED數據獲取器 - 第1章規格實現
    
    功能：
    - 多層級API金鑰獲取
    - 容錯機制與重試
    - 精確的數據處理
    - 1年期國債殖利率獲取
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        初始化FRED數據獲取器
        
        Args:
            api_key: API金鑰，如果未提供則使用多層級獲取
        """
        # 多層級API金鑰獲取：Streamlit Secrets → 環境變數 → .env檔案
        if api_key is None:
            api_key = get_api_key('FRED_API_KEY')
        
        if not api_key:
            raise ValueError("無法獲取FRED API金鑰")
        
        if not validate_api_key_format('FRED_API_KEY', api_key):
            raise ValueError("FRED API金鑰格式無效")
        
        self.api_key = api_key
        self.base_url = "https://api.stlouisfed.org/fred/series/observations"
        
        # 第1章規格：APIFaultToleranceManager 容錯機制
        from .fault_tolerance import RetryConfig
        retry_config = RetryConfig(
            max_retries=3,
            base_delay=1.0,
            backoff_factor=2.0
        )
        self.fault_tolerance = APIFaultToleranceManager(retry_config)
        
        logger.info("FRED數據獲取器已初始化")
    
    def get_treasury_yields(self, start_date: str, end_date: str, series_id: str = "DGS1") -> List[MarketDataPoint]:
        """
        獲取美國國債殖利率數據
        
        Args:
            start_date: 起始日期 (YYYY-MM-DD)
            end_date: 結束日期 (YYYY-MM-DD)
            series_id: FRED系列ID，預設為DGS1（1年期國債）
            
        Returns:
            List[MarketDataPoint]: 市場數據點列表
        """
        params = {
            'series_id': series_id,
            'observation_start': start_date,
            'observation_end': end_date,
            'api_key': self.api_key,
            'file_type': 'json',
            'frequency': 'd',  # 日頻率
            'sort_order': 'asc'
        }
        
        logger.info(f"正在獲取FRED數據: {series_id} {start_date} 至 {end_date}")
        
        try:
            # 使用容錯機制執行API請求
            response_data = self.fault_tolerance.execute_with_retry(
                self._make_api_request,
                self.base_url,
                params
            )
            
            if not response_data:
                logger.error("FRED API請求失敗")
                return []
            
            # 轉換為MarketDataPoint對象，確保殖利率精度
            market_data = self._convert_to_market_data(response_data)
            
            logger.info(f"成功獲取 {len(market_data)} 筆FRED數據")
            return market_data
            
        except Exception as e:
            logger.error(f"獲取FRED數據失敗: {str(e)}")
            return []
    
    def _make_api_request(self, url: str, params: Dict[str, Any]) -> Optional[Dict]:
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
            
            if 'observations' not in data:
                raise ValueError("API回應格式錯誤")
            
            return data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"API請求失敗: {str(e)}")
            raise e
        except Exception as e:
            logger.error(f"處理API回應失敗: {str(e)}")
            raise e
    
    def _convert_to_market_data(self, api_data: Dict) -> List[MarketDataPoint]:
        """
        轉換API數據為MarketDataPoint對象
        
        Args:
            api_data: API回應數據
            
        Returns:
            List[MarketDataPoint]: 市場數據點列表
        """
        market_data = []
        
        for obs in api_data.get('observations', []):
            try:
                # 跳過缺失值（FRED用'.'表示缺失值）
                if obs['value'] == '.':
                    continue
                
                # 確保殖利率精度：小數點後4位
                yield_value = round(float(obs['value']), YIELD_PRECISION)
                
                # 簡化債券定價計算
                bond_price = round(100.0 / (1 + yield_value/100), 2)
                
                data_point = MarketDataPoint(
                    date=obs['date'],
                    spy_price=0.0,  # FRED不提供股票價格
                    bond_yield=yield_value,
                    bond_price=bond_price,
                    data_source='fred'
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
        test_params = {
            'series_id': 'DGS1',
            'limit': '1',
            'api_key': self.api_key,
            'file_type': 'json'
        }
        
        start_time = time.time()
        
        try:
            response = requests.get(self.base_url, params=test_params, timeout=10)
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                result_data = response.json()
                if 'observations' in result_data:
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
    
    def get_optimized_treasury_data(self, target_dates: List[str], series_id: str = "DGS1") -> List[MarketDataPoint]:
        """
        獲取優化的國債數據（針對特定日期）
        
        Args:
            target_dates: 目標日期列表
            series_id: FRED系列ID
            
        Returns:
            List[MarketDataPoint]: 市場數據點列表
        """
        if not target_dates:
            return []
        
        # 確定日期範圍
        start_date = min(target_dates)
        end_date = max(target_dates)
        
        # 獲取完整日期範圍的數據
        all_data = self.get_treasury_yields(start_date, end_date, series_id)
        
        # 篩選目標日期的數據
        target_data = []
        target_date_set = set(target_dates)
        
        for data_point in all_data:
            if data_point.date in target_date_set:
                target_data.append(data_point)
        
        return target_data


# 向後兼容性別名
FREDAPIClient = FREDDataFetcher 