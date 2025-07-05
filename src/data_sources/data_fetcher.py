"""
數據獲取模組

提供Tiingo API和FRED API的數據獲取功能，支援批次獲取優化和完整的錯誤處理機制。
實現高效的數據預處理和精確的目標日期數據提取。
"""

import logging
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from src.models.data_models import MarketDataPoint, DataModelFactory, ValidationResult
from src.data_sources.fault_tolerance import APIFaultToleranceManager
from src.data_sources.trading_calendar import adjust_for_trading_days

# 設定日誌
logger = logging.getLogger(__name__)


class TiingoDataFetcher:
    """Tiingo API數據獲取器"""
    
    def __init__(self, api_key: str):
        """
        初始化Tiingo數據獲取器
        
        Args:
            api_key: Tiingo API金鑰
        """
        self.api_key = api_key
        self.base_url = "https://api.tiingo.com/tiingo/daily"
        self.fault_tolerance = APIFaultToleranceManager()
        
        logger.info("Tiingo數據獲取器已初始化")
    
    def fetch_spy_data(self, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """
        獲取SPY股票數據
        
        Args:
            start_date: 開始日期 (YYYY-MM-DD)
            end_date: 結束日期 (YYYY-MM-DD)
        
        Returns:
            list: SPY價格數據列表
            
        Raises:
            Exception: 當API請求失敗時
        """
        url = f"{self.base_url}/SPY/prices"
        params = {
            'startDate': start_date,
            'endDate': end_date,
            'columns': 'date,adjClose',
            'token': self.api_key
        }
        
        logger.info(f"開始獲取SPY數據: {start_date} 至 {end_date}")
        
        try:
            # 使用容錯機制進行API請求
            response = self.fault_tolerance.fetch_with_retry(
                self._make_api_request, url, params
            )
            
            if response and isinstance(response, list):
                logger.info(f"成功獲取SPY數據 {len(response)} 筆記錄")
                return self._process_tiingo_response(response)
            else:
                logger.warning("Tiingo API回應數據格式異常")
                return []
                
        except Exception as e:
            logger.error(f"Tiingo API請求失敗: {e}")
            # 嘗試備援策略
            try:
                backup_data, fallback_method = self.fault_tolerance.execute_fallback_strategy(
                    'tiingo', start_date, end_date
                )
                logger.info(f"使用備援方案 {fallback_method} 獲取數據")
                return self._process_tiingo_response(backup_data)
            except Exception as backup_error:
                logger.error(f"備援策略也失敗: {backup_error}")
                raise Exception(f"無法獲取SPY數據: 主要API失敗 ({e})，備援也失敗 ({backup_error})")
    
    def _make_api_request(self, url: str, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """執行API請求"""
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()  # 如果HTTP狀態碼錯誤會拋出異常
        return response.json()
    
    def _process_tiingo_response(self, raw_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        處理Tiingo API回應數據
        
        Args:
            raw_data: 原始API回應數據
        
        Returns:
            list: 處理後的數據
        """
        processed_data = []
        
        for item in raw_data:
            try:
                # 處理日期格式
                if 'date' in item:
                    date_str = item['date']
                    if 'T' in date_str:
                        # 移除時區資訊，只保留日期部分
                        date_str = date_str.split('T')[0]
                    
                    # 驗證和處理價格
                    adj_close = item.get('adjClose')
                    if adj_close is not None:
                        processed_item = {
                            'date': date_str,
                            'adjClose': round(float(adj_close), 2)
                        }
                        processed_data.append(processed_item)
                    else:
                        logger.warning(f"缺少adjClose數據: {item}")
                else:
                    logger.warning(f"缺少date欄位: {item}")
                    
            except (ValueError, KeyError) as e:
                logger.warning(f"處理Tiingo數據項目失敗: {item}, 錯誤: {e}")
                continue
        
        logger.debug(f"Tiingo數據處理完成: {len(processed_data)} 筆有效記錄")
        return processed_data
    
    def get_target_prices(self, target_dates: List[datetime], 
                         buffer_days: int = 7) -> Dict[str, float]:
        """
        獲取特定目標日期的SPY價格
        
        Args:
            target_dates: 目標日期列表
            buffer_days: 緩衝天數，用於確保獲取到足夠的數據
        
        Returns:
            dict: 日期到價格的映射 {YYYY-MM-DD: price}
        """
        if not target_dates:
            return {}
        
        # 計算數據獲取範圍（加上緩衝）
        earliest_date = min(target_dates) - timedelta(days=buffer_days)
        latest_date = max(target_dates) + timedelta(days=buffer_days)
        
        start_str = earliest_date.strftime('%Y-%m-%d')
        end_str = latest_date.strftime('%Y-%m-%d')
        
        # 批次獲取數據
        all_data = self.fetch_spy_data(start_str, end_str)
        
        # 建立日期到價格的映射
        price_map = {}
        for item in all_data:
            price_map[item['date']] = item['adjClose']
        
        # 提取目標日期的價格
        target_prices = {}
        for target_date in target_dates:
            date_str = target_date.strftime('%Y-%m-%d')
            
            if date_str in price_map:
                target_prices[date_str] = price_map[date_str]
            else:
                # 如果目標日期沒有數據，尋找最近的交易日
                nearest_price = self._find_nearest_price(target_date, price_map)
                if nearest_price is not None:
                    target_prices[date_str] = nearest_price
                    logger.warning(f"目標日期 {date_str} 無數據，使用最近交易日價格: {nearest_price}")
                else:
                    logger.error(f"無法找到目標日期 {date_str} 附近的價格數據")
        
        logger.info(f"成功獲取 {len(target_prices)}/{len(target_dates)} 個目標日期的價格")
        return target_prices
    
    def _find_nearest_price(self, target_date: datetime, 
                           price_map: Dict[str, float]) -> Optional[float]:
        """尋找最近交易日的價格"""
        for days_offset in range(1, 8):  # 往前後各找7天
            for direction in [-1, 1]:
                check_date = target_date + timedelta(days=direction * days_offset)
                check_str = check_date.strftime('%Y-%m-%d')
                if check_str in price_map:
                    return price_map[check_str]
        return None


class FREDDataFetcher:
    """FRED API數據獲取器"""
    
    def __init__(self, api_key: str):
        """
        初始化FRED數據獲取器
        
        Args:
            api_key: FRED API金鑰
        """
        self.api_key = api_key
        self.base_url = "https://api.stlouisfed.org/fred/series/observations"
        self.fault_tolerance = APIFaultToleranceManager()
        
        logger.info("FRED數據獲取器已初始化")
    
    def fetch_yield_data(self, start_date: str, end_date: str, 
                        series_id: str = 'DGS1') -> List[Dict[str, Any]]:
        """
        獲取債券殖利率數據
        
        Args:
            start_date: 開始日期 (YYYY-MM-DD)
            end_date: 結束日期 (YYYY-MM-DD)
            series_id: FRED數據系列ID，預設為DGS1 (1年期國債)
        
        Returns:
            list: 殖利率數據列表
            
        Raises:
            Exception: 當API請求失敗時
        """
        params = {
            'series_id': series_id,
            'observation_start': start_date,
            'observation_end': end_date,
            'api_key': self.api_key,
            'file_type': 'json'
        }
        
        logger.info(f"開始獲取FRED數據({series_id}): {start_date} 至 {end_date}")
        
        try:
            # 使用容錯機制進行API請求
            response = self.fault_tolerance.fetch_with_retry(
                self._make_api_request, self.base_url, params
            )
            
            if response and 'observations' in response:
                observations = response['observations']
                logger.info(f"成功獲取FRED數據 {len(observations)} 筆記錄")
                return self._process_fred_response(observations)
            else:
                logger.warning("FRED API回應數據格式異常")
                return []
                
        except Exception as e:
            logger.error(f"FRED API請求失敗: {e}")
            # 嘗試備援策略
            try:
                backup_data, fallback_method = self.fault_tolerance.execute_fallback_strategy(
                    'fred', start_date, end_date
                )
                logger.info(f"使用備援方案 {fallback_method} 獲取數據")
                return self._process_fred_response(backup_data)
            except Exception as backup_error:
                logger.error(f"備援策略也失敗: {backup_error}")
                raise Exception(f"無法獲取FRED數據: 主要API失敗 ({e})，備援也失敗 ({backup_error})")
    
    def _make_api_request(self, url: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """執行API請求"""
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        return response.json()
    
    def _process_fred_response(self, raw_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        處理FRED API回應數據
        
        Args:
            raw_data: 原始API回應數據
        
        Returns:
            list: 處理後的數據
        """
        processed_data = []
        
        for item in raw_data:
            try:
                date_str = item.get('date')
                value_str = item.get('value')
                
                if date_str and value_str and value_str != '.':
                    # FRED API中的'.'表示缺失數據
                    try:
                        yield_value = float(value_str)
                        processed_item = {
                            'date': date_str,
                            'value': value_str  # 保持字串格式以符合API規範
                        }
                        processed_data.append(processed_item)
                    except ValueError:
                        logger.warning(f"無法解析殖利率數值: {value_str}")
                        continue
                else:
                    logger.debug(f"跳過無效的FRED數據項目: {item}")
                    
            except KeyError as e:
                logger.warning(f"處理FRED數據項目失敗: {item}, 缺少欄位: {e}")
                continue
        
        logger.debug(f"FRED數據處理完成: {len(processed_data)} 筆有效記錄")
        return processed_data
    
    def get_target_yields(self, target_dates: List[datetime], 
                         buffer_days: int = 7) -> Dict[str, float]:
        """
        獲取特定目標日期的債券殖利率
        
        Args:
            target_dates: 目標日期列表
            buffer_days: 緩衝天數
        
        Returns:
            dict: 日期到殖利率的映射 {YYYY-MM-DD: yield}
        """
        if not target_dates:
            return {}
        
        # 計算數據獲取範圍
        earliest_date = min(target_dates) - timedelta(days=buffer_days)
        latest_date = max(target_dates) + timedelta(days=buffer_days)
        
        start_str = earliest_date.strftime('%Y-%m-%d')
        end_str = latest_date.strftime('%Y-%m-%d')
        
        # 批次獲取數據
        all_data = self.fetch_yield_data(start_str, end_str)
        
        # 建立日期到殖利率的映射
        yield_map = {}
        for item in all_data:
            try:
                yield_value = float(item['value'])
                yield_map[item['date']] = yield_value
            except ValueError:
                continue
        
        # 提取目標日期的殖利率
        target_yields = {}
        for target_date in target_dates:
            date_str = target_date.strftime('%Y-%m-%d')
            
            if date_str in yield_map:
                target_yields[date_str] = yield_map[date_str]
            else:
                # 尋找最近的殖利率數據
                nearest_yield = self._find_nearest_yield(target_date, yield_map)
                if nearest_yield is not None:
                    target_yields[date_str] = nearest_yield
                    logger.warning(f"目標日期 {date_str} 無殖利率數據，使用最近日期數據: {nearest_yield}")
                else:
                    logger.error(f"無法找到目標日期 {date_str} 附近的殖利率數據")
        
        logger.info(f"成功獲取 {len(target_yields)}/{len(target_dates)} 個目標日期的殖利率")
        return target_yields
    
    def _find_nearest_yield(self, target_date: datetime, 
                           yield_map: Dict[str, float]) -> Optional[float]:
        """尋找最近的殖利率數據"""
        for days_offset in range(1, 15):  # 債券數據可能有更多缺失，搜尋範圍更大
            for direction in [-1, 1]:
                check_date = target_date + timedelta(days=direction * days_offset)
                check_str = check_date.strftime('%Y-%m-%d')
                if check_str in yield_map:
                    return yield_map[check_str]
        return None
    
    def calculate_bond_prices(self, yields: Dict[str, float]) -> Dict[str, float]:
        """
        根據殖利率計算債券價格
        
        假設：面值100，無息債券，到期1年
        公式：Bond_Price = 100 / (1 + Yield_Rate/100)
        
        Args:
            yields: 日期到殖利率的映射
        
        Returns:
            dict: 日期到債券價格的映射
        """
        bond_prices = {}
        
        for date_str, yield_rate in yields.items():
            try:
                # 債券定價公式
                bond_price = 100.0 / (1 + yield_rate / 100.0)
                bond_prices[date_str] = round(bond_price, 2)
            except (ZeroDivisionError, ValueError) as e:
                logger.warning(f"計算債券價格失敗 {date_str}: yield={yield_rate}, 錯誤: {e}")
                continue
        
        logger.info(f"成功計算 {len(bond_prices)} 個債券價格")
        return bond_prices


class BatchDataFetcher:
    """批次數據獲取器 - 統一管理多個數據源"""
    
    def __init__(self, tiingo_api_key: str, fred_api_key: str):
        """
        初始化批次數據獲取器
        
        Args:
            tiingo_api_key: Tiingo API金鑰
            fred_api_key: FRED API金鑰
        """
        self.tiingo_fetcher = TiingoDataFetcher(tiingo_api_key)
        self.fred_fetcher = FREDDataFetcher(fred_api_key)
        self.data_factory = DataModelFactory()
        
        logger.info("批次數據獲取器已初始化")
    
    def fetch_all_market_data(self, target_dates: List[datetime]) -> Tuple[
        Dict[str, MarketDataPoint], Dict[str, MarketDataPoint], ValidationResult
    ]:
        """
        批次獲取所有市場數據（股票和債券）
        
        Args:
            target_dates: 目標日期列表
        
        Returns:
            tuple: (股票數據字典, 債券數據字典, 驗證結果)
        """
        logger.info(f"開始批次獲取市場數據，目標日期數量: {len(target_dates)}")
        
        validation_result = ValidationResult()
        stock_data = {}
        bond_data = {}
        
        try:
            # 1. 獲取股票數據
            logger.info("步驟1: 獲取SPY股票數據")
            stock_prices = self.tiingo_fetcher.get_target_prices(target_dates)
            
            for date_str, price in stock_prices.items():
                try:
                    stock_point = self.data_factory.create_market_data_point(
                        date=date_str,
                        price=price,
                        data_source='tiingo'
                    )
                    stock_data[date_str] = stock_point
                except Exception as e:
                    validation_result.add_error(f"創建股票數據點失敗 {date_str}: {e}")
            
            # 2. 獲取債券數據
            logger.info("步驟2: 獲取債券殖利率數據")
            bond_yields = self.fred_fetcher.get_target_yields(target_dates)
            bond_prices = self.fred_fetcher.calculate_bond_prices(bond_yields)
            
            for date_str, price in bond_prices.items():
                try:
                    bond_point = self.data_factory.create_market_data_point(
                        date=date_str,
                        price=price,
                        data_source='fred'
                    )
                    bond_data[date_str] = bond_point
                except Exception as e:
                    validation_result.add_error(f"創建債券數據點失敗 {date_str}: {e}")
            
            # 3. 數據完整性檢查
            missing_stock_dates = []
            missing_bond_dates = []
            
            for target_date in target_dates:
                date_str = target_date.strftime('%Y-%m-%d')
                if date_str not in stock_data:
                    missing_stock_dates.append(date_str)
                if date_str not in bond_data:
                    missing_bond_dates.append(date_str)
            
            if missing_stock_dates:
                validation_result.add_warning(f"缺少股票數據的日期: {missing_stock_dates}")
            if missing_bond_dates:
                validation_result.add_warning(f"缺少債券數據的日期: {missing_bond_dates}")
            
            # 4. 計算數據覆蓋率
            stock_coverage = len(stock_data) / len(target_dates) if target_dates else 0
            bond_coverage = len(bond_data) / len(target_dates) if target_dates else 0
            
            logger.info(f"數據獲取完成 - 股票覆蓋率: {stock_coverage:.1%}, 債券覆蓋率: {bond_coverage:.1%}")
            
            if stock_coverage < 0.8:
                validation_result.add_error(f"股票數據覆蓋率過低: {stock_coverage:.1%}")
            if bond_coverage < 0.8:
                validation_result.add_error(f"債券數據覆蓋率過低: {bond_coverage:.1%}")
            
        except Exception as e:
            error_msg = f"批次數據獲取失敗: {e}"
            logger.error(error_msg)
            validation_result.add_error(error_msg)
        
        return stock_data, bond_data, validation_result
    
    def get_period_data(self, period_start: datetime, period_end: datetime) -> Tuple[
        Optional[MarketDataPoint], Optional[MarketDataPoint], 
        Optional[MarketDataPoint], Optional[MarketDataPoint]
    ]:
        """
        獲取單一期間的期初期末數據
        
        Args:
            period_start: 期初日期
            period_end: 期末日期
        
        Returns:
            tuple: (期初股票, 期末股票, 期初債券, 期末債券)
        """
        target_dates = [period_start, period_end]
        stock_data, bond_data, validation_result = self.fetch_all_market_data(target_dates)
        
        start_str = period_start.strftime('%Y-%m-%d')
        end_str = period_end.strftime('%Y-%m-%d')
        
        period_start_stock = stock_data.get(start_str)
        period_end_stock = stock_data.get(end_str)
        period_start_bond = bond_data.get(start_str)
        period_end_bond = bond_data.get(end_str)
        
        if not validation_result.is_valid:
            logger.warning(f"期間數據獲取有問題: {validation_result.errors}")
        
        return period_start_stock, period_end_stock, period_start_bond, period_end_bond 