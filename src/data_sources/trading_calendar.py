"""
交易日曆與日期計算模組

提供投資期間的日期計算、交易日調整和美國股市假期處理功能。
實現精確的期初期末日期計算和交易日驗證機制。
"""

import logging
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from typing import List, Tuple

# 設定日誌
logger = logging.getLogger(__name__)


def calculate_period_start_date(base_start_date: datetime, frequency: str, period_number: int) -> datetime:
    """
    計算各期的期初日期
    
    Args:
        base_start_date: 第1期起始日期 (例如: 2025-01-01)
        frequency: 投資頻率 ('monthly', 'quarterly', 'semi-annually', 'annually')
        period_number: 期數 (1, 2, 3, ...)
    
    Returns:
        datetime: 該期的起始日期
        
    Raises:
        ValueError: 當frequency不支援或period_number無效時
    """
    if period_number < 1:
        raise ValueError(f"期數必須大於等於1，收到: {period_number}")
    
    if frequency == 'monthly':
        # 每月1日開始
        start_date = base_start_date + relativedelta(months=period_number - 1)
        
    elif frequency == 'quarterly':
        # 每季第一日：1/1, 4/1, 7/1, 10/1
        quarter_start_months = [1, 4, 7, 10]
        month_index = (period_number - 1) % 4
        year_offset = (period_number - 1) // 4
        start_date = datetime(
            base_start_date.year + year_offset, 
            quarter_start_months[month_index], 
            1
        )
        
    elif frequency == 'semi-annually':
        # 每半年第一日：1/1, 7/1
        if period_number % 2 == 1:  # 奇數期：1月1日
            target_month = 1
        else:  # 偶數期：7月1日
            target_month = 7
        year_offset = (period_number - 1) // 2
        start_date = datetime(
            base_start_date.year + year_offset, 
            target_month, 
            1
        )
        
    elif frequency == 'annually':
        # 每年1月1日開始
        start_date = datetime(
            base_start_date.year + period_number - 1, 
            1, 
            1
        )
    else:
        raise ValueError(f"不支援的投資頻率: {frequency}")
    
    logger.debug(f"計算第{period_number}期({frequency})起始日期: {start_date.strftime('%Y-%m-%d')}")
    return start_date


def calculate_period_end_dates(base_start_date: datetime, frequency: str, period_number: int) -> datetime:
    """
    計算各期的期末日期
    
    Args:
        base_start_date: 第1期起始日期 (例如: 2025-01-01)
        frequency: 投資頻率 ('monthly', 'quarterly', 'semi-annually', 'annually')
        period_number: 期數 (1, 2, 3, ...)
    
    Returns:
        datetime: 該期的結束日期
        
    Raises:
        ValueError: 當frequency不支援或period_number無效時
    """
    if period_number < 1:
        raise ValueError(f"期數必須大於等於1，收到: {period_number}")
    
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
        end_date = datetime(
            base_start_date.year + period_number - 1, 
            12, 
            31
        )
    else:
        raise ValueError(f"不支援的投資頻率: {frequency}")
    
    logger.debug(f"計算第{period_number}期({frequency})結束日期: {end_date.strftime('%Y-%m-%d')}")
    return end_date


def get_us_market_holidays(year: int) -> List[datetime]:
    """
    取得特定年份的美國股市假期
    
    Args:
        year: 年份
    
    Returns:
        list: 該年度所有股市假期的日期列表
    """
    holidays = []
    
    # 固定日期假期
    holidays.extend([
        datetime(year, 1, 1),   # 元旦
        datetime(year, 7, 4),   # 獨立日
        datetime(year, 12, 25), # 聖誕節
    ])
    
    # 浮動假期 (需要計算的)
    holidays.extend([
        _get_mlk_day(year),           # 馬丁路德金恩日 (1月第3個週一)
        _get_presidents_day(year),    # 總統日 (2月第3個週一)
        _get_good_friday(year),       # 耶穌受難日 (復活節前的週五)
        _get_memorial_day(year),      # 陣亡將士紀念日 (5月最後一個週一)
        _get_labor_day(year),         # 勞動節 (9月第1個週一)
        _get_thanksgiving(year),      # 感恩節 (11月第4個週四)
    ])
    
    # 調整假期遇到週末的情況
    adjusted_holidays = []
    for holiday in holidays:
        if holiday.weekday() == 5:  # 週六
            adjusted_holidays.append(holiday - timedelta(days=1))  # 提前到週五
        elif holiday.weekday() == 6:  # 週日
            adjusted_holidays.append(holiday + timedelta(days=1))  # 延後到週一
        else:
            adjusted_holidays.append(holiday)
    
    return sorted(set(adjusted_holidays))


def _get_mlk_day(year: int) -> datetime:
    """馬丁路德金恩日 - 1月第3個週一"""
    return _get_nth_weekday(year, 1, 0, 3)  # 1月的第3個週一


def _get_presidents_day(year: int) -> datetime:
    """總統日 - 2月第3個週一"""
    return _get_nth_weekday(year, 2, 0, 3)  # 2月的第3個週一


def _get_memorial_day(year: int) -> datetime:
    """陣亡將士紀念日 - 5月最後一個週一"""
    return _get_last_weekday(year, 5, 0)  # 5月最後一個週一


def _get_labor_day(year: int) -> datetime:
    """勞動節 - 9月第1個週一"""
    return _get_nth_weekday(year, 9, 0, 1)  # 9月的第1個週一


def _get_thanksgiving(year: int) -> datetime:
    """感恩節 - 11月第4個週四"""
    return _get_nth_weekday(year, 11, 3, 4)  # 11月的第4個週四


def _get_good_friday(year: int) -> datetime:
    """耶穌受難日 - 復活節前的週五"""
    easter = _calculate_easter(year)
    return easter - timedelta(days=2)  # 復活節前的週五


def _calculate_easter(year: int) -> datetime:
    """計算復活節日期 (使用Anonymous Gregorian Algorithm)"""
    a = year % 19
    b = year // 100
    c = year % 100
    d = b // 4
    e = b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i = c // 4
    k = c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    month = (h + l - 7 * m + 114) // 31
    day = ((h + l - 7 * m + 114) % 31) + 1
    
    return datetime(year, month, day)


def _get_nth_weekday(year: int, month: int, weekday: int, n: int) -> datetime:
    """取得指定月份的第n個指定星期幾"""
    first_day = datetime(year, month, 1)
    first_weekday = first_day.weekday()
    
    # 計算第一個指定星期幾的日期
    days_ahead = weekday - first_weekday
    if days_ahead < 0:
        days_ahead += 7
    
    first_occurrence = first_day + timedelta(days=days_ahead)
    nth_occurrence = first_occurrence + timedelta(weeks=n-1)
    
    return nth_occurrence


def _get_last_weekday(year: int, month: int, weekday: int) -> datetime:
    """取得指定月份的最後一個指定星期幾"""
    # 先取得下個月的第一天，然後往前找
    if month == 12:
        next_month = datetime(year + 1, 1, 1)
    else:
        next_month = datetime(year, month + 1, 1)
    
    last_day = next_month - timedelta(days=1)
    
    # 往前找到最後一個指定星期幾
    days_back = (last_day.weekday() - weekday) % 7
    return last_day - timedelta(days=days_back)


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
    date_only = datetime(date.year, date.month, date.day)
    if date_only in year_holidays:
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
        
    Raises:
        ValueError: 當adjustment_type無效或找不到交易日時
    """
    if adjustment_type not in ['next', 'previous']:
        raise ValueError(f"adjustment_type必須為'next'或'previous'，收到: {adjustment_type}")
    
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
    
    if adjustments > 0:
        logger.debug(f"日期調整: {target_date.strftime('%Y-%m-%d')} -> {adjusted_date.strftime('%Y-%m-%d')} ({adjustment_type})")
    
    return adjusted_date


def generate_trading_days(start_date: datetime, end_date: datetime) -> List[datetime]:
    """
    生成指定期間內的所有交易日
    
    Args:
        start_date: 起始日期
        end_date: 結束日期
    
    Returns:
        list: 期間內所有交易日的列表
        
    Raises:
        ValueError: 當start_date > end_date時
    """
    if start_date > end_date:
        raise ValueError(f"起始日期不能晚於結束日期: {start_date} > {end_date}")
    
    trading_days = []
    current_date = start_date
    
    while current_date <= end_date:
        if is_trading_day(current_date):
            trading_days.append(current_date)
        current_date += timedelta(days=1)
    
    logger.debug(f"期間 {start_date.strftime('%Y-%m-%d')} 至 {end_date.strftime('%Y-%m-%d')} 共有 {len(trading_days)} 個交易日")
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


def generate_investment_timeline(investment_years: int, frequency: str, base_year: int = None) -> List[dict]:
    """
    生成完整投資時間軸，包含交易日調整
    
    Args:
        investment_years: 投資年數
        frequency: 投資頻率 ('monthly', 'quarterly', 'semi-annually', 'annually')
        base_year: 基準年份，預設為明年
    
    Returns:
        list: 包含每期完整時間資訊的列表
        
    Raises:
        ValueError: 當參數無效時
    """
    if investment_years <= 0:
        raise ValueError(f"投資年數必須大於0，收到: {investment_years}")
    
    # 設定起始日期為指定年份的1月1日
    if base_year is None:
        base_year = datetime.now().year + 1
    base_start_date = datetime(base_year, 1, 1)
    
    # 計算總期數
    periods_per_year = {
        'monthly': 12, 
        'quarterly': 4, 
        'semi-annually': 2, 
        'annually': 1
    }
    
    if frequency not in periods_per_year:
        raise ValueError(f"不支援的投資頻率: {frequency}")
    
    total_periods = investment_years * periods_per_year[frequency]
    
    # 生成每期的詳細時間資訊
    timeline = []
    for period in range(1, total_periods + 1):
        # 計算原始日期
        raw_start = calculate_period_start_date(base_start_date, frequency, period)
        raw_end = calculate_period_end_dates(base_start_date, frequency, period)
        
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
    
    logger.info(f"生成{frequency}投資時間軸：{total_periods}期，基準年份: {base_year}")
    return timeline


def get_target_dates_for_data_fetching(timeline: List[dict]) -> Tuple[datetime, datetime, List[datetime]]:
    """
    從投資時間軸中提取數據獲取所需的目標日期
    
    Args:
        timeline: 投資時間軸（從generate_investment_timeline獲得）
    
    Returns:
        tuple: (整體起始日期, 整體結束日期, 所有關鍵日期列表)
    """
    if not timeline:
        raise ValueError("投資時間軸不能為空")
    
    # 找出整體的起始和結束日期
    overall_start = timeline[0]['adjusted_start_date']
    overall_end = timeline[-1]['adjusted_end_date']
    
    # 收集所有關鍵日期（期初和期末）
    key_dates = []
    for period_info in timeline:
        key_dates.append(period_info['adjusted_start_date'])
        key_dates.append(period_info['adjusted_end_date'])
    
    # 去重並排序
    key_dates = sorted(set(key_dates))
    
    logger.info(f"數據獲取範圍: {overall_start.strftime('%Y-%m-%d')} 至 {overall_end.strftime('%Y-%m-%d')}")
    logger.info(f"關鍵日期數量: {len(key_dates)}")
    
    return overall_start, overall_end, key_dates 