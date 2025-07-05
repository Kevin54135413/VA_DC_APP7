"""
投資策略比較系統 - 數據源模組

此模組提供外部API數據源的安全訪問、批次獲取優化和容錯處理機制。
支援 Tiingo API (股票數據) 和 FRED API (債券數據)。

主要組件：
- api_client: API客戶端和安全機制
- data_fetcher: 數據獲取和批次處理
- trading_calendar: 交易日計算和日期調整
- fault_tolerance: 增強版容錯機制與數據品質驗證
- simulation: 模擬數據生成器
- cache_manager: 智能快取管理系統
"""

from .api_client import (
    get_api_key,
    validate_api_key_format,
    test_api_connectivity
)

from .data_fetcher import (
    TiingoDataFetcher,
    FREDDataFetcher,
    BatchDataFetcher
)

from .trading_calendar import (
    calculate_period_start_date,
    calculate_period_end_dates,
    adjust_for_trading_days,
    generate_trading_days,
    is_trading_day
)

from .fault_tolerance import (
    APIFaultToleranceManager,  # 增強版容錯管理器
    DataQualityValidator,
    RetryConfig,
    ValidationRules
)

from .simulation import (
    SimulationDataGenerator,
    MarketRegime,
    MarketScenarioConfig,
    YieldCurveConfig
)

from .cache_manager import (
    IntelligentCacheManager,
    CacheConfig,
    CacheEntry,
    cached_data,
    cached_resource,
    get_cache_manager,
    set_cache_manager
)

__all__ = [
    # API安全機制
    'get_api_key',
    'validate_api_key_format', 
    'test_api_connectivity',
    
    # 數據獲取器
    'TiingoDataFetcher',
    'FREDDataFetcher', 
    'BatchDataFetcher',
    
    # 交易日計算
    'calculate_period_start_date',
    'calculate_period_end_dates',
    'adjust_for_trading_days',
    'generate_trading_days',
    'is_trading_day',
    
    # 容錯機制與品質控制
    'APIFaultToleranceManager',  # 使用增強版
    'DataQualityValidator',
    'RetryConfig',
    'ValidationRules',
    
    # 模擬數據生成
    'SimulationDataGenerator',
    'MarketRegime',
    'MarketScenarioConfig',
    'YieldCurveConfig',
    
    # 智能快取管理
    'IntelligentCacheManager',
    'CacheConfig',
    'CacheEntry',
    'cached_data',
    'cached_resource',
    'get_cache_manager',
    'set_cache_manager'
] 