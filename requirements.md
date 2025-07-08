# 投資策略比較系統開發需求規格

## 專案概述

**目標**：開發一個互動式 Streamlit 應用程式，比較 Value Averaging（定期定值）與 Dollar Cost Averaging（定期定額）兩種投資策略。

**核心功能**：
- 提供參數輸入界面和動態圖表顯示
- 支援歷史數據回測與模擬情境分析
- 提供績效比較與 CSV 下載功能

---

## 1. 數據源與資訊流定義

本章節完整定義投資策略比較系統的所有數據來源、處理流程、安全機制與驗證標準，確保數據完整性與系統穩定性。

### 1.1 外部數據源配置與管理

#### 1.1.1 Tiingo API - 股票數據來源

**API 基本配置**
- **服務提供商**: Tiingo Financial Data Platform
- **主要標的**: SPY (SPDR S&P 500 ETF Trust)
- **API 端點**: `https://api.tiingo.com/tiingo/daily/SPY/prices`
- **認證方式**: Token 參數認證
- **數據頻率**: 日線數據（後續依投資頻率聚合）
- **數據覆蓋期間**: 1993-01-29 至當前日期

**請求參數規格**
```
GET https://api.tiingo.com/tiingo/daily/SPY/prices
?startDate={起始日期 YYYY-MM-DD}
&endDate={結束日期 YYYY-MM-DD}
&columns=date,adjClose
&token={TIINGO_API_KEY}
```

**回應數據格式** (僅包含必要欄位)
```json
[
  {
    "date": "2024-01-02T00:00:00.000Z",
    "adjClose": 476.28
  }
]
```

**數據處理規則**
- **使用欄位**: `date`, `adjClose` (調整後收盤價)
- **日期處理**: 轉換為 YYYY-MM-DD 格式，移除時區資訊
- **價格驗證**: 確保 adjClose > 0，異常值記錄警告
- **缺失數據**: 非交易日採用前一交易日價格

**優化版數據獲取策略**
- **目標日期計算**: 根據投資頻率與期數，預先計算所有期初/期末目標日期
- **交易日調整**: 將目標日期調整為最近的美股有效交易日
- **批次API調用**: 一次性獲取涵蓋所有目標日期的完整日期範圍數據
- **精準提取**: 從完整數據中僅提取期初/期末所需的數據點

**頻率聚合規則**
- **每月投資**: 期初取每月第一個交易日，期末取最後一個交易日
- **每季投資**: 期初取每季第一個交易日，期末取最後一個交易日  
- **每半年投資**: 期初取每半年第一個交易日，期末取最後一個交易日
- **每年投資**: 期初取每年第一個交易日，期末取最後一個交易日

**效能優化效益**
- **減少API調用次數**: 從N次調用減少至1次批次調用
- **降低數據傳輸量**: 僅獲取必要日期範圍，避免冗餘數據
- **提升處理速度**: 消除重複的數據聚合與預處理步驟
- **改善用戶體驗**: 顯著縮短數據載入等待時間

#### 1.1.2 FRED API - 債券數據來源

**API 基本配置**
- **服務提供商**: Federal Reserve Economic Data (FRED)
- **主要標的**: DGS1 (1-Year Treasury Constant Maturity Rate)
- **API 端點**: `https://api.stlouisfed.org/fred/series/observations`
- **認證方式**: api_key 參數認證
- **數據單位**: 年化殖利率百分比
- **數據更新頻率**: 每工作日

**請求參數規格**
```
GET https://api.stlouisfed.org/fred/series/observations
?series_id=DGS1
&observation_start={起始日期 YYYY-MM-DD}
&observation_end={結束日期 YYYY-MM-DD}
&api_key={FRED_API_KEY}
&file_type=json
```

**回應數據格式**
```json
{
  "realtime_start": "2024-01-01",
  "realtime_end": "2024-01-01",
  "observation_start": "1962-01-02",
  "observation_end": "9999-12-31",
  "units": "lin",
  "output_type": 1,
  "file_type": "json",
  "order_by": "observation_date",
  "sort_order": "asc",
  "count": 15000,
  "offset": 0,
  "limit": 100000,
  "observations": [
    {
      "realtime_start": "2024-01-01",
      "realtime_end": "2024-01-01",
      "date": "2024-01-01",
      "value": "5.02"
    }
  ]
}
```

**債券價格計算**
- **債券定價公式**: `Bond_Price = 100 / (1 + Yield_Rate/100)`
- **假設條件**: 面值100，無息債券，到期1年
- **殖利率處理**: 字串轉浮點數，"." 值視為缺失數據
- **價格驗證**: 確保計算後價格在合理範圍 (70-130)

**批次數據獲取優化**
- **完整範圍調用**: 一次性獲取投資期間的完整債券殖利率數據
- **目標日期匹配**: 從完整數據中精確匹配期初/期末交易日的殖利率
- **缺失值處理**: 若目標日期無數據，使用最近可用交易日的殖利率
- **數據快取**: 批次獲取的完整數據進行快取，避免重複API調用

#### 1.1.3 模擬數據生成規格

**市場情境模擬參數**
- **牛市特徵**:
  - 年化報酬率: 8% ~ 12% (正態分佈)
  - 年化波動率: 15% ~ 20%
  - 持續期間: 3 ~ 7年 (隨機)
- **熊市特徵**:
  - 年化報酬率: -10% ~ 2% (偏態分佈)
  - 年化波動率: 25% ~ 35%
  - 持續期間: 1 ~ 3年 (隨機)

**模擬數據日期設定規則**

**第1期初始日期設定原則**
- **使用者輸入**: 由使用者透過日期選擇器輸入第1期起始日期
- **預設值**: 當下日期的次一年1月1日作為預設起始日
- **範例**: 若當前為2025年任何日期，預設第1期起始日期為2026年1月1日，使用者可自由修改
- **設計原因**: 提供彈性的投資起始時間設定，同時保持合理的預設值
- **輸入限制**: 
  - 最早日期：當前日期
  - 最晚日期：當前日期後10年
  - 自動調整為交易日：若選擇非交易日，系統自動調整為下一個交易日

**期初期末日期計算邏輯**

**期初日期計算函數**
```python
def calculate_period_start_date(base_start_date, frequency, period_number):
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

def calculate_period_end_dates(base_start_date, frequency, period_number):
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
```

**具體日期範例表格**

*基準設定：第1期起始日為2026年1月1日，投資4期*

| 投資頻率 | 第1期期間 | 第2期期間 | 第3期期間 | 第4期期間 |
|----------|-----------|-----------|-----------|-----------|
| **每月投資** | 2026/01/01 - 2026/01/31 | 2026/02/01 - 2026/02/28 | 2026/03/01 - 2026/03/31 | 2026/04/01 - 2026/04/30 |
| **每季投資** | 2026/01/01 - 2026/03/31 | 2026/04/01 - 2026/06/30 | 2026/07/01 - 2026/09/30 | 2026/10/01 - 2026/12/31 |
| **每半年投資** | 2026/01/01 - 2026/06/30 | 2026/07/01 - 2026/12/31 | 2027/01/01 - 2027/06/30 | 2027/07/01 - 2027/12/31 |
| **每年投資** | 2026/01/01 - 2026/12/31 | 2027/01/01 - 2027/12/31 | 2028/01/01 - 2028/12/31 | 2029/01/01 - 2029/12/31 |

**交易日調整與驗證**

*不同頻率在遇到非交易日時的具體調整範例*

| 情境 | 原始日期 | 調整後日期 | 調整原因 |
|------|----------|------------|----------|
| 月初為週末 | 2025/06/01 (週日) | 2025/06/02 (週一) | 期初日期往後調整至交易日 |
| 月末為週末 | 2025/08/31 (週日) | 2025/08/29 (週五) | 期末日期往前調整至交易日 |
| 遇到國定假日 | 2025/07/04 (獨立日) | 2025/07/03 (週四) | 期末日期避開假期 |
| 新年假期 | 2025/01/01 (元旦) | 2025/01/02 (週四) | 期初日期順延至下一交易日 |

**完整時間軸生成架構**

**完整時間軸生成架構**
```python
def generate_simulation_timeline(investment_years, frequency, user_start_date=None):
    """
    生成完整模擬數據時間軸，包含交易日調整
    
    Args:
        investment_years: 投資年數
        frequency: 投資頻率
        user_start_date: 使用者指定的起始日期，若為None則使用預設值
    
    Returns:
        list: 包含每期完整時間資訊的列表
    """
    # 設定起始日期：使用者輸入或預設為次年1月1日
    if user_start_date is None:
        current_year = datetime.now().year
        base_start_date = datetime(current_year + 1, 1, 1)
    else:
        # 確保使用者輸入的日期為交易日
        base_start_date = adjust_for_trading_days(user_start_date, 'next')
    
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
    
    return timeline

def generate_period_price_timeline(period_info, initial_price, market_params):
    """
    為特定期間生成完整的價格時間序列
    
    Args:
        period_info: 從 generate_simulation_timeline 取得的期間資訊
        initial_price: 期初價格
        market_params: 市場參數 (均值回歸、波動率等)
    
    Returns:
        dict: 包含每日價格和關鍵日期價格的字典
    """
    trading_days = period_info['trading_days']
    daily_prices = []
    
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
            drift = market_params['annual_return'] - 0.5 * market_params['volatility']**2
            diffusion = market_params['volatility'] * np.random.normal(0, np.sqrt(dt))
            
            current_price = current_price * np.exp(drift * dt + diffusion)
            
            price_type = 'period_end' if i == len(trading_days) - 1 else 'intermediate'
            daily_prices.append({
                'date': date,
                'price': current_price,
                'price_type': price_type
            })
    
    return {
        'period': period_info['period'],
        'period_start_price': daily_prices[0]['price'],
        'period_end_price': daily_prices[-1]['price'],
        'daily_prices': daily_prices,
        'period_return': (daily_prices[-1]['price'] / daily_prices[0]['price']) - 1,
        'price_statistics': {
            'min_price': min([p['price'] for p in daily_prices]),
            'max_price': max([p['price'] for p in daily_prices]),
            'avg_price': sum([p['price'] for p in daily_prices]) / len(daily_prices)
        }
    }
```

**數據生成方法**
- **股票價格**: 幾何布朗運動 (Geometric Brownian Motion)
  ```
  S(t+1) = S(t) * exp((μ - σ²/2) * dt + σ * √dt * Z)
  其中 Z ~ N(0,1)
  ```
- **債券殖利率**: Vasicek 利率模型
  ```
  dr = α(θ - r)dt + σ dW
  ```
- **隨機種子**: 支援設定固定種子確保結果可重現

**交易日處理與假期管理規則**

**美國股市交易日規則**
```python
def get_us_market_holidays(year):
    """
    取得特定年份的美國股市假期
    
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
        get_mlk_day(year),           # 馬丁路德金恩日 (1月第3個週一)
        get_presidents_day(year),    # 總統日 (2月第3個週一)
        get_good_friday(year),       # 耶穌受難日 (復活節前的週五)
        get_memorial_day(year),      # 陣亡將士紀念日 (5月最後一個週一)
        get_labor_day(year),         # 勞動節 (9月第1個週一)
        get_thanksgiving(year),      # 感恩節 (11月第4個週四)
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

def is_trading_day(date):
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

def adjust_for_trading_days(target_date, adjustment_type='next'):
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

def generate_trading_days(start_date, end_date):
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

def get_trading_day_count(start_date, end_date):
    """
    計算期間內的交易日數量
    
    Returns:
        int: 交易日總數
    """
    return len(generate_trading_days(start_date, end_date))
```

**模擬數據精確度與驗證機制**

**價格模擬精確度設定**
- **價格精度**: 保留至小數點後2位 (美元分)
- **殖利率精度**: 保留至小數點後4位 (基點)
- **比例精度**: 保留至小數點後2位 (百分比)

**數據一致性驗證規則**
```python
def validate_simulation_data(timeline_data):
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
    
    # 3. 價格合理性檢查
    for period_data in timeline_data:
        if 'price_statistics' in period_data:
            price_stats = period_data['price_statistics']
            
            # 檢查價格是否為正數
            if price_stats['min_price'] <= 0:
                validation_report['errors'].append(
                    f"第{period_data['period']}期出現非正數價格"
                )
                validation_report['is_valid'] = False
            
            # 檢查單期波動是否過大 (超過50%)
            period_volatility = abs(
                price_stats['max_price'] / price_stats['min_price'] - 1
            )
            if period_volatility > 0.5:
                validation_report['warnings'].append(
                    f"第{period_data['period']}期波動過大: {period_volatility:.2%}"
                )
    
    return validation_report

def estimate_trading_days(start_date, end_date):
    """
    估算期間內的交易日數量 (用於驗證)
    
    Returns:
        int: 估算的交易日數量
    """
    total_days = (end_date - start_date).days + 1
    
    # 粗略估算: 總天數 * 5/7 (週一到週五) * 0.95 (扣除假期)
    estimated_trading_days = int(total_days * (5/7) * 0.95)
    
    return estimated_trading_days
```

### 1.2 API安全機制與容錯處理

#### 1.2.1 API金鑰安全管理機制

**多層級金鑰獲取策略**
```python
def get_api_key(key_name, required=True):
    """
    安全獲取API金鑰的多層級策略
    
    Args:
        key_name: 金鑰名稱 ('TIINGO_API_KEY', 'FRED_API_KEY')
        required: 是否為必要金鑰
    
    Returns:
        str: API金鑰，如果找不到且required=True則拋出異常
    """
    import os
    import streamlit as st
    from dotenv import load_dotenv
    
    # 第1層：Streamlit Secrets (雲端部署優先)
    try:
        if hasattr(st, 'secrets') and key_name in st.secrets:
            key = st.secrets[key_name]
            if validate_api_key_format(key_name, key):
                return key
    except Exception as e:
        logging.warning(f"無法從Streamlit Secrets獲取{key_name}: {e}")
    
    # 第2層：環境變數
    key = os.environ.get(key_name)
    if key and validate_api_key_format(key_name, key):
        return key
    
    # 第3層：.env檔案 (本地開發)
    load_dotenv()
    key = os.getenv(key_name)
    if key and validate_api_key_format(key_name, key):
        return key
    
    # 第4層：錯誤處理
    if required:
        raise ValueError(f"必要API金鑰 {key_name} 未設定或格式無效")
    else:
        logging.warning(f"選用API金鑰 {key_name} 未設定，將使用備用方案")
        return None

def validate_api_key_format(key_name, key_value):
    """
    驗證API金鑰格式
    
    Args:
        key_name: 金鑰名稱
        key_value: 金鑰值
    
    Returns:
        bool: 是否為有效格式
    """
    if not key_value or not isinstance(key_value, str):
        return False
    
    # Tiingo API金鑰驗證
    if key_name == 'TIINGO_API_KEY':
        # 至少20字符的字母數字組合
        return len(key_value) >= 20 and key_value.replace('_', '').replace('-', '').isalnum()
    
    # FRED API金鑰驗證  
    elif key_name == 'FRED_API_KEY':
        # 32字符的字母數字組合
        return len(key_value) == 32 and key_value.isalnum()
    
    return False

def test_api_connectivity(api_service, api_key):
    """
    測試API連通性
    
    Args:
        api_service: 'tiingo' 或 'fred'
        api_key: API金鑰
    
    Returns:
        dict: 連通性測試結果
    """
    import requests
    from datetime import datetime, timedelta
    
    test_result = {
        'service': api_service,
        'is_connected': False,
        'response_time': None,
        'error_message': None,
        'status_code': None
    }
    
    try:
        start_time = datetime.now()
        
        if api_service == 'tiingo':
            # 測試Tiingo API
            test_url = "https://api.tiingo.com/tiingo/daily/SPY/prices"
            test_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
            params = {
                'startDate': test_date,
                'endDate': test_date,
                'token': api_key,
                'columns': 'date,adjClose'
            }
            response = requests.get(test_url, params=params, timeout=10)
            
        elif api_service == 'fred':
            # 測試FRED API
            test_url = "https://api.stlouisfed.org/fred/series/observations"
            params = {
                'series_id': 'DGS1',
                'api_key': api_key,
                'file_type': 'json',
                'limit': 1,
                'sort_order': 'desc'
            }
            response = requests.get(test_url, params=params, timeout=10)
        
        response_time = (datetime.now() - start_time).total_seconds()
        test_result['response_time'] = response_time
        test_result['status_code'] = response.status_code
        
        if response.status_code == 200:
            # 進一步驗證回應內容
            data = response.json()
            if api_service == 'tiingo' and isinstance(data, list) and len(data) > 0:
                test_result['is_connected'] = True
            elif api_service == 'fred' and 'observations' in data:
                test_result['is_connected'] = True
            else:
                test_result['error_message'] = "API回應格式異常"
        else:
            test_result['error_message'] = f"HTTP {response.status_code}: {response.text[:100]}"
            
    except requests.exceptions.Timeout:
        test_result['error_message'] = "API請求超時"
    except requests.exceptions.ConnectionError:
        test_result['error_message'] = "無法連接到API服務"
    except Exception as e:
        test_result['error_message'] = f"API測試失敗: {str(e)}"
    
    return test_result
```

#### 1.2.2 API容錯與備援機制

**分級容錯策略管理器**
```python
class APIFaultToleranceManager:
    """API容錯與備援管理器"""
    
    def __init__(self):
        self.retry_config = {
            'max_retries': 3,
            'base_delay': 1.0,  # 基礎延遲秒數
            'backoff_factor': 2.0,  # 退避係數
            'timeout': 30
        }
        
        self.fallback_strategies = {
            'tiingo': ['yahoo_finance', 'local_csv', 'simulation'],
            'fred': ['local_yield_data', 'fixed_yield_assumption']
        }
    
    def fetch_with_retry(self, api_function, *args, **kwargs):
        """
        具備重試機制的API請求
        
        Args:
            api_function: API請求函數
            *args, **kwargs: API函數的參數
        
        Returns:
            API回應數據或None
        """
        import time
        import random
        
        last_exception = None
        
        for attempt in range(self.retry_config['max_retries']):
            try:
                # 執行API請求
                result = api_function(*args, **kwargs)
                
                if result is not None:
                    if attempt > 0:
                        logging.info(f"API請求在第{attempt + 1}次嘗試後成功")
                    return result
                    
            except Exception as e:
                last_exception = e
                logging.warning(f"API請求第{attempt + 1}次失敗: {e}")
                
                # 計算延遲時間（指數退避 + 隨機抖動）
                if attempt < self.retry_config['max_retries'] - 1:
                    delay = self.retry_config['base_delay'] * (
                        self.retry_config['backoff_factor'] ** attempt
                    )
                    jitter = random.uniform(0.1, 0.5)  # 添加隨機抖動
                    time.sleep(delay + jitter)
        
        # 所有重試都失敗
        logging.error(f"API請求在{self.retry_config['max_retries']}次嘗試後全部失敗")
        raise last_exception if last_exception else Exception("API請求失敗")
    
    def execute_fallback_strategy(self, primary_service, start_date, end_date):
        """
        執行備援策略
        
        Args:
            primary_service: 主要服務名稱 ('tiingo' 或 'fred')
            start_date: 開始日期
            end_date: 結束日期
        
        Returns:
            tuple: (data, fallback_method_used)
        """
        fallback_methods = self.fallback_strategies.get(primary_service, [])
        
        for method in fallback_methods:
            try:
                logging.info(f"嘗試備援方案: {method}")
                
                if method == 'yahoo_finance':
                    data = self._fetch_yahoo_finance(start_date, end_date)
                elif method == 'local_csv':
                    data = self._fetch_local_csv(start_date, end_date)
                elif method == 'simulation':
                    data = self._generate_simulation_data(start_date, end_date)
                elif method == 'local_yield_data':
                    data = self._fetch_local_yield_data(start_date, end_date)
                elif method == 'fixed_yield_assumption':
                    data = self._generate_fixed_yield_data(start_date, end_date)
                
                if data is not None and len(data) > 0:
                    logging.info(f"備援方案 {method} 成功獲取數據")
                    return data, method
                    
            except Exception as e:
                logging.warning(f"備援方案 {method} 失敗: {e}")
                continue
        
        # 所有備援方案都失敗
        raise Exception(f"所有{primary_service}備援方案都失敗")
    
    def _fetch_yahoo_finance(self, start_date, end_date):
        """Yahoo Finance備援數據獲取"""
        try:
            import yfinance as yf
            ticker = yf.Ticker("SPY")
            data = ticker.history(start=start_date, end=end_date)
            return [{'date': idx.strftime('%Y-%m-%d'), 'adjClose': row['Close']} 
                   for idx, row in data.iterrows()]
        except ImportError:
            logging.warning("yfinance套件未安裝，跳過Yahoo Finance備援")
            return None
        except Exception as e:
            logging.error(f"Yahoo Finance數據獲取失敗: {e}")
            return None
    
    def _fetch_local_csv(self, start_date, end_date):
        """本地CSV檔案備援數據"""
        try:
            import pandas as pd
            csv_path = "data/spy_backup.csv"
            
            if os.path.exists(csv_path):
                df = pd.read_csv(csv_path)
                df['date'] = pd.to_datetime(df['date'])
                
                # 篩選日期範圍
                mask = (df['date'] >= start_date) & (df['date'] <= end_date)
                filtered_df = df.loc[mask]
                
                return [{'date': row['date'].strftime('%Y-%m-%d'), 
                        'adjClose': row['adjClose']} 
                       for _, row in filtered_df.iterrows()]
        except Exception as e:
            logging.error(f"本地CSV數據讀取失敗: {e}")
            return None
    
    def _generate_simulation_data(self, start_date, end_date):
        """生成模擬數據作為最終備援"""
        try:
            from datetime import datetime, timedelta
            import numpy as np
            
            # 簡化的模擬數據生成
            dates = pd.date_range(start=start_date, end=end_date, freq='D')
            initial_price = 400.0  # SPY假設初始價格
            
            data = []
            current_price = initial_price
            
            for date in dates:
                # 簡單的隨機遊走
                daily_return = np.random.normal(0.0007, 0.015)  # 約年化8%報酬，15%波動
                current_price *= (1 + daily_return)
                
                data.append({
                    'date': date.strftime('%Y-%m-%d'),
                    'adjClose': round(current_price, 2)
                })
            
            return data
            
        except Exception as e:
            logging.error(f"模擬數據生成失敗: {e}")
            return None
```

#### 1.2.3 數據品質控制與驗證

**統一數據品質驗證標準**
```python
class DataQualityValidator:
    """數據品質控制與驗證器"""
    
    def __init__(self):
        self.validation_rules = {
            'price_data': {
                'min_price': 0.01,
                'max_price': 10000.0,
                'max_daily_change': 0.2,  # 20%
                'min_data_points': 1
            },
            'yield_data': {
                'min_yield': -5.0,  # -5%
                'max_yield': 25.0,  # 25%
                'max_daily_change': 5.0,  # 5個百分點
                'min_data_points': 1
            },
            'date_continuity': {
                'max_gap_days': 10,  # 最大允許的數據缺口
                'required_coverage': 0.8  # 期間內至少80%的交易日有數據
            }
        }
    
    def validate_market_data(self, data, data_type='price_data'):
        """
        驗證市場數據品質
        
        Args:
            data: 市場數據列表
            data_type: 數據類型 ('price_data' 或 'yield_data')
        
        Returns:
            dict: 驗證結果報告
        """
        validation_result = {
            'is_valid': True,
            'errors': [],
            'warnings': [],
            'statistics': {},
            'data_quality_score': 0.0
        }
        
        if not data or len(data) == 0:
            validation_result['is_valid'] = False
            validation_result['errors'].append("數據為空")
            return validation_result
        
        rules = self.validation_rules[data_type]
        
        # 1. 數據量檢查
        if len(data) < rules['min_data_points']:
            validation_result['errors'].append(
                f"數據點數量不足: {len(data)} < {rules['min_data_points']}"
            )
            validation_result['is_valid'] = False
        
        # 2. 數值範圍檢查
        value_field = 'adjClose' if data_type == 'price_data' else 'value'
        
        values = []
        for item in data:
            if value_field in item and item[value_field] is not None:
                try:
                    value = float(item[value_field])
                    values.append(value)
                    
                    # 檢查範圍
                    if data_type == 'price_data':
                        if value < rules['min_price'] or value > rules['max_price']:
                            validation_result['warnings'].append(
                                f"價格超出合理範圍: {value} 在 {item['date']}"
                            )
                    elif data_type == 'yield_data':
                        if value < rules['min_yield'] or value > rules['max_yield']:
                            validation_result['warnings'].append(
                                f"殖利率超出合理範圍: {value}% 在 {item['date']}"
                            )
                            
                except (ValueError, TypeError):
                    validation_result['errors'].append(
                        f"無效的數值格式: {item[value_field]} 在 {item['date']}"
                    )
        
        # 3. 日間變化檢查
        if len(values) > 1:
            daily_changes = []
            for i in range(1, len(values)):
                change = abs((values[i] - values[i-1]) / values[i-1])
                daily_changes.append(change)
                
                if change > rules['max_daily_change']:
                    validation_result['warnings'].append(
                        f"異常的日間變化: {change:.2%} 在 {data[i]['date']}"
                    )
            
            validation_result['statistics']['max_daily_change'] = max(daily_changes)
            validation_result['statistics']['avg_daily_change'] = sum(daily_changes) / len(daily_changes)
        
        # 4. 日期連續性檢查
        date_continuity = self._check_date_continuity(data)
        validation_result['statistics']['date_continuity'] = date_continuity
        
        if date_continuity['coverage_ratio'] < rules['required_coverage']:
            validation_result['warnings'].append(
                f"數據覆蓋率不足: {date_continuity['coverage_ratio']:.2%}"
            )
        
        # 5. 計算數據品質分數
        validation_result['data_quality_score'] = self._calculate_quality_score(
            validation_result, len(values)
        )
        
        # 6. 基本統計
        if values:
            validation_result['statistics'].update({
                'count': len(values),
                'min_value': min(values),
                'max_value': max(values),
                'mean_value': sum(values) / len(values),
                'value_range': max(values) - min(values)
            })
        
        return validation_result
    
    def _check_date_continuity(self, data):
        """檢查日期連續性"""
        try:
            from datetime import datetime, timedelta
            
            dates = [datetime.strptime(item['date'], '%Y-%m-%d') for item in data]
            dates.sort()
            
            if len(dates) < 2:
                return {'coverage_ratio': 1.0, 'gaps': [], 'total_days': 1}
            
            start_date = dates[0]
            end_date = dates[-1]
            total_days = (end_date - start_date).days + 1
            
            # 計算預期的交易日數量（假設約70%的日子是交易日）
            expected_trading_days = int(total_days * 0.7)
            actual_data_days = len(dates)
            coverage_ratio = actual_data_days / expected_trading_days if expected_trading_days > 0 else 1.0
            
            # 尋找數據缺口
            gaps = []
            for i in range(1, len(dates)):
                gap_days = (dates[i] - dates[i-1]).days
                if gap_days > self.validation_rules['date_continuity']['max_gap_days']:
                    gaps.append({
                        'start': dates[i-1].strftime('%Y-%m-%d'),
                        'end': dates[i].strftime('%Y-%m-%d'), 
                        'gap_days': gap_days
                    })
            
            return {
                'coverage_ratio': min(coverage_ratio, 1.0),
                'gaps': gaps,
                'total_days': total_days,
                'actual_days': actual_data_days
            }
            
        except Exception as e:
            logging.error(f"日期連續性檢查失敗: {e}")
            return {'coverage_ratio': 0.0, 'gaps': [], 'total_days': 0}
    
    def _calculate_quality_score(self, validation_result, data_count):
        """計算數據品質分數 (0-100)"""
        score = 100.0
        
        # 錯誤扣分
        score -= len(validation_result['errors']) * 20
        
        # 警告扣分
        score -= len(validation_result['warnings']) * 5
        
        # 數據覆蓋率加分
        if 'date_continuity' in validation_result['statistics']:
            coverage = validation_result['statistics']['date_continuity']['coverage_ratio']
            score *= coverage
        
        # 數據量加分
        if data_count >= 100:
            score += 5
        elif data_count >= 50:
            score += 2
        
        return max(0.0, min(100.0, score))

def smart_cache_manager():
    """智能快取管理系統"""
    
    cache_config = {
        'historical_data': {
            'ttl': 86400,  # 24小時
            'max_size': 100,  # 最多100個快取項目
            'strategy': 'LRU'  # 最近最少使用
        },
        'simulation_data': {
            'ttl': 3600,   # 1小時
            'max_size': 50,
            'strategy': 'TTL'  # 基於過期時間
        },
        'api_test_results': {
            'ttl': 300,    # 5分鐘
            'max_size': 20,
            'strategy': 'TTL'
        }
    }
    
    @st.cache_data(ttl=cache_config['historical_data']['ttl'])
    def cached_historical_data(service, start_date, end_date, params_hash):
        """歷史數據快取"""
        return fetch_historical_data(service, start_date, end_date, params_hash)
    
    @st.cache_data(ttl=cache_config['api_test_results']['ttl'])
    def cached_api_connectivity(service, api_key_hash):
        """API連通性測試結果快取"""
        return test_api_connectivity(service, api_key_hash)
    
    def get_cache_key(service, start_date, end_date, **kwargs):
        """生成統一的快取鍵"""
        import hashlib
        
        key_parts = [
            service,
            start_date.strftime('%Y-%m-%d') if hasattr(start_date, 'strftime') else str(start_date),
            end_date.strftime('%Y-%m-%d') if hasattr(end_date, 'strftime') else str(end_date)
        ]
        
        # 添加額外參數
        for k, v in sorted(kwargs.items()):
            key_parts.append(f"{k}:{v}")
        
        cache_key = "_".join(key_parts)
        
        # 如果鍵太長，使用MD5雜湊
        if len(cache_key) > 200:
            cache_key = hashlib.md5(cache_key.encode()).hexdigest()
        
        return cache_key
    
    return {
        'cached_historical_data': cached_historical_data,
        'cached_api_connectivity': cached_api_connectivity,
        'get_cache_key': get_cache_key
    }
```

### 1.3 數據模型與結構定義

#### 1.3.1 統一數據模型規範

**原始市場數據模型**
```python
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List, Dict, Any

@dataclass
class MarketDataPoint:
    """單一市場數據點"""
    date: str                    # YYYY-MM-DD格式
    spy_price: float            # SPY價格 (USD)
    bond_yield: Optional[float] # 債券殖利率 (%)
    bond_price: Optional[float] # 債券價格 (USD)
    data_source: str            # 數據來源 ('tiingo', 'fred', 'simulation', 'backup')
    
    def __post_init__(self):
        """數據驗證"""
        # 價格驗證
        if self.spy_price <= 0:
            raise ValueError(f"無效的SPY價格: {self.spy_price}")
        
        # 日期格式驗證
        try:
            datetime.strptime(self.date, '%Y-%m-%d')
        except ValueError:
            raise ValueError(f"無效的日期格式: {self.date}")
        
        # 債券數據驗證
        if self.bond_yield is not None:
            if not (-5.0 <= self.bond_yield <= 25.0):
                raise ValueError(f"債券殖利率超出合理範圍: {self.bond_yield}%")
        
        if self.bond_price is not None:
            if not (50.0 <= self.bond_price <= 200.0):
                raise ValueError(f"債券價格超出合理範圍: {self.bond_price}")

@dataclass 
class AggregatedPeriodData:
    """聚合期間數據"""
    period: int                 # 期數
    start_date: str            # 期初日期
    end_date: str              # 期末日期
    spy_price_start: float     # 期初SPY價格
    spy_price_end: float       # 期末SPY價格
    bond_yield_start: Optional[float]  # 期初債券殖利率
    bond_yield_end: Optional[float]    # 期末債券殖利率
    bond_price_start: Optional[float]  # 期初債券價格
    bond_price_end: Optional[float]    # 期末債券價格
    trading_days: int          # 期間交易日數
    period_return: float       # 期間報酬率
    data_quality_score: float  # 數據品質分數
    
    def calculate_period_return(self) -> float:
        """計算期間報酬率"""
        if self.spy_price_start <= 0:
            return 0.0
        return (self.spy_price_end / self.spy_price_start) - 1.0

@dataclass
class StrategyResult:
    """策略計算結果"""
    period: int
    date_origin: str
    spy_price_origin: float
    bond_yield_origin: Optional[float]
    bond_price_origin: Optional[float]
    
    # 股票部位
    stock_investment: float      # 當期股票投資金額
    cum_stock_investment: float  # 累計股票投資金額
    stock_units_purchased: float # 當期購買股票單位數
    cum_stock_units: float       # 累計股票單位數
    stock_value: float           # 當期股票市值
    
    # 債券部位
    bond_investment: float       # 當期債券投資金額
    cum_bond_investment: float   # 累計債券投資金額
    bond_units_purchased: float  # 當期購買債券單位數
    cum_bond_units: float        # 累計債券單位數
    bond_value: float            # 當期債券市值
    
    # 投資組合總覽
    total_investment: float      # 當期總投資金額
    cum_total_investment: float  # 累計總投資金額
    total_value: float           # 當期總市值
    unrealized_gain_loss: float  # 未實現損益
    unrealized_return: float     # 未實現報酬率
    
    # 策略特有參數
    strategy_specific: Dict[str, Any]  # 策略特定參數 (VA目標值、DCA固定金額等)
    
    def calculate_total_value(self) -> float:
        """計算總市值"""
        return self.stock_value + self.bond_value
    
    def calculate_unrealized_return(self) -> float:
        """計算未實現報酬率"""
        if self.cum_total_investment <= 0:
            return 0.0
        return (self.total_value / self.cum_total_investment) - 1.0

class DataModelFactory:
    """數據模型工廠"""
    
    @staticmethod
    def create_market_data_from_api(api_response: Dict, source: str) -> List[MarketDataPoint]:
        """從API回應創建市場數據"""
        data_points = []
        
        if source == 'tiingo':
            for item in api_response:
                # 處理Tiingo格式
                date_str = item['date'][:10]  # 取YYYY-MM-DD部分
                
                data_point = MarketDataPoint(
                    date=date_str,
                    spy_price=float(item['adjClose']),
                    bond_yield=None,
                    bond_price=None,
                    data_source='tiingo'
                )
                data_points.append(data_point)
                
        elif source == 'fred':
            for obs in api_response.get('observations', []):
                if obs['value'] != '.':  # FRED用'.'表示缺失值
                    data_point = MarketDataPoint(
                        date=obs['date'],
                        spy_price=0.0,  # FRED不提供股票價格
                        bond_yield=float(obs['value']),
                        bond_price=100.0 / (1 + float(obs['value'])/100),  # 簡化債券定價
                        data_source='fred'
                    )
                    data_points.append(data_point)
        
        return data_points
    
    @staticmethod
    def aggregate_to_periods(
        market_data: List[MarketDataPoint], 
        frequency: str, 
        investment_years: int
    ) -> List[AggregatedPeriodData]:
        """將日線數據聚合為投資期間數據"""
        
        from datetime import datetime, timedelta
        import pandas as pd
        
        # 轉換為DataFrame便於處理
        df = pd.DataFrame([
            {
                'date': datetime.strptime(dp.date, '%Y-%m-%d'),
                'spy_price': dp.spy_price,
                'bond_yield': dp.bond_yield,
                'bond_price': dp.bond_price,
                'data_source': dp.data_source
            }
            for dp in market_data
        ])
        
        df = df.sort_values('date').reset_index(drop=True)
        
        # 根據頻率設定期間
        freq_mapping = {
            'monthly': 'M',
            'quarterly': 'Q', 
            'semi-annually': '6M',
            'annually': 'A'
        }
        
        periods_per_year = {
            'monthly': 12,
            'quarterly': 4,
            'semi-annually': 2,
            'annually': 1
        }
        
        total_periods = investment_years * periods_per_year[frequency]
        
        # 按期間聚合數據
        aggregated_data = []
        
        for period in range(1, total_periods + 1):
            # 計算期間起止日期 (這裡簡化處理，實際應用時應使用更精確的方法)
            period_start_idx = (period - 1) * len(df) // total_periods
            period_end_idx = period * len(df) // total_periods - 1
            
            if period_end_idx >= len(df):
                period_end_idx = len(df) - 1
            
            period_data = df.iloc[period_start_idx:period_end_idx + 1]
            
            if len(period_data) > 0:
                start_row = period_data.iloc[0]
                end_row = period_data.iloc[-1]
                
                aggregated_period = AggregatedPeriodData(
                    period=period,
                    start_date=start_row['date'].strftime('%Y-%m-%d'),
                    end_date=end_row['date'].strftime('%Y-%m-%d'),
                    spy_price_start=start_row['spy_price'],
                    spy_price_end=end_row['spy_price'],
                    bond_yield_start=start_row['bond_yield'],
                    bond_yield_end=end_row['bond_yield'],
                    bond_price_start=start_row['bond_price'],
                    bond_price_end=end_row['bond_price'],
                    trading_days=len(period_data),
                    period_return=0.0,  # 將在後面計算
                    data_quality_score=95.0  # 簡化處理
                )
                
                # 計算期間報酬率
                aggregated_period.period_return = aggregated_period.calculate_period_return()
                
                aggregated_data.append(aggregated_period)
        
        return aggregated_data
```

#### 1.3.2 統一數據流程圖

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   用戶輸入參數    │    │   參數驗證檢查    │    │   快取檢查機制    │
│  (日期/頻率/情境) │───▶│  (範圍/格式/邏輯) │───▶│  (鍵值/TTL/版本)  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                        │
                       ┌─────────────────────────────────┘
                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   數據源選擇     │    │   API安全驗證    │    │   多層級容錯     │
│ (歷史數據/模擬)   │───▶│ (金鑰/連通性/限制) │───▶│ (重試/備援/降級)  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                        │
                       ┌─────────────────────────────────┘
                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   原始數據獲取    │    │   數據品質驗證    │    │   數據預處理     │
│ (Tiingo/FRED/模擬)│───▶│ (範圍/連續/異常)  │───▶│ (清洗/格式/聚合)  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                        │
                       ┌─────────────────────────────────┘
                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   期間數據聚合    │    │   策略計算引擎    │    │   結果驗證       │
│ (頻率/交易日/價格) │───▶│ (VA算法/DCA算法)  │───▶│ (邏輯/一致/合理)  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                        │
                       ┌─────────────────────────────────┘
                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   圖表數據準備    │    │   UI界面更新     │    │   快取結果儲存    │
│ (時間序列/統計)   │───▶│ (表格/圖表/下載)  │───▶│ (TTL/版本/清理)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

---

## 2. 表格與圖表架構與公式模組

本章節詳細定義投資策略比較系統的核心計算邏輯、數據處理規範與圖表生成標準，確保計算準確性與視覺效果的一致性。

### 2.1 核心計算公式模組

#### 2.1.1 參數頻率轉換模組

**基礎轉換係數定義**
```python
# 頻率轉換映射表
frequency_mapping = {
    "Monthly": {"periods_per_year": 12, "label": "每月"},
    "Quarterly": {"periods_per_year": 4, "label": "每季"},
    "Semi-annually": {"periods_per_year": 2, "label": "每半年"},
    "Annually": {"periods_per_year": 1, "label": "每年"}
}
```

**核心轉換公式**
```python
def convert_annual_to_period_parameters(annual_investment, annual_growth_rate, 
                                      annual_inflation_rate, investment_years, frequency):
    """
    年度參數轉換為期間參數
    
    輸入參數:
    - annual_investment: 年度投入金額 ($)
    - annual_growth_rate: 年化成長率 (%)
    - annual_inflation_rate: 年化通膨率 (%)
    - investment_years: 投資年數
    - frequency: 投資頻率 (Monthly/Quarterly/Semi-annually/Annually)
    
    輸出參數:
    - C_period: 每期基準投入金額
    - r_period: 每期成長率
    - g_period: 每期通膨率
    - total_periods: 總投資期數
    """
    periods_per_year = frequency_mapping[frequency]["periods_per_year"]
    
    # 每期基準投入金額
    C_period = annual_investment / periods_per_year
    
    # 複利轉換：年化率轉每期率
    r_period = (1 + annual_growth_rate / 100) ** (1/periods_per_year) - 1
    g_period = (1 + annual_inflation_rate / 100) ** (1/periods_per_year) - 1
    
    # 總投資期數
    total_periods = investment_years * periods_per_year
    
    return {
        "C_period": C_period,
        "r_period": r_period, 
        "g_period": g_period,
        "total_periods": total_periods,
        "periods_per_year": periods_per_year
    }
```

**邊界條件處理**
```python
def validate_conversion_parameters(annual_growth_rate, annual_inflation_rate):
    """參數轉換前的驗證邏輯"""
    # 確保成長率與通膨率在合理範圍
    if annual_growth_rate < -20 or annual_growth_rate > 50:
        raise ValueError("年化成長率必須在 -20% 到 50% 之間")
    
    if annual_inflation_rate < -5 or annual_inflation_rate > 15:
        raise ValueError("年化通膨率必須在 -5% 到 15% 之間")
    
    # 檢查極限情況：成長率與通膨率相等的處理
    if abs(annual_growth_rate - annual_inflation_rate) < 1e-6:
        return True  # 需要使用極限公式
    
    return False
```

#### 2.1.2 Value Averaging (VA) 策略公式模組

**VA理論終值計算核心**
```python
def calculate_va_target_value(C0, C_period, r_period, g_period, t):
    """
    計算VA策略第t期目標價值
    
    參數說明:
    - C0: 期初投入金額 (Initial Investment)
    - C_period: 基準每期投入金額
    - r_period: 每期資產成長率
    - g_period: 每期通膨率
    - t: 期數 (1-based)
    """
    
    # 檢查是否為極限情況
    if abs(r_period - g_period) < 1e-10:
        # 當 r_period = g_period 時的極限公式
        term1 = C0 * ((1 + r_period) ** t)
        term2 = C_period * t * ((1 + r_period) ** (t - 1))
        Vt = term1 + term2
    else:
        # 一般情況的VA公式
        term1 = C0 * ((1 + r_period) ** t)
        growth_factor = (1 + r_period) ** t
        inflation_factor = (1 + g_period) ** t
        term2 = C_period * (1 / (r_period - g_period)) * (growth_factor - inflation_factor)
        Vt = term1 + term2
    
    return Vt
```

**VA策略執行邏輯**
```python
def execute_va_strategy(target_value, current_value, stock_ratio, bond_ratio, 
                       spy_price, bond_price, strategy_type):
    """
    執行VA策略的買賣邏輯 - 每期期末依資產目標與資產現值進行買賣
    
    參數:
    - target_value: 目標資產價值Vt (使用C_period計算得出的理論目標)
    - current_value: 當期期末累積單位數所對應的資產價值
    - stock_ratio, bond_ratio: 股債配置比例
    - spy_price, bond_price: 當期期末資產價格
    - strategy_type: "Rebalance" 或 "No Sell"
    
    返回:
    - investment_gap: 投資缺口
    - stock_trade_units: 股票交易單位數 (正為買入，負為賣出)
    - bond_trade_units: 債券交易單位數
    - actual_investment: 實際投入金額 (負值表示賣出)
    
    說明:
    - VA策略第1期初投入C0，接著第1期期末依Vt公式計算第1期的期末資產價值後視投資缺口調整
    - C_period僅為計算目標價值Vt的參數，不是實際投入金額
    - 資產價值計算於各期末進行（累積單位數*期末股或債價值）
    """
    
    investment_gap = target_value - current_value
    
    if investment_gap > 0:
        # 需要買入
        stock_investment = investment_gap * stock_ratio
        bond_investment = investment_gap * bond_ratio
        
        stock_trade_units = stock_investment / spy_price
        bond_trade_units = bond_investment / bond_price
        
        actual_investment = investment_gap
        
    elif investment_gap < 0 and strategy_type == "Rebalance":
        # Rebalance策略：需要賣出
        stock_divestment = abs(investment_gap) * stock_ratio
        bond_divestment = abs(investment_gap) * bond_ratio
        
        stock_trade_units = -stock_divestment / spy_price  # 負值表示賣出
        bond_trade_units = -bond_divestment / bond_price
        
        actual_investment = investment_gap  # 負值
        
    else:
        # No Sell策略且investment_gap <= 0：不執行任何操作
        stock_trade_units = 0
        bond_trade_units = 0
        actual_investment = 0
    
    return {
        "investment_gap": investment_gap,
        "stock_trade_units": stock_trade_units,
        "bond_trade_units": bond_trade_units,
        "actual_investment": actual_investment
    }
```

#### 2.1.3 Dollar Cost Averaging (DCA) 策略公式模組

**DCA每期投入金額計算**
```python
def calculate_dca_investment(C_period, g_period, t):
    """
    計算DCA策略第t期投入金額(含通膨調整) - 僅適用於第1期及以後的C_period投入
    
    參數:
    - C_period: 基準每期投入金額
    - g_period: 每期通膨率  
    - t: 期數 (1-based)
    """
    # 通膨調整後的投入金額
    adjusted_investment = C_period * ((1 + g_period) ** (t - 1))
    return adjusted_investment
```

**DCA累積投入金額計算**
```python
def calculate_dca_cumulative_investment(C0, C_period, g_period, t):
    """
    計算DCA策略截至第t期的累積投入金額
    
    參數:
    - C0: 期初投入金額（僅第1期投入）
    - C_period: 基準每期投入金額（每期初都投入，含第1期）
    - g_period: 每期通膨率
    - t: 期數 (1-based)
    
    說明:
    - C0僅在第1期投入
    - C_period每期初都投入（含第1期），並按通膨調整
    - 累積投入 = C0 + Σ(C_period * (1+g)^(i-1)) for i=1 to t
    """
    if abs(g_period) < 1e-10:
        # 當通膨率為0時
        cumulative_regular = C_period * t
    else:
        # 等比數列求和公式
        cumulative_regular = C_period * (((1 + g_period) ** t - 1) / g_period)
    
    total_cumulative = C0 + cumulative_regular
    return total_cumulative
```

**DCA策略執行邏輯**
```python
def execute_dca_strategy(fixed_investment, stock_ratio, bond_ratio, 
                        spy_price, bond_price):
    """
    執行DCA策略的投資邏輯 - 每期期初固定投入，無賣出操作
    
    參數:
    - fixed_investment: 當期固定投入金額
      - 第1期：C0 + calculate_dca_investment(C_period, g_period, 1)
      - 第t期：calculate_dca_investment(C_period, g_period, t)
    - stock_ratio, bond_ratio: 股債配置比例
    - spy_price, bond_price: 當期期初資產價格
    
    返回:
    - stock_trade_units: 股票購買單位數
    - bond_trade_units: 債券購買單位數
    
    說明:
    - DCA策略：每期期初固定投入，C0僅第1期投入，C_period於各期初投入，無賣出操作
    - 所有投資均在期初以期初價格執行
    - 沒有賣出操作，僅於各期末計算DCA的資產價值（累積單位數*期末股或債價值）
    """
    
    stock_investment = fixed_investment * stock_ratio
    bond_investment = fixed_investment * bond_ratio
    
    stock_trade_units = stock_investment / spy_price
    bond_trade_units = bond_investment / bond_price
    
    return {
        "stock_trade_units": stock_trade_units,
        "bond_trade_units": bond_trade_units,
        "stock_investment": stock_investment,
        "bond_investment": bond_investment
    }
```

#### 2.1.3.1 投資時機與價格使用規範

**VA策略投資時機規定**

1. **第1期投資時機**：
   - **投資內容**：投入期初金額C0
   - **投資時點**：VA策略第1期初投入C0，接著第1期期末依Vt公式計算第1期的期末資產價值後視投資缺口調整
   - **價格使用**：期初價格（SPY_Price_Origin, Bond_Price_Origin），期末價格（SPY_Price_End, Bond_Price_End）
   - **計算邏輯**：期末計算投資缺口
     ```python
    c0_investment = C0  # 期初投入（僅第1期）
    va_target = calculate_va_target_value(C0, C_period, r_period, g_period, 
    period)
    current_asset_value = 期末累積單位數 * 期末價格
    investment_gap = va_target - current_asset_value
    # 期末依investment_gap進行買入/賣出
     ```

2. **第2期及以後投資時機**：
   - **投資內容**：每期僅於期末依Vt公式計算目標資產價值，視投資缺口調整
   - **投資時點**：期末
   - **C_period**：僅作為Vt計算參數，不直接投入

3. **C_period參數用途說明**：
   - **功能定位**：僅用於計算VA目標價值Vt的理論參數
   - **實際投入**：C_period本身不作為實際投入金額
   - **投入計算**：實際投入/賣出金額 = investment_gap
   - **資產價值計算**：於各期末計算VA的資產價值（累積單位數*股或債價值）

**DCA策略投資時機規定**

1. **第1期投資時機**：
   - **投資內容**：C0 + 第1期調整後的C_period
   - **投資時點**：期初執行
   - **價格使用**：期初價格（SPY_Price_Origin, Bond_Price_Origin）
   - **計算邏輯**：
     ```python
     c0_investment = C0  # 期初投入（僅第1期）
     period_investment = calculate_dca_investment(C_period, g_period, 1)  # 第1期調整後投入
     total_investment = c0_investment + period_investment
     ```

2. **第2期及以後投資時機**：
   - **投資內容**：調整後的C_period（C0僅第1期投入）
   - **投資時點**：期初執行
   - **價格使用**：期初價格（SPY_Price_Origin, Bond_Price_Origin）
   - **計算邏輯**：
     ```python
     investment_amount = calculate_dca_investment(C_period, g_period, period)
     ```

3. **賣出操作規定**：
   - **操作限制**：DCA策略不允許任何賣出操作
   - **實施原則**：僅執行買入交易，不進行資產減持
   - **資產價值計算**：僅於各期末計算DCA的資產價值（累積單位數*股或債價值）

4. **資金投入原則總結**：
   - **C0投入時機**：僅在第1期期初投入
   - **C_period投入時機**：每期期初投入（含第1期）
   - **通膨調整**：C_period按期數進行通膨調整
   - **無賣出限制**：DCA策略永不賣出，純粹定期買入


#### 2.1.4 股債混合組合計算模組

**資產配置計算**
```python
def calculate_portfolio_allocation(stock_ratio, bond_ratio):
    """
    驗證並標準化股債配置比例
    
    參數:
    - stock_ratio: 股票比例 (0-100)
    - bond_ratio: 債券比例 (自動計算為 100-stock_ratio)
    
    返回:
    - normalized_stock_ratio: 標準化股票比例 (0-1)
    - normalized_bond_ratio: 標準化債券比例 (0-1)
    """
    # 驗證股票比例
    if stock_ratio < 0 or stock_ratio > 100:
        raise ValueError("股票比例必須在 0% 到 100% 之間")
    
    # 自動計算債券比例
    bond_ratio = 100 - stock_ratio
    
    # 標準化為 0-1 範圍
    normalized_stock_ratio = stock_ratio / 100
    normalized_bond_ratio = bond_ratio / 100
    
    return normalized_stock_ratio, normalized_bond_ratio
```

**債券價格計算模組**
```python
def calculate_bond_price(yield_rate, face_value=100, time_to_maturity=1):
    """
    根據殖利率計算債券價格
    
    參數:
    - yield_rate: 債券殖利率 (%)
    - face_value: 債券面值 (預設100)
    - time_to_maturity: 到期時間 (年，預設1年)
    
    返回:
    - bond_price: 債券價格
    """
    # 簡化債券定價模型（零息債券）
    bond_price = face_value / ((1 + yield_rate / 100) ** time_to_maturity)
    return bond_price
```

#### 2.1.5 績效指標計算模組

**時間加權報酬率計算** (主要投資報酬率指標)
```python
def calculate_time_weighted_return(period_returns: List[float], periods_per_year: int) -> float:
    """
    計算時間加權報酬率 (Time-Weighted Return, TWR)
    
    解決VA Rebalance策略中累積投入<0時投報率計算問題的專業方案
    時間加權報酬率不受現金流進出影響，反映真實的投資策略績效
    
    參數:
    - period_returns: 各期報酬率列表 (百分比形式)
    - periods_per_year: 每年期數
    
    返回:
    - annualized_twr: 年化時間加權報酬率 (%)
    
    財務金融理論基礎:
    TWR = [(1+R1) × (1+R2) × ... × (1+Rn)]^(1/年數) - 1
    此方法是投資組合績效評估的國際標準，消除了現金流時機的影響
    """
    if not period_returns or len(period_returns) == 0:
        return 0.0
    
    if periods_per_year <= 0:
        raise ValueError("每年期數必須大於0")
    
    # 過濾有效的報酬率數據（移除NaN和第一期的0值）
    valid_returns = [r for r in period_returns if pd.notna(r) and r != 0]
    
    if len(valid_returns) == 0:
        return 0.0
    
    # 將百分比轉為小數形式
    returns_decimal = [r / 100 for r in valid_returns]
    
    # 複合計算：將各期報酬率相乘
    compound_return = 1.0
    for r in returns_decimal:
        compound_return *= (1 + r)
    
    # 計算投資年數
    total_periods = len(returns_decimal)
    years = total_periods / periods_per_year
    
    if years > 0 and compound_return > 0:
        # 年化處理
        annualized_twr = (compound_return ** (1 / years)) - 1
        return annualized_twr * 100
    
    return 0.0


def calculate_enhanced_annualized_return(final_value: float, total_investment: float, 
                                       investment_years: float, period_returns: List[float] = None,
                                       periods_per_year: int = 4) -> float:
    """
    增強的年化報酬率計算（智能選擇計算方法）
    
    根據累積投入情況自動選擇最適當的計算方法：
    - 累積投入>0：使用傳統CAGR
    - 累積投入≤0：使用時間加權報酬率作為主要指標
    
    參數:
    - final_value: 期末總資產價值
    - total_investment: 累計總投入金額 (可能為負)
    - investment_years: 投資年數
    - period_returns: 各期報酬率列表 (可選)
    - periods_per_year: 每年期數
    
    返回:
    - recommended_return: 推薦的年化報酬率 (%)
    """
    if final_value < 0:
        raise ValueError("資產價值必須非負")
    
    if investment_years <= 0:
        raise ValueError("投資年數必須大於0")
    
    try:
        # 情況1：累積投入>0，使用傳統CAGR
        if total_investment > 0:
            return ((final_value / total_investment) ** (1 / investment_years) - 1) * 100
        
        # 情況2：累積投入≤0，使用時間加權報酬率
        elif period_returns and len(period_returns) > 0:
            twr = calculate_time_weighted_return(period_returns, periods_per_year)
            logger.info(f"累積投入≤0，使用時間加權報酬率: {twr:.2f}%")
            return twr
        
        # 情況3：無有效數據，返回0
        else:
            logger.warning("無足夠數據計算年化報酬率，返回0")
            return 0.0
            
    except Exception as e:
        logger.error(f"增強年化報酬率計算失敗: {e}")
        return 0.0


def calculate_annualized_return(final_value, total_investment, investment_years):
    """
    傳統年化報酬率計算（向後兼容）
    
    注意：此函數保留作為向後兼容，新程式碼建議使用 calculate_enhanced_annualized_return
    
    參數:
    - final_value: 期末總資產價值
    - total_investment: 累計總投入金額
    - investment_years: 投資年數
    
    返回:
    - annualized_return: 年化報酬率 (%)
    """
    if total_investment <= 0 or investment_years <= 0:
        return 0
    
    # 年化報酬率公式
    annualized_return = ((final_value / total_investment) ** (1 / investment_years)) - 1
    return annualized_return * 100
```

**內部報酬率 (IRR) 計算**
```python
def calculate_irr(cash_flows):
    """
    計算內部報酬率
    
    參數:
    - cash_flows: 現金流序列 [期初投入(負), 各期投入(負), ..., 期末回收(正)]
    
    返回:
    - irr: 內部報酬率 (%)
    """
    import numpy as np
    from scipy.optimize import fsolve
    
    def npv(rate, cash_flows):
        """計算淨現值"""
        return sum(cf / (1 + rate) ** i for i, cf in enumerate(cash_flows))
    
    try:
        # 使用數值方法求解 NPV = 0 的利率
        irr_rate = fsolve(npv, 0.1, args=(cash_flows,))[0]
        return irr_rate * 100
    except:
        return None  # 無法收斂時返回None
```

**現金流序列建構**
```python
def build_va_cash_flows(C0, investment_history, final_value, final_investment):
    """
    建構VA策略的現金流序列用於IRR計算
    
    參數:
    - C0: 期初投入金額
    - investment_history: 各期實際投入金額列表 (包含負值賣出)
    - final_value: 期末總資產價值
    - final_investment: 最後一期投入金額
    
    返回:
    - cash_flows: 現金流序列
    """
    cash_flows = [-C0]  # 期初投入為負值
    
    # 中間各期投入
    for investment in investment_history[:-1]:
        cash_flows.append(-investment)  # 投入為負值，賣出為正值
    
    # 最後一期：期末總價值減去最後投入
    final_cash_flow = final_value - final_investment
    cash_flows.append(final_cash_flow)
    
    return cash_flows

def build_dca_cash_flows(C0, fixed_investment, periods, final_value):
    """
    建構DCA策略的現金流序列用於IRR計算
    
    參數:
    - C0: 期初投入金額
    - fixed_investment: 固定投入金額(已含通膨調整)
    - periods: 總期數
    - final_value: 期末總資產價值
    
    返回:
    - cash_flows: 現金流序列
    """
    cash_flows = [-C0]  # 期初投入
    
    # 中間各期固定投入
    for i in range(1, periods):
        cash_flows.append(-fixed_investment)
    
    # 最後一期：期末總價值減去最後投入
    final_cash_flow = final_value - fixed_investment
    cash_flows.append(final_cash_flow)
    
    return cash_flows
```

**波動率與夏普比率計算**
```python
def calculate_volatility_and_sharpe(period_returns, periods_per_year, risk_free_rate=0.02):
    """
    計算年化波動率與夏普比率
    
    參數:
    - period_returns: 各期報酬率列表
    - periods_per_year: 每年期數
    - risk_free_rate: 無風險利率 (年化，預設2%)
    
    返回:
    - annualized_volatility: 年化波動率 (%)
    - sharpe_ratio: 夏普比率
    """
    import numpy as np
    
    if len(period_returns) < 2:
        return 0, 0
    
    # 計算期間報酬率標準差
    period_std = np.std(period_returns, ddof=1)
    
    # 年化波動率
    annualized_volatility = period_std * np.sqrt(periods_per_year) * 100
    
    # 平均年化報酬率
    avg_period_return = np.mean(period_returns)
    annualized_avg_return = ((1 + avg_period_return) ** periods_per_year) - 1
    
    # 夏普比率
    if annualized_volatility == 0:
        sharpe_ratio = 0
    else:
        sharpe_ratio = (annualized_avg_return - risk_free_rate) / (annualized_volatility / 100)
    
    return annualized_volatility, sharpe_ratio
```

**最大回撤計算**
```python
def calculate_max_drawdown(cumulative_values):
    """
    計算最大回撤
    
    參數:
    - cumulative_values: 累積資產價值序列
    
    返回:
    - max_drawdown: 最大回撤 (%)
    - drawdown_period: 回撤期間 (起始期-結束期)
    """
    import numpy as np
    
    if len(cumulative_values) < 2:
        return 0, (0, 0)
    
    values = np.array(cumulative_values)
    
    # 計算各期的歷史最高點
    running_max = np.maximum.accumulate(values)
    
    # 計算回撤 (當前值相對歷史最高點的下跌幅度)
    drawdown = (values - running_max) / running_max
    
    # 找出最大回撤
    max_drawdown_idx = np.argmin(drawdown)
    max_drawdown = drawdown[max_drawdown_idx] * 100  # 轉為百分比
    
    # 找出回撤期間的起始點
    peak_idx = np.argmax(running_max[:max_drawdown_idx + 1])
    
    return abs(max_drawdown), (peak_idx, max_drawdown_idx)
```

### 2.2 表格架構與數據處理模組

#### 2.2.1 VA策略完整數據結構定義

**VA策略輸出欄位規格**
```python
VA_COLUMN_SPECS = {
    # 期間與日期欄位
    "Period": {
        "type": "int", 
        "description": "期數（1,2,3,4,...）",
        "format": "整數",
        "validation": ">=1"
    },
    "Date_Origin": {
        "type": "date",
        "description": "當期起始日期", 
        "format": "YYYY-MM-DD",
        "validation": "valid_date"
    },
    "Date_End": {
        "type": "date",
        "description": "當期期末日期",
        "format": "YYYY-MM-DD", 
        "validation": "valid_date"
    },
    
    # 市場價格欄位
    "SPY_Price_Origin": {
        "type": "float",
        "description": "當期期初SPY調整後收盤價",
        "format": "2位小數",
        "validation": ">0"
    },
    "SPY_Price_End": {
        "type": "float", 
        "description": "當期期末SPY調整後收盤價",
        "format": "2位小數",
        "validation": ">0"
    },
    "Bond_Yield_Origin": {
        "type": "float",
        "description": "當期期初債券殖利率(%)",
        "format": "2位小數",
        "validation": "合理範圍"
    },
    "Bond_Yield_End": {
        "type": "float",
        "description": "當期期末債券殖利率(%)", 
        "format": "2位小數",
        "validation": "合理範圍"
    },
    "Bond_Price_Origin": {
        "type": "float",
        "description": "當期期初債券價格",
        "format": "2位小數", 
        "validation": ">0"
    },
    "Bond_Price_End": {
        "type": "float",
        "description": "當期期末債券價格",
        "format": "2位小數",
        "validation": ">0"
    },
    
    # VA策略特有欄位
    "Prev_Stock_Units": {
        "type": "float",
        "description": "前期累積股票單位數",
        "format": "4位小數",
        "validation": ">=0"
    },
    "Prev_Bond_Units": {
        "type": "float",
        "description": "前期累積債券單位數",
        "format": "4位小數",
        "validation": ">=0"
    },
    "Initial_Investment": {
        "type": "float", 
        "description": "期初投入金額",
        "format": "千分位符號",
        "validation": ">0"
    },
    "VA_Target": {
        "type": "float",
        "description": "VA公式計算的當期目標資產價值", 
        "format": "千分位符號",
        "validation": ">0"
    },
    "Current_Asset_Value": {
        "type": "float",
        "description": "當期調整前資產價值 = 當期期末股票價格×前期股票累積單位數 + 當期期末債券價格×前期債券累積單位數",
        "format": "千分位符號", 
        "validation": ">=0"
    },
    "Invested": {
        "type": "float",
        "description": "當期實際投入/賣出金額（須視再平衡機制調整）",
        "format": "千分位符號，負值顯示括號",
        "validation": "可為負值"
    },
    
    # 交易單位欄位
    "stock_trade_units": {
        "type": "float",
        "description": "當期股票買賣單位數",
        "format": "4位小數，負值顯示括號",
        "validation": "可為負值"
    },
    "bond_trade_units": {
        "type": "float", 
        "description": "當期債券買賣單位數",
        "format": "4位小數，負值顯示括號",
        "validation": "可為負值"
    },
    
    # 累積欄位
    "Cum_stock_units": {
        "type": "float",
        "description": "累積股票單位數",
        "format": "4位小數",
        "validation": ">=0"
    },
    "Cum_bond_units": {
        "type": "float",
        "description": "累積債券單位數", 
        "format": "4位小數",
        "validation": ">=0"
    },
    "Cum_Inv": {
        "type": "float",
        "description": "累計投入金額",
        "format": "千分位符號", 
        "validation": ">0"
    },
    "Cum_Value": {
        "type": "float",
        "description": "當期期末資產價值 = 當期期末股票價格×當期股票累積單位數 + 當期期末債券價格×當期債券累積單位數",
        "format": "千分位符號",
        "validation": ">0"
    },
    
    # 績效指標欄位
    "Period_Return": {
        "type": "float",
        "description": "當期報酬率(%)",
        "format": "2位小數%",
        "validation": "合理範圍"
    },
    "Cumulative_Return": {
        "type": "float", 
        "description": "累計報酬率(%)",
        "format": "2位小數%",
        "validation": "合理範圍"
    },
    "Annualized_Return": {
        "type": "float",
        "description": "截至當期的年化報酬率(%)",
        "format": "2位小數%",
        "validation": "合理範圍"
    }
}

# 完整VA欄位順序定義 - 期末相關欄位調整到VA_Target附近，反映VA策略期末執行特性
VA_COLUMNS_ORDER = [
    "Period", "Date_Origin", "SPY_Price_Origin", "Bond_Yield_Origin",
    "Bond_Price_Origin", "Prev_Stock_Units", "Prev_Bond_Units", "Initial_Investment",
    "Date_End", "VA_Target", "SPY_Price_End", "Bond_Yield_End", "Bond_Price_End",
    "Current_Asset_Value", "Invested", "Cum_Inv", "stock_trade_units", "bond_trade_units",
    "Cum_stock_units", "Cum_bond_units", "Cum_Value", "Period_Return", 
    "Cumulative_Return", "Annualized_Return"
]
```

#### 2.2.2 DCA策略完整數據結構定義

**DCA策略輸出欄位規格**
```python
DCA_COLUMN_SPECS = {
    # 繼承VA策略的基本欄位（保留Prev_Stock_Units和Prev_Bond_Units用於股債比例計算）
    **{k: v for k, v in VA_COLUMN_SPECS.items() 
       if k not in ["VA_Target", "Current_Asset_Value", "Invested"]},
    
    # DCA策略特有欄位
    "Fixed_Investment": {
        "type": "float",
        "description": "固定投入金額(含通膨調整)",
        "format": "千分位符號",
        "validation": ">0"
    }
}

# 完整DCA欄位順序
DCA_COLUMNS_ORDER = [
    "Period", "Date_Origin", "SPY_Price_Origin", "Bond_Yield_Origin",
    "Bond_Price_Origin", "Initial_Investment", "Prev_Stock_Units", "Prev_Bond_Units", 
    "Fixed_Investment", "stock_trade_units", "bond_trade_units", "Cum_stock_units", "Cum_bond_units",
    "Cum_Inv", "Date_End", "SPY_Price_End", "Bond_Yield_End", "Bond_Price_End",
    "Cum_Value", "Period_Return", "Cumulative_Return", "Annualized_Return"
]
```

#### 2.2.3 綜合比較摘要表格規格

**Summary策略比較輸出欄位**
```python
SUMMARY_COLUMN_SPECS = {
    # 與原始requirements.md保持一致的欄位規格
    "Strategy": {
        "type": "str",
        "description": "策略名稱(VA/DCA)", 
        "format": "字串",
        "validation": "預設選項"
    },
    "Final_Value": {
        "type": "float",
        "description": "期末總資產價值",
        "format": "千分位符號",
        "validation": ">0"
    },
    "Total_Investment": {
        "type": "float", 
        "description": "累計總投入金額",
        "format": "千分位符號",
        "validation": ">0"
    },
    "Total_Return": {
        "type": "float",
        "description": "總報酬率(%)",
        "format": "2位小數%",
        "validation": "合理範圍"
    },
    "Annualized_Return": {
        "type": "float",
        "description": "年化報酬率(%)",
        "format": "2位小數%", 
        "validation": "合理範圍"
    },
    "Volatility": {
        "type": "float",
        "description": "年化波動率(%)",
        "format": "2位小數%",
        "validation": ">0"
    },
    "Sharpe_Ratio": {
        "type": "float", 
        "description": "夏普比率",
        "format": "2位小數",
        "validation": "合理範圍"
    },
    "Max_Drawdown": {
        "type": "float",
        "description": "最大回撤(%)",
        "format": "2位小數%",
        "validation": ">=0"
    }
}

# 完整Summary欄位順序 - 與原始requirements.md一致
SUMMARY_COLUMNS_ORDER = [
    "Strategy", "Final_Value", "Total_Investment", "Total_Return", 
    "Annualized_Return", "Volatility", "Sharpe_Ratio", "Max_Drawdown"
]
```

#### 2.2.4 表格格式化與驗證模組

**數據格式化函數**
```python
# 統一百分比格式精度標準
PERCENTAGE_PRECISION_RULES = {
    "Period_Return": 2,        # 期間報酬率: 2位小數
    "Cumulative_Return": 2,    # 累計報酬率: 2位小數  
    "Annualized_Return": 2,    # 年化報酬率: 2位小數
    "Volatility": 2,           # 波動率: 2位小數
    "Sharpe_Ratio": 3,         # 夏普比率: 3位小數（需更高精度）
    "Total_Return": 2,         # 總報酬率: 2位小數
    "Max_Drawdown": 2          # 最大回撤: 2位小數
}

# 數值比較容差標準
NUMERIC_TOLERANCE = 1e-6

def format_currency(value, decimal_places=2):
    """格式化金額顯示（千分位符號）"""
    if pd.isna(value) or value is None:
        return "N/A"
    return f"${value:,.{decimal_places}f}"

def format_percentage(value, column_name=None, decimal_places=2):
    """格式化百分比顯示（支援欄位特定精度）"""
    if pd.isna(value) or value is None:
        return "N/A"
    
    # 使用欄位特定精度，若未定義則使用預設值
    if column_name and column_name in PERCENTAGE_PRECISION_RULES:
        decimal_places = PERCENTAGE_PRECISION_RULES[column_name]
    
    return f"{value:.{decimal_places}f}%"

def format_units(value, decimal_places=4):
    """格式化單位數顯示"""
    if pd.isna(value) or value is None:
        return "N/A"
    return f"{value:.{decimal_places}f}"

def format_negative_with_minus(value, format_func=format_currency):
    """負值統一使用負號顯示（避免Excel解析問題）"""
    if pd.isna(value) or value is None:
        return "N/A"
    if value < 0:
        return f"-{format_func(abs(value)).lstrip('$')}"
    return format_func(value)

def format_negative_parentheses(value, format_func=format_currency):
    """負值使用括號顯示（僅限表格顯示用）"""
    if pd.isna(value) or value is None:
        return "N/A"
    if value < 0:
        return f"({format_func(abs(value))})"
    return format_func(value)

def validate_numeric_consistency(streamlit_val, csv_val, tolerance=NUMERIC_TOLERANCE):
    """增強數值比較精度檢查"""
    if pd.isna(streamlit_val) and pd.isna(csv_val):
        return True
    if pd.isna(streamlit_val) or pd.isna(csv_val):
        return False
    
    # 對於很小的數值，使用相對誤差
    if abs(csv_val) > 1e-10:
        relative_error = abs(streamlit_val - csv_val) / abs(csv_val)
        return relative_error <= tolerance
    else:
        # 對於接近零的數值，使用絕對誤差
        return abs(streamlit_val - csv_val) <= tolerance
```

**表格生成與驗證模組（增強版）**
```python
def generate_formatted_table(data_df, strategy_type):
    """
    生成格式化的策略表格（增強版）
    
    參數:
    - data_df: 原始計算數據DataFrame
    - strategy_type: "VA", "DCA", 或 "SUMMARY"
    
    返回:
    - formatted_df: 格式化後的DataFrame
    """
    formatted_df = data_df.copy()
    
    # 根據策略類型選擇欄位規格和順序
    if strategy_type == "VA":
        column_specs = VA_COLUMN_SPECS
        columns_order = VA_COLUMNS_ORDER
    elif strategy_type == "DCA":
        column_specs = DCA_COLUMN_SPECS
        columns_order = DCA_COLUMNS_ORDER
    elif strategy_type == "SUMMARY":
        column_specs = SUMMARY_COLUMN_SPECS
        columns_order = SUMMARY_COLUMNS_ORDER
    else:
        raise ValueError(f"未支援的策略類型: {strategy_type}")
    
    # 確保欄位順序一致
    ordered_columns = [col for col in columns_order if col in formatted_df.columns]
    formatted_df = formatted_df[ordered_columns]
    
    # 應用統一格式化規則
    for column, spec in column_specs.items():
        if column in formatted_df.columns:
            if "千分位符號" in spec["format"]:
                if "負值顯示括號" in spec["format"]:
                    formatted_df[column] = formatted_df[column].apply(
                        lambda x: format_negative_parentheses(x, format_currency)
                    )
                else:
                    formatted_df[column] = formatted_df[column].apply(
                        lambda x: format_currency(x, decimal_places=2)
                    )
            elif "%" in spec["format"] or column in PERCENTAGE_PRECISION_RULES:
                # 應用統一百分比格式標準
                formatted_df[column] = formatted_df[column].apply(
                    lambda x: format_percentage(x, column_name=column)
                )
            elif "位小數" in spec["format"]:
                decimal_places = int(spec["format"].split("位")[0])
                formatted_df[column] = formatted_df[column].apply(
                    lambda x: format_units(x, decimal_places)
                )
            elif spec["type"] == "date":
                # 確保日期格式統一
                if formatted_df[column].dtype == 'datetime64[ns]':
                    formatted_df[column] = formatted_df[column].dt.strftime('%Y-%m-%d')
    
    return formatted_df

def validate_table_data(data_df, strategy_type):
    """
    驗證表格數據的完整性和正確性（增強版）
    
    參數:
    - data_df: 計算數據DataFrame
    - strategy_type: "VA", "DCA", 或 "SUMMARY"
    
    返回:
    - validation_result: 驗證結果字典
    """
    errors = []
    warnings = []
    
    # 選擇對應的欄位規格
    if strategy_type == "VA":
        required_columns = set(VA_COLUMN_SPECS.keys())
        column_specs = VA_COLUMN_SPECS
    elif strategy_type == "DCA":
        required_columns = set(DCA_COLUMN_SPECS.keys())
        column_specs = DCA_COLUMN_SPECS
    elif strategy_type == "SUMMARY":
        required_columns = set(SUMMARY_COLUMN_SPECS.keys())
        column_specs = SUMMARY_COLUMN_SPECS
    else:
        return {"is_valid": False, "errors": [f"未知策略類型: {strategy_type}"], "warnings": []}
    
    # 檢查必要欄位
    missing_columns = required_columns - set(data_df.columns)
    if missing_columns:
        errors.append(f"缺少必要欄位: {missing_columns}")
    
    # 檢查數據合理性
    for column in data_df.columns:
        if column in column_specs:
            spec = column_specs[column]
            
            # 檢查非空值
            null_count = data_df[column].isnull().sum()
            if null_count > 0:
                warnings.append(f"{column} 有 {null_count} 個空值")
            
            # 檢查數值範圍（增強版）
            if spec["type"] in ["float", "int"] and len(data_df[column].dropna()) > 0:
                numeric_values = data_df[column].dropna()
                
                if spec["validation"] == ">0":
                    negative_count = (numeric_values <= 0).sum()
                    if negative_count > 0:
                        errors.append(f"{column} 有 {negative_count} 個非正值")
                elif spec["validation"] == ">=0":
                    negative_count = (numeric_values < 0).sum()
                    if negative_count > 0:
                        errors.append(f"{column} 有 {negative_count} 個負值")
                elif spec["validation"] == "合理範圍":
                    # 檢查異常值（使用IQR方法）
                    Q1 = numeric_values.quantile(0.25)
                    Q3 = numeric_values.quantile(0.75)
                    IQR = Q3 - Q1
                    outlier_count = ((numeric_values < (Q1 - 1.5 * IQR)) | 
                                   (numeric_values > (Q3 + 1.5 * IQR))).sum()
                    if outlier_count > len(numeric_values) * 0.1:  # 超過10%為異常值
                        warnings.append(f"{column} 有 {outlier_count} 個潛在異常值")
    
    return {
        "is_valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "data_quality_score": max(0, 100 - len(errors) * 20 - len(warnings) * 5)
    }
```

#### 2.2.5 衍生欄位計算模組

**績效指標衍生計算**
```python
def calculate_derived_metrics(df, initial_investment, periods_per_year):
    """
    計算表格中的衍生欄位
    
    參數:
    - df: 基礎數據DataFrame
    - initial_investment: 期初投入金額
    - periods_per_year: 每年期數
    
    返回:
    - enhanced_df: 添加衍生欄位的DataFrame
    """
    enhanced_df = df.copy()
    
    # 計算期間報酬率
    enhanced_df["Period_Return"] = enhanced_df["Cum_Value"].pct_change() * 100
    enhanced_df.loc[0, "Period_Return"] = 0  # 報酬率設為0
    
    # 計算累計報酬率
    enhanced_df["Cumulative_Return"] = ((enhanced_df["Cum_Value"] / 
                                       enhanced_df["Cum_Inv"]) - 1) * 100
    
    # 計算年化報酬率 - 使用增強版本（自動處理累積投入≤0的情況）
    enhanced_df["Annualized_Return"] = 0.0
    
    for i in range(len(enhanced_df)):
        period = enhanced_df.loc[i, "Period"]
        cum_value = enhanced_df.loc[i, "Cum_Value"]
        cum_inv = enhanced_df.loc[i, "Cum_Inv"]
        
        if period > 0 and pd.notna(cum_value) and pd.notna(cum_inv):
            investment_years = (period + 1) / periods_per_year
            if investment_years > 0:
                # 獲取到目前為止的期間報酬率用於TWR計算
                period_returns = enhanced_df.loc[:i, "Period_Return"].dropna().tolist()
                
                # 使用增強年化報酬率計算（自動處理累積投入≤0的情況）
                ann_return = calculate_enhanced_annualized_return(
                    cum_value, cum_inv, investment_years, 
                    period_returns, periods_per_year
                )
                enhanced_df.loc[i, "Annualized_Return"] = ann_return
    
    return enhanced_df

def calculate_summary_metrics(va_rebalance_df, va_nosell_df, dca_df, 
                            initial_investment, periods_per_year):
    """
    計算三種策略的綜合比較指標
    
    參數:
    - va_rebalance_df, va_nosell_df, dca_df: 各策略完整數據
    - initial_investment: 期初投入金額
    - periods_per_year: 每年期數
    
    返回:
    - summary_df: 綜合比較摘要DataFrame
    """
    strategies = {
        "VA_Rebalance": va_rebalance_df,
        "VA_NoSell": va_nosell_df, 
        "DCA": dca_df
    }
    
    summary_data = []
    
    for strategy_name, strategy_df in strategies.items():
        if strategy_df is not None and len(strategy_df) > 0:
            final_row = strategy_df.iloc[-1]
            
            # 基本指標
            final_value = final_row["Cum_Value"]
            total_investment = final_row["Cum_Inv"]
            
            # 總報酬率計算 - 處理累積投入≤0的情況
            if total_investment > 0:
                total_return = ((final_value / total_investment) - 1) * 100
            else:
                # 累積投入≤0：使用最終期的累積報酬率或TWR
                if "Cumulative_Return" in final_row:
                    total_return = final_row["Cumulative_Return"]
                else:
                    period_returns = strategy_df["Period_Return"].dropna().tolist() if "Period_Return" in strategy_df.columns else []
                    if period_returns:
                        # 計算總複合報酬率（非年化）
                        compound_return = 1.0
                        for r in [r/100 for r in period_returns if r != 0]:
                            compound_return *= (1 + r)
                        total_return = (compound_return - 1) * 100
                    else:
                        total_return = 0
            
            # 年化報酬率 - 使用增強版本處理累積投入≤0的情況
            investment_years = len(strategy_df) / periods_per_year
            if investment_years > 0:
                # 獲取期間報酬率用於TWR計算
                period_returns = strategy_df["Period_Return"].dropna().tolist() if "Period_Return" in strategy_df.columns else []
                
                # 使用增強年化報酬率計算
                annualized_return = calculate_enhanced_annualized_return(
                    final_value, total_investment, investment_years,
                    period_returns, periods_per_year
                )
            else:
                annualized_return = 0
            
            # IRR計算
            cash_flows = build_cash_flows_for_strategy(strategy_df, strategy_name)
            irr = calculate_irr(cash_flows)
            
            # 風險指標
            period_returns = strategy_df["Period_Return"].dropna().tolist()
            volatility, sharpe_ratio = calculate_volatility_and_sharpe(
                [r/100 for r in period_returns], periods_per_year
            )
            
            # 最大回撤
            cumulative_values = strategy_df["Cum_Value"].tolist()
            max_drawdown, _ = calculate_max_drawdown(cumulative_values)
            
            summary_data.append({
                "Strategy": strategy_name,
                "Final_Value": final_value,
                "Total_Investment": total_investment,
                "Total_Return": total_return,
                "Annualized_Return": annualized_return,
                "IRR": irr if irr is not None else 0,
                "Volatility": volatility,
                "Sharpe_Ratio": sharpe_ratio,
                "Max_Drawdown": max_drawdown
            })
    
    return pd.DataFrame(summary_data)

def build_cash_flows_for_strategy(strategy_df, strategy_name):
    """根據策略類型建構現金流序列"""
    initial_investment = strategy_df.iloc[0]["Initial_Investment"]
    
    if strategy_name.startswith("VA"):
        # VA策略現金流
        investments = strategy_df["Invested"].tolist()
        final_value = strategy_df.iloc[-1]["Cum_Value"]
        return build_va_cash_flows(
            initial_investment, investments, final_value, investments[-1]
        )
    else:
        # DCA策略現金流
        fixed_investment = strategy_df.iloc[1]["Fixed_Investment"] if len(strategy_df) > 1 else 0
        periods = len(strategy_df) - 1  # 扣除期初
        final_value = strategy_df.iloc[-1]["Cum_Value"]
        return build_dca_cash_flows(
            initial_investment, fixed_investment, periods, final_value
        )
```

#### 2.2.6 時間加權報酬率計算模組
def calculate_time_weighted_return(period_returns: List[float], periods_per_year: int) -> float:
    """
    計算時間加權報酬率 (Time-Weighted Return, TWR)
    
    解決VA Rebalance策略中累積投入<0時投報率計算問題的專業方案
    時間加權報酬率不受現金流進出影響，反映真實的投資策略績效
    
    Args:
        period_returns: 各期報酬率列表 (百分比形式)
        periods_per_year: 每年期數
    
    Returns:
        float: 年化時間加權報酬率 (%)
    
    財務金融理論基礎:
    TWR = [(1+R1) × (1+R2) × ... × (1+Rn)]^(1/年數) - 1
    此方法是投資組合績效評估的國際標準，消除了現金流時機的影響
    """
    if not period_returns or len(period_returns) == 0:
        return 0.0
    
    if periods_per_year <= 0:
        raise ValueError("每年期數必須大於0")
    
    # 過濾有效的報酬率數據
    valid_returns = [r for r in period_returns if pd.notna(r)]
    
    if len(valid_returns) == 0:
        return 0.0
    
    # 將百分比轉為小數形式
    returns_decimal = [r / 100 for r in valid_returns]
    
    # 複合計算：將各期報酬率相乘
    compound_return = 1.0
    for r in returns_decimal:
        compound_return *= (1 + r)
    
    # 計算投資年數
    total_periods = len(returns_decimal)
    years = total_periods / periods_per_year
    
    if years > 0 and compound_return > 0:
        # 年化處理
        annualized_twr = (compound_return ** (1 / years)) - 1
        return annualized_twr * 100
    
    return 0.0

def calculate_va_enhanced_return(strategy_df: pd.DataFrame, periods_per_year: int) -> Dict[str, float]:
    """
    計算VA策略的增強投報率指標
    
    專門解決累積投入<0時的投報率計算問題
    提供多種財務金融專業指標：
    1. 時間加權報酬率 (TWR) - 主要指標
    2. 修正IRR - 基於完整現金流
    3. 幾何平均報酬率 - 複合成長率
    
    Args:
        strategy_df: 策略計算結果DataFrame
        periods_per_year: 每年期數
    
    Returns:
        Dict: 包含多種投報率指標的字典
    """
    if strategy_df is None or len(strategy_df) == 0:
        return {
            'time_weighted_return': 0.0,
            'modified_irr': 0.0,
            'geometric_mean_return': 0.0,
            'calculation_method': 'insufficient_data'
        }
    
    try:
        # 1. 時間加權報酬率 (主要指標)
        if "Period_Return" in strategy_df.columns:
            period_returns = strategy_df["Period_Return"].dropna().tolist()
            twr = calculate_time_weighted_return(period_returns, periods_per_year)
        else:
            twr = 0.0
        
        # 2. 修正IRR計算
        modified_irr = 0.0
        try:
            if "Invested" in strategy_df.columns and "Cum_Value" in strategy_df.columns:
                investments = strategy_df["Invested"].fillna(0).tolist()
                final_value = strategy_df.iloc[-1]["Cum_Value"]
                
                # 建構現金流：所有投入為負，最終價值為正
                cash_flows = [-inv for inv in investments]
                cash_flows.append(final_value)
                
                irr_result = calculate_irr(cash_flows)
                if irr_result is not None:
                    modified_irr = irr_result
        except Exception as e:
            logger.warning(f"修正IRR計算失敗: {e}")
        
        # 3. 幾何平均報酬率
        geometric_mean = twr  # 與TWR相同的概念
        
        # 4. 判斷主要使用的計算方法
        final_cum_inv = strategy_df.iloc[-1].get("Cum_Inv", 0) if len(strategy_df) > 0 else 0
        
        if final_cum_inv <= 0:
            # 累積投入≤0的情況，使用TWR作為主要指標
            calculation_method = 'time_weighted_return_preferred'
            primary_return = twr
        else:
            # 累積投入>0的情況，可使用傳統方法
            calculation_method = 'traditional_with_twr_validation'
            primary_return = twr
        
        return {
            'time_weighted_return': round(twr, 4),
            'modified_irr': round(modified_irr, 4),
            'geometric_mean_return': round(geometric_mean, 4),
            'primary_return': round(primary_return, 4),
            'calculation_method': calculation_method,
            'cum_investment_status': 'negative' if final_cum_inv <= 0 else 'positive'
        }
        
    except Exception as e:
        logger.error(f"VA增強投報率計算失敗: {e}")
        return {
            'time_weighted_return': 0.0,
            'modified_irr': 0.0,
            'geometric_mean_return': 0.0,
            'primary_return': 0.0,
            'calculation_method': 'calculation_error',
            'error_message': str(e)
        }

def calculate_enhanced_annualized_return(final_value: float, total_investment: float, 
                                       investment_years: float, period_returns: List[float] = None,
                                       periods_per_year: int = 4) -> Dict[str, float]:
    """
    增強的年化報酬率計算
    
    根據累積投入情況自動選擇最適當的計算方法：
    - 累積投入>0：使用傳統CAGR + TWR驗證
    - 累積投入≤0：使用時間加權報酬率作為主要指標
    
    Args:
        final_value: 期末總資產價值
        total_investment: 累計總投入金額 (可能為負)
        investment_years: 投資年數
        period_returns: 各期報酬率列表 (可選)
        periods_per_year: 每年期數
    
    Returns:
        Dict: 包含多種計算結果和推薦指標
    """
    results = {
        'traditional_cagr': 0.0,
        'time_weighted_return': 0.0,
        'recommended_return': 0.0,
        'calculation_status': '',
        'recommendation_reason': ''
    }
    
    try:
        # 1. 嘗試傳統CAGR計算
        if total_investment > 0 and investment_years > 0:
            traditional_cagr = calculate_annualized_return(final_value, total_investment, investment_years)
            results['traditional_cagr'] = traditional_cagr
        
        # 2. 計算時間加權報酬率
        if period_returns and len(period_returns) > 0:
            twr = calculate_time_weighted_return(period_returns, periods_per_year)
            results['time_weighted_return'] = twr
        
        # 3. 根據累積投入狀況決定推薦指標
        if total_investment <= 0:
            # 累積投入≤0：推薦TWR
            results['recommended_return'] = results['time_weighted_return']
            results['calculation_status'] = 'negative_cumulative_investment'
            results['recommendation_reason'] = '累積投入≤0，使用時間加權報酬率避免失真'
        elif abs(results['traditional_cagr'] - results['time_weighted_return']) > 2.0:
            # 兩種方法差異過大：推薦TWR
            results['recommended_return'] = results['time_weighted_return']
            results['calculation_status'] = 'method_divergence'
            results['recommendation_reason'] = 'CAGR與TWR差異過大，TWR更能反映投資績效'
        else:
            # 正常情況：使用CAGR，TWR作為驗證
            results['recommended_return'] = results['traditional_cagr']
            results['calculation_status'] = 'normal_calculation'
            results['recommendation_reason'] = '累積投入>0且方法一致，使用傳統CAGR'
        
        logger.info(f"增強投報率計算完成: 推薦={results['recommended_return']:.2f}%, 原因={results['recommendation_reason']}")
        
    except Exception as e:
        logger.error(f"增強年化報酬率計算失敗: {e}")
        results['calculation_status'] = 'calculation_error'
        results['recommendation_reason'] = f'計算錯誤: {str(e)}'
    
    return results




#### 2.3 圖表架構與視覺化模組

**主要圖表類型定義**
```python
CHART_TYPES = {
    "cumulative_value": {
        "title": "Cumulative Asset Value Comparison",
        "x_field": "Period",
        "y_field": "Cum_Value",
        "chart_type": "line",
        "color_scheme": "category10",
        "interactive": True
    },
    "cumulative_return": {
        "title": "Cumulative Return Comparison", 
        "x_field": "Period",
        "y_field": "Cumulative_Return",
        "chart_type": "line",
        "y_format": "%",
        "interactive": True
    },
    "period_return": {
        "title": "Period Return Analysis",
        "x_field": "Period", 
        "y_field": "Period_Return",
        "chart_type": "bar",
        "y_format": "%",
        "interactive": True
    },
    "investment_flow": {
        "title": "Investment Flow (VA Strategy)",
        "x_field": "Period",
        "y_field": "Invested", 
        "chart_type": "bar",
        "color_scheme": "redblue",
        "interactive": True
    },
    "drawdown_analysis": {
        "title": "Drawdown Analysis",
        "x_field": "Period",
        "y_field": "Drawdown",
        "chart_type": "area",
        "color": "red",
        "opacity": 0.6
    },
    "allocation_pie": {
        "title": "Asset Allocation",
        "chart_type": "pie", 
        "color_scheme": "set2",
        "interactive": True
    },
    "risk_return_scatter": {
        "title": "Risk vs Return Analysis",
        "x_field": "Volatility",
        "y_field": "Annualized_Return",
        "chart_type": "scatter",
        "size_field": "Final_Value"
    }
}
```

**圖表全域配置**
```python
CHART_GLOBAL_CONFIG = {
    "theme": "streamlit",
    "width": 700,
    "height": 400,
    "background": "white",
    "font_size": 12,
    "title_font_size": 16,
    "legend_position": "top-right",
    "grid": True,
    "toolbar": True,
    "language": "en",  # 強制使用英文標籤
    "responsive": True,
    "padding": {"top": 20, "bottom": 40, "left": 60, "right": 60}
}
```

#### 2.3.2 Altair圖表生成模組

**基礎圖表生成器**
```python
import altair as alt
import pandas as pd

def create_line_chart(data_df, x_field, y_field, color_field=None, title=""):
    """
    創建線圖
    
    參數:
    - data_df: 數據DataFrame
    - x_field, y_field: X軸和Y軸欄位名
    - color_field: 分組顏色欄位 
    - title: 圖表標題
    """
    chart = alt.Chart(data_df).mark_line(
        point=True,
        strokeWidth=2
    ).add_selection(
        alt.selection_interval(bind='scales')
    ).encode(
        x=alt.X(f"{x_field}:Q", title=x_field.replace("_", " ").title()),
        y=alt.Y(f"{y_field}:Q", title=y_field.replace("_", " ").title()),
        color=alt.Color(f"{color_field}:N") if color_field else alt.value("steelblue"),
        tooltip=[x_field, y_field, color_field] if color_field else [x_field, y_field]
    ).properties(
        title=title,
        width=CHART_GLOBAL_CONFIG["width"],
        height=CHART_GLOBAL_CONFIG["height"]
    )
    
    return chart

def create_bar_chart(data_df, x_field, y_field, color_field=None, title=""):
    """創建柱狀圖"""
    chart = alt.Chart(data_df).mark_bar().encode(
        x=alt.X(f"{x_field}:Q", title=x_field.replace("_", " ").title()),
        y=alt.Y(f"{y_field}:Q", title=y_field.replace("_", " ").title()),
        color=alt.Color(f"{color_field}:N") if color_field else alt.value("lightblue"),
        tooltip=[x_field, y_field, color_field] if color_field else [x_field, y_field]
    ).properties(
        title=title,
        width=CHART_GLOBAL_CONFIG["width"], 
        height=CHART_GLOBAL_CONFIG["height"]
    )
    
    return chart

def create_scatter_chart(data_df, x_field, y_field, size_field=None, color_field=None, title=""):
    """創建散點圖"""
    encoding = {
        "x": alt.X(f"{x_field}:Q", title=x_field.replace("_", " ").title()),
        "y": alt.Y(f"{y_field}:Q", title=y_field.replace("_", " ").title()),
        "tooltip": [x_field, y_field]
    }
    
    if size_field:
        encoding["size"] = alt.Size(f"{size_field}:Q", title=size_field.replace("_", " ").title())
        encoding["tooltip"].append(size_field)
    
    if color_field:
        encoding["color"] = alt.Color(f"{color_field}:N")
        encoding["tooltip"].append(color_field)
    
    chart = alt.Chart(data_df).mark_circle(
        size=100,
        opacity=0.7
    ).encode(**encoding).properties(
        title=title,
        width=CHART_GLOBAL_CONFIG["width"],
        height=CHART_GLOBAL_CONFIG["height"] 
    )
    
    return chart
```

**策略比較圖表生成器**
```python
def create_strategy_comparison_chart(va_rebalance_df, va_nosell_df, dca_df, chart_type="cumulative_value"):
    """
    創建策略比較圖表
    
    參數:
    - va_rebalance_df, va_nosell_df, dca_df: 各策略數據
    - chart_type: 圖表類型（來自CHART_TYPES）
    
    返回:
    - alt.Chart: Altair圖表對象
    """
    # 準備比較數據
    comparison_data = []
    
    strategies = {
        "VA_Rebalance": va_rebalance_df,
        "VA_NoSell": va_nosell_df,
        "DCA": dca_df
    }
    
    chart_config = CHART_TYPES[chart_type]
    
    for strategy_name, df in strategies.items():
        if df is not None and len(df) > 0:
            strategy_data = df.copy()
            strategy_data["Strategy"] = strategy_name
            comparison_data.append(strategy_data)
    
    if not comparison_data:
        return alt.Chart().mark_text(text="No data available")
    
    combined_df = pd.concat(comparison_data, ignore_index=True)
    
    # 根據圖表類型生成相應圖表
    if chart_config["chart_type"] == "line":
        return create_line_chart(
            combined_df,
            chart_config["x_field"],
            chart_config["y_field"],
            "Strategy",
            chart_config["title"]
        )
    elif chart_config["chart_type"] == "bar":
        return create_bar_chart(
            combined_df,
            chart_config["x_field"], 
            chart_config["y_field"],
            "Strategy",
            chart_config["title"]
        )

def create_investment_flow_chart(va_df):
    """
    創建VA與DCA策略投資流圖表（顯示買入/賣出）
    
    參數:
    - va_df: VA策略數據DataFrame
    
    返回:
    - alt.Chart: 投資流圖表
    """
    if va_df is None or len(va_df) == 0:
        return alt.Chart().mark_text(text="No VA data available")
    
    # 為正負投資額設置不同顏色
    va_df_copy = va_df.copy()
    va_df_copy["Investment_Type"] = va_df_copy["Invested"].apply(
        lambda x: "Buy" if x > 0 else "Sell" if x < 0 else "Hold"
    )
    
    chart = alt.Chart(va_df_copy).mark_bar().encode(
        x=alt.X("Period:Q", title="Period"),
        y=alt.Y("Invested:Q", title="Investment Amount ($)"),
        color=alt.Color(
            "Investment_Type:N",
            scale=alt.Scale(
                domain=["Buy", "Sell", "Hold"],
                range=["green", "red", "gray"]
            ),
            title="Action"
        ),
        tooltip=["Period", "Invested", "Investment_Type"]
    ).properties(
        title="VA Strategy Investment Flow",
        width=CHART_GLOBAL_CONFIG["width"],
        height=CHART_GLOBAL_CONFIG["height"]
    )
    
    return chart

def create_allocation_pie_chart(stock_ratio, bond_ratio):
    """
    創建資產配置圓餅圖
    
    參數:
    - stock_ratio: 股票比例 (0-1)
    - bond_ratio: 債券比例 (0-1)
    
    返回:
    - alt.Chart: 圓餅圖
    """
    allocation_data = pd.DataFrame({
        "Asset": ["Stock (SPY)", "Bond"], 
        "Ratio": [stock_ratio * 100, bond_ratio * 100],
        "Color": ["#1f77b4", "#ff7f0e"]
    })
    
    chart = alt.Chart(allocation_data).mark_arc(
        innerRadius=50,
        outerRadius=120
    ).encode(
        theta=alt.Theta("Ratio:Q", title="Allocation (%)"),
        color=alt.Color(
            "Asset:N",
            scale=alt.Scale(range=allocation_data["Color"].tolist()),
            title="Asset Type"
        ),
        tooltip=["Asset", "Ratio"]
    ).properties(
        title="Asset Allocation",
        width=300,
        height=300
    )
    
    return chart
```

#### 2.3.3 進階圖表功能模組

**回撤分析圖表**
```python
def create_drawdown_chart(strategy_df, strategy_name):
    """
    創建回撤分析圖表
    
    參數:
    - strategy_df: 策略數據DataFrame
    - strategy_name: 策略名稱
    
    返回:
    - alt.Chart: 回撤分析圖表
       """
    if strategy_df is None or len(strategy_df) < 2:
        return alt.Chart().mark_text(text="Insufficient data for drawdown analysis")
    
    # 計算回撤序列
    cumulative_values = strategy_df["Cum_Value"].values
    running_max = np.maximum.accumulate(cumulative_values)
    drawdown = (cumulative_values - running_max) / running_max * 100
    
    drawdown_df = pd.DataFrame({
        "Period": strategy_df["Period"],
        "Drawdown": drawdown,
        "Running_Max": running_max
    })
    
    # 回撤面積圖
    drawdown_chart = alt.Chart(drawdown_df).mark_area(
        color="red",
        opacity=0.6
    ).encode(
        x=alt.X("Period:Q", title="Period"),
        y=alt.Y("Drawdown:Q", title="Drawdown (%)", scale=alt.Scale(domain=[drawdown.min(), 0])),
        tooltip=["Period", "Drawdown"]
    )
    
    # 零線
    zero_line = alt.Chart(pd.DataFrame({"y": [0]})).mark_rule(
        color="black",
        strokeWidth=1
    ).encode(y="y:Q")
    
    combined_chart = (drawdown_chart + zero_line).properties(
        title=f"{strategy_name} Drawdown Analysis",
        width=CHART_GLOBAL_CONFIG["width"],
        height=CHART_GLOBAL_CONFIG["height"]
    )
    
    return combined_chart

def create_risk_return_scatter(summary_df):
    """
    創建風險收益散點圖
    
    參數:
    - summary_df: 綜合比較摘要DataFrame
    
    返回:
    - alt.Chart: 風險收益散點圖
    """
    if summary_df is None or len(summary_df) == 0:
        return alt.Chart().mark_text(text="No summary data available")
    
    chart = alt.Chart(summary_df).mark_circle(
        size=200,
        opacity=0.8
    ).encode(
        x=alt.X("Volatility:Q", title="Volatility (%)"),
        y=alt.Y("Annualized_Return:Q", title="Annualized Return (%)"),
        color=alt.Color("Strategy:N", title="Strategy"),
        size=alt.Size("Final_Value:Q", title="Final Value ($)"),
        tooltip=["Strategy", "Volatility", "Annualized_Return", "Final_Value", "Sharpe_Ratio"]
    ).properties(
        title="Risk vs Return Analysis",
        width=CHART_GLOBAL_CONFIG["width"],
        height=CHART_GLOBAL_CONFIG["height"]
    )
    
    return chart
```

---

## 3. 現代化UI介面設計規格

本章節根據第1章數據源管理與安全機制、第2章核心計算公式與表格架構，設計簡潔易用的現代化UI界面，確保新手用戶5分鐘內上手，同時保持所有技術規範的完整性。

### 3.1 設計原則與布局架構

#### 3.1.1 核心設計原則

```python
APP_HEADER_SPECS = {
    "main_title": {
        "text": "投資策略績效比較分析系統",
        "font_size": "2.5rem",
        "font_weight": "bold",
        "color": "#1f2937",
        "text_align": "center",
        "margin_bottom": "0.5rem"
    },
    "subtitle": {
        "text": "VA(定期定值) vs DCA(定期定額) 策略比較",
        "font_size": "1.2rem", 
        "color": "#6b7280",
        "text_align": "center",
        "margin_bottom": "1rem"
    },
    "visual_simplicity": {
        "clean_interface": "移除非必要視覺元素",
        "intuitive_navigation": "符合用戶心理模型的操作流程",
        "friendly_guidance": "使用emoji和簡潔文案提升親和力"
    }
}
```

#### 3.1.2 三欄式響應式布局

```python
RESPONSIVE_LAYOUT_CONFIG = {
    "desktop_layout": {
        "structure": """
        ┌─────────────────────────────────────────────────┐
        │ 🏠 投資策略比較分析 - 輕鬆比較兩種投資方法 │
        └─────────────────────────────────────────────────┘
        ┌──────────┬─────────────────┬─────────────────┐
        │ 🎯 投資設定│ 📊 即時結果預覽 │ 💡 智能建議 │
        │ (350px) │ (主要區域) │ (300px) │
        └──────────┴─────────────────┴─────────────────┘
        """,
        "implementation": {
            "left_panel": {
                "width": 350,
                "content": "simplified_parameter_inputs",
                "collapsible": False
            },
            "center_panel": {
                "width": "auto",
                "content": "results_visualization",
                "responsive": True
            },
            "right_panel": {
                "width": 300,
                "content": "smart_recommendations",
                "hide_on_tablet": True
            }
        },
        "breakpoint": ">=1024px"
    },
    "mobile_layout": {
        "structure": "tab_navigation",
        "tabs": [
            {
                "name": "🎯 設定",
                "icon": "⚙️",
                "content": "parameter_inputs",
                "priority": 1
            },
            {
                "name": "📊 結果", 
                "icon": "📈",
                "content": "results_display",
                "priority": 2
            },
            {
                "name": "💡 建議",
                "icon": "🎯", 
                "content": "recommendations",
                "priority": 3
            }
        ],
        "navigation_position": "bottom",
        "breakpoint": "<1024px"
    }
}
```

#### 3.1.3 簡潔標題設計

```python
MODERN_HEADER_SPECS = {
    "main_header": {
        "title": "🏠 投資策略比較分析",
        "subtitle": "輕鬆比較兩種投資方法",
        "style": "minimal_centered",
        "mobile_optimized": True
    },
    "smart_status_indicator": {
        # 第1章API狀態整合（背景化、非干擾）
        "data_source_status": {
            "display_mode": "icon_with_tooltip",
            "states": {
                "real_data": {"icon": "🟢", "tooltip": "使用真實市場數據"},
                "simulation": {"icon": "🟡", "tooltip": "使用模擬數據"},
                "offline": {"icon": "🔴", "tooltip": "離線模式"}
            },
            "intelligent_fallback": True,  # 智能數據源回退機制
            "user_notification": "minimal"  # 僅必要時提醒
        },
        "chapter1_integration": {
            "multilevel_api_security": "background_processing",
            "fault_tolerance": "automatic",
            "data_quality_monitoring": "silent",
            "backup_strategy": "seamless_switching"
        }
    }
}
```

### 3.2 左側參數設定區域

#### 3.2.1 基本參數（永遠可見）

```python
BASIC_PARAMETERS = {
    "initial_investment": {
        "component": "slider_with_input",
        "label": "💰 期初投入金額",
        "range": [0, 10000000],  # 0-1000萬
        "default": 10000,
        "step": 50000,
        "format": "currency",
        "help": "投資策略的起始資金",
        # 第1章精確度規範集成
        "precision": 2,  # 符合第1章價格精確度
        "validation": {
            "chapter1_compliance": True,
            "price_format_check": True
        },
        # 第2章計算邏輯集成
        "calculation_integration": {
            "va_initial_investment": "C0參數",
            "dca_initial_component": "DCA策略第1期部分投入",
            "formula_references": ["calculate_va_target_value", "calculate_dca_investment"]
        }
    },
    "investment_start_date": {
        "component": "date_input",
        "label": "📅 投資起始日期",
        "default": "next_year_jan_1",  # 預設為次年1月1日
        "min_date": "today",  # 最早為當前日期
        "max_date": "today_plus_10_years",  # 最晚為當前日期後10年
        "format": "YYYY-MM-DD",
        "help": "第1期投資的起始日期，系統會自動調整為交易日",
        "auto_adjustment": {
            "trading_day_check": True,
            "adjustment_direction": "next",  # 若非交易日，調整為下一個交易日
            "holiday_calendar": "US_Federal_Holiday"
        },
        # 第1章時間軸生成集成
        "chapter1_integration": {
            "timeline_generation": "generate_simulation_timeline",
            "trading_day_adjustment": "adjust_for_trading_days",
            "period_calculation": "calculate_period_start_date",
            "data_fetching_range": "get_target_dates_for_data_fetching"
        },
        # 第2章計算邏輯集成
        "chapter2_integration": {
            "base_date_parameter": "所有期間計算的基準日期",
            "timeline_dependency": "影響所有期初期末日期計算",
            "market_data_scope": "決定API數據獲取範圍"
        }
    },
    "investment_years": {
        "component": "slider",
        "label": "⏱️ 投資年數",
        "range": [5, 40],
        "default": 30,
        "step": 1,
        "format": "integer",
        "help": "投資策略執行的總年數",
        # 第1章時間軸生成集成
        "chapter1_integration": {
            "timeline_generation": True,
            "trading_day_calculation": True,
            "period_boundary_adjustment": True
        },
        # 第2章期數計算集成
        "chapter2_integration": {
            "total_periods_calculation": True,
            "table_rows_preparation": True,
            "frequency_conversion": True
        }
    },
    "investment_frequency": {
        "component": "radio_buttons",
        "label": "📅 投資頻率",
        "options": [
            {"value": "monthly", "label": "每月", "icon": "📅"},
            {"value": "quarterly", "label": "每季", "icon": "📊"},
            {"value": "semi_annually", "label": "每半年", "icon": "📈"},
            {"value": "annually", "label": "每年", "icon": "🗓️"}
        ],
        "default": "annually",
        "layout": "horizontal",
        "help": "投資操作的執行頻率",
        # 第1章交易日調整集成
        "chapter1_integration": {
            "trading_day_rules": True,
            "frequency_aggregation": True,
            "holiday_adjustment": True
        },
        # 第2章參數轉換集成
        "chapter2_integration": {
            "parameter_conversion": "convert_annual_to_period_parameters",
            "periods_per_year_calculation": True,
            "frequency_based_validation": True
        }
    },
    "asset_allocation": {
        "component": "dual_slider",
        "label": "📊 股債配置",
        "stock_percentage": {
            "label": "股票比例",
            "range": [0, 100],
            "default": 80,
            "color": "#3b82f6"
        },
        "bond_percentage": {
            "label": "債券比例", 
            "range": [0, 100],
            "default": 20,
            "color": "#f59e0b",
            "auto_calculate": True  # 自動計算為100-股票比例
        },
        "visual": "interactive_pie_chart",
        "help": "投資組合的股票與債券分配比例",
        # 第1章數據源集成
        "chapter1_integration": {
            "stock_data_source": "Tiingo API (SPY)",
            "bond_data_source": "FRED API (DGS1)",
            "pricing_formulas": "第1章債券定價公式"
        },
        # 第2章配置計算集成
        "chapter2_integration": {
            "portfolio_allocation_module": True,
            "asset_value_calculation": True,
            "rebalancing_logic": True
        }
    }
}
```

**起始日期參數實現函數**

```python
def _render_investment_start_date(self):
    """渲染投資起始日期參數 - 嚴格按照規格"""
    param = self.basic_params["investment_start_date"]
    
    # 計算預設日期（次年1月1日）
    from datetime import datetime, timedelta
    current_year = datetime.now().year
    default_date = datetime(current_year + 1, 1, 1).date()
    
    # 計算日期範圍
    min_date = datetime.now().date()  # 今天
    max_date = (datetime.now() + timedelta(days=365*10)).date()  # 10年後
    
    # 渲染日期選擇器
    selected_date = st.date_input(
        param["label"],
        value=st.session_state.get('investment_start_date', default_date),
        min_value=min_date,
        max_value=max_date,
        format=param["format"],
        help=param["help"],
        key="investment_start_date"
    )
    
    # 交易日調整檢查
    if selected_date:
        from src.data_sources.trading_calendar import adjust_for_trading_days
        
        # 轉換為datetime進行交易日檢查
        selected_datetime = datetime.combine(selected_date, datetime.min.time())
        adjusted_datetime = adjust_for_trading_days(selected_datetime, 'next')
        adjusted_date = adjusted_datetime.date()
        
        # 顯示調整資訊
        if selected_date != adjusted_date:
            st.warning(f"⚠️ 所選日期 {selected_date} 非交易日，已自動調整為 {adjusted_date}")
            st.session_state.investment_start_date = adjusted_date
        else:
            st.success(f"✅ 已選擇投資起始日期: {selected_date}")
            st.session_state.investment_start_date = selected_date
    
    # 顯示時間軸預覽
    if hasattr(st.session_state, 'investment_start_date') and hasattr(st.session_state, 'investment_years') and hasattr(st.session_state, 'investment_frequency'):
        start_date = st.session_state.investment_start_date
        years = st.session_state.investment_years
        frequency = st.session_state.investment_frequency
        
        # 計算結束日期
        if frequency == "monthly":
            end_date = start_date.replace(year=start_date.year + years)
        elif frequency == "quarterly":
            end_date = start_date.replace(year=start_date.year + years)
        elif frequency == "semi_annually":
            end_date = start_date.replace(year=start_date.year + years)
        elif frequency == "annually":
            end_date = start_date.replace(year=start_date.year + years)
        
        st.info(f"📅 投資期間預覽: {start_date} 至 {end_date} ({years} 年)")
    
    # 顯示第1章和第2章整合資訊
    with st.expander("🔧 技術整合資訊", expanded=False):
        st.markdown("**第1章時間軸生成整合**")
        ch1_integration = param['chapter1_integration']
        for key, value in ch1_integration.items():
            st.markdown(f"• **{key}**: {value}")
        
        st.markdown("**第2章計算邏輯整合**")
        ch2_integration = param['chapter2_integration']
        for key, value in ch2_integration.items():
            st.markdown(f"• **{key}**: {value}")

def render_basic_parameters(self):
    """渲染基本參數區域 - 永遠可見，包含起始日期"""
    st.header("🎯 投資設定")
    
    # 💰 期初投入金額 - slider_with_input
    self._render_initial_investment()
    
    # 📅 投資起始日期 - date_input (新增)
    self._render_investment_start_date()
    
    # 💳 年度投入金額 - slider_with_input
    self._render_annual_investment()
    
    # ⏱️ 投資年數 - slider
    self._render_investment_years()
    
    # 📅 投資頻率 - radio_buttons
    self._render_investment_frequency()
    
    # 📊 股債配置 - dual_slider
    self._render_asset_allocation()
```

#### 3.2.2 進階設定（可摺疊）

```python
ADVANCED_SETTINGS = {
    "expandable_section": {
        "title": "⚙️ 進階設定",
        "expanded": False,
        "description": "調整策略細節參數"
    },
    "va_growth_rate": {
        "component": "slider",
        "label": "📈 VA策略目標成長率",
        "range": [0, 100],  # 支援負成長率到極高成長率
        "default": 13,
        "step": 1.0,
        "format": "percentage",
        "help": "VA策略的年化目標成長率，支援極端市場情境",
        # 第1章精確度集成
        "precision": 4,  # 內部計算精度
        "display_precision": 1,  # 用戶界面精度
        # 第2章VA公式核心集成
        "chapter2_integration": {
            "core_formula": "calculate_va_target_value",
            "parameter_role": "r_period (年化成長率)",
            "validation_logic": "極端情境合理性檢查",
            "extreme_scenarios": True
        }
    },
    "inflation_adjustment": {
        "enable_toggle": {
            "component": "switch",
            "label": "通膨調整",
            "default": True,
            "help": "是否對DCA投入金額進行通膨調整"
        },
        "inflation_rate": {
            "component": "slider",
            "label": "年通膨率",
            "range": [0, 15],
            "default": 2,
            "step": 0.5,
            "format": "percentage",
            "enabled_when": "inflation_adjustment.enable_toggle == True",
            # 第2章DCA投入公式集成
            "chapter2_integration": {
                "formula_impact": "calculate_dca_investment中的g_period參數",
                "cumulative_calculation": "calculate_dca_cumulative_investment",
                "parameter_conversion": "convert_annual_to_period_parameters"
            }
        }
    },
    "data_source": {
        "component": "user_controlled_selection",
        "label": "📊 數據來源",
        "default_mode": "real_data",  # 預設使用真實市場數據
        "user_options": {
            "options": [
                {
                    "value": "real_data",
                    "label": "真實市場數據",
                    "description": "Tiingo API + FRED API",
                    "icon": "🌐",
                    "priority": 1  # 預設選項
                },
                {
                    "value": "simulation",
                    "label": "模擬數據",
                    "description": "基於歷史統計的模擬",
                    "icon": "🎲",
                    "priority": 2
                }
            ]
        },
        "intelligent_fallback": {
            "enabled": True,
            "trigger_condition": "date_range_data_unavailable",  # 當指定日期範圍無API數據時觸發
            "fallback_logic": {
                "step1": "檢查用戶指定的起始日期+投資年數範圍",
                "step2": "驗證該期間內API數據可用性",
                "step3": "若API數據不足，自動啟用模擬數據並通知用戶",
                "step4": "保留用戶原始選擇，僅在必要時臨時切換"
            },
            "user_notification": {
                "data_sufficient": "✅ 指定期間內API數據完整可用",
                "data_insufficient": "⚠️ 指定期間部分時段無API數據，已自動補充模擬數據",
                "data_unavailable": "🔄 指定期間無API數據，已切換為模擬數據模式"
            }
        },
        # 第1章數據源完整集成
        "chapter1_integration": {
            "api_security_mechanisms": True,
            "fault_tolerance_strategy": True,
            "data_quality_validation": True,
            "simulation_model_specs": "幾何布朗運動 + Vasicek模型",
            "date_range_validation": True  # 新增：日期範圍數據可用性驗證
        }
    }
}
```

### 3.3 中央結果展示區域

#### 3.3.1 頂部摘要卡片

```python
SUMMARY_METRICS_DISPLAY = {
    "layout": "three_column_metrics",
    "cards": [
        {
            "title": "🏆 推薦策略",
            "content": "dynamic_recommendation",
            "calculation": "基於風險收益比較",
            "format": "strategy_name_with_delta",
            "mobile_priority": 1
        },
        {
            "title": "💰 預期最終價值", 
            "content": "final_portfolio_value",
            "calculation": "基於第2章計算結果",
            "format": "currency_with_comparison",
            "mobile_priority": 2
        },
        {
            "title": "📈 年化報酬率",
            "content": "enhanced_annualized_return",
            "calculation": "第2章calculate_enhanced_annualized_return函數（時間加權報酬率）",
            "format": "percentage_with_delta",
            "mobile_priority": 3,
            "tooltip": "採用時間加權報酬率(TWR)計算，消除現金流時機影響，反映真實投資策略績效"
        }
    ],
    "responsive_behavior": {
        "desktop": "horizontal_layout",
        "tablet": "two_plus_one_layout",
        "mobile": "vertical_stack"
    }
}
```

#### 3.3.2 策略對比卡片

```python
STRATEGY_COMPARISON_CARDS = {
    "layout": "side_by_side",
    "va_strategy_card": {
        "title": "🎯 定期定值 (VA策略)",
        "style": "modern_info_card",
        "content": {
            "final_value": "dynamic_calculation",
            "annualized_return": "dynamic_calculation", 
            "suitability": "有經驗投資者",
            "key_feature": "智能調節投入金額",
            "pros": ["可能獲得更高報酬", "有效控制市場波動"],
            "cons": ["需要主動管理", "可能錯過部分漲幅"]
        },
        # 第2章VA計算集成
        "calculation_backend": {
            "final_value": "VA策略表格最後一行Cum_Value",
            "return_calculation": "calculate_enhanced_annualized_return",
            "table_reference": "VA_COLUMNS_ORDER"
        }
    },
    "dca_strategy_card": {
        "title": "💰 定期定額 (DCA策略)",
        "style": "modern_info_card",
        "content": {
            "final_value": "dynamic_calculation",
            "annualized_return": "dynamic_calculation",
            "suitability": "投資新手",
            "key_feature": "固定金額定期投入",
            "pros": ["操作簡單", "情緒影響較小"],
            "cons": ["報酬可能較低", "無法優化時機"]
        },
        # 第2章DCA計算集成
        "calculation_backend": {
            "final_value": "DCA策略表格最後一行Cum_Value",
            "return_calculation": "calculate_enhanced_annualized_return", 
            "table_reference": "DCA_COLUMNS_ORDER"
        }
    }
}
```

#### 3.3.3 圖表顯示規範

```python
SIMPLIFIED_CHARTS_CONFIG = {
    "tab_navigation": {
        "tabs": [
            {
                "name": "📈 資產成長",
                "chart_type": "line_chart",
                "description": "兩種策略的資產累積對比",
                "mobile_optimized": True
            },
            {
                "name": "📊 報酬比較",
                "chart_type": "bar_chart", 
                "description": "年化報酬率對比",
                "mobile_optimized": True
            },
            {
                "name": "⚠️ 風險分析",
                "chart_type": "risk_metrics",
                "description": "風險指標比較",
                "mobile_optimized": True
            }
        ]
    },
    "chart_configurations": {
        "asset_growth_chart": {
            "data_source": "第2章策略計算結果",
            "x_axis": "Period (期數)",
            "y_axis": "Cum_Value (累積價值)", 
            "lines": ["VA_Rebalance", "DCA"],
            "interactive": True,
            "mobile_optimized": True,
            "touch_friendly": True
        },
        "return_comparison_chart": {
            "data_source": "第2章summary_comparison",
            "chart_type": "horizontal_bar",
            "metrics": ["Total_Return", "Annualized_Return", "IRR"],
            "color_scheme": "strategy_based",
            "mobile_layout": "vertical_bars"
        },
        "risk_analysis_chart": {
            "data_source": "第2章績效指標計算模組",
            "chart_type": "simplified_comparison",
            "metrics": ["風險度", "報酬率", "穩定性"],
            "visualization": "horizontal_comparison_bars",
            "mobile_friendly": True
        }
    }
}
```

### 3.4 右側智能建議區域

#### 3.4.1 個人化建議系統

```python
SMART_RECOMMENDATIONS = {
    "recommendation_engine": {
        "input_factors": [
            "investment_amount",
            "time_horizon", 
            "risk_tolerance_derived",
            "strategy_performance_comparison"
        ],
        "output_format": "user_friendly_advice",
        "personalization": "high"
    },
    "recommendation_templates": {
        "va_recommended": {
            "title": "🎯 推薦：定期定值策略",
            "style": "success_card",
            "content_template": """
            **推薦原因**
            - 預期多賺 {amount_difference}
            - 適合您的 {investment_period} 年投資期間
            - 風險收益比更優

            **注意事項**
            - 需要定期關注市場調整
            - 可能涉及賣出操作
            """,
            "calculation_basis": "基於第2章策略比較結果"
        },
        "dca_recommended": {
            "title": "💰 推薦：定期定額策略",
            "style": "info_card", 
            "content_template": """
            **推薦原因**
            - 操作簡單，適合新手
            - 風險相對較低
            - 長期穩定成長

            **預期表現**
            - 最終價值：{final_value}
            - 年化報酬：{annualized_return}
            """,
            "calculation_basis": "基於第2章DCA計算結果"
        },
        "neutral_analysis": {
            "title": "📊 策略分析",
            "style": "neutral_card",
            "content_template": """
            **兩種策略都有優勢**
            - VA策略：{va_advantage}
            - DCA策略：{dca_advantage}

            **建議**
            考慮您的投資經驗和時間投入來選擇
            """,
            "show_when": "performance_difference < 5%"
        }
    }
}
```

#### 3.4.2 投資知識卡片

```python
EDUCATIONAL_CONTENT = {
    "knowledge_cards": {
        "what_is_va": {
            "title": "💡 什麼是定期定值？",
            "content": "就像設定目標存款，不夠就多存，超過就少存。當市場下跌時自動加碼，上漲時減少投入，追求平穩的成長軌跡。",
            "expandable": True,
            "beginner_friendly": True,
            "icon": "🎯"
        },
        "what_is_dca": {
            "title": "💡 什麼是定期定額？",
            "content": "每月固定投入相同金額，就像定期定額存款。不管市場漲跌都持續投入，用時間來分散成本。",
            "expandable": True,
            "beginner_friendly": True,
            "icon": "💰"
        },
        "risk_explanation": {
            "title": "⚠️ 投資風險說明",
            "content": "所有投資都有風險，過去績效不代表未來表現。請根據自身風險承受能力謹慎投資。",
            "importance": "high",
            "always_visible": True
        }
    },
    "help_section": {
        "title": "🙋‍♀️ 需要幫助？",
        "quick_links": [
            {"text": "📖 新手指南", "action": "show_beginner_guide"},
            {"text": "❓ 常見問題", "action": "show_faq"},
            {"text": "📞 線上客服", "action": "contact_support"}
        ],
        "tutorial_button": {
            "text": "🚀 5分鐘快速上手",
            "style": "primary",
            "action": "start_interactive_tutorial"
        }
    }
}
```

#### 3.3.4 數據表格與下載

```python
DATA_TABLES_CONFIG = {
    "display_options": {
        "expandable_section": True,
        "strategy_selector": ["VA策略", "DCA策略", "比較摘要"],
        "mobile_responsive": True
    },
    "va_strategy_table": {
        "column_specs": "VA_COLUMNS_ORDER",  # 第2章定義的27個欄位
        "formatting_rules": {
            "use_chapter2_precision": True,
            "precision_config": {
                "Period_Return": 2,
                "Cumulative_Return": 2,
                "Annualized_Return": 2,
                "Volatility": 2,
                "Sharpe_Ratio": 3,
                "Max_Drawdown": 2
            }
        },
        "validation": {
            "chapter2_compliance_check": True,
            "formula_reference_validation": True
        }
    },
    "dca_strategy_table": {
        "column_specs": "DCA_COLUMNS_ORDER",  # 第2章定義的28個欄位
        "formatting_rules": {
            "use_chapter2_dca_logic": True,
            "apply_inflation_adjustment": True,
            "validate_cumulative_investment": True
        }
    },
    "csv_download": {
        "three_button_layout": ["VA策略數據", "DCA策略數據", "績效摘要"],
        "filename_convention": "投資策略比較_{strategy}_{timestamp}.csv",
        "include_metadata": True,
        "chapter1_2_compliance_validation": True
    }
}
```

### 3.4 智能功能與用戶體驗

#### 3.4.1 用戶控制的數據源管理

```python
@st.cache_data(ttl=3600)
def user_controlled_data_source_manager(user_selection, start_date, investment_years):
    """
    用戶控制的數據源管理（第1章完整技術規範保留）
    
    Args:
        user_selection: 用戶選擇的數據源 ('real_data' 或 'simulation')
        start_date: 投資起始日期
        investment_years: 投資年數
    
    Returns:
        數據源狀態和數據
    """
    # 計算投資期間範圍
    end_date = start_date + timedelta(days=investment_years * 365)
    
    if user_selection == "real_data":
        try:
            # 檢查指定期間內API數據可用性
            data_coverage = check_api_data_coverage(start_date, end_date)
            
            if data_coverage["coverage_ratio"] >= 0.95:  # 95%以上數據可用
                # 使用真實API數據
                data = get_real_market_data_with_security(start_date, end_date)
                st.session_state.data_source_status = "real_data"
                st.success("✅ 指定期間內API數據完整可用")
                return {"status": "real_data", "data": data}
                
            elif data_coverage["coverage_ratio"] >= 0.5:  # 50%-95%數據可用
                # 混合使用：API數據 + 模擬數據補充
                data = get_hybrid_market_data(start_date, end_date)
                st.session_state.data_source_status = "hybrid"
                st.warning("⚠️ 指定期間部分時段無API數據，已自動補充模擬數據")
                return {"status": "hybrid", "data": data}
                
            else:  # 數據不足50%
                # 自動切換到模擬數據並通知用戶
                data = get_simulation_data_chapter1_compliant(start_date, end_date)
                st.session_state.data_source_status = "simulation_fallback"
                st.info("🔄 指定期間無充足API數據，已切換為模擬數據模式")
                return {"status": "simulation_fallback", "data": data}
                
        except APIConnectionError:
            # API連接失敗，切換到模擬數據
            st.warning("🌐 API連接失敗，已切換為模擬數據模式")
            data = get_simulation_data_chapter1_compliant(start_date, end_date)
            st.session_state.data_source_status = "simulation_fallback"
            return {"status": "simulation_fallback", "data": data}
            
    elif user_selection == "simulation":
        # 用戶主動選擇模擬數據
        data = get_simulation_data_chapter1_compliant(start_date, end_date)
        st.session_state.data_source_status = "simulation"
        st.info("🎲 正在使用模擬數據進行分析")
        return {"status": "simulation", "data": data}
    
    # 預設回退
    st.session_state.data_source_status = "offline"
    return {"status": "offline", "data": get_cached_data_or_default()}

def check_api_data_coverage(start_date, end_date):
    """
    檢查指定日期範圍內API數據的覆蓋率
    
    Returns:
        Dict: 包含覆蓋率和缺失期間的資訊
    """
    try:
        # 檢查Tiingo API數據可用性
        tiingo_coverage = check_tiingo_data_range(start_date, end_date)
        # 檢查FRED API數據可用性  
        fred_coverage = check_fred_data_range(start_date, end_date)
        
        overall_coverage = min(tiingo_coverage, fred_coverage)
        
        return {
            "coverage_ratio": overall_coverage,
            "tiingo_coverage": tiingo_coverage,
            "fred_coverage": fred_coverage,
            "data_sufficient": overall_coverage >= 0.95
        }
    except Exception:
        return {"coverage_ratio": 0.0, "data_sufficient": False}

def user_friendly_error_handler(error_type, technical_error=None):
    """
    將技術錯誤轉換為用戶友善訊息
    """
    error_messages = {
                        "api_error": "🌐 網路連線問題，已根據用戶設定切換數據源",
        "calculation_error": "⚠️ 參數設定需要調整，請檢查投入金額範圍", 
        "data_error": "📊 數據載入中，請稍候片刻",
        "validation_error": "🔍 輸入參數有誤，請檢查設定值"
    }
    
    user_message = error_messages.get(error_type, "系統忙碌中，請稍後再試")
    
    if st.session_state.get("debug_mode", False) and technical_error:
        with st.expander("🔧 技術詳情（開發者模式）"):
            st.code(str(technical_error))
    
    return user_message
```

#### 3.4.2 漸進式載入與反饋

```python
def progressive_calculation_with_feedback():
    """
    漸進式計算過程，提供即時反饋
    """
    progress_container = st.container()
    
    with progress_container:
        st.info("🔄 正在分析您的投資策略...")
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # 階段1：數據準備（第1章數據源處理）
        status_text.text("📊 準備市場數據...")
        market_data = prepare_market_data()
        progress_bar.progress(25)
        
        # 階段2：VA策略計算（第2章計算公式）
        status_text.text("🎯 計算定期定值策略...")
        va_results = calculate_va_strategy(market_data)
        progress_bar.progress(50)
        
        # 階段3：DCA策略計算（第2章計算公式）
        status_text.text("💰 計算定期定額策略...")
        dca_results = calculate_dca_strategy(market_data)
        progress_bar.progress(75)
        
        # 階段4：績效比較（第2章績效指標）
        status_text.text("📈 生成績效比較...")
        comparison_results = generate_comparison_analysis(va_results, dca_results)
        progress_bar.progress(100)
        
        # 清理進度顯示
        progress_container.empty()
        
    return va_results, dca_results, comparison_results
```

#### 3.4.3 智能建議系統

```python
SMART_RECOMMENDATIONS = {
    "personalized_advice": {
        "recommendation_engine": {
            "factors": [
                "investment_amount",      # 投資金額規模
                "time_horizon",          # 投資時間長度
                "risk_tolerance",        # 風險承受度
                "strategy_performance"   # 策略表現比較
            ],
            "templates": {
                "va_preferred": {
                    "title": "🎯 建議採用VA策略",
                    "reason": "基於您的參數，VA策略預期表現較佳",
                    "key_points": ["較高預期報酬", "適合您的風險承受度", "投資金額充足"]
                },
                "dca_preferred": {
                    "title": "💰 建議採用DCA策略", 
                    "reason": "DCA策略更適合您的投資目標",
                    "key_points": ["操作簡單", "風險相對較低", "適合長期投資"]
                },
                "neutral_analysis": {
                    "title": "⚖️ 兩種策略各有優勢",
                    "reason": "根據分析結果，兩種策略表現相近",
                    "key_points": ["可考慮混合策略", "建議進一步調整參數", "關注個人偏好"]
                }
            }
        },
        # 第2章策略比較結果集成
        "calculation_basis": {
            "comparison_metrics": ["final_value", "annualized_return", "sharpe_ratio", "max_drawdown"],
            "chapter2_integration": "基於完整策略表格計算結果"
        }
    },
    "investment_knowledge": {
        "strategy_explanation_cards": {
            "what_is_va": {
                "title": "什麼是定期定值(VA)？",
                "content": "根據目標價值動態調整投入金額的策略",
                "beginner_friendly": True
            },
            "what_is_dca": {
                "title": "什麼是定期定額(DCA)？", 
                "content": "固定時間間隔投入固定金額的策略",
                "beginner_friendly": True
            }
        },
        "risk_warnings": {
            "importance": "high",
            "content": "投資有風險，過去績效不代表未來結果",
            "prominence": "always_visible"
        },
        "help_section": {
            "quick_start_guide": "5分鐘快速上手教程",
            "faq": "常見問題解答",
            "contact": "線上客服支援"
        }
    }
}
```

### 3.5 響應式設計實現

#### 3.5.1 設備檢測與適配

```python
def detect_device_and_layout():
    """
    檢測設備類型並調整布局
    """
    # 使用CSS媒體查詢檢測設備寬度
    screen_width_js = """
    <script>
    function getScreenWidth() {
        return window.innerWidth;
    }
    </script>
    """
    
    if st.session_state.get("screen_width", 1024) >= 1024:
        st.session_state.layout_mode = "desktop"
        return render_desktop_layout()
    elif st.session_state.get("screen_width", 768) >= 768:
        st.session_state.layout_mode = "tablet" 
        return render_tablet_layout()
    else:
        st.session_state.layout_mode = "mobile"
        return render_mobile_layout()

def render_mobile_layout():
    """
    手機版標籤式導航布局
    """
    tab1, tab2, tab3 = st.tabs(["🎯 設定", "📊 結果", "💡 建議"])
    
    with tab1:
        render_simplified_parameters()
    
    with tab2:
        render_mobile_optimized_results()
        
    with tab3:
        render_compact_recommendations()

def render_desktop_layout():
    """
    桌面版三欄布局
    """
    left_col, center_col, right_col = st.columns([350, None, 300])
    
    with left_col:
        render_full_parameter_panel()
    
    with center_col:
        render_main_results_area()
        
    with right_col:
        render_smart_suggestions_panel()
```

#### 3.5.2 移動端優化

```python
MOBILE_OPTIMIZED_COMPONENTS = {
    "touch_friendly_controls": {
        "min_touch_target": "44px",
        "slider_thumb_size": "24px", 
        "button_min_height": "48px",
        "tap_feedback": True
    },
    "readable_typography": {
        "min_font_size": "16px",
        "line_height": "1.6",
        "contrast_ratio": "4.5:1",
        "readable_color_scheme": True
    },
    "simplified_interactions": {
        "reduce_decimal_precision": True,
        "larger_step_sizes": True,
        "preset_value_shortcuts": True,
        "swipe_gestures": True
    },
    "performance_optimization": {
        "lazy_loading": True,
        "image_compression": True,
        "minimal_animations": True,
        "efficient_rendering": True
    }
}
```

### 3.6 完整Streamlit應用實現

```python
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import time

# 第1章和第2章模組導入（保持不變）
from src.data_sources import TiingoDataSource, FREDDataSource, SimulationDataSource
from src.calculations import calculate_va_target_value, calculate_dca_investment
from src.strategies import VAStrategy, DCAStrategy
from src.performance_metrics import calculate_annualized_return, calculate_enhanced_annualized_return, calculate_time_weighted_return, calculate_irr

def main():
    """
    現代化投資策略比較應用程式
    """
    # 頁面配置
    st.set_page_config(
        page_title="投資策略比較分析",
        page_icon="🏠",
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    
    # 應用現代化樣式
    apply_modern_styling()
    
    # 顯示簡潔標題
    render_modern_header()
    
    # 檢測設備並渲染對應布局
    detect_device_and_layout()

def apply_modern_styling():
    """
    現代化CSS樣式
    """
    st.markdown("""
    <style>
    /* 隱藏Streamlit預設元素 */
    .stAppDeployButton {display: none;}
    .stDecoration {display: none;}
    #MainMenu {visibility: hidden;}
    
    /* 現代化卡片樣式 */
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        border: 1px solid #e5e7eb;
        margin-bottom: 1rem;
    }
    
    /* 響應式字體大小 */
    @media (max-width: 768px) {
        .stMarkdown h1 { font-size: 1.75rem !important; }
        .stMarkdown h2 { font-size: 1.5rem !important; }
        .stMarkdown h3 { font-size: 1.25rem !important; }
        .stSlider > div > div > div { min-height: 48px; }
        .stButton > button { min-height: 48px; font-size: 16px; }
    }
    
    /* 改進的互動元件 */
    .stSlider > div > div > div > div {
        background: #3b82f6;
    }
    
    .stButton > button {
        border-radius: 8px;
        font-weight: 500;
        transition: all 0.2s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
    
    /* 智能狀態指示器 */
    .status-indicator {
        display: inline-block;
        width: 12px;
        height: 12px;
        border-radius: 50%;
        margin-right: 8px;
    }
    
    .status-healthy { background: #10b981; }
    .status-warning { background: #f59e0b; }
    .status-error { background: #ef4444; }
    </style>
    """, unsafe_allow_html=True)

def render_modern_header():
    """
    渲染簡潔的現代化標題
    """
    # 主標題
    st.markdown("# 🏠 投資策略比較分析")
    st.markdown("##### 輕鬆比較兩種投資方法")
    
    # 智能狀態指示器
    status_col1, status_col2, status_col3 = st.columns([1, 1, 8])
    
    with status_col1:
        data_status = st.session_state.get("data_source_status", "real_data")
        if data_status == "real_data":
            st.markdown("🟢 真實數據")
        elif data_status == "simulation":
            st.markdown("🟡 模擬數據")
        else:
            st.markdown("🔴 離線模式")
    
    st.markdown("---")

if __name__ == "__main__":
    main()
```

#### 3.6.1 技術規範完整性保證

**第1章技術規範集成確認**：
- ✅ 數據精度：價格2位、殖利率4位、比例2位小數
- ✅ API安全：多層級金鑰、容錯機制、重試策略、備援降級
- ✅ 數據源：Tiingo API、FRED API、模擬引擎、品質驗證
- ✅ 交易日：美股規則、假期調整、期間計算

**第2章技術規範集成確認**：
- ✅ 核心公式：VA目標價值、DCA投資、參數轉換函數保持不變
- ✅ 表格結構：VA 27欄位、DCA 28欄位、摘要8欄位
- ✅ 績效指標：IRR、年化報酬、夏普比率、最大回撤
- ✅ 執行邏輯：VA期末執行、DCA期初執行、投資時機規定

#### 3.6.2 實作檢查清單

**用戶體驗目標**：
- ✅ 5分鐘上手：簡化參數設定、智能預設值、漸進式指導
- ✅ 移動友善：響應式布局、觸控優化、可讀性設計
- ✅ 漸進式披露：基本功能突出、進階功能可選展開
- ✅ 友善錯誤：技術錯誤轉用戶語言、自動恢復建議
- ✅ 載入反饋：四階段進度、即時狀態更新
- ✅ 清晰結果：直觀指標卡片、策略對比、圖表簡化

**技術合規性**：
- ✅ 第1-2章規範保留：所有函數、公式、精確度標準維持不變
- ✅ 函數相容性：calculate_va_target_value、calculate_dca_investment等調用保持一致
- ✅ 精確度標準：第1章數據精度設定完整實施
- ✅ API安全：第1章多層級安全機制背景運行
- ✅ 數據品質：第1章驗證規則自動執行

**設計品質**：
- ✅ 響應式布局：桌面三欄、平板二欄、手機標籤
- ✅ 現代美學：簡潔卡片、emoji指引、和諧配色
- ✅ 直觀導航：符合心理模型、清晰層級、易用流程
- ✅ 性能優化：快取策略、懶載入、最小動畫
- ✅ 無障礙設計：對比度達標、觸控友善、可讀性佳

**智能特色**：
- ✅ 自動數據源：智能切換、無感降級、狀態提醒
- ✅ 個人化建議：基於計算結果、投資者輪廓、策略偏好
- ✅ 漸進載入：四階段反饋、計算進度、結果預覽
- ✅ 錯誤恢復：友善提示、自動重試、替代方案

---

### 3.8 技術規範完整性保證

#### 3.8.1 第1章技術規範集成確認

```python
CHAPTER1_INTEGRATION_CHECKLIST = {
    "data_precision": {
        "price_precision": "小數點後2位",
        "yield_precision": "小數點後4位", 
        "percentage_precision": "小數點後2位",
        "implementation": "所有UI組件強制精確度驗證"
    },
    "api_security": {
        "multilevel_keys": "背景自動管理",
        "fault_tolerance": "用戶控制的智能回退",
        "retry_mechanism": "智能重試策略",
        "backup_strategy": "模擬數據降級",
        "user_experience": "零感知切換"
    },
    "data_sources": {
        "tiingo_api": "SPY股票數據",
        "fred_api": "債券殖利率數據", 
        "simulation_engine": "幾何布朗運動+Vasicek模型",
        "quality_validation": "數據品質評分系統"
    },
    "trading_days": {
        "us_market_rules": "美股交易日規則",
        "holiday_adjustment": "假期調整機制",
        "period_calculation": "期初期末日期計算"
    }
}
```

#### 3.8.2 第2章技術規範集成確認

```python
CHAPTER2_INTEGRATION_CHECKLIST = {
    "core_formulas": {
        "va_target_value": "calculate_va_target_value函數保持不變",
        "dca_investment": "calculate_dca_investment函數保持不變",
        "parameter_conversion": "convert_annual_to_period_parameters保持不變",
        "ui_integration": "UI參數直接對應公式參數"
    },
    "table_structures": {
        "va_strategy": "27個欄位，VA_COLUMNS_ORDER",
        "dca_strategy": "28個欄位，DCA_COLUMNS_ORDER", 
        "summary_comparison": "8個欄位，SUMMARY_COLUMNS_ORDER",
        "csv_export": "格式一致性保證機制"
    },
    "performance_metrics": {
        "irr_calculation": "calculate_irr函數",
        "annualized_return": "calculate_enhanced_annualized_return函數（時間加權報酬率）",
        "sharpe_ratio": "3位小數精度",
        "max_drawdown": "calculate_max_drawdown函數"
    },
    "execution_logic": {
        "va_timing": "期末執行，第1期期初投入C0",
        "dca_timing": "期初執行，每期固定投入",
        "investment_sequence": "符合2.1.3.1投資時機規定"
    }
}
```

### 3.9 實作檢查清單

```python
IMPLEMENTATION_CHECKLIST = {
    "user_experience_goals": {
        "5_minute_onboarding": "✅ 新用戶能在5分鐘內完成第一次分析",
        "mobile_functionality": "✅ 手機端所有功能正常使用",
        "progressive_disclosure": "✅ 進階功能不干擾基本操作",
        "friendly_errors": "✅ 錯誤訊息對用戶友善",
        "loading_feedback": "✅ 載入過程有明確反饋",
        "clear_results": "✅ 結果展示一目了然"
    },
    "technical_compliance": {
        "chapter1_preserved": "✅ 第1章所有技術規範完整保留",
        "chapter2_preserved": "✅ 第2章所有計算公式保持不變",
        "function_compatibility": "✅ 所有函數調用保持相容性",
        "precision_standards": "✅ 精確度標準嚴格執行",
        "api_security": "✅ API安全機制背景運行",
        "data_quality": "✅ 數據品質驗證無感執行"
    },
    "design_quality": {
        "responsive_layout": "✅ 響應式布局完美適配各設備",
        "modern_aesthetics": "✅ 現代化視覺設計",
        "intuitive_navigation": "✅ 直觀的操作流程",
        "performance_optimized": "✅ 載入速度和響應速度優化",
        "accessibility": "✅ 無障礙設計符合標準"
    },
    "smart_features": {
        "user_controlled_data_source": "✅ 用戶控制的智能數據源選擇",
        "personalized_recommendations": "✅ 個人化投資建議",
        "progressive_loading": "✅ 漸進式載入與反饋",
        "error_recovery": "✅ 智能錯誤恢復機制"
    }
}
```

**策略說明卡片（依據第2章核心計算公式）**
```python
STRATEGY_INFO_CARDS = {
    "va_strategy": {
        "title": "VA策略 (Value Averaging)",
        "description": "根據預設成長率調整投資金額，資產價值低於目標時加碼，高於目標時減碼或賣出",
        "key_features": [
            "動態調整投資金額",
            "高買低賣機械操作", 
            "追求穩定成長軌跡",
            "對市場波動的反向操作"
        ],
        "formula_reference": "第2章 calculate_va_target_value 函數",
        "execution_timing": "各期末依第1章交易日調整規則執行",
        "price_precision": "符合第1章精確度設定（小數點後2位）",
        "color": "#3b82f6",
        "icon": "📈"
    },
    "dca_strategy": {
        "title": "DCA策略 (Dollar Cost Averaging)",
        "description": "定期定額投資固定金額，不論市場漲跌都持續買入，依靠時間分散成本",
        "key_features": [
            "固定投入金額",
            "僅有買入操作",
            "簡單易執行",
            "長期平均成本"
        ],
        "formula_reference": "第2章 calculate_dca_investment 和 calculate_dca_cumulative_investment 函數",
        "execution_timing": "各期期初依第1章交易日調整規則執行",
        "price_precision": "符合第1章精確度設定（小數點後2位）",
        "color": "#f59e0b", 
        "icon": "💰"
    },
    # 第1-2章技術規範整合驗證
    "strategy_validation": {
        "chapter1_compliance": {
            "trading_day_adjustment": True,
            "price_precision_check": True,
            "api_data_source_validation": True
        },
        "chapter2_compliance": {
            "formula_accuracy_check": True,
            "execution_timing_validation": True,
            "table_structure_consistency": True
        }
    }
}
```

## 4. 資訊流邏輯(控制流與資料流整合) - 快速部署版

### 4.1 應用程式啟動流程（簡化版）

#### 4.1.1 基本初始化序列
```python
def simple_app_initialization():
    """簡化版應用程式啟動初始化"""
    # 1. 基本日誌配置
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    logger.info("應用程式啟動")
    
    # 2. 環境變數檢查
    api_keys = {
        'tiingo': get_api_key('TIINGO_API_KEY'),
        'fred': get_api_key('FRED_API_KEY')
    }
    
    # 3. 基本健康檢查
    if not any(api_keys.values()):
        logger.warning("未檢測到API金鑰，將使用模擬數據")
    
    # 4. Streamlit配置
    st.set_page_config(
        page_title="投資策略比較系統",
        page_icon="📈",
        layout="wide"
    )
    
    logger.info("應用程式初始化完成")
    return api_keys

def get_api_key(key_name: str) -> str:
    """簡化版API金鑰獲取"""
    # 優先順序：Streamlit Secrets > 環境變數
    try:
        return st.secrets[key_name]
    except:
        return os.getenv(key_name, '')
```

#### 4.1.2 錯誤處理機制
```python
import logging
from enum import Enum
from typing import Optional, Dict, Any

class ErrorSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class SystemError(Exception):
    """系統級錯誤"""
    pass

def error_handling_flow():
    """統一錯誤處理流程"""
    logger = get_logger(__name__)
    
    try:
        # API連接測試
        api_status = test_api_connectivity_comprehensive()
        
        if not api_status['tiingo']['healthy']:
            handle_api_error('tiingo', api_status['tiingo'], ErrorSeverity.HIGH)
        
        if not api_status['fred']['healthy']:
            handle_api_error('fred', api_status['fred'], ErrorSeverity.MEDIUM)
            
    except APIConnectionError as e:
        logger.error(f"API連接錯誤: {str(e)}")
        # 啟用離線模式或備用數據源
        fallback_success = activate_fallback_mode()
        if fallback_success:
            display_warning_message("已切換至離線模式，部分功能可能受限")
        else:
            display_error_message("無法建立數據連接，請檢查網路設定")
            
    except SystemError as e:
        logger.critical(f"系統錯誤: {str(e)}")
        display_critical_error_message(str(e))
        
    except Exception as e:
        # 記錄詳細錯誤資訊
        error_context = {
            'error_type': type(e).__name__,
            'error_message': str(e),
            'user_action': get_current_user_action(),
            'system_state': get_system_state_snapshot()
        }
        
        logger.error(f"未預期錯誤: {error_context}")
        
        # 根據錯誤嚴重程度決定處理方式
        severity = assess_error_severity(e)
        handle_error_by_severity(e, severity, error_context)

def handle_api_error(api_name: str, error_info: Dict, severity: ErrorSeverity):
    """處理API錯誤"""
    logger = get_logger(__name__)
    
    if severity == ErrorSeverity.CRITICAL:
        logger.critical(f"{api_name} API完全不可用: {error_info}")
        st.error(f"❌ {api_name} 服務不可用，系統將使用備用數據")
    elif severity == ErrorSeverity.HIGH:
        logger.error(f"{api_name} API錯誤: {error_info}")
        st.warning(f"⚠️ {api_name} 服務異常，正在嘗試備用方案")
    else:
        logger.warning(f"{api_name} API警告: {error_info}")
        st.info(f"ℹ️ {api_name} 服務回應較慢，請稍候")

def get_logger(name: str) -> logging.Logger:
    """獲取配置好的日誌記錄器"""
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger
```

### 4.2 主要業務流程

#### 4.2.1 參數驗證與計算流程
```python
import time
from contextlib import contextmanager
from typing import Optional, Dict, Any

@contextmanager
def performance_monitor(operation_name: str):
    """效能監控上下文管理器"""
    logger = get_logger(__name__)
    start_time = time.time()
    
    try:
        logger.info(f"開始執行: {operation_name}")
        yield
    finally:
        end_time = time.time()
        duration = end_time - start_time
        logger.info(f"完成執行: {operation_name}, 耗時: {duration:.2f}秒")
        
        # 記錄效能指標
        record_performance_metric(operation_name, duration)

def main_calculation_flow() -> Optional[Dict[str, Any]]:
    """主要計算流程控制"""
    logger = get_logger(__name__)
    
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
                market_data = get_market_data_with_retry(user_params)
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

def calculate_strategies_parallel(market_data, user_params):
    """並行計算策略"""
    import concurrent.futures
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        # 提交並行任務
        va_future = executor.submit(calculate_va_strategy_safe, market_data, user_params)
        dca_future = executor.submit(calculate_dca_strategy_safe, market_data, user_params)
        
        # 等待結果
        try:
            va_results = va_future.result(timeout=30)  # 30秒超時
            dca_results = dca_future.result(timeout=30)
            return va_results, dca_results
        except concurrent.futures.TimeoutError:
            logger.error("策略計算超時")
            return None, None

def calculate_va_strategy_safe(market_data, user_params):
    """安全的VA策略計算"""
    try:
        return calculate_va_strategy(market_data, user_params)
    except Exception as e:
        logger.error(f"VA策略計算錯誤: {str(e)}")
        return None

def calculate_dca_strategy_safe(market_data, user_params):
    """安全的DCA策略計算"""
    try:
        return calculate_dca_strategy(market_data, user_params)
    except Exception as e:
        logger.error(f"DCA策略計算錯誤: {str(e)}")
        return None
```

#### 4.2.2 數據獲取流程 (優化版 - 目標日期批次獲取)
```python
import hashlib
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
import pandas as pd

def data_acquisition_flow(params) -> Optional[Dict[str, Any]]:
    """優化版數據獲取流程控制 - 基於目標日期批次獲取"""
    logger = get_logger(__name__)
    
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
        logger.info(f"快取失效，獲取新數據 - 場景: {params.scenario}")
        
        with performance_monitor("數據獲取"):
            if params.scenario == "historical":
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
            'source': params.scenario
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
    """優化版歷史數據獲取 - 基於目標日期批次獲取"""
    logger = get_logger(__name__)
    
    try:
        # 步驟1: 計算所有期初/期末目標日期
        target_dates = calculate_target_dates(
            start_date=params.start_date,
            frequency=params.frequency,
            periods=params.periods
        )
        
        logger.info(f"計算目標日期: {len(target_dates)}個期間，共{len(target_dates)*2}個目標日期")
        
        # 步驟2: 調整為有效交易日
        adjusted_dates = adjust_to_trading_days(target_dates)
        
        # 步驟3: 確定API調用的日期範圍
        api_start_date = min(adjusted_dates['period_starts'] + adjusted_dates['period_ends'])
        api_end_date = max(adjusted_dates['period_starts'] + adjusted_dates['period_ends'])
        
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
        
        logger.info(f"成功提取{len(market_data)}個期間的目標日期數據")
        return market_data
        
    except Exception as e:
        logger.error(f"優化版歷史數據獲取錯誤: {str(e)}")
        return None

def calculate_target_dates(start_date: datetime, frequency: str, periods: int) -> Dict[str, List[datetime]]:
    """計算所有期初/期末目標日期"""
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

def adjust_to_trading_days(target_dates: Dict[str, List[datetime]]) -> Dict[str, List[datetime]]:
    """將目標日期調整為最近的有效交易日"""
    from pandas.tseries.holiday import USFederalHolidayCalendar
    from pandas.tseries.offsets import CustomBusinessDay
    
    # 美股交易日規則
    us_bd = CustomBusinessDay(calendar=USFederalHolidayCalendar())
    
    adjusted_starts = []
    adjusted_ends = []
    
    # 調整期初日期（向後找最近交易日）
    for date in target_dates['period_starts']:
        # 如果是交易日則使用原日期，否則找下一個交易日
        if pd.Timestamp(date).weekday() < 5:  # 週一到週五
            adjusted_date = pd.Timestamp(date) + us_bd * 0  # 驗證是否為交易日
        else:
            adjusted_date = pd.Timestamp(date) + us_bd * 1  # 下一個交易日
        adjusted_starts.append(adjusted_date.to_pydatetime())
    
    # 調整期末日期（向前找最近交易日）
    for date in target_dates['period_ends']:
        # 如果是交易日則使用原日期，否則找前一個交易日
        if pd.Timestamp(date).weekday() < 5:  # 週一到週五
            adjusted_date = pd.Timestamp(date) + us_bd * 0  # 驗證是否為交易日
        else:
            adjusted_date = pd.Timestamp(date) - us_bd * 1  # 前一個交易日
        adjusted_ends.append(adjusted_date.to_pydatetime())
    
    return {
        'period_starts': adjusted_starts,
        'period_ends': adjusted_ends
    }

def fetch_tiingo_data_batch(start_date: datetime, end_date: datetime, max_retries=3):
    """批次獲取Tiingo數據 - 一次性獲取完整日期範圍"""
    for attempt in range(max_retries):
        try:
            return fetch_tiingo_data_range(start_date, end_date)
        except Exception as e:
            if attempt == max_retries - 1:
                raise e
            time.sleep(2 ** attempt)  # 指數退避

def fetch_fred_data_batch(start_date: datetime, end_date: datetime, max_retries=3):
    """批次獲取FRED數據 - 一次性獲取完整日期範圍"""
    for attempt in range(max_retries):
        try:
            return fetch_fred_data_range(start_date, end_date)
        except Exception as e:
            if attempt == max_retries - 1:
                raise e
            time.sleep(2 ** attempt)  # 指數退避

def extract_target_date_data(stock_data_full: pd.DataFrame, bond_data_full: pd.DataFrame, 
                           adjusted_dates: Dict[str, List[datetime]]) -> Dict[str, Any]:
    """從完整數據中提取目標日期的數據點"""
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
    """從數據中獲取最接近目標日期的價格"""
    # 將目標日期轉換為字符串格式
    target_str = target_date.strftime('%Y-%m-%d')
    
    # 尋找最接近的日期
    data['date_diff'] = abs(pd.to_datetime(data['date']) - pd.to_datetime(target_str))
    closest_idx = data['date_diff'].idxmin()
    
    return data.loc[closest_idx, 'price']

def generate_cache_key_enhanced(params) -> str:
    """生成增強版快取鍵"""
    # 包含更多參數以確保快取準確性
    cache_params = {
        'scenario': params.scenario,
        'start_date': getattr(params, 'start_date', None),
        'end_date': getattr(params, 'end_date', None),
        'frequency': params.frequency,
        'stock_ratio': getattr(params, 'stock_ratio', None),
        'simulation_params': getattr(params, 'simulation_params', None)
    }
    
    # 移除None值
    cache_params = {k: v for k, v in cache_params.items() if v is not None}
    
    # 生成哈希
    params_str = json.dumps(cache_params, sort_keys=True, default=str)
    return hashlib.md5(params_str.encode()).hexdigest()

def assess_data_quality(data) -> float:
    """評估數據品質分數 (0-1)"""
    if data is None:
        return 0.0
    
    score = 1.0
    
    # 檢查數據完整性
    if len(data) == 0:
        return 0.0
    
    # 檢查缺失值
    missing_ratio = data.isnull().sum().sum() / (data.shape[0] * data.shape[1])
    score -= missing_ratio * 0.3
    
    # 檢查數據連續性
    date_gaps = check_date_continuity(data)
    score -= date_gaps * 0.2
    
    # 檢查異常值
    outlier_ratio = detect_outliers(data)
    score -= outlier_ratio * 0.1
    
    return max(0.0, min(1.0, score))
```

### 4.3 狀態管理與快取策略

#### 4.3.1 應用程式狀態管理
```python
def state_management():
    """Streamlit狀態管理"""
    
    # 初始化狀態
    if 'calculation_results' not in st.session_state:
        st.session_state.calculation_results = None
    
    if 'last_params' not in st.session_state:
        st.session_state.last_params = None
    
    # 參數變更檢測
    current_params = get_current_parameters()
    
    if params_changed(current_params, st.session_state.last_params):
        # 觸發重新計算
        st.session_state.calculation_results = main_calculation_flow()
        st.session_state.last_params = current_params
        st.rerun()
```

#### 4.3.2 快取策略
```python
import pickle
from datetime import datetime, timedelta
from typing import Any, Optional

class CacheManager:
    """快取管理器"""
    
    def __init__(self):
        self.cache_stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0
        }
    
    def get_cache_hit_ratio(self) -> float:
        """獲取快取命中率"""
        total = self.cache_stats['hits'] + self.cache_stats['misses']
        return self.cache_stats['hits'] / total if total > 0 else 0.0

# 增強的快取裝飾器
@st.cache_data(
    ttl=86400,  # 24小時TTL
    max_entries=100,  # 最大快取條目數
    show_spinner="正在獲取市場數據...",
    persist="disk"  # 持久化到磁碟
)
def cached_market_data(start_date: str, end_date: str, scenario: str) -> Optional[Dict]:
    """市場數據快取"""
    logger = get_logger(__name__)
    
    try:
        if scenario == "historical":
            data = fetch_market_data_comprehensive(start_date, end_date)
        else:
            data = generate_simulation_data_comprehensive(scenario)
        
        # 添加快取元數據
        return {
            'data': data,
            'cached_at': datetime.now().isoformat(),
            'data_source': scenario,
            'quality_score': assess_data_quality(data)
        }
    except Exception as e:
        logger.error(f"市場數據快取錯誤: {str(e)}")
        return None

@st.cache_data(
    ttl=3600,  # 1小時TTL，計算結果變化較頻繁
    max_entries=50,
    show_spinner="正在計算策略結果..."
)
def cached_strategy_calculation(
    market_data_hash: str, 
    params_hash: str,
    calculation_type: str
) -> Optional[Dict]:
    """策略計算結果快取"""
    logger = get_logger(__name__)
    
    try:
        # 根據計算類型執行相應策略
        if calculation_type == "va":
            results = calculate_va_strategy_from_hash(market_data_hash, params_hash)
        elif calculation_type == "dca":
            results = calculate_dca_strategy_from_hash(market_data_hash, params_hash)
        else:
            raise ValueError(f"未知計算類型: {calculation_type}")
        
        return {
            'results': results,
            'calculated_at': datetime.now().isoformat(),
            'calculation_duration': getattr(results, 'duration', 0),
            'data_hash': market_data_hash,
            'params_hash': params_hash
        }
    except Exception as e:
        logger.error(f"策略計算快取錯誤: {str(e)}")
        return None

@st.cache_data(ttl=300)  # 5分鐘TTL，效能指標更新較頻繁
def cached_performance_metrics(va_hash: str, dca_hash: str) -> Optional[Dict]:
    """績效指標快取"""
    try:
        metrics = calculate_performance_metrics_from_hash(va_hash, dca_hash)
        return {
            'metrics': metrics,
            'calculated_at': datetime.now().isoformat()
        }
    except Exception as e:
        logger = get_logger(__name__)
        logger.error(f"績效指標快取錯誤: {str(e)}")
        return None

def intelligent_cache_invalidation():
    """智能快取失效"""
    logger = get_logger(__name__)
    
    # 檢查並清理過期快取
    expired_keys = find_expired_cache_keys()
    for key in expired_keys:
        st.cache_data.clear()
        logger.info(f"清理過期快取: {key[:16]}...")
    
    # 檢查快取大小，必要時進行LRU清理
    cache_size = get_cache_size()
    if cache_size > MAX_CACHE_SIZE:
        perform_lru_cleanup()
        logger.info(f"執行LRU快取清理，釋放空間: {cache_size - get_cache_size()}MB")

def cache_warming():
    """快取預熱"""
    logger = get_logger(__name__)
    
    # 預加載常用的市場數據
    common_scenarios = [
        ("2020-01-01", "2023-12-31", "historical"),
        ("2018-01-01", "2023-12-31", "historical")
    ]
    
    for start_date, end_date, scenario in common_scenarios:
        try:
            cached_market_data(start_date, end_date, scenario)
            logger.info(f"預熱快取: {scenario} {start_date}-{end_date}")
        except Exception as e:
            logger.warning(f"快取預熱失敗: {str(e)}")

# 快取統計監控
def get_cache_statistics() -> Dict[str, Any]:
    """獲取快取統計資訊"""
    try:
        cache_info = st.cache_data.get_stats()
        return {
            'hit_ratio': cache_info.get('hit_ratio', 0),
            'total_entries': cache_info.get('total_entries', 0),
            'memory_usage': cache_info.get('memory_usage', 0),
            'last_cleanup': cache_info.get('last_cleanup', 'Never')
        }
    except:
        return {'status': 'unavailable'}
```

### 4.4 簡化資料流整合

#### 4.4.1 基本資料流程
```
[用戶輸入] → [基本驗證] → [數據獲取] → [策略計算] → [結果顯示]
```

#### 4.4.2 基本錯誤恢復
```python
def basic_error_recovery():
    """基本錯誤恢復機制"""
    fallback_methods = [
        ("歷史數據API", lambda: fetch_historical_data_simple),
        ("模擬數據", lambda: generate_simulation_data_simple)
    ]
    
    for method_name, method_func in fallback_methods:
        try:
            result = method_func()
            if result:
                st.info(f"使用 {method_name}")
                return result
        except:
            continue
    
    st.error("所有數據源都無法使用")
    return None

### 4.5 部署配置（簡化版）

#### 4.5.1 Streamlit Cloud 快速部署

**必要文件清單**
```
app.py                    # 主應用程式
requirements.txt          # 套件依賴
.streamlit/config.toml   # 基本配置
.streamlit/secrets.toml  # API金鑰（本地開發用）
.gitignore               # 版本控制排除
README.md                # 說明文件
```

**簡化的 requirements.txt**
```
streamlit>=1.28.0
pandas>=1.5.0
numpy>=1.21.0
requests>=2.25.0
plotly>=5.0.0
```

**簡化的 .streamlit/config.toml**
```toml
[server]
headless = true
enableCORS = false

[browser]
gatherUsageStats = false

[theme]
primaryColor = "#FF6B6B"
backgroundColor = "#FFFFFF"
```

#### 4.5.2 部署前檢查（簡化版）
```python
def quick_deployment_check():
    """快速部署檢查"""
    issues = []
    
    # 檢查必要文件
    required_files = ['app.py', 'requirements.txt']
    for file in required_files:
        if not Path(file).exists():
            issues.append(f"❌ 缺少 {file}")
    
    # 檢查基本導入
    try:
        import streamlit, pandas, numpy, requests
        issues.append("✅ 基本套件可用")
    except ImportError as e:
        issues.append(f"❌ 套件導入錯誤: {e}")
    
    # 檢查API金鑰（警告但不阻止）
    if not (get_api_key('TIINGO_API_KEY') or get_api_key('FRED_API_KEY')):
        issues.append("⚠️  未設定API金鑰，將使用模擬數據")
    else:
        issues.append("✅ API金鑰已設定")
    
         return issues

### 4.6 主應用程式架構（簡化版）

```python
# app.py - 簡化版主程式架構
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import requests
import os

def main():
    """主應用程式函數"""
    
    # 初始化
    api_keys = simple_app_initialization()
    
    # 側邊欄輸入控件
    render_sidebar_controls()
    
    # 主內容區域
    render_main_content()
    
    # 狀態管理
    simple_state_management()

def render_sidebar_controls():
    """渲染側邊欄控件（簡化版）"""
    st.sidebar.header("📊 投資參數設定")
    
    # 基本投資參數
    st.sidebar.number_input("初始投資金額", 
                           min_value=1000, max_value=1000000, 
                           value=10000, step=1000,
                           key='initial_investment')
    
    st.sidebar.number_input("每月投資金額", 
                           min_value=100, max_value=50000, 
                           value=1000, step=100,
                           key='monthly_investment')
    
    st.sidebar.slider("投資年數", 
                     min_value=1, max_value=30, 
                     value=10, step=1,
                     key='investment_years')
    
    st.sidebar.slider("股票比例", 
                     min_value=0.0, max_value=1.0, 
                     value=0.8, step=0.1,
                     key='stock_ratio')
    
    # 情境選擇
    st.sidebar.selectbox("數據情境", 
                        options=['historical', 'bull_market', 'bear_market'],
                        format_func=lambda x: {'historical': '歷史數據', 
                                              'bull_market': '牛市模擬', 
                                              'bear_market': '熊市模擬'}[x],
                        key='scenario')

def render_main_content():
    """渲染主內容區域（簡化版）"""
    st.title("📈 投資策略比較系統")
    st.markdown("比較 **定期定值 (VA)** 與 **定期定額 (DCA)** 投資策略")
    
    # 顯示結果
    if st.session_state.get('results'):
        display_results_simple(st.session_state.results)
    else:
        st.info("👈 請在左側設定投資參數，然後點擊「開始分析」")

def display_results_simple(results):
    """顯示結果（簡化版）"""
    
    # 基本指標卡片
    col1, col2, col3 = st.columns(3)
    
    with col1:
        va_final = results['va_results']['final_value']
        st.metric("VA策略最終價值", f"${va_final:,.0f}")
    
    with col2:
        dca_final = results['dca_results']['final_value']
        st.metric("DCA策略最終價值", f"${dca_final:,.0f}")
    
    with col3:
        difference = va_final - dca_final
        st.metric("VA vs DCA差異", f"${difference:,.0f}", 
                 delta=f"{difference/dca_final*100:.1f}%")
    
    # 簡化圖表
    if 'chart_data' in results:
        st.subheader("📊 投資成長趨勢")
        st.line_chart(results['chart_data'])
    
    # 基本下載功能
    if st.button("下載結果 (CSV)"):
        csv_data = generate_simple_csv(results)
        st.download_button(
            label="💾 下載 CSV 檔案",
            data=csv_data,
            file_name=f"investment_analysis_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )

@simple_error_handler
def simplified_calculation_flow(user_params):
    """簡化版計算流程"""
    
    # Step 1: 參數驗證
    if not validate_basic_parameters(user_params):
        st.error("參數設定有誤，請檢查輸入值")
        return None
    
    # Step 2: 數據獲取（帶進度提示）
    with st.spinner("正在獲取市場數據..."):
        market_data = get_market_data_simple(user_params)
        if not market_data:
            st.warning("數據獲取失敗，使用模擬數據")
            market_data = generate_simulation_data_simple(user_params)
    
    # Step 3: 策略計算
    with st.spinner("正在計算投資策略..."):
        va_results = calculate_va_strategy_simple(market_data, user_params)
        dca_results = calculate_dca_strategy_simple(market_data, user_params)
    
    # Step 4: 績效分析
    with st.spinner("正在分析績效指標..."):
        metrics = calculate_basic_metrics(va_results, dca_results)
    
    return {
        'va_results': va_results,
        'dca_results': dca_results,
        'metrics': metrics,
        'market_data': market_data
    }

def simple_state_management():
    """簡化版狀態管理"""
    
    # 初始化基本狀態
    if 'results' not in st.session_state:
        st.session_state.results = None
    
    if 'last_calculation_params' not in st.session_state:
        st.session_state.last_calculation_params = None
    
    # 檢查是否需要重新計算
    current_params = collect_user_parameters()
    
    if (st.session_state.last_calculation_params != current_params or 
        st.session_state.results is None):
        
        # 觸發重新計算
        if st.button("開始分析", type="primary"):
            st.session_state.results = simplified_calculation_flow(current_params)
            st.session_state.last_calculation_params = current_params
            st.rerun()

if __name__ == "__main__":
    main()
```

---

## 🚀 快速部署步驟總結

1. **保留核心功能**：基本計算、簡單UI、基礎快取
2. **移除複雜功能**：異步處理、詳細監控、複雜錯誤恢復
3. **簡化部署**：僅支援Streamlit Cloud，移除Docker配置
4. **降低依賴**：最小化套件需求，使用內建功能

這樣的簡化版本可以快速部署，同時保持系統的核心功能完整性。

---

## 📅 起始日期參數整合更新

### 參數獲取函數更新

```python
def get_all_parameters(self) -> Dict[str, Any]:
    """獲取所有參數值 - 供計算引擎使用，包含起始日期"""
    return {
        # 基本參數
        "initial_investment": st.session_state.initial_investment,
        "investment_start_date": st.session_state.get('investment_start_date', None),  # 新增起始日期
        "annual_investment": st.session_state.annual_investment,
        "investment_years": st.session_state.investment_years,
        "investment_frequency": st.session_state.investment_frequency,
        "stock_ratio": st.session_state.stock_ratio,
        "bond_ratio": 100 - st.session_state.stock_ratio,
        
        # 進階設定
        "va_growth_rate": st.session_state.va_growth_rate,
        "inflation_adjustment": st.session_state.inflation_adjustment,
        "inflation_rate": st.session_state.inflation_rate if st.session_state.inflation_adjustment else 0,
        "data_source_mode": st.session_state.get("data_source_mode", "auto"),
        
        # 計算衍生參數
        "total_periods": self._calculate_total_periods(),
        "periods_per_year": self._get_periods_per_year()
    }
```

### Session State 初始化更新

```python
def _initialize_session_state(self):
    """初始化Streamlit會話狀態 - 包含起始日期"""
    # 基本參數預設值
    if 'initial_investment' not in st.session_state:
        st.session_state.initial_investment = self.basic_params["initial_investment"]["default"]
    
    if 'investment_start_date' not in st.session_state:
        # 預設為次年1月1日
        from datetime import datetime
        current_year = datetime.now().year
        default_date = datetime(current_year + 1, 1, 1).date()
        st.session_state.investment_start_date = default_date
    
    if 'annual_investment' not in st.session_state:
        st.session_state.annual_investment = self.basic_params["annual_investment"]["default"]
    
    # ... 其他參數初始化保持不變
```

### 時間軸生成函數調用更新

```python
def _fetch_real_market_data(self, parameters: Dict[str, Any]) -> pd.DataFrame:
    """獲取真實市場數據 - 使用使用者指定的起始日期"""
    try:
        # 使用使用者指定的起始日期
        if parameters.get("investment_start_date"):
            start_date = parameters["investment_start_date"]
            if isinstance(start_date, str):
                start_date = datetime.strptime(start_date, '%Y-%m-%d')
            elif hasattr(start_date, 'date'):
                start_date = start_date.date()
            start_date = datetime.combine(start_date, datetime.min.time())
        else:
            # 回退到預設值
            current_year = datetime.now().year
            start_date = datetime(current_year + 1, 1, 1)
        
        # 計算結束日期
        total_periods = parameters["total_periods"]
        end_date = start_date + timedelta(days=total_periods * 30)
        
        # ... 其餘實現保持不變
```

這些更新確保起始日期參數完全整合到系統中，使用者可以靈活設定投資開始時間。