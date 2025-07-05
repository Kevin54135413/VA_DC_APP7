"""
交易日處理與假期管理模組
實現第一章規格中定義的美國股市交易日計算功能
"""

import holidays
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)


def get_us_market_holidays(year: int) -> List[datetime]:
    """
    取得特定年份的美國股市假期
    
    Args:
        year: 年份
        
    Returns:
        list: 該年度所有股市假期的日期列表
    """
    # 使用holidays套件獲取美國假期
    us_holidays = holidays.US(years=year)
    
    # 股市假期（不包含一些銀行假期）
    market_holidays = []
    
    for date, name in us_holidays.items():
        # 篩選股市會關閉的假期
        if any(keyword in name.lower() for keyword in [
            'new year', 'martin luther king', 'presidents', 'good friday',
            'memorial day', 'independence', 'labor day', 'thanksgiving', 'christmas'
        ]):
            # 轉換為datetime對象
            market_holidays.append(datetime.combine(date, datetime.min.time()))
    
    # 手動添加一些特殊假期
    special_dates = [
        datetime(year, 1, 1),   # 元旦
        datetime(year, 7, 4),   # 獨立日
        datetime(year, 12, 25), # 聖誕節
    ]
    
    for date in special_dates:
        if date not in market_holidays:
            market_holidays.append(date)
    
    # 調整假期遇到週末的情況
    adjusted_holidays = []
    for holiday in market_holidays:
        if holiday.weekday() == 5:  # 週六
            adjusted_holidays.append(holiday - timedelta(days=1))  # 提前到週五
        elif holiday.weekday() == 6:  # 週日
            adjusted_holidays.append(holiday + timedelta(days=1))  # 延後到週一
        else:
            adjusted_holidays.append(holiday)
    
    return sorted(list(set(adjusted_holidays)))


def is_trading_day(date: datetime) -> bool:
    """
    判斷指定日期是否為交易日
    
    Args:
        date: 要檢查的日期
        
    Returns:
        bool: True if 是交易日, False otherwise
    """
    # 檢查是否為週末
    if date.weekday() >= 5:  # 週六(5) 或 週日(6)
        return False
    
    # 檢查是否為假期
    year_holidays = get_us_market_holidays(date.year)
    if date.date() in [h.date() for h in year_holidays]:
        return False
    
    return True


def adjust_for_trading_days(target_date: datetime, adjustment_type: str = 'next') -> datetime:
    """
    調整非交易日到最近的交易日
    
    Args:
        target_date: 目標日期
        adjustment_type: 'next' (往後調整) 或 'previous' (往前調整)
        
    Returns:
        datetime: 調整後的交易日
    """
    adjusted_date = target_date
    max_adjustments = 10  # 避免無限迴圈
    adjustments = 0
    
    while not is_trading_day(adjusted_date) and adjustments < max_adjustments:
        if adjustment_type == 'next':
            adjusted_date += timedelta(days=1)
        else:
            adjusted_date -= timedelta(days=1)
        adjustments += 1
    
    if adjustments >= max_adjustments:
        raise ValueError(f"無法在{max_adjustments}天內找到交易日")
    
    return adjusted_date


def generate_trading_days(start_date: datetime, end_date: datetime) -> List[datetime]:
    """
    生成指定期間內的所有交易日
    
    Args:
        start_date: 起始日期
        end_date: 結束日期
        
    Returns:
        list: 期間內所有交易日的列表
    """
    trading_days = []
    current_date = start_date
    
    while current_date <= end_date:
        if is_trading_day(current_date):
            trading_days.append(current_date)
        current_date += timedelta(days=1)
    
    return trading_days


def get_trading_day_count(start_date: datetime, end_date: datetime) -> int:
    """
    計算期間內的交易日數量
    
    Args:
        start_date: 起始日期
        end_date: 結束日期
        
    Returns:
        int: 交易日總數
    """
    return len(generate_trading_days(start_date, end_date))


def calculate_period_start_date(base_start_date: datetime, frequency: str, period_number: int) -> datetime:
    """
    計算各期的期初日期
    
    Args:
        base_start_date: 第1期起始日期 (例如: 2025-01-01)
        frequency: 投資頻率 ('monthly', 'quarterly', 'semi-annually', 'annually')
        period_number: 期數 (1, 2, 3, ...)
        
    Returns:
        datetime: 該期的起始日期
    """
    if frequency == 'monthly':
        # 每月1日開始
        start_date = base_start_date + relativedelta(months=period_number - 1)
        
    elif frequency == 'quarterly':
        # 每季第一日：1/1, 4/1, 7/1, 10/1
        quarter_start_months = [1, 4, 7, 10]
        month_index = (period_number - 1) % 4
        year_offset = (period_number - 1) // 4
        start_date = datetime(base_start_date.year + year_offset, 
                            quarter_start_months[month_index], 1)
        
    elif frequency == 'semi-annually':
        # 每半年第一日：1/1, 7/1
        if period_number % 2 == 1:  # 奇數期：1月1日
            target_month = 1
        else:  # 偶數期：7月1日
            target_month = 7
        year_offset = (period_number - 1) // 2
        start_date = datetime(base_start_date.year + year_offset, target_month, 1)
        
    elif frequency == 'annually':
        # 每年1月1日開始
        start_date = datetime(base_start_date.year + period_number - 1, 1, 1)
    
    return start_date


def calculate_period_end_date(base_start_date: datetime, frequency: str, period_number: int) -> datetime:
    """
    計算各期的期末日期
    
    Args:
        base_start_date: 第1期起始日期 (例如: 2025-01-01)
        frequency: 投資頻率 ('monthly', 'quarterly', 'semi-annually', 'annually')
        period_number: 期數 (1, 2, 3, ...)
        
    Returns:
        datetime: 該期的結束日期
    """
    if frequency == 'monthly':
        # 每月底：1月31日、2月28/29日、3月31日...
        start_of_month = base_start_date + relativedelta(months=period_number - 1)
        end_date = start_of_month + relativedelta(months=1) - timedelta(days=1)
        
    elif frequency == 'quarterly':
        # 每季底：3月31日、6月30日、9月30日、12月31日
        quarter_end_months = [3, 6, 9, 12]
        month_index = (period_number - 1) % 4
        year_offset = (period_number - 1) // 4
        target_month = quarter_end_months[month_index]
        end_date = datetime(base_start_date.year + year_offset, target_month, 1) + \
                   relativedelta(months=1) - timedelta(days=1)
        
    elif frequency == 'semi-annually':
        # 每半年底：6月30日、12月31日
        if period_number % 2 == 1:  # 奇數期：6月30日
            target_month = 6
        else:  # 偶數期：12月31日
            target_month = 12
        year_offset = (period_number - 1) // 2
        end_date = datetime(base_start_date.year + year_offset, target_month, 1) + \
                   relativedelta(months=1) - timedelta(days=1)
        
    elif frequency == 'annually':
        # 每年底：12月31日
        end_date = datetime(base_start_date.year + period_number - 1, 12, 31)
    
    return end_date


def generate_simulation_timeline(investment_years: int, frequency: str) -> List[Dict]:
    """
    生成完整模擬數據時間軸，包含交易日調整
    
    Args:
        investment_years: 投資年數
        frequency: 投資頻率
        
    Returns:
        list: 包含每期完整時間資訊的列表
    """
    # 設定起始日期為次年1月1日
    current_year = datetime.now().year
    base_start_date = datetime(current_year + 1, 1, 1)
    
    # 計算總期數
    periods_per_year = {
        'monthly': 12, 
        'quarterly': 4, 
        'semi-annually': 2, 
        'annually': 1
    }
    total_periods = investment_years * periods_per_year[frequency]
    
    # 生成每期的詳細時間資訊
    timeline = []
    for period in range(1, total_periods + 1):
        # 計算原始日期
        raw_start = calculate_period_start_date(base_start_date, frequency, period)
        raw_end = calculate_period_end_date(base_start_date, frequency, period)
        
        # 調整為交易日
        adjusted_start = adjust_for_trading_days(raw_start, 'next')
        adjusted_end = adjust_for_trading_days(raw_end, 'previous')
        
        # 生成期間內的所有交易日
        trading_days = generate_trading_days(adjusted_start, adjusted_end)
        
        period_info = {
            'period': period,
            'raw_start_date': raw_start,
            'raw_end_date': raw_end,
            'adjusted_start_date': adjusted_start,
            'adjusted_end_date': adjusted_end,
            'trading_days': trading_days,
            'trading_days_count': len(trading_days),
            'date_adjustments': {
                'start_adjusted': raw_start != adjusted_start,
                'end_adjusted': raw_end != adjusted_end,
                'start_adjustment_days': (adjusted_start - raw_start).days,
                'end_adjustment_days': (raw_end - adjusted_end).days
            }
        }
        
        timeline.append(period_info)
    
    return timeline


def estimate_trading_days(start_date: datetime, end_date: datetime) -> int:
    """
    估算期間內的交易日數量 (用於驗證)
    
    Args:
        start_date: 起始日期
        end_date: 結束日期
        
    Returns:
        int: 估算的交易日數量
    """
    total_days = (end_date - start_date).days + 1
    
    # 粗略估算: 總天數 * 5/7 (週一到週五) * 0.95 (扣除假期)
    estimated_trading_days = int(total_days * (5/7) * 0.95)
    
    return estimated_trading_days


def validate_simulation_data(timeline_data: List[Dict]) -> Dict:
    """
    驗證模擬數據的一致性和正確性
    
    Args:
        timeline_data: 完整的時間軸模擬數據
        
    Returns:
        dict: 驗證結果報告
    """
    validation_report = {
        'is_valid': True,
        'errors': [],
        'warnings': [],
        'statistics': {}
    }
    
    # 1. 日期連續性檢查
    for i in range(1, len(timeline_data)):
        prev_end = timeline_data[i-1]['adjusted_end_date']
        curr_start = timeline_data[i]['adjusted_start_date']
        
        # 檢查期間是否有重疊或缺失
        if curr_start <= prev_end:
            validation_report['errors'].append(
                f"第{i}期與第{i+1}期日期重疊或缺失"
            )
            validation_report['is_valid'] = False
    
    # 2. 交易日數量合理性檢查
    for period_data in timeline_data:
        expected_trading_days = estimate_trading_days(
            period_data['adjusted_start_date'],
            period_data['adjusted_end_date']
        )
        actual_trading_days = period_data['trading_days_count']
        
        if abs(actual_trading_days - expected_trading_days) > 3:
            validation_report['warnings'].append(
                f"第{period_data['period']}期交易日數量異常: "
                f"預期{expected_trading_days}, 實際{actual_trading_days}"
            )
    
    return validation_report


def generate_period_price_timeline(period_info: Dict, initial_price: float, market_params: Dict) -> Dict:
    """
    為特定期間生成完整的價格時間序列
    
    依據需求文件1.1.3節規格實作，使用幾何布朗運動生成每日價格
    
    Args:
        period_info: 從 generate_simulation_timeline 取得的期間資訊
        initial_price: 期初價格
        market_params: 市場參數 (均值回歸、波動率等)
            - annual_return: 年化報酬率
            - volatility: 年化波動率
    
    Returns:
        dict: 包含每日價格和關鍵日期價格的字典
    """
    import numpy as np
    
    try:
        trading_days = period_info['trading_days']
        daily_prices = []
        
        # 提取市場參數
        annual_return = market_params.get('annual_return', 0.08)
        volatility = market_params.get('volatility', 0.15)
        
        # 使用幾何布朗運動生成每日價格
        current_price = initial_price
        for i, date in enumerate(trading_days):
            if i == 0:
                # 期初價格
                daily_prices.append({
                    'date': date,
                    'price': current_price,
                    'price_type': 'period_start'
                })
            else:
                # 使用隨機過程生成下一日價格
                dt = 1/252  # 每日時間增量
                drift = annual_return - 0.5 * volatility**2
                diffusion = volatility * np.random.normal(0, np.sqrt(dt))
                
                current_price = current_price * np.exp(drift * dt + diffusion)
                
                price_type = 'period_end' if i == len(trading_days) - 1 else 'intermediate'
                daily_prices.append({
                    'date': date,
                    'price': round(current_price, 2),
                    'price_type': price_type
                })
        
        # 計算統計信息
        prices_only = [p['price'] for p in daily_prices]
        period_return = (daily_prices[-1]['price'] / daily_prices[0]['price']) - 1
        
        return {
            'period': period_info['period'],
            'period_start_price': daily_prices[0]['price'],
            'period_end_price': daily_prices[-1]['price'],
            'daily_prices': daily_prices,
            'period_return': period_return,
            'price_statistics': {
                'min_price': min(prices_only),
                'max_price': max(prices_only),
                'avg_price': sum(prices_only) / len(prices_only)
            }
        }
        
    except Exception as e:
        # 錯誤處理：返回基本結構
        return {
            'period': period_info.get('period', 1),
            'period_start_price': initial_price,
            'period_end_price': initial_price,
            'daily_prices': [],
            'period_return': 0.0,
            'price_statistics': {
                'min_price': initial_price,
                'max_price': initial_price,
                'avg_price': initial_price
            },
            'error': str(e)
        } 