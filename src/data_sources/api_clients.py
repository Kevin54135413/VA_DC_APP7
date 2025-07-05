"""
API客戶端模組
實現第一章規格中定義的Tiingo和FRED API數據獲取功能
"""

import requests
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import pandas as pd

from ..utils.api_security import safe_api_request, APIKeyManager
from ..models.data_models import MarketDataPoint, DataModelFactory

logger = logging.getLogger(__name__)


class TiingoAPIClient:
    """Tiingo API客戶端"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.tiingo.com"
        
    def get_spy_prices(self, start_date: str, end_date: str) -> List[MarketDataPoint]:
        """
        獲取SPY股票價格數據
        
        Args:
            start_date: 起始日期 (YYYY-MM-DD)
            end_date: 結束日期 (YYYY-MM-DD)
            
        Returns:
            List[MarketDataPoint]: 市場數據點列表
        """
        url = f"{self.base_url}/tiingo/daily/SPY/prices"
        
        params = {
            'startDate': start_date,
            'endDate': end_date,
            'columns': 'date,adjClose',
            'token': self.api_key
        }
        
        logger.info(f"正在獲取SPY數據: {start_date} 至 {end_date}")
        
        response_data = safe_api_request(url, params, "Tiingo")
        
        if response_data is None:
            logger.error("Tiingo API請求失敗")
            return []
        
        # 轉換為MarketDataPoint對象
        market_data = DataModelFactory.create_market_data_from_api(response_data, 'tiingo')
        
        logger.info(f"成功獲取 {len(market_data)} 筆SPY數據")
        return market_data
    
    def get_optimized_spy_data(self, target_dates: List[str]) -> Dict[str, float]:
        """
        優化版SPY數據獲取 - 一次性獲取範圍數據然後提取目標日期
        
        Args:
            target_dates: 目標日期列表 (YYYY-MM-DD格式)
            
        Returns:
            Dict[str, float]: 日期對應價格的字典
        """
        if not target_dates:
            return {}
        
        # 確定數據範圍
        start_date = min(target_dates)
        end_date = max(target_dates)
        
        # 獲取完整範圍的數據
        all_data = self.get_spy_prices(start_date, end_date)
        
        # 建立日期到價格的映射
        price_map = {data.date: data.spy_price for data in all_data}
        
        # 提取目標日期的價格
        result = {}
        for date in target_dates:
            if date in price_map:
                result[date] = price_map[date]
            else:
                # 尋找最接近的前一個交易日
                closest_date = self._find_closest_trading_day(date, price_map)
                if closest_date:
                    result[date] = price_map[closest_date]
                    logger.warning(f"日期 {date} 無數據，使用 {closest_date} 的價格")
        
        return result
    
    def _find_closest_trading_day(self, target_date: str, price_map: Dict[str, float]) -> Optional[str]:
        """尋找最接近的前一個交易日"""
        target = datetime.strptime(target_date, '%Y-%m-%d')
        
        # 往前尋找最多10天
        for i in range(10):
            check_date = target - timedelta(days=i)
            check_date_str = check_date.strftime('%Y-%m-%d')
            if check_date_str in price_map:
                return check_date_str
        
        return None


class FREDAPIClient:
    """FRED API客戶端"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.stlouisfed.org/fred"
        
    def get_bond_yields(self, start_date: str, end_date: str) -> List[MarketDataPoint]:
        """
        獲取1年期國債殖利率數據
        
        Args:
            start_date: 起始日期 (YYYY-MM-DD)
            end_date: 結束日期 (YYYY-MM-DD)
            
        Returns:
            List[MarketDataPoint]: 市場數據點列表
        """
        url = f"{self.base_url}/series/observations"
        
        params = {
            'series_id': 'DGS1',
            'observation_start': start_date,
            'observation_end': end_date,
            'api_key': self.api_key,
            'file_type': 'json'
        }
        
        logger.info(f"正在獲取債券殖利率數據: {start_date} 至 {end_date}")
        
        response_data = safe_api_request(url, params, "FRED")
        
        if response_data is None:
            logger.error("FRED API請求失敗")
            return []
        
        # 轉換為MarketDataPoint對象
        market_data = DataModelFactory.create_market_data_from_api(response_data, 'fred')
        
        logger.info(f"成功獲取 {len(market_data)} 筆債券數據")
        return market_data
    
    def get_optimized_bond_data(self, target_dates: List[str]) -> Dict[str, tuple]:
        """
        優化版債券數據獲取
        
        Args:
            target_dates: 目標日期列表
            
        Returns:
            Dict[str, tuple]: 日期對應(殖利率, 債券價格)的字典
        """
        if not target_dates:
            return {}
        
        # 確定數據範圍
        start_date = min(target_dates)
        end_date = max(target_dates)
        
        # 獲取完整範圍的數據
        all_data = self.get_bond_yields(start_date, end_date)
        
        # 建立日期到數據的映射
        data_map = {
            data.date: (data.bond_yield, data.bond_price) 
            for data in all_data 
            if data.bond_yield is not None
        }
        
        # 提取目標日期的數據
        result = {}
        for date in target_dates:
            if date in data_map:
                result[date] = data_map[date]
            else:
                # 尋找最接近的前一個交易日
                closest_date = self._find_closest_trading_day(date, data_map)
                if closest_date:
                    result[date] = data_map[closest_date]
                    logger.warning(f"日期 {date} 無債券數據，使用 {closest_date} 的數據")
        
        return result
    
    def _find_closest_trading_day(self, target_date: str, data_map: Dict[str, tuple]) -> Optional[str]:
        """尋找最接近的前一個有數據的交易日"""
        target = datetime.strptime(target_date, '%Y-%m-%d')
        
        # 往前尋找最多30天（債券數據更新頻率較低）
        for i in range(30):
            check_date = target - timedelta(days=i)
            check_date_str = check_date.strftime('%Y-%m-%d')
            if check_date_str in data_map:
                return check_date_str
        
        return None


class MarketDataProvider:
    """統一市場數據提供者"""
    
    def __init__(self, api_key_manager: APIKeyManager):
        self.api_key_manager = api_key_manager
        self.tiingo_client = None
        self.fred_client = None
        
        # 初始化可用的客戶端
        if api_key_manager.is_service_available('tiingo'):
            tiingo_key = api_key_manager.get_key('tiingo')
            self.tiingo_client = TiingoAPIClient(tiingo_key)
            
        if api_key_manager.is_service_available('fred'):
            fred_key = api_key_manager.get_key('fred')
            self.fred_client = FREDAPIClient(fred_key)
    
    def get_complete_market_data(self, start_date: str, end_date: str) -> List[MarketDataPoint]:
        """
        獲取完整的市場數據（股票+債券）
        
        Args:
            start_date: 起始日期
            end_date: 結束日期
            
        Returns:
            List[MarketDataPoint]: 合併後的市場數據
        """
        all_data = {}
        
        # 獲取股票數據
        if self.tiingo_client:
            try:
                spy_data = self.tiingo_client.get_spy_prices(start_date, end_date)
                for data in spy_data:
                    all_data[data.date] = {
                        'date': data.date,
                        'spy_price': data.spy_price,
                        'bond_yield': None,
                        'bond_price': None
                    }
            except Exception as e:
                logger.error(f"獲取SPY數據失敗: {e}")
        
        # 獲取債券數據
        if self.fred_client:
            try:
                bond_data = self.fred_client.get_bond_yields(start_date, end_date)
                for data in bond_data:
                    if data.date in all_data:
                        all_data[data.date]['bond_yield'] = data.bond_yield
                        all_data[data.date]['bond_price'] = data.bond_price
                    else:
                        all_data[data.date] = {
                            'date': data.date,
                            'spy_price': 0.0,  # 將在後面處理
                            'bond_yield': data.bond_yield,
                            'bond_price': data.bond_price
                        }
            except Exception as e:
                logger.error(f"獲取債券數據失敗: {e}")
        
        # 轉換為MarketDataPoint列表
        market_data_points = []
        for date_str in sorted(all_data.keys()):
            data = all_data[date_str]
            try:
                market_data_point = MarketDataPoint(
                    date=data['date'],
                    spy_price=data['spy_price'],
                    bond_yield=data['bond_yield'],
                    bond_price=data['bond_price'],
                    data_source='combined'
                )
                market_data_points.append(market_data_point)
            except ValueError as e:
                # 跳過無效數據
                logger.warning(f"跳過無效數據 {date_str}: {e}")
                continue
        
        return market_data_points
    
    def get_optimized_period_data(self, period_dates: List[Dict[str, str]]) -> Dict:
        """
        優化版期間數據獲取
        
        Args:
            period_dates: 包含期初期末日期的列表
                格式: [{'start': 'YYYY-MM-DD', 'end': 'YYYY-MM-DD'}, ...]
                
        Returns:
            Dict: 期間數據字典
        """
        # 收集所有需要的日期
        all_dates = set()
        for period in period_dates:
            all_dates.add(period['start'])
            all_dates.add(period['end'])
        
        target_dates = sorted(list(all_dates))
        
        result = {
            'spy_data': {},
            'bond_data': {},
            'data_quality': {
                'spy_coverage': 0.0,
                'bond_coverage': 0.0,
                'missing_dates': []
            }
        }
        
        # 獲取股票數據
        if self.tiingo_client:
            try:
                spy_data = self.tiingo_client.get_optimized_spy_data(target_dates)
                result['spy_data'] = spy_data
                result['data_quality']['spy_coverage'] = len(spy_data) / len(target_dates)
            except Exception as e:
                logger.error(f"獲取優化SPY數據失敗: {e}")
        
        # 獲取債券數據
        if self.fred_client:
            try:
                bond_data = self.fred_client.get_optimized_bond_data(target_dates)
                result['bond_data'] = bond_data
                result['data_quality']['bond_coverage'] = len(bond_data) / len(target_dates)
            except Exception as e:
                logger.error(f"獲取優化債券數據失敗: {e}")
        
        # 檢查缺失的日期
        missing_dates = []
        for date in target_dates:
            if date not in result['spy_data'] and date not in result['bond_data']:
                missing_dates.append(date)
        
        result['data_quality']['missing_dates'] = missing_dates
        
        return result
    
    def is_available(self) -> bool:
        """檢查是否有任何可用的數據源"""
        return self.tiingo_client is not None or self.fred_client is not None
    
    def get_availability_status(self) -> Dict[str, bool]:
        """獲取各數據源的可用性狀態"""
        return {
            'tiingo': self.tiingo_client is not None,
            'fred': self.fred_client is not None
        } 