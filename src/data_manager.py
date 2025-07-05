"""
數據管理器
統一管理第一章定義的所有數據源和數據流程
"""

import logging
from typing import List, Dict, Optional, Union
from datetime import datetime

from .utils.api_security import APIKeyManager
from .data_sources.api_clients import MarketDataProvider
from .data_sources.simulation import SimulationDataProvider
from .models.data_models import MarketDataPoint, AggregatedPeriodData, DataModelFactory
from .utils.trading_days import validate_simulation_data

logger = logging.getLogger(__name__)


class DataManager:
    """統一數據管理器"""
    
    def __init__(self):
        """初始化數據管理器"""
        # 初始化API金鑰管理器
        self.api_key_manager = APIKeyManager()
        self.api_key_status = self.api_key_manager.initialize_keys()
        
        # 初始化數據提供者
        self.market_data_provider = MarketDataProvider(self.api_key_manager)
        self.simulation_provider = SimulationDataProvider()
        
        # 測試API連通性
        self.connectivity_status = self.api_key_manager.test_all_connections()
        
        logger.info("數據管理器初始化完成")
        logger.info(f"API金鑰狀態: {self.api_key_status}")
        logger.info(f"API連通性: {self.connectivity_status}")
    
    def get_market_data(self, 
                       start_date: str, 
                       end_date: str, 
                       data_source: str = 'auto') -> List[MarketDataPoint]:
        """
        獲取市場數據
        
        Args:
            start_date: 起始日期 (YYYY-MM-DD)
            end_date: 結束日期 (YYYY-MM-DD)
            data_source: 數據源選擇 ('auto', 'api', 'simulation')
            
        Returns:
            List[MarketDataPoint]: 市場數據列表
        """
        if data_source == 'auto':
            # 自動選擇數據源
            if self.market_data_provider.is_available():
                data_source = 'api'
            else:
                data_source = 'simulation'
                logger.warning("API不可用，切換到模擬數據")
        
        if data_source == 'api':
            return self._get_api_data(start_date, end_date)
        elif data_source == 'simulation':
            return self._get_simulation_data(start_date, end_date)
        else:
            raise ValueError(f"不支援的數據源: {data_source}")
    
    def _get_api_data(self, start_date: str, end_date: str) -> List[MarketDataPoint]:
        """從API獲取數據"""
        if not self.market_data_provider.is_available():
            raise RuntimeError("API數據源不可用")
        
        try:
            market_data = self.market_data_provider.get_complete_market_data(
                start_date, end_date
            )
            logger.info(f"成功從API獲取 {len(market_data)} 筆數據")
            return market_data
        except Exception as e:
            logger.error(f"API數據獲取失敗: {e}")
            raise
    
    def _get_simulation_data(self, start_date: str, end_date: str) -> List[MarketDataPoint]:
        """生成模擬數據"""
        try:
            # 計算模擬年數（簡化計算）
            start = datetime.strptime(start_date, '%Y-%m-%d')
            end = datetime.strptime(end_date, '%Y-%m-%d')
            years = max(1, int((end - start).days / 365))
            
            market_data = self.simulation_provider.generate_complete_simulation(
                investment_years=years,
                frequency='monthly'  # 預設使用月度頻率
            )
            
            # 過濾日期範圍
            filtered_data = [
                data for data in market_data
                if start_date <= data.date <= end_date
            ]
            
            logger.info(f"成功生成 {len(filtered_data)} 筆模擬數據")
            return filtered_data
        except Exception as e:
            logger.error(f"模擬數據生成失敗: {e}")
            raise
    
    def get_period_data(self, 
                       investment_years: int,
                       frequency: str,
                       data_source: str = 'auto') -> List[AggregatedPeriodData]:
        """
        獲取期間聚合數據
        
        Args:
            investment_years: 投資年數
            frequency: 投資頻率
            data_source: 數據源選擇
            
        Returns:
            List[AggregatedPeriodData]: 期間聚合數據列表
        """
        # 計算日期範圍
        if data_source == 'simulation':
            # 模擬數據使用未來日期
            current_year = datetime.now().year
            start_date = f"{current_year + 1}-01-01"
            end_date = f"{current_year + 1 + investment_years}-12-31"
        else:
            # 歷史數據使用過去日期
            current_date = datetime.now()
            start_date = (current_date.replace(year=current_date.year - investment_years)).strftime('%Y-%m-%d')
            end_date = current_date.strftime('%Y-%m-%d')
        
        # 獲取原始數據
        market_data = self.get_market_data(start_date, end_date, data_source)
        
        # 聚合為期間數據
        period_data = DataModelFactory.aggregate_to_periods(
            market_data, frequency, investment_years
        )
        
        logger.info(f"成功聚合 {len(period_data)} 期數據")
        return period_data
    
    def get_optimized_period_data(self,
                                 period_dates: List[Dict[str, str]],
                                 data_source: str = 'auto') -> Dict:
        """
        獲取優化的期間數據（僅獲取需要的日期）
        
        Args:
            period_dates: 期間日期列表
            data_source: 數據源選擇
            
        Returns:
            Dict: 優化的期間數據
        """
        if data_source == 'auto':
            data_source = 'api' if self.market_data_provider.is_available() else 'simulation'
        
        if data_source == 'api' and self.market_data_provider.is_available():
            return self.market_data_provider.get_optimized_period_data(period_dates)
        else:
            # 模擬數據的簡化實現
            all_dates = set()
            for period in period_dates:
                all_dates.add(period['start'])
                all_dates.add(period['end'])
            
            start_date = min(all_dates)
            end_date = max(all_dates)
            
            market_data = self._get_simulation_data(start_date, end_date)
            
            # 轉換為優化格式
            spy_data = {data.date: data.spy_price for data in market_data}
            bond_data = {
                data.date: (data.bond_yield, data.bond_price) 
                for data in market_data 
                if data.bond_yield is not None
            }
            
            return {
                'spy_data': spy_data,
                'bond_data': bond_data,
                'data_quality': {
                    'spy_coverage': len(spy_data) / len(all_dates),
                    'bond_coverage': len(bond_data) / len(all_dates),
                    'missing_dates': []
                }
            }
    
    def validate_data_quality(self, market_data: List[MarketDataPoint]) -> Dict:
        """
        驗證數據品質
        
        Args:
            market_data: 市場數據列表
            
        Returns:
            Dict: 數據品質報告
        """
        if not market_data:
            return {
                'is_valid': False,
                'errors': ['數據為空'],
                'warnings': [],
                'statistics': {}
            }
        
        report = {
            'is_valid': True,
            'errors': [],
            'warnings': [],
            'statistics': {
                'total_records': len(market_data),
                'date_range': {
                    'start': market_data[0].date,
                    'end': market_data[-1].date
                },
                'data_completeness': {
                    'spy_price': sum(1 for d in market_data if d.spy_price > 0) / len(market_data),
                    'bond_yield': sum(1 for d in market_data if d.bond_yield is not None) / len(market_data),
                    'bond_price': sum(1 for d in market_data if d.bond_price is not None) / len(market_data)
                }
            }
        }
        
        # 檢查數據連續性
        dates = [datetime.strptime(d.date, '%Y-%m-%d') for d in market_data]
        for i in range(1, len(dates)):
            gap_days = (dates[i] - dates[i-1]).days
            if gap_days > 7:  # 超過一週的間隔
                report['warnings'].append(
                    f"數據間隔過大: {dates[i-1].strftime('%Y-%m-%d')} 到 {dates[i].strftime('%Y-%m-%d')}"
                )
        
        # 檢查異常值
        spy_prices = [d.spy_price for d in market_data if d.spy_price > 0]
        if spy_prices:
            mean_price = sum(spy_prices) / len(spy_prices)
            for data in market_data:
                if data.spy_price > 0 and abs(data.spy_price - mean_price) / mean_price > 0.5:
                    report['warnings'].append(
                        f"SPY價格異常: {data.date} = {data.spy_price}"
                    )
        
        return report
    
    def get_data_source_status(self) -> Dict:
        """
        獲取數據源狀態
        
        Returns:
            Dict: 數據源狀態報告
        """
        return {
            'api_keys': self.api_key_status,
            'connectivity': self.connectivity_status,
            'available_sources': {
                'tiingo': self.api_key_manager.is_service_available('tiingo'),
                'fred': self.api_key_manager.is_service_available('fred'),
                'simulation': True
            },
            'recommended_source': (
                'api' if self.market_data_provider.is_available() else 'simulation'
            )
        }
    
    def refresh_connections(self) -> Dict:
        """
        重新測試API連接
        
        Returns:
            Dict: 更新後的連接狀態
        """
        logger.info("重新測試API連接...")
        self.connectivity_status = self.api_key_manager.test_all_connections()
        
        # 重新初始化數據提供者
        self.market_data_provider = MarketDataProvider(self.api_key_manager)
        
        return self.connectivity_status 