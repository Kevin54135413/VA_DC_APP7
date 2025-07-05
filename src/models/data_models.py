"""
投資策略比較系統 - 數據模型模組
實現第一章第1.3節規範中定義的所有核心數據結構類別

作者：VA_DC_APP7 系統
版本：1.0
日期：2025年
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List, Union
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
import logging
import pandas as pd
import numpy as np
from enum import Enum

# 配置日誌系統
from ..utils.logger import get_component_logger
logger = get_component_logger('DataModels')

# 精確度設定 - 根據需求文件第1章規範
class PrecisionConfig:
    """精確度配置類別 - 符合第1章精確度設定"""
    PRICE_PRECISION = 2          # 價格精度：小數點後2位（美元分）
    YIELD_PRECISION = 4          # 殖利率精度：小數點後4位（基點）
    PERCENTAGE_PRECISION = 2     # 比例精度：小數點後2位（百分比）
    UNITS_PRECISION = 4          # 單位數精度：小數點後4位
    CURRENCY_PRECISION = 2       # 貨幣精度：小數點後2位
    SHARPE_RATIO_PRECISION = 3   # 夏普比率精度：小數點後3位
    NUMERIC_TOLERANCE = 1e-6     # 數值容差：用於浮點數比較
    
    @staticmethod
    def round_price(value: float) -> float:
        """價格四捨五入到指定精度"""
        if value is None:
            return None
        return float(Decimal(str(value)).quantize(
            Decimal('0.' + '0' * PrecisionConfig.PRICE_PRECISION),
            rounding=ROUND_HALF_UP
        ))
    
    @staticmethod
    def round_yield(value: float) -> float:
        """殖利率四捨五入到指定精度"""
        if value is None:
            return None
        return float(Decimal(str(value)).quantize(
            Decimal('0.' + '0' * PrecisionConfig.YIELD_PRECISION),
            rounding=ROUND_HALF_UP
        ))
    
    @staticmethod
    def round_percentage(value: float) -> float:
        """百分比四捨五入到指定精度"""
        if value is None:
            return None
        return float(Decimal(str(value)).quantize(
            Decimal('0.' + '0' * PrecisionConfig.PERCENTAGE_PRECISION),
            rounding=ROUND_HALF_UP
        ))
    
    @staticmethod
    def round_units(value: float) -> float:
        """單位數四捨五入到指定精度"""
        if value is None:
            return None
        return float(Decimal(str(value)).quantize(
            Decimal('0.' + '0' * PrecisionConfig.UNITS_PRECISION),
            rounding=ROUND_HALF_UP
        ))
    
    @staticmethod
    def is_equal(value1: float, value2: float) -> bool:
        """
        使用數值容差進行浮點數比較
        
        Args:
            value1: 第一個數值
            value2: 第二個數值
            
        Returns:
            bool: 是否在容差範圍內相等
        """
        if value1 is None or value2 is None:
            return value1 == value2
        return abs(value1 - value2) < PrecisionConfig.NUMERIC_TOLERANCE
    
    @staticmethod
    def is_zero(value: float) -> bool:
        """
        檢查數值是否為零（在容差範圍內）
        
        Args:
            value: 要檢查的數值
            
        Returns:
            bool: 是否為零
        """
        if value is None:
            return False
        return abs(value) < PrecisionConfig.NUMERIC_TOLERANCE

# 錯誤處理機制
class DataValidationError(Exception):
    """數據驗證錯誤"""
    pass

class DataQualityError(Exception):
    """數據品質錯誤"""
    pass

class CalculationError(Exception):
    """計算錯誤"""
    pass

class ErrorSeverity(Enum):
    """錯誤嚴重程度"""
    LOW = "低"
    MEDIUM = "中"
    HIGH = "高"
    CRITICAL = "嚴重"

@dataclass
class ValidationResult:
    """驗證結果"""
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    data_quality_score: float = 100.0
    severity: ErrorSeverity = ErrorSeverity.LOW

# 核心數據模型類別

@dataclass
class MarketDataPoint:
    """
    單一市場數據點
    
    符合第1章第1.3節規範：
    - 價格精度：小數點後2位
    - 殖利率精度：小數點後4位
    - 嚴格數據驗證
    """
    date: str                      # YYYY-MM-DD 格式
    spy_price: float              # SPY 調整後收盤價（USD）
    bond_yield: Optional[float]   # 1年期國債殖利率（%）
    bond_price: Optional[float]   # 債券價格（USD）
    data_source: str              # 數據來源標識
    
    def __post_init__(self):
        """
        數據驗證與精確度處理
        實施第1章精確度設定和驗證邏輯
        """
        try:
            # 1. 日期格式驗證
            self._validate_date()
            
            # 2. 價格數據精確度處理與驗證
            self._process_price_precision()
            
            # 3. 債券數據精確度處理與驗證
            self._process_bond_precision()
            
            # 4. 數據源驗證
            self._validate_data_source()
            
            logger.debug(f"MarketDataPoint驗證成功: {self.date}")
            
        except Exception as e:
            error_msg = f"MarketDataPoint驗證失敗 {self.date}: {str(e)}"
            logger.error(error_msg)
            raise DataValidationError(error_msg) from e
    
    def _validate_date(self):
        """驗證日期格式"""
        try:
            datetime.strptime(self.date, '%Y-%m-%d')
        except ValueError:
            raise ValueError(f"日期格式錯誤: {self.date}，必須為 YYYY-MM-DD 格式")
    
    def _process_price_precision(self):
        """處理價格精確度"""
        # SPY價格驗證與精確度處理
        # 對於FRED數據源，允許SPY價格為0（因為FRED不提供股票數據）
        if self.spy_price < 0:
            raise ValueError(f"SPY價格不能為負數: {self.spy_price}")
        
        if self.spy_price == 0 and self.data_source not in ['fred', 'backup']:
            raise ValueError(f"SPY價格必須為正數: {self.spy_price}")
        
        # 應用價格精確度設定
        self.spy_price = PrecisionConfig.round_price(self.spy_price)
        
        # 合理範圍檢查（SPY歷史價格範圍）- 僅對非零價格檢查
        if self.spy_price > 0 and not (10.0 <= self.spy_price <= 1000.0):
            logger.warning(f"SPY價格超出常見範圍: {self.spy_price}")
    
    def _process_bond_precision(self):
        """處理債券數據精確度"""
        if self.bond_yield is not None:
            # 債券殖利率精確度處理
            self.bond_yield = PrecisionConfig.round_yield(self.bond_yield)
            
            # 合理範圍檢查
            if not (-5.0 <= self.bond_yield <= 25.0):
                raise ValueError(f"債券殖利率超出合理範圍: {self.bond_yield}%")
        
        if self.bond_price is not None:
            # 債券價格精確度處理
            self.bond_price = PrecisionConfig.round_price(self.bond_price)
            
            # 合理範圍檢查
            if not (50.0 <= self.bond_price <= 200.0):
                raise ValueError(f"債券價格超出合理範圍: {self.bond_price}")
    
    def _validate_data_source(self):
        """驗證數據源"""
        valid_sources = {'tiingo', 'fred', 'simulation', 'backup', 'yahoo', 'csv'}
        if self.data_source not in valid_sources:
            raise ValueError(f"無效的數據源: {self.data_source}")
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典格式"""
        return {
            'date': self.date,
            'spy_price': self.spy_price,
            'bond_yield': self.bond_yield,
            'bond_price': self.bond_price,
            'data_source': self.data_source
        }

@dataclass 
class AggregatedPeriodData:
    """
    聚合期間數據
    
    符合第1章第1.3節規範：
    - 期間數據聚合邏輯
    - 報酬率計算精確度
    - 數據品質評分機制
    """
    period: int                             # 期數
    start_date: str                        # 期初日期
    end_date: str                          # 期末日期
    spy_price_start: float                 # 期初SPY價格
    spy_price_end: float                   # 期末SPY價格
    bond_yield_start: Optional[float]      # 期初債券殖利率
    bond_yield_end: Optional[float]        # 期末債券殖利率
    bond_price_start: Optional[float]      # 期初債券價格
    bond_price_end: Optional[float]        # 期末債券價格
    trading_days: int                      # 期間交易日數
    period_return: float = 0.0             # 期間報酬率
    data_quality_score: float = 100.0      # 數據品質分數
    volatility: Optional[float] = None     # 期間價格波動率（標準差）
    average_price: Optional[float] = None  # 期間平均價格
    
    def __post_init__(self):
        """數據驗證與計算"""
        try:
            self._validate_period_data()
            self._apply_precision()
            self.period_return = self.calculate_period_return()
            logger.debug(f"AggregatedPeriodData創建成功: 期間{self.period}")
        except Exception as e:
            error_msg = f"AggregatedPeriodData驗證失敗 期間{self.period}: {str(e)}"
            logger.error(error_msg)
            raise DataValidationError(error_msg) from e
    
    def _validate_period_data(self):
        """驗證期間數據"""
        if self.period <= 0:
            raise ValueError(f"期數必須為正整數: {self.period}")
        
        if self.trading_days <= 0:
            raise ValueError(f"交易日數必須為正整數: {self.trading_days}")
        
        if self.spy_price_start <= 0 or self.spy_price_end <= 0:
            raise ValueError("SPY價格必須為正數")
    
    def _apply_precision(self):
        """應用精確度設定"""
        self.spy_price_start = PrecisionConfig.round_price(self.spy_price_start)
        self.spy_price_end = PrecisionConfig.round_price(self.spy_price_end)
        
        if self.bond_yield_start is not None:
            self.bond_yield_start = PrecisionConfig.round_yield(self.bond_yield_start)
        if self.bond_yield_end is not None:
            self.bond_yield_end = PrecisionConfig.round_yield(self.bond_yield_end)
        
        if self.bond_price_start is not None:
            self.bond_price_start = PrecisionConfig.round_price(self.bond_price_start)
        if self.bond_price_end is not None:
            self.bond_price_end = PrecisionConfig.round_price(self.bond_price_end)
        
        # 新增欄位的精確度處理
        if self.volatility is not None:
            self.volatility = PrecisionConfig.round_percentage(self.volatility)
        if self.average_price is not None:
            self.average_price = PrecisionConfig.round_price(self.average_price)
    
    def calculate_period_return(self) -> float:
        """
        計算期間報酬率
        公式：(期末價格 / 期初價格) - 1
        """
        if self.spy_price_start <= 0:
            logger.warning(f"期間{self.period}期初價格為零，返回0報酬率")
            return 0.0
        
        period_return = (self.spy_price_end / self.spy_price_start) - 1.0
        return PrecisionConfig.round_percentage(period_return)
    
    def calculate_data_quality_score(self) -> float:
        """計算數據品質分數"""
        score = 100.0
        
        # 價格數據完整性
        if self.spy_price_start <= 0 or self.spy_price_end <= 0:
            score -= 30
        
        # 債券數據完整性
        if self.bond_yield_start is None or self.bond_yield_end is None:
            score -= 10
        
        # 交易日數合理性
        if self.trading_days < 15:  # 少於15個交易日視為不完整
            score -= 20
        
        return max(0.0, PrecisionConfig.round_percentage(score))

@dataclass
class StrategyResult:
    """
    策略計算結果
    
    符合第1章第1.3節規範：
    - 完整的投資組合追蹤
    - 精確的金額計算
    - 報酬率計算邏輯
    """
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
    strategy_specific: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """計算驗證與精確度處理"""
        try:
            self._apply_precision()
            self._calculate_derived_values()
            self._validate_calculations()
            logger.debug(f"StrategyResult創建成功: 期間{self.period}")
        except Exception as e:
            error_msg = f"StrategyResult計算失敗 期間{self.period}: {str(e)}"
            logger.error(error_msg)
            raise CalculationError(error_msg) from e
    
    def _apply_precision(self):
        """應用精確度設定"""
        # 價格精確度
        self.spy_price_origin = PrecisionConfig.round_price(self.spy_price_origin)
        if self.bond_yield_origin is not None:
            self.bond_yield_origin = PrecisionConfig.round_yield(self.bond_yield_origin)
        if self.bond_price_origin is not None:
            self.bond_price_origin = PrecisionConfig.round_price(self.bond_price_origin)
        
        # 金額精確度
        self.stock_investment = PrecisionConfig.round_price(self.stock_investment)
        self.cum_stock_investment = PrecisionConfig.round_price(self.cum_stock_investment)
        self.bond_investment = PrecisionConfig.round_price(self.bond_investment)
        self.cum_bond_investment = PrecisionConfig.round_price(self.cum_bond_investment)
        self.stock_value = PrecisionConfig.round_price(self.stock_value)
        self.bond_value = PrecisionConfig.round_price(self.bond_value)
        
        # 單位數精確度
        self.stock_units_purchased = PrecisionConfig.round_units(self.stock_units_purchased)
        self.cum_stock_units = PrecisionConfig.round_units(self.cum_stock_units)
        self.bond_units_purchased = PrecisionConfig.round_units(self.bond_units_purchased)
        self.cum_bond_units = PrecisionConfig.round_units(self.cum_bond_units)
    
    def _calculate_derived_values(self):
        """計算衍生值"""
        self.total_investment = self.stock_investment + self.bond_investment
        self.cum_total_investment = self.cum_stock_investment + self.cum_bond_investment
        self.total_value = self.calculate_total_value()
        self.unrealized_gain_loss = self.total_value - self.cum_total_investment
        self.unrealized_return = self.calculate_unrealized_return()
        
        # 應用精確度
        self.total_investment = PrecisionConfig.round_price(self.total_investment)
        self.cum_total_investment = PrecisionConfig.round_price(self.cum_total_investment)
        self.total_value = PrecisionConfig.round_price(self.total_value)
        self.unrealized_gain_loss = PrecisionConfig.round_price(self.unrealized_gain_loss)
        self.unrealized_return = PrecisionConfig.round_percentage(self.unrealized_return)
    
    def _validate_calculations(self):
        """驗證計算結果"""
        if self.cum_total_investment < 0:
            raise ValueError("累計投資金額不能為負數")
        
        if self.total_value < 0:
            raise ValueError("總市值不能為負數")
        
        # 驗證總市值計算一致性（使用NUMERIC_TOLERANCE進行精確比較）
        calculated_total = self.stock_value + self.bond_value
        if not PrecisionConfig.is_equal(self.total_value, calculated_total):
            raise ValueError(f"總市值計算不一致: {self.total_value} vs {calculated_total}")
        
        # 驗證單位數和價格的一致性
        if self.cum_stock_units > 0:
            calculated_stock_value = self.cum_stock_units * self.spy_price_origin
            if not PrecisionConfig.is_equal(self.stock_value, calculated_stock_value):
                logger.warning(f"股票市值計算可能不一致: {self.stock_value} vs {calculated_stock_value}")
        
        if self.cum_bond_units > 0 and self.bond_price_origin is not None:
            calculated_bond_value = self.cum_bond_units * self.bond_price_origin
            if not PrecisionConfig.is_equal(self.bond_value, calculated_bond_value):
                logger.warning(f"債券市值計算可能不一致: {self.bond_value} vs {calculated_bond_value}")
    
    def calculate_total_value(self) -> float:
        """計算總市值"""
        return self.stock_value + self.bond_value
    
    def calculate_unrealized_return(self) -> float:
        """計算未實現報酬率"""
        if self.cum_total_investment <= 0:
            return 0.0
        return (self.total_value / self.cum_total_investment) - 1.0

class DataModelFactory:
    """
    數據模型工廠
    
    符合第1章第1.3節規範：
    - 統一數據創建介面
    - API回應解析
    - 數據聚合邏輯
    - 錯誤處理機制
    """
    
    @staticmethod
    def create_market_data_from_api(api_response: Dict, source: str) -> List[MarketDataPoint]:
        """
        從API回應創建市場數據
        
        Args:
            api_response: API回應數據
            source: 數據源標識
            
        Returns:
            MarketDataPoint列表
            
        Raises:
            DataValidationError: 數據格式錯誤
        """
        try:
            data_points = []
            
            if source == 'tiingo':
                data_points = DataModelFactory._parse_tiingo_response(api_response)
            elif source == 'fred':
                data_points = DataModelFactory._parse_fred_response(api_response)
            else:
                raise ValueError(f"不支援的數據源: {source}")
            
            logger.info(f"成功創建 {len(data_points)} 個 {source} 數據點")
            return data_points
            
        except Exception as e:
            error_msg = f"API數據解析失敗 {source}: {str(e)}"
            logger.error(error_msg)
            raise DataValidationError(error_msg) from e
    
    @staticmethod
    def _parse_tiingo_response(api_response: Dict) -> List[MarketDataPoint]:
        """解析Tiingo API回應"""
        data_points = []
        
        for item in api_response:
            date_str = item['date'][:10]  # 取YYYY-MM-DD部分
            
            data_point = MarketDataPoint(
                date=date_str,
                spy_price=float(item['adjClose']),
                bond_yield=None,
                bond_price=None,
                data_source='tiingo'
            )
            data_points.append(data_point)
            
        return data_points
    
    @staticmethod
    def _parse_fred_response(api_response: Dict) -> List[MarketDataPoint]:
        """解析FRED API回應"""
        data_points = []
        
        for obs in api_response.get('observations', []):
            if obs['value'] != '.':  # FRED用'.'表示缺失值
                yield_rate = float(obs['value'])
                bond_price = 100.0 / (1 + yield_rate/100) if yield_rate > 0 else 100.0
                
                data_point = MarketDataPoint(
                    date=obs['date'],
                    spy_price=0.0,  # FRED不提供股票價格
                    bond_yield=yield_rate,
                    bond_price=bond_price,
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
        """
        將日線數據聚合為投資期間數據
        
        Args:
            market_data: 市場數據列表
            frequency: 投資頻率
            investment_years: 投資年數
            
        Returns:
            AggregatedPeriodData列表
        """
        try:
            if not market_data:
                raise ValueError("市場數據為空")
            
            # 頻率映射
            periods_per_year = {
                'monthly': 12,
                'quarterly': 4,
                'semi-annually': 2,
                'annually': 1
            }
            
            if frequency not in periods_per_year:
                raise ValueError(f"不支援的投資頻率: {frequency}")
            
            total_periods = investment_years * periods_per_year[frequency]
            
            # 轉換為DataFrame
            df = pd.DataFrame([dp.to_dict() for dp in market_data])
            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values('date').reset_index(drop=True)
            
            # 聚合數據
            aggregated_data = []
            
            for period in range(1, total_periods + 1):
                period_data = DataModelFactory._extract_period_data(df, period, total_periods)
                
                if len(period_data) > 0:
                    aggregated_period = DataModelFactory._create_aggregated_period(
                        period_data, period
                    )
                    aggregated_data.append(aggregated_period)
            
            logger.info(f"成功聚合 {len(aggregated_data)} 個期間數據")
            return aggregated_data
            
        except Exception as e:
            error_msg = f"數據聚合失敗: {str(e)}"
            logger.error(error_msg)
            raise DataQualityError(error_msg) from e
    
    @staticmethod
    def _extract_period_data(df: pd.DataFrame, period: int, total_periods: int) -> pd.DataFrame:
        """提取期間數據"""
        period_start_idx = (period - 1) * len(df) // total_periods
        period_end_idx = min(period * len(df) // total_periods - 1, len(df) - 1)
        
        return df.iloc[period_start_idx:period_end_idx + 1]
    
    @staticmethod
    def _create_aggregated_period(period_data: pd.DataFrame, period: int) -> AggregatedPeriodData:
        """創建聚合期間數據"""
        start_row = period_data.iloc[0]
        end_row = period_data.iloc[-1]
        
        # 計算統計值
        spy_prices = period_data['spy_price']
        valid_prices = spy_prices[spy_prices > 0]  # 過濾掉零價格（如FRED數據）
        
        # 計算平均價格
        average_price = valid_prices.mean() if len(valid_prices) > 0 else None
        
        # 計算波動率（價格標準差/平均價格）
        volatility = None
        if len(valid_prices) > 1 and average_price and average_price > 0:
            price_std = valid_prices.std()
            volatility = (price_std / average_price) * 100  # 轉換為百分比
        
        return AggregatedPeriodData(
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
            data_quality_score=95.0,  # 基準分數
            volatility=volatility,
            average_price=average_price
        )
    
    @staticmethod
    def validate_data_integrity(data: List[Union[MarketDataPoint, AggregatedPeriodData]]) -> ValidationResult:
        """
        驗證數據完整性
        
        Args:
            data: 要驗證的數據列表
            
        Returns:
            ValidationResult: 驗證結果
        """
        result = ValidationResult(is_valid=True)
        
        try:
            if not data:
                result.errors.append("數據列表為空")
                result.is_valid = False
                result.severity = ErrorSeverity.CRITICAL
                return result
            
            # 檢查數據連續性
            if isinstance(data[0], MarketDataPoint):
                result = DataModelFactory._validate_market_data(data, result)
            elif isinstance(data[0], AggregatedPeriodData):
                result = DataModelFactory._validate_aggregated_data(data, result)
            
            # 計算數據品質分數
            result.data_quality_score = max(0, 100 - len(result.errors) * 20 - len(result.warnings) * 5)
            
            logger.info(f"數據完整性驗證完成，品質分數: {result.data_quality_score}")
            return result
            
        except Exception as e:
            logger.error(f"數據完整性驗證失敗: {e}")
            result.errors.append(f"驗證過程異常: {str(e)}")
            result.is_valid = False
            result.severity = ErrorSeverity.HIGH
            return result
    
    @staticmethod
    def _validate_market_data(data: List[MarketDataPoint], result: ValidationResult) -> ValidationResult:
        """驗證市場數據"""
        dates = [datetime.strptime(dp.date, '%Y-%m-%d') for dp in data]
        
        # 檢查日期排序
        if dates != sorted(dates):
            result.warnings.append("數據日期未按順序排列")
        
        # 檢查價格合理性
        for dp in data:
            if dp.spy_price <= 0:
                result.errors.append(f"發現無效價格: {dp.date} SPY={dp.spy_price}")
        
        return result
    
    @staticmethod
    def _validate_aggregated_data(data: List[AggregatedPeriodData], result: ValidationResult) -> ValidationResult:
        """驗證聚合數據"""
        # 檢查期間連續性
        periods = [ap.period for ap in data]
        expected_periods = list(range(1, len(data) + 1))
        
        if periods != expected_periods:
            result.errors.append("期間編號不連續")
        
        # 檢查計算結果
        for ap in data:
            calculated_return = ap.calculate_period_return()
            if abs(calculated_return - ap.period_return) > 0.0001:
                result.warnings.append(f"期間{ap.period}報酬率計算不一致")
        
        return result 