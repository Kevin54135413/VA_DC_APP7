"""
第4.2節 - 主要業務流程 (Main Business Process)

本模組實作投資策略比較系統的主要業務流程，包括：
- 效能監控系統 (performance_monitor)
- 主要計算流程控制 (main_calculation_flow)
- 並行策略計算 (calculate_strategies_parallel)
- 安全策略計算函數 (calculate_va_strategy_safe, calculate_dca_strategy_safe)
- 數據獲取流程 (data_acquisition_flow)
- 優化版歷史數據獲取 (fetch_historical_data_optimized)
- 目標日期計算與交易日調整 (calculate_target_dates, adjust_to_trading_days)
- 批次數據獲取 (fetch_tiingo_data_batch, fetch_fred_data_batch)
- 數據提取與品質評估 (extract_target_date_data, get_closest_price, assess_data_quality)
- 快取鍵生成 (generate_cache_key_enhanced)

嚴格遵循需求文件第4.2節的所有規格要求，確保函數簽名與返回值完全一致。
"""

import logging
import time
import json
import hashlib
import concurrent.futures
from contextlib import contextmanager
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple, ContextManager
import pandas as pd
import numpy as np
from pandas.tseries.holiday import USFederalHolidayCalendar
from pandas.tseries.offsets import CustomBusinessDay

# 導入第1章API安全機制
from ..data_sources.api_clients import TiingoAPIClient, FREDAPIClient
from ..data_sources.data_fetcher import TiingoDataFetcher, FREDDataFetcher

# 導入第2章策略計算引擎
from ..models.strategy_engine import calculate_va_strategy, calculate_dca_strategy

# 導入第3章UI組件（用於錯誤顯示）
# from ..ui.error_handling import display_validation_errors_with_suggestions, display_data_error_message, display_calculation_error_message

# 導入第4.1章應用程式初始化
from .app_initialization import get_logger

# 設置日誌
logger = get_logger(__name__)

# ============================================================================
# 效能監控系統
# ============================================================================

@contextmanager
def performance_monitor(operation_name: str) -> ContextManager:
    """
    效能監控上下文管理器
    
    Args:
        operation_name: 操作名稱
        
    Yields:
        ContextManager: 上下文管理器
    """
    start_time = time.time()
    logger.info(f"開始執行: {operation_name}")
    
    try:
        yield
        
    except Exception as e:
        end_time = time.time()
        duration = end_time - start_time
        logger.error(f"操作失敗: {operation_name}, 耗時: {duration:.2f}秒, 錯誤: {str(e)}")
        record_performance_metric(operation_name, duration, "failed", str(e))
        raise
        
    else:
        end_time = time.time()
        duration = end_time - start_time
        logger.info(f"完成執行: {operation_name}, 耗時: {duration:.2f}秒")
        record_performance_metric(operation_name, duration, "success")

def record_performance_metric(operation_name: str, duration: float, status: str, error_message: str = None):
    """記錄效能指標"""
    metric = {
        'operation': operation_name,
        'duration': duration,
        'status': status,
        'timestamp': datetime.now().isoformat(),
        'error_message': error_message
    }
    
    # 記錄到日誌
    logger.info(f"效能指標: {json.dumps(metric, ensure_ascii=False)}")
    
    # 這裡可以擴展到其他監控系統
    # 例如：存儲到數據庫、發送到監控服務等

# ============================================================================
# 主要計算流程控制
# ============================================================================

def main_calculation_flow() -> Optional[Dict[str, Any]]:
    """
    主要計算流程控制
    
    Returns:
        Optional[Dict[str, Any]]: 計算結果字典，包含VA結果、DCA結果、績效指標和元數據
    """
    logger.info("開始主要計算流程")
    
    try:
        with performance_monitor("完整計算流程"):
            # Step 1: 參數收集與驗證
            with performance_monitor("參數驗證"):
                user_params = collect_user_parameters()
                validation_result = validate_parameters_comprehensive(user_params)
                
                if not validation_result.is_valid:
                    logger.warning(f"參數驗證失敗: {validation_result.errors}")
                    display_validation_errors_with_suggestions(validation_result)
                    return None
                
                logger.info("參數驗證通過")
            
            # Step 2: 數據獲取
            with performance_monitor("數據獲取"):
                market_data = data_acquisition_flow(user_params)
                if market_data is None:
                    logger.error("數據獲取失敗")
                    display_data_error_message()
                    return None
            
            # Step 3: 策略計算（並行處理）
            with performance_monitor("策略計算"):
                va_results, dca_results = calculate_strategies_parallel(
                    market_data, user_params
                )
                
                if va_results is None or dca_results is None:
                    logger.error("策略計算失敗")
                    return None
            
            # Step 4: 績效分析
            with performance_monitor("績效分析"):
                performance_metrics = calculate_performance_metrics_enhanced(
                    va_results, dca_results, user_params
                )
            
            # Step 5: 結果驗證與輸出
            with performance_monitor("結果驗證"):
                results = {
                    'va_results': va_results,
                    'dca_results': dca_results,
                    'metrics': performance_metrics,
                    'metadata': {
                        'calculation_time': time.time(),
                        'parameters_hash': generate_params_hash(user_params),
                        'data_quality_score': assess_data_quality(market_data)
                    }
                }
                
                # 結果合理性檢查
                if validate_calculation_results(results):
                    logger.info("計算完成，結果驗證通過")
                    return results
                else:
                    logger.error("計算結果驗證失敗")
                    return None
                    
    except Exception as e:
        logger.error(f"計算流程異常: {str(e)}", exc_info=True)
        display_calculation_error_message(str(e))
        return None

# ============================================================================
# 並行策略計算
# ============================================================================

def calculate_strategies_parallel(market_data, user_params) -> Tuple[Optional[Any], Optional[Any]]:
    """
    並行計算策略
    
    Args:
        market_data: 市場數據
        user_params: 用戶參數
        
    Returns:
        Tuple[Optional, Optional]: (VA結果, DCA結果)
    """
    logger.info("開始並行策略計算")
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        # 提交並行任務
        va_future = executor.submit(calculate_va_strategy_safe, market_data, user_params)
        dca_future = executor.submit(calculate_dca_strategy_safe, market_data, user_params)
        
        # 等待結果
        try:
            va_results = va_future.result(timeout=30)  # 30秒超時
            dca_results = dca_future.result(timeout=30)
            
            logger.info("並行策略計算完成")
            return va_results, dca_results
            
        except concurrent.futures.TimeoutError:
            logger.error("策略計算超時")
            return None, None
        except Exception as e:
            logger.error(f"並行策略計算錯誤: {str(e)}")
            return None, None

def calculate_va_strategy_safe(market_data, user_params) -> Optional[Any]:
    """
    安全VA策略計算
    
    Args:
        market_data: 市場數據
        user_params: 用戶參數
        
    Returns:
        Optional: VA策略計算結果
    """
    try:
        logger.info("開始VA策略計算")
        
        # 調用第2章的VA策略計算函數
        va_results = calculate_va_strategy(
            C0=user_params.get('initial_investment', 10000),
            annual_investment=user_params.get('annual_investment', 12000),
            annual_growth_rate=user_params.get('annual_growth_rate', 7.0),
            annual_inflation_rate=user_params.get('annual_inflation_rate', 2.0),
            investment_years=user_params.get('investment_years', 10),
            frequency=user_params.get('frequency', 'monthly'),
            stock_ratio=user_params.get('stock_ratio', 80.0),
            strategy_type=user_params.get('va_strategy_type', 'Rebalance'),
            market_data=market_data
        )
        
        logger.info("VA策略計算完成")
        return va_results
        
    except Exception as e:
        logger.error(f"VA策略計算錯誤: {str(e)}")
        return None

def calculate_dca_strategy_safe(market_data, user_params) -> Optional[Any]:
    """
    安全DCA策略計算
    
    Args:
        market_data: 市場數據
        user_params: 用戶參數
        
    Returns:
        Optional: DCA策略計算結果
    """
    try:
        logger.info("開始DCA策略計算")
        
        # 調用第2章的DCA策略計算函數
        dca_results = calculate_dca_strategy(
            C0=user_params.get('initial_investment', 10000),
            annual_investment=user_params.get('annual_investment', 12000),
            annual_growth_rate=user_params.get('annual_growth_rate', 7.0),
            annual_inflation_rate=user_params.get('annual_inflation_rate', 2.0),
            investment_years=user_params.get('investment_years', 10),
            frequency=user_params.get('frequency', 'monthly'),
            stock_ratio=user_params.get('stock_ratio', 80.0),
            market_data=market_data
        )
        
        logger.info("DCA策略計算完成")
        return dca_results
        
    except Exception as e:
        logger.error(f"DCA策略計算錯誤: {str(e)}")
        return None

# ============================================================================
# 數據獲取流程
# ============================================================================

def data_acquisition_flow(params) -> Optional[Dict[str, Any]]:
    """
    數據獲取流程
    
    Args:
        params: 參數對象
        
    Returns:
        Optional[Dict[str, Any]]: 市場數據字典
    """
    logger.info("開始數據獲取流程")
    
    try:
        # 生成快取鍵
        cache_key = generate_cache_key_enhanced(params)
        logger.info(f"查找快取: {cache_key[:16]}...")
        
        # 檢查快取
        cached_data = get_from_cache_with_validation(cache_key)
        
        if cached_data and not is_cache_expired(cached_data):
            logger.info("使用快取數據")
            update_cache_hit_metrics(cache_key)
            return cached_data
        
        # 快取失效，獲取新數據
        logger.info(f"快取失效，獲取新數據 - 場景: {getattr(params, 'scenario', 'unknown')}")
        
        with performance_monitor("數據獲取"):
            if getattr(params, 'scenario', 'historical') == "historical":
                market_data = fetch_historical_data_optimized(params)
            else:
                market_data = generate_simulation_data_enhanced(params)
        
        if market_data is None:
            logger.error("數據獲取失敗")
            return None
        
        # 數據品質檢查
        quality_score = assess_data_quality(market_data)
        if quality_score < 0.7:  # 品質閾值
            logger.warning(f"數據品質較低: {quality_score:.2f}")
            display_data_quality_warning(quality_score)
        
        # 更新快取
        cache_data = {
            'data': market_data,
            'timestamp': datetime.now().isoformat(),
            'params_hash': generate_params_hash(params),
            'quality_score': quality_score,
            'source': getattr(params, 'scenario', 'historical')
        }
        
        update_cache_with_metadata(cache_key, cache_data)
        logger.info("數據獲取完成並更新快取")
        
        return market_data
        
    except Exception as e:
        logger.error(f"數據獲取流程錯誤: {str(e)}", exc_info=True)
        
        # 嘗試使用備用數據源
        backup_data = try_backup_data_sources(params)
        if backup_data:
            logger.info("使用備用數據源")
            return backup_data
        
        return None

def fetch_historical_data_optimized(params) -> Optional[Dict[str, Any]]:
    """
    優化版歷史數據獲取 - 基於目標日期批次獲取
    
    Args:
        params: 參數對象
        
    Returns:
        Optional[Dict[str, Any]]: 歷史數據字典
    """
    logger.info("開始優化版歷史數據獲取")
    
    try:
        # 步驟1: 計算所有期初/期末目標日期
        target_dates = calculate_target_dates(
            start_date=getattr(params, 'start_date', datetime.now()),
            frequency=getattr(params, 'frequency', 'monthly'),
            periods=getattr(params, 'periods', 12)
        )
        
        logger.info(f"計算目標日期: {len(target_dates['period_starts'])}個期間，共{len(target_dates['period_starts'])*2}個目標日期")
        
        # 步驟2: 調整為有效交易日
        adjusted_dates = adjust_to_trading_days(target_dates)
        
        # 步驟3: 確定API調用的日期範圍
        all_dates = adjusted_dates['period_starts'] + adjusted_dates['period_ends']
        api_start_date = min(all_dates)
        api_end_date = max(all_dates)
        
        logger.info(f"API調用範圍: {api_start_date} 到 {api_end_date}")
        
        # 步驟4: 批次獲取完整日期範圍的數據
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            stock_future = executor.submit(
                fetch_tiingo_data_batch,
                api_start_date, api_end_date
            )
            bond_future = executor.submit(
                fetch_fred_data_batch,
                api_start_date, api_end_date
            )
            
            stock_data_full = stock_future.result(timeout=30)
            bond_data_full = bond_future.result(timeout=30)
        
        if stock_data_full is None or bond_data_full is None:
            logger.error("批次數據獲取不完整")
            return None
        
        # 步驟5: 從完整數據中提取目標日期的數據點
        market_data = extract_target_date_data(
            stock_data_full, bond_data_full, adjusted_dates
        )
        
        logger.info(f"成功提取{len(market_data.get('periods_data', []))}個期間的目標日期數據")
        return market_data
        
    except Exception as e:
        logger.error(f"優化版歷史數據獲取錯誤: {str(e)}")
        return None

# ============================================================================
# 目標日期計算與交易日調整
# ============================================================================

def calculate_target_dates(start_date: datetime, frequency: str, periods: int) -> Dict[str, List[datetime]]:
    """
    計算所有期初/期末目標日期
    
    Args:
        start_date: 開始日期
        frequency: 投資頻率 ('monthly', 'quarterly', 'semi-annually', 'annually')
        periods: 期數
        
    Returns:
        Dict[str, List[datetime]]: 包含period_starts和period_ends的字典
    """
    logger.info(f"計算目標日期: {frequency}, {periods}期")
    
    period_starts = []
    period_ends = []
    
    for period in range(1, periods + 1):
        period_start = calculate_period_start_date(start_date, frequency, period)
        period_end = calculate_period_end_date(start_date, frequency, period)
        
        period_starts.append(period_start)
        period_ends.append(period_end)
    
    return {
        'period_starts': period_starts,
        'period_ends': period_ends
    }

def calculate_period_start_date(base_start_date: datetime, frequency: str, period_number: int) -> datetime:
    """計算各期的期初日期"""
    from dateutil.relativedelta import relativedelta
    
    if frequency == 'monthly':
        return base_start_date + relativedelta(months=period_number - 1)
    elif frequency == 'quarterly':
        return base_start_date + relativedelta(months=(period_number - 1) * 3)
    elif frequency == 'semi-annually':
        return base_start_date + relativedelta(months=(period_number - 1) * 6)
    elif frequency == 'annually':
        return base_start_date + relativedelta(years=period_number - 1)
    else:
        raise ValueError(f"不支援的頻率: {frequency}")

def calculate_period_end_date(base_start_date: datetime, frequency: str, period_number: int) -> datetime:
    """計算各期的期末日期"""
    from dateutil.relativedelta import relativedelta
    
    if frequency == 'monthly':
        next_start = base_start_date + relativedelta(months=period_number)
        return next_start - relativedelta(days=1)
    elif frequency == 'quarterly':
        next_start = base_start_date + relativedelta(months=period_number * 3)
        return next_start - relativedelta(days=1)
    elif frequency == 'semi-annually':
        next_start = base_start_date + relativedelta(months=period_number * 6)
        return next_start - relativedelta(days=1)
    elif frequency == 'annually':
        next_start = base_start_date + relativedelta(years=period_number)
        return next_start - relativedelta(days=1)
    else:
        raise ValueError(f"不支援的頻率: {frequency}")

def adjust_to_trading_days(target_dates: Dict[str, List[datetime]]) -> Dict[str, List[datetime]]:
    """
    將目標日期調整為最近的有效交易日
    
    Args:
        target_dates: 包含period_starts和period_ends的日期字典
        
    Returns:
        Dict[str, List[datetime]]: 調整後的交易日字典
    """
    logger.info("調整目標日期為交易日")
    
    # 美股交易日規則
    us_bd = CustomBusinessDay(calendar=USFederalHolidayCalendar())
    
    adjusted_starts = []
    adjusted_ends = []
    
    # 調整期初日期（向後找最近交易日）
    for date in target_dates['period_starts']:
        pd_date = pd.Timestamp(date)
        if pd_date.weekday() < 5:  # 週一到週五
            # 檢查是否為假日
            if us_bd.is_on_offset(pd_date):
                adjusted_date = pd_date
            else:
                adjusted_date = pd_date + us_bd * 1  # 下一個交易日
        else:
            adjusted_date = pd_date + us_bd * 1  # 下一個交易日
        adjusted_starts.append(adjusted_date.to_pydatetime())
    
    # 調整期末日期（向前找最近交易日）
    for date in target_dates['period_ends']:
        pd_date = pd.Timestamp(date)
        if pd_date.weekday() < 5:  # 週一到週五
            # 檢查是否為假日
            if us_bd.is_on_offset(pd_date):
                adjusted_date = pd_date
            else:
                adjusted_date = pd_date - us_bd * 1  # 前一個交易日
        else:
            adjusted_date = pd_date - us_bd * 1  # 前一個交易日
        adjusted_ends.append(adjusted_date.to_pydatetime())
    
    return {
        'period_starts': adjusted_starts,
        'period_ends': adjusted_ends
    }

# ============================================================================
# 批次數據獲取
# ============================================================================

def fetch_tiingo_data_batch(start_date: datetime, end_date: datetime, max_retries=3):
    """
    批次獲取Tiingo數據 - 一次性獲取完整日期範圍
    
    Args:
        start_date: 開始日期
        end_date: 結束日期
        max_retries: 最大重試次數
        
    Returns:
        pd.DataFrame: 股票數據DataFrame
    """
    logger.info(f"批次獲取Tiingo數據: {start_date} 到 {end_date}")
    
    for attempt in range(max_retries):
        try:
            # 使用第1章的API客戶端
            client = TiingoAPIClient()
            
            # 調用API獲取數據
            start_str = start_date.strftime('%Y-%m-%d')
            end_str = end_date.strftime('%Y-%m-%d')
            
            data = client.get_spy_prices(start_str, end_str)
            
            # 轉換為DataFrame
            df_data = []
            for item in data:
                df_data.append({
                    'date': item.date,
                    'price': item.spy_price
                })
            
            df = pd.DataFrame(df_data)
            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values('date')
            
            logger.info(f"成功獲取Tiingo數據: {len(df)}筆記錄")
            return df
            
        except Exception as e:
            logger.warning(f"Tiingo數據獲取失敗 (嘗試 {attempt + 1}/{max_retries}): {str(e)}")
            if attempt == max_retries - 1:
                logger.error("Tiingo數據獲取最終失敗")
                raise e
            time.sleep(2 ** attempt)  # 指數退避

def fetch_fred_data_batch(start_date: datetime, end_date: datetime, max_retries=3):
    """
    批次獲取FRED數據 - 一次性獲取完整日期範圍
    
    Args:
        start_date: 開始日期
        end_date: 結束日期
        max_retries: 最大重試次數
        
    Returns:
        pd.DataFrame: 債券數據DataFrame
    """
    logger.info(f"批次獲取FRED數據: {start_date} 到 {end_date}")
    
    for attempt in range(max_retries):
        try:
            # 使用第1章的API客戶端
            client = FREDAPIClient()
            
            # 調用API獲取數據
            start_str = start_date.strftime('%Y-%m-%d')
            end_str = end_date.strftime('%Y-%m-%d')
            
            data = client.get_bond_yields(start_str, end_str)
            
            # 轉換為DataFrame
            df_data = []
            for item in data:
                if item.bond_yield is not None:
                    df_data.append({
                        'date': item.date,
                        'price': item.bond_price
                    })
            
            df = pd.DataFrame(df_data)
            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values('date')
            
            logger.info(f"成功獲取FRED數據: {len(df)}筆記錄")
            return df
            
        except Exception as e:
            logger.warning(f"FRED數據獲取失敗 (嘗試 {attempt + 1}/{max_retries}): {str(e)}")
            if attempt == max_retries - 1:
                logger.error("FRED數據獲取最終失敗")
                raise e
            time.sleep(2 ** attempt)  # 指數退避

# ============================================================================
# 數據提取與處理
# ============================================================================

def extract_target_date_data(stock_data_full: pd.DataFrame, bond_data_full: pd.DataFrame, 
                           adjusted_dates: Dict[str, List[datetime]]) -> Dict[str, Any]:
    """
    從完整數據中提取目標日期的數據點
    
    Args:
        stock_data_full: 完整股票數據DataFrame
        bond_data_full: 完整債券數據DataFrame
        adjusted_dates: 調整後的目標日期字典
        
    Returns:
        Dict[str, Any]: 提取的市場數據字典
    """
    logger.info("從完整數據中提取目標日期數據")
    
    periods_data = []
    
    for i, (start_date, end_date) in enumerate(zip(
        adjusted_dates['period_starts'], 
        adjusted_dates['period_ends']
    )):
        # 提取期初數據
        start_stock_price = get_closest_price(stock_data_full, start_date)
        start_bond_price = get_closest_price(bond_data_full, start_date)
        
        # 提取期末數據
        end_stock_price = get_closest_price(stock_data_full, end_date)
        end_bond_price = get_closest_price(bond_data_full, end_date)
        
        periods_data.append({
            'period': i + 1,
            'start_date': start_date,
            'end_date': end_date,
            'start_stock_price': start_stock_price,
            'start_bond_price': start_bond_price,
            'end_stock_price': end_stock_price,
            'end_bond_price': end_bond_price
        })
    
    return {
        'periods_data': periods_data,
        'data_source': 'historical_optimized',
        'total_periods': len(periods_data)
    }

def get_closest_price(data: pd.DataFrame, target_date: datetime) -> float:
    """
    從數據中獲取最接近目標日期的價格
    
    Args:
        data: 價格數據DataFrame (包含date和price列)
        target_date: 目標日期
        
    Returns:
        float: 最接近的價格
    """
    if data.empty:
        logger.warning("數據為空，返回預設價格")
        return 100.0
    
    # 將目標日期轉換為pandas Timestamp
    target_ts = pd.Timestamp(target_date)
    
    # 計算與目標日期的時間差
    data = data.copy()
    data['date_diff'] = abs(data['date'] - target_ts)
    
    # 找到最接近的記錄
    closest_idx = data['date_diff'].idxmin()
    closest_price = data.loc[closest_idx, 'price']
    
    logger.debug(f"目標日期: {target_date}, 最接近價格: {closest_price}")
    return float(closest_price)

# ============================================================================
# 快取與品質管理
# ============================================================================

def generate_cache_key_enhanced(params) -> str:
    """
    生成增強版快取鍵
    
    Args:
        params: 參數對象
        
    Returns:
        str: 快取鍵字符串
    """
    # 包含更多參數以確保快取準確性
    cache_params = {
        'scenario': getattr(params, 'scenario', 'historical'),
        'start_date': getattr(params, 'start_date', None),
        'end_date': getattr(params, 'end_date', None),
        'frequency': getattr(params, 'frequency', 'monthly'),
        'periods': getattr(params, 'periods', 12),
        'stock_ratio': getattr(params, 'stock_ratio', 80.0),
        'simulation_params': getattr(params, 'simulation_params', None)
    }
    
    # 移除None值並轉換為字符串
    cache_params = {k: str(v) for k, v in cache_params.items() if v is not None}
    
    # 生成哈希
    params_str = json.dumps(cache_params, sort_keys=True)
    cache_key = hashlib.md5(params_str.encode()).hexdigest()
    
    logger.debug(f"生成快取鍵: {cache_key}")
    return cache_key

def assess_data_quality(data) -> float:
    """
    評估數據品質分數 (0-1)
    
    Args:
        data: 數據對象 (可以是DataFrame或字典)
        
    Returns:
        float: 品質分數，範圍0-1
    """
    if data is None:
        return 0.0
    
    score = 1.0
    
    try:
        # 處理不同類型的數據
        if isinstance(data, dict):
            if 'periods_data' in data:
                periods_data = data['periods_data']
                if not periods_data:
                    return 0.0
                
                # 檢查期間數據完整性
                total_periods = len(periods_data)
                complete_periods = 0
                
                for period in periods_data:
                    required_fields = ['start_stock_price', 'start_bond_price', 
                                     'end_stock_price', 'end_bond_price']
                    if all(field in period and period[field] is not None 
                          for field in required_fields):
                        complete_periods += 1
                
                # 計算完整性分數
                completeness_score = complete_periods / total_periods
                score *= completeness_score
                
                # 檢查價格合理性
                for period in periods_data:
                    for price_field in ['start_stock_price', 'start_bond_price', 
                                      'end_stock_price', 'end_bond_price']:
                        if price_field in period and period[price_field] is not None:
                            price = period[price_field]
                            if price <= 0 or price > 10000:  # 不合理的價格
                                score *= 0.9  # 扣分
                
        elif isinstance(data, pd.DataFrame):
            if data.empty:
                return 0.0
            
            # 檢查缺失值
            missing_ratio = data.isnull().sum().sum() / (data.shape[0] * data.shape[1])
            score -= missing_ratio * 0.3
            
            # 檢查數據連續性
            if 'date' in data.columns:
                date_gaps = check_date_continuity(data)
                score -= date_gaps * 0.2
            
            # 檢查異常值
            numeric_cols = data.select_dtypes(include=[np.number]).columns
            if len(numeric_cols) > 0:
                outlier_ratio = detect_outliers(data[numeric_cols])
                score -= outlier_ratio * 0.1
        
        # 確保分數在0-1範圍內
        score = max(0.0, min(1.0, score))
        
        logger.info(f"數據品質評估分數: {score:.3f}")
        return score
        
    except Exception as e:
        logger.error(f"數據品質評估錯誤: {str(e)}")
        return 0.5  # 返回中等品質分數

def check_date_continuity(data: pd.DataFrame) -> float:
    """檢查日期連續性"""
    if 'date' not in data.columns:
        return 0.0
    
    dates = pd.to_datetime(data['date']).sort_values()
    if len(dates) <= 1:
        return 0.0
    
    # 計算日期間隔
    date_diffs = dates.diff().dt.days.dropna()
    
    # 檢查異常間隔（超過10天）
    abnormal_gaps = (date_diffs > 10).sum()
    gap_ratio = abnormal_gaps / len(date_diffs)
    
    return gap_ratio

def detect_outliers(data: pd.DataFrame) -> float:
    """檢測異常值"""
    if data.empty:
        return 0.0
    
    total_values = data.count().sum()
    outlier_count = 0
    
    for col in data.columns:
        if data[col].dtype in [np.int64, np.float64]:
            Q1 = data[col].quantile(0.25)
            Q3 = data[col].quantile(0.75)
            IQR = Q3 - Q1
            
            # 定義異常值範圍
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            
            # 計算異常值數量
            outliers = ((data[col] < lower_bound) | (data[col] > upper_bound)).sum()
            outlier_count += outliers
    
    if total_values == 0:
        return 0.0
    
    return outlier_count / total_values

# ============================================================================
# 輔助函數 (模擬實作，實際應該從其他模組導入)
# ============================================================================

def collect_user_parameters():
    """收集用戶參數 (模擬實作)"""
    return {
        'initial_investment': 10000,
        'annual_investment': 12000,
        'annual_growth_rate': 7.0,
        'annual_inflation_rate': 2.0,
        'investment_years': 10,
        'frequency': 'monthly',
        'stock_ratio': 80.0,
        'scenario': 'historical',
        'start_date': datetime(2020, 1, 1),
        'periods': 120
    }

def validate_parameters_comprehensive(params):
    """參數綜合驗證 (模擬實作)"""
    class ValidationResult:
        def __init__(self):
            self.is_valid = True
            self.errors = []
    
    return ValidationResult()

def calculate_performance_metrics_enhanced(va_results, dca_results, user_params):
    """增強版績效指標計算 (模擬實作)"""
    return {
        'va_total_return': 0.08,
        'dca_total_return': 0.075,
        'va_volatility': 0.15,
        'dca_volatility': 0.12
    }

def validate_calculation_results(results):
    """驗證計算結果 (模擬實作)"""
    return results is not None and 'va_results' in results and 'dca_results' in results

def generate_params_hash(params):
    """生成參數哈希 (模擬實作)"""
    return hashlib.md5(str(params).encode()).hexdigest()

def get_from_cache_with_validation(cache_key):
    """從快取獲取數據並驗證 (模擬實作)"""
    return None

def is_cache_expired(cached_data):
    """檢查快取是否過期 (模擬實作)"""
    return True

def update_cache_hit_metrics(cache_key):
    """更新快取命中指標 (模擬實作)"""
    pass

def display_data_quality_warning(quality_score):
    """顯示數據品質警告 (模擬實作)"""
    logger.warning(f"數據品質警告: {quality_score}")

def generate_simulation_data_enhanced(params):
    """生成增強版模擬數據 (模擬實作)"""
    return {
        'periods_data': [
            {
                'period': 1,
                'start_date': datetime(2020, 1, 1),
                'end_date': datetime(2020, 1, 31),
                'start_stock_price': 100.0,
                'start_bond_price': 98.0,
                'end_stock_price': 102.0,
                'end_bond_price': 98.5
            }
        ],
        'data_source': 'simulation',
        'total_periods': 1
    }

def update_cache_with_metadata(cache_key, cache_data):
    """更新快取與元數據 (模擬實作)"""
    pass

def try_backup_data_sources(params):
    """嘗試備用數據源 (模擬實作)"""
    return None

def display_validation_errors_with_suggestions(validation_result):
    """顯示參數驗證錯誤 (模擬實作)"""
    logger.error(f"參數驗證錯誤: {validation_result.errors}")

def display_data_error_message():
    """顯示數據錯誤訊息 (模擬實作)"""
    logger.error("數據獲取失敗")

def display_calculation_error_message(error_message):
    """顯示計算錯誤訊息 (模擬實作)"""
    logger.error(f"計算錯誤: {error_message}")

def display_data_quality_warning(quality_score):
    """顯示數據品質警告 (模擬實作)"""
    logger.warning(f"數據品質警告: {quality_score}") 