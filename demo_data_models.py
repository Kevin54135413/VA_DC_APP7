#!/usr/bin/env python3
"""
投資策略比較系統 - 數據模型演示腳本
展示第一章第1.3節規格中定義的所有核心數據結構類別的使用方法

作者：VA_DC_APP7 系統
版本：1.0
日期：2024年
"""

import sys
import os
from datetime import datetime, timedelta
import random

# 添加專案根目錄到路徑
sys.path.insert(0, os.path.dirname(__file__))

from src.models.data_models import (
    MarketDataPoint, AggregatedPeriodData, StrategyResult, 
    DataModelFactory, PrecisionConfig, ValidationResult,
    DataValidationError, DataQualityError, CalculationError, ErrorSeverity
)
from src.utils.logger import setup_application_logging

def demo_precision_config():
    """演示精確度配置功能"""
    print("=== 精確度配置演示 ===")
    
    # 價格精確度
    original_price = 123.456789
    rounded_price = PrecisionConfig.round_price(original_price)
    print(f"價格精確度: {original_price} -> {rounded_price}")
    
    # 殖利率精確度
    original_yield = 4.123456
    rounded_yield = PrecisionConfig.round_yield(original_yield)
    print(f"殖利率精確度: {original_yield} -> {rounded_yield}")
    
    # 百分比精確度
    original_percentage = 0.123456
    rounded_percentage = PrecisionConfig.round_percentage(original_percentage)
    print(f"百分比精確度: {original_percentage} -> {rounded_percentage}")
    
    # 單位數精確度
    original_units = 10.123456
    rounded_units = PrecisionConfig.round_units(original_units)
    print(f"單位數精確度: {original_units} -> {rounded_units}")
    
    print()

def demo_market_data_point():
    """演示MarketDataPoint類別"""
    print("=== MarketDataPoint演示 ===")
    
    # 創建有效的市場數據點
    try:
        data_point = MarketDataPoint(
            date="2024-01-15",
            spy_price=450.789123,  # 會被自動四捨五入到450.79
            bond_yield=4.5678,
            bond_price=95.789,
            data_source="tiingo"
        )
        
        print(f"創建MarketDataPoint成功:")
        print(f"  日期: {data_point.date}")
        print(f"  SPY價格: {data_point.spy_price} (精確度處理後)")
        print(f"  債券殖利率: {data_point.bond_yield}")
        print(f"  債券價格: {data_point.bond_price}")
        print(f"  數據源: {data_point.data_source}")
        
        # 轉換為字典
        data_dict = data_point.to_dict()
        print(f"  轉換為字典: {data_dict}")
        
    except DataValidationError as e:
        print(f"數據驗證錯誤: {e}")
    
    # 演示錯誤處理
    print("\n錯誤處理演示:")
    try:
        invalid_data_point = MarketDataPoint(
            date="2024/01/15",  # 錯誤的日期格式
            spy_price=450.75,
            bond_yield=None,
            bond_price=None,
            data_source="tiingo"
        )
    except DataValidationError as e:
        print(f"  捕獲到預期錯誤: {e}")
    
    print()

def demo_aggregated_period_data():
    """演示AggregatedPeriodData類別"""
    print("=== AggregatedPeriodData演示 ===")
    
    try:
        aggregated_data = AggregatedPeriodData(
            period=1,
            start_date="2024-01-01",
            end_date="2024-01-31",
            spy_price_start=400.123,  # 會被精確度處理
            spy_price_end=420.789,
            bond_yield_start=4.0123,
            bond_yield_end=4.2567,
            bond_price_start=96.123,
            bond_price_end=95.876,
            trading_days=21
        )
        
        print(f"創建AggregatedPeriodData成功:")
        print(f"  期數: {aggregated_data.period}")
        print(f"  期間: {aggregated_data.start_date} ~ {aggregated_data.end_date}")
        print(f"  期初SPY價格: {aggregated_data.spy_price_start}")
        print(f"  期末SPY價格: {aggregated_data.spy_price_end}")
        print(f"  期間報酬率: {aggregated_data.period_return:.4f}")
        print(f"  交易日數: {aggregated_data.trading_days}")
        
        # 計算數據品質分數
        quality_score = aggregated_data.calculate_data_quality_score()
        print(f"  數據品質分數: {quality_score}")
        
    except DataValidationError as e:
        print(f"數據驗證錯誤: {e}")
    
    print()

def demo_strategy_result():
    """演示StrategyResult類別"""
    print("=== StrategyResult演示 ===")
    
    try:
        strategy_result = StrategyResult(
            period=1,
            date_origin="2024-01-31",
            spy_price_origin=420.789123,  # 會被精確度處理
            bond_yield_origin=4.23456,
            bond_price_origin=95.789,
            stock_investment=1000.123,
            cum_stock_investment=1000.123,
            stock_units_purchased=2.381234567,
            cum_stock_units=2.381234567,
            stock_value=1100.567,
            bond_investment=500.789,
            cum_bond_investment=500.789,
            bond_units_purchased=5.218834567,
            cum_bond_units=5.218834567,
            bond_value=520.234,
            total_investment=1500.0,
            cum_total_investment=1500.0,
            total_value=1620.0,
            unrealized_gain_loss=120.0,
            unrealized_return=0.08
        )
        
        print(f"創建StrategyResult成功:")
        print(f"  期數: {strategy_result.period}")
        print(f"  日期: {strategy_result.date_origin}")
        print(f"  SPY價格: {strategy_result.spy_price_origin} (精確度處理後)")
        print(f"  股票投資: ${strategy_result.stock_investment}")
        print(f"  股票單位數: {strategy_result.stock_units_purchased}")
        print(f"  股票市值: ${strategy_result.stock_value}")
        print(f"  債券投資: ${strategy_result.bond_investment}")
        print(f"  債券市值: ${strategy_result.bond_value}")
        print(f"  總市值: ${strategy_result.total_value}")
        print(f"  未實現報酬率: {strategy_result.unrealized_return:.4f}")
        
    except CalculationError as e:
        print(f"計算錯誤: {e}")
    
    print()

def demo_data_model_factory():
    """演示DataModelFactory類別"""
    print("=== DataModelFactory演示 ===")
    
    # 演示Tiingo API數據解析
    print("Tiingo API數據解析:")
    tiingo_response = [
        {'date': '2024-01-15T00:00:00Z', 'adjClose': 450.75},
        {'date': '2024-01-16T00:00:00Z', 'adjClose': 452.30},
        {'date': '2024-01-17T00:00:00Z', 'adjClose': 449.88}
    ]
    
    try:
        tiingo_data = DataModelFactory.create_market_data_from_api(tiingo_response, 'tiingo')
        print(f"  成功解析 {len(tiingo_data)} 個Tiingo數據點")
        for i, dp in enumerate(tiingo_data[:2]):  # 只顯示前2個
            print(f"    {i+1}. {dp.date}: SPY=${dp.spy_price}")
    except DataValidationError as e:
        print(f"  Tiingo數據解析錯誤: {e}")
    
    # 演示FRED API數據解析
    print("\nFRED API數據解析:")
    fred_response = {
        'observations': [
            {'date': '2024-01-15', 'value': '4.5'},
            {'date': '2024-01-16', 'value': '4.6'},
            {'date': '2024-01-17', 'value': '.'}  # 缺失值
        ]
    }
    
    try:
        fred_data = DataModelFactory.create_market_data_from_api(fred_response, 'fred')
        print(f"  成功解析 {len(fred_data)} 個FRED數據點")
        for i, dp in enumerate(fred_data):
            print(f"    {i+1}. {dp.date}: 殖利率={dp.bond_yield}%, 債券價格=${dp.bond_price}")
    except DataValidationError as e:
        print(f"  FRED數據解析錯誤: {e}")
    
    # 演示數據聚合
    print("\n數據聚合演示:")
    try:
        # 創建模擬市場數據
        market_data = []
        base_date = datetime(2024, 1, 1)
        for i in range(90):  # 90天數據
            date = base_date + timedelta(days=i)
            spy_price = 400 + i * 0.5 + random.uniform(-5, 5)
            bond_yield = 4.0 + i * 0.01 + random.uniform(-0.1, 0.1)
            
            market_data.append(MarketDataPoint(
                date=date.strftime('%Y-%m-%d'),
                spy_price=spy_price,
                bond_yield=bond_yield,
                bond_price=100.0 / (1 + bond_yield/100),
                data_source='simulation'
            ))
        
        # 按季度聚合
        aggregated_data = DataModelFactory.aggregate_to_periods(
            market_data, 'quarterly', 1
        )
        
        print(f"  成功聚合 {len(aggregated_data)} 個季度數據")
        for i, ap in enumerate(aggregated_data):
            print(f"    Q{i+1}: {ap.start_date}~{ap.end_date}, 報酬率: {ap.period_return:.4f}")
            
    except DataQualityError as e:
        print(f"  數據聚合錯誤: {e}")
    
    # 演示數據完整性驗證
    print("\n數據完整性驗證:")
    validation_result = DataModelFactory.validate_data_integrity(market_data[:10])
    print(f"  驗證結果: {'通過' if validation_result.is_valid else '失敗'}")
    print(f"  數據品質分數: {validation_result.data_quality_score}")
    if validation_result.errors:
        print(f"  錯誤: {validation_result.errors}")
    if validation_result.warnings:
        print(f"  警告: {validation_result.warnings}")
    
    print()

def demo_error_handling():
    """演示錯誤處理機制"""
    print("=== 錯誤處理機制演示 ===")
    
    # 演示不同類型的錯誤
    error_cases = [
        ("數據驗證錯誤", lambda: MarketDataPoint(
            date="invalid-date", spy_price=450, bond_yield=None, 
            bond_price=None, data_source="tiingo")),
        ("數據品質錯誤", lambda: DataModelFactory.aggregate_to_periods(
            [], 'monthly', 1)),
        ("計算錯誤", lambda: StrategyResult(
            period=1, date_origin="2024-01-31", spy_price_origin=420,
            bond_yield_origin=None, bond_price_origin=None,
            stock_investment=1000, cum_stock_investment=-1000,  # 負數累計投資
            stock_units_purchased=2.381, cum_stock_units=2.381,
            stock_value=1000, bond_investment=0, cum_bond_investment=0,
            bond_units_purchased=0, cum_bond_units=0, bond_value=0,
            total_investment=1000, cum_total_investment=1000,
            total_value=1000, unrealized_gain_loss=0, unrealized_return=0))
    ]
    
    for error_name, error_func in error_cases:
        try:
            error_func()
            print(f"  {error_name}: 未發生預期錯誤")
        except (DataValidationError, DataQualityError, CalculationError) as e:
            print(f"  {error_name}: ✓ 正確捕獲 - {type(e).__name__}")
        except Exception as e:
            print(f"  {error_name}: ✗ 意外錯誤 - {type(e).__name__}: {e}")
    
    print()

def demo_validation_result():
    """演示ValidationResult類別"""
    print("=== ValidationResult演示 ===")
    
    # 創建驗證結果
    validation_result = ValidationResult(
        is_valid=False,
        errors=['價格數據缺失', '日期格式錯誤'],
        warnings=['數據品質需要改善'],
        data_quality_score=75.0,
        severity=ErrorSeverity.MEDIUM
    )
    
    print(f"驗證結果:")
    print(f"  是否有效: {validation_result.is_valid}")
    print(f"  錯誤數量: {len(validation_result.errors)}")
    print(f"  警告數量: {len(validation_result.warnings)}")
    print(f"  數據品質分數: {validation_result.data_quality_score}")
    print(f"  嚴重程度: {validation_result.severity.value}")
    
    for i, error in enumerate(validation_result.errors, 1):
        print(f"    錯誤{i}: {error}")
    
    for i, warning in enumerate(validation_result.warnings, 1):
        print(f"    警告{i}: {warning}")
    
    print()

def main():
    """主函數"""
    # 設定日誌系統
    logger = setup_application_logging(
        app_name="DataModelsDemo",
        log_level="INFO",
        enable_file_logging=True,
        log_directory="demo_logs"
    )
    
    print("🚀 投資策略比較系統 - 數據模型演示")
    print("=" * 50)
    
    try:
        # 運行各個演示
        demo_precision_config()
        demo_market_data_point()
        demo_aggregated_period_data()
        demo_strategy_result()
        demo_data_model_factory()
        demo_error_handling()
        demo_validation_result()
        
        print("✅ 所有演示完成！")
        print("📁 詳細日誌請查看 demo_logs/ 目錄")
        
    except Exception as e:
        logger.error(f"演示過程中發生異常: {e}")
        print(f"❌ 演示失敗: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code) 