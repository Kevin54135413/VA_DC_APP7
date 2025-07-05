"""
投資策略比較系統 - 數據模型測試
測試第一章第1.3節規格中定義的所有核心數據結構類別

作者：VA_DC_APP7 系統
版本：1.0
日期：2024年
"""

import unittest
import sys
import os
from decimal import Decimal
from datetime import datetime

# 添加專案根目錄到路徑
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.models.data_models import (
    MarketDataPoint, AggregatedPeriodData, StrategyResult, 
    DataModelFactory, PrecisionConfig, ValidationResult,
    DataValidationError, DataQualityError, CalculationError, ErrorSeverity
)
from src.utils.logger import setup_application_logging

class TestPrecisionConfig(unittest.TestCase):
    """測試精確度配置"""
    
    def test_price_precision(self):
        """測試價格精確度設定"""
        # 測試正常價格
        self.assertEqual(PrecisionConfig.round_price(123.456789), 123.46)
        self.assertEqual(PrecisionConfig.round_price(123.454), 123.45)
        self.assertEqual(PrecisionConfig.round_price(123.455), 123.46)  # 四捨五入
        
        # 測試邊界值
        self.assertEqual(PrecisionConfig.round_price(0.01), 0.01)
        self.assertEqual(PrecisionConfig.round_price(0.004), 0.00)
        self.assertEqual(PrecisionConfig.round_price(0.005), 0.01)
        
        # 測試None值
        self.assertIsNone(PrecisionConfig.round_price(None))
    
    def test_yield_precision(self):
        """測試殖利率精確度設定"""
        self.assertEqual(PrecisionConfig.round_yield(2.123456), 2.1235)
        self.assertEqual(PrecisionConfig.round_yield(2.12344), 2.1234)
        self.assertEqual(PrecisionConfig.round_yield(2.12345), 2.1235)
        
        # 測試None值
        self.assertIsNone(PrecisionConfig.round_yield(None))
    
    def test_percentage_precision(self):
        """測試百分比精確度設定"""
        self.assertEqual(PrecisionConfig.round_percentage(0.123456), 0.12)
        self.assertEqual(PrecisionConfig.round_percentage(0.125), 0.13)
        
    def test_units_precision(self):
        """測試單位數精確度設定"""
        self.assertEqual(PrecisionConfig.round_units(10.123456), 10.1235)
        self.assertEqual(PrecisionConfig.round_units(10.12345), 10.1235)

class TestMarketDataPoint(unittest.TestCase):
    """測試MarketDataPoint類別"""
    
    def setUp(self):
        """設定測試環境"""
        setup_application_logging(log_level="DEBUG", enable_file_logging=False)
    
    def test_valid_market_data_point(self):
        """測試有效的市場數據點"""
        data_point = MarketDataPoint(
            date="2024-01-15",
            spy_price=450.75,
            bond_yield=4.5678,
            bond_price=95.75,
            data_source="tiingo"
        )
        
        # 驗證精確度處理
        self.assertEqual(data_point.spy_price, 450.75)
        self.assertEqual(data_point.bond_yield, 4.5678)
        self.assertEqual(data_point.bond_price, 95.75)
    
    def test_price_precision_applied(self):
        """測試價格精確度自動應用"""
        data_point = MarketDataPoint(
            date="2024-01-15",
            spy_price=450.789123,  # 應被四捨五入到450.79
            bond_yield=None,
            bond_price=None,
            data_source="tiingo"
        )
        
        self.assertEqual(data_point.spy_price, 450.79)
    
    def test_invalid_date_format(self):
        """測試無效日期格式"""
        with self.assertRaises(DataValidationError):
            MarketDataPoint(
                date="2024/01/15",  # 錯誤格式
                spy_price=450.75,
                bond_yield=None,
                bond_price=None,
                data_source="tiingo"
            )
    
    def test_invalid_spy_price(self):
        """測試無效SPY價格"""
        with self.assertRaises(DataValidationError):
            MarketDataPoint(
                date="2024-01-15",
                spy_price=-100.0,  # 負價格
                bond_yield=None,
                bond_price=None,
                data_source="tiingo"
            )
        
        with self.assertRaises(DataValidationError):
            MarketDataPoint(
                date="2024-01-15",
                spy_price=0.0,  # 零價格
                bond_yield=None,
                bond_price=None,
                data_source="tiingo"
            )
    
    def test_invalid_bond_yield(self):
        """測試無效債券殖利率"""
        with self.assertRaises(DataValidationError):
            MarketDataPoint(
                date="2024-01-15",
                spy_price=450.75,
                bond_yield=30.0,  # 超出範圍
                bond_price=None,
                data_source="fred"
            )
        
        with self.assertRaises(DataValidationError):
            MarketDataPoint(
                date="2024-01-15",
                spy_price=450.75,
                bond_yield=-10.0,  # 超出範圍
                bond_price=None,
                data_source="fred"
            )
    
    def test_invalid_bond_price(self):
        """測試無效債券價格"""
        with self.assertRaises(DataValidationError):
            MarketDataPoint(
                date="2024-01-15",
                spy_price=450.75,
                bond_yield=None,
                bond_price=300.0,  # 超出範圍
                data_source="fred"
            )
    
    def test_invalid_data_source(self):
        """測試無效數據源"""
        with self.assertRaises(DataValidationError):
            MarketDataPoint(
                date="2024-01-15",
                spy_price=450.75,
                bond_yield=None,
                bond_price=None,
                data_source="invalid_source"
            )
    
    def test_to_dict(self):
        """測試字典轉換"""
        data_point = MarketDataPoint(
            date="2024-01-15",
            spy_price=450.75,
            bond_yield=4.5,
            bond_price=95.75,
            data_source="tiingo"
        )
        
        expected_dict = {
            'date': '2024-01-15',
            'spy_price': 450.75,
            'bond_yield': 4.5,
            'bond_price': 95.75,
            'data_source': 'tiingo'
        }
        
        self.assertEqual(data_point.to_dict(), expected_dict)

class TestAggregatedPeriodData(unittest.TestCase):
    """測試AggregatedPeriodData類別"""
    
    def test_valid_aggregated_data(self):
        """測試有效的聚合數據"""
        aggregated_data = AggregatedPeriodData(
            period=1,
            start_date="2024-01-01",
            end_date="2024-01-31",
            spy_price_start=400.0,
            spy_price_end=420.0,
            bond_yield_start=4.0,
            bond_yield_end=4.2,
            bond_price_start=96.0,
            bond_price_end=95.8,
            trading_days=21
        )
        
        # 驗證期間報酬率計算
        expected_return = (420.0 / 400.0) - 1.0
        self.assertAlmostEqual(aggregated_data.period_return, expected_return, places=4)
    
    def test_period_return_calculation(self):
        """測試期間報酬率計算"""
        aggregated_data = AggregatedPeriodData(
            period=1,
            start_date="2024-01-01",
            end_date="2024-01-31",
            spy_price_start=100.0,
            spy_price_end=110.0,
            bond_yield_start=None,
            bond_yield_end=None,
            bond_price_start=None,
            bond_price_end=None,
            trading_days=21
        )
        
        # 預期報酬率: (110-100)/100 = 0.10 = 10%
        self.assertAlmostEqual(aggregated_data.period_return, 0.10, places=4)
    
    def test_zero_start_price(self):
        """測試期初價格為零的情況"""
        aggregated_data = AggregatedPeriodData(
            period=1,
            start_date="2024-01-01",
            end_date="2024-01-31",
            spy_price_start=0.01,  # 接近零但大於零
            spy_price_end=110.0,
            bond_yield_start=None,
            bond_yield_end=None,
            bond_price_start=None,
            bond_price_end=None,
            trading_days=21
        )
        
        # 應該正常計算
        expected_return = (110.0 / 0.01) - 1.0
        self.assertAlmostEqual(aggregated_data.period_return, expected_return, places=2)
    
    def test_invalid_period(self):
        """測試無效期數"""
        with self.assertRaises(DataValidationError):
            AggregatedPeriodData(
                period=0,  # 無效期數
                start_date="2024-01-01",
                end_date="2024-01-31",
                spy_price_start=400.0,
                spy_price_end=420.0,
                bond_yield_start=None,
                bond_yield_end=None,
                bond_price_start=None,
                bond_price_end=None,
                trading_days=21
            )
    
    def test_invalid_trading_days(self):
        """測試無效交易日數"""
        with self.assertRaises(DataValidationError):
            AggregatedPeriodData(
                period=1,
                start_date="2024-01-01",
                end_date="2024-01-31",
                spy_price_start=400.0,
                spy_price_end=420.0,
                bond_yield_start=None,
                bond_yield_end=None,
                bond_price_start=None,
                bond_price_end=None,
                trading_days=0  # 無效交易日數
            )
    
    def test_data_quality_score_calculation(self):
        """測試數據品質分數計算"""
        # 完整數據
        complete_data = AggregatedPeriodData(
            period=1,
            start_date="2024-01-01",
            end_date="2024-01-31",
            spy_price_start=400.0,
            spy_price_end=420.0,
            bond_yield_start=4.0,
            bond_yield_end=4.2,
            bond_price_start=96.0,
            bond_price_end=95.8,
            trading_days=21
        )
        
        score = complete_data.calculate_data_quality_score()
        self.assertEqual(score, 100.0)  # 完整數據應得滿分
        
        # 缺少債券數據
        incomplete_data = AggregatedPeriodData(
            period=1,
            start_date="2024-01-01",
            end_date="2024-01-31",
            spy_price_start=400.0,
            spy_price_end=420.0,
            bond_yield_start=None,  # 缺少債券數據
            bond_yield_end=None,
            bond_price_start=None,
            bond_price_end=None,
            trading_days=21
        )
        
        score = incomplete_data.calculate_data_quality_score()
        self.assertEqual(score, 90.0)  # 應扣10分

class TestStrategyResult(unittest.TestCase):
    """測試StrategyResult類別"""
    
    def test_valid_strategy_result(self):
        """測試有效的策略結果"""
        strategy_result = StrategyResult(
            period=1,
            date_origin="2024-01-31",
            spy_price_origin=420.0,
            bond_yield_origin=4.2,
            bond_price_origin=95.8,
            stock_investment=1000.0,
            cum_stock_investment=1000.0,
            stock_units_purchased=2.3810,
            cum_stock_units=2.3810,
            stock_value=1000.0,
            bond_investment=500.0,
            cum_bond_investment=500.0,
            bond_units_purchased=5.2188,
            cum_bond_units=5.2188,
            bond_value=500.0,
            total_investment=1500.0,
            cum_total_investment=1500.0,
            total_value=1500.0,
            unrealized_gain_loss=0.0,
            unrealized_return=0.0
        )
        
        # 驗證計算結果
        self.assertEqual(strategy_result.total_value, 1500.0)
        self.assertEqual(strategy_result.unrealized_return, 0.0)
    
    def test_precision_application(self):
        """測試精確度應用"""
        strategy_result = StrategyResult(
            period=1,
            date_origin="2024-01-31",
            spy_price_origin=420.789123,  # 應被四捨五入
            bond_yield_origin=4.23456,    # 應被四捨五入
            bond_price_origin=95.789,     # 應被四捨五入
            stock_investment=1000.123,
            cum_stock_investment=1000.123,
            stock_units_purchased=2.381234567,
            cum_stock_units=2.381234567,
            stock_value=1000.12,
            bond_investment=500.789,
            cum_bond_investment=500.789,
            bond_units_purchased=5.218834567,
            cum_bond_units=5.218834567,
            bond_value=500.78,
            total_investment=1500.0,
            cum_total_investment=1500.0,
            total_value=1500.0,
            unrealized_gain_loss=0.0,
            unrealized_return=0.0
        )
        
        # 驗證精確度應用
        self.assertEqual(strategy_result.spy_price_origin, 420.79)
        self.assertEqual(strategy_result.bond_yield_origin, 4.2346)
        self.assertEqual(strategy_result.bond_price_origin, 95.79)
        self.assertEqual(strategy_result.stock_units_purchased, 2.3812)
        self.assertEqual(strategy_result.cum_stock_units, 2.3812)
    
    def test_calculation_validation(self):
        """測試計算驗證"""
        # 測試負數累計投資金額
        with self.assertRaises(CalculationError):
            StrategyResult(
                period=1,
                date_origin="2024-01-31",
                spy_price_origin=420.0,
                bond_yield_origin=None,
                bond_price_origin=None,
                stock_investment=1000.0,
                cum_stock_investment=-1000.0,  # 負數累計投資
                stock_units_purchased=2.381,
                cum_stock_units=2.381,
                stock_value=1000.0,
                bond_investment=0.0,
                cum_bond_investment=0.0,
                bond_units_purchased=0.0,
                cum_bond_units=0.0,
                bond_value=0.0,
                total_investment=1000.0,
                cum_total_investment=1000.0,
                total_value=1000.0,
                unrealized_gain_loss=0.0,
                unrealized_return=0.0
            )
        
        # 測試負數總市值
        with self.assertRaises(CalculationError):
            StrategyResult(
                period=1,
                date_origin="2024-01-31",
                spy_price_origin=420.0,
                bond_yield_origin=None,
                bond_price_origin=None,
                stock_investment=1000.0,
                cum_stock_investment=1000.0,
                stock_units_purchased=2.381,
                cum_stock_units=2.381,
                stock_value=-500.0,  # 負數股票市值
                bond_investment=0.0,
                cum_bond_investment=0.0,
                bond_units_purchased=0.0,
                cum_bond_units=0.0,
                bond_value=-500.0,  # 負數債券市值  
                total_investment=1000.0,
                cum_total_investment=1000.0,
                total_value=-1000.0,  # 負數總市值
                unrealized_gain_loss=-2000.0,
                unrealized_return=-2.0
            )
    
    def test_unrealized_return_calculation(self):
        """測試未實現報酬率計算"""
        strategy_result = StrategyResult(
            period=1,
            date_origin="2024-01-31",
            spy_price_origin=420.0,
            bond_yield_origin=None,
            bond_price_origin=None,
            stock_investment=1000.0,
            cum_stock_investment=1000.0,
            stock_units_purchased=2.381,
            cum_stock_units=2.381,
            stock_value=1100.0,  # 增值到1100
            bond_investment=0.0,
            cum_bond_investment=0.0,
            bond_units_purchased=0.0,
            cum_bond_units=0.0,
            bond_value=0.0,
            total_investment=1000.0,
            cum_total_investment=1000.0,
            total_value=1100.0,
            unrealized_gain_loss=100.0,
            unrealized_return=0.1  # 10%報酬率
        )
        
        # 驗證未實現報酬率計算
        calculated_return = strategy_result.calculate_unrealized_return()
        self.assertAlmostEqual(calculated_return, 0.1, places=4)

class TestDataModelFactory(unittest.TestCase):
    """測試DataModelFactory類別"""
    
    def test_create_tiingo_data(self):
        """測試Tiingo數據創建"""
        tiingo_response = [
            {
                'date': '2024-01-15T00:00:00Z',
                'adjClose': 450.75
            },
            {
                'date': '2024-01-16T00:00:00Z',
                'adjClose': 452.30
            }
        ]
        
        data_points = DataModelFactory.create_market_data_from_api(tiingo_response, 'tiingo')
        
        self.assertEqual(len(data_points), 2)
        self.assertEqual(data_points[0].date, '2024-01-15')
        self.assertEqual(data_points[0].spy_price, 450.75)
        self.assertEqual(data_points[0].data_source, 'tiingo')
        self.assertIsNone(data_points[0].bond_yield)
    
    def test_create_fred_data(self):
        """測試FRED數據創建"""
        fred_response = {
            'observations': [
                {
                    'date': '2024-01-15',
                    'value': '4.5'
                },
                {
                    'date': '2024-01-16',
                    'value': '4.6'
                },
                {
                    'date': '2024-01-17',
                    'value': '.'  # 缺失值
                }
            ]
        }
        
        data_points = DataModelFactory.create_market_data_from_api(fred_response, 'fred')
        
        self.assertEqual(len(data_points), 2)  # 應忽略缺失值
        self.assertEqual(data_points[0].date, '2024-01-15')
        self.assertEqual(data_points[0].bond_yield, 4.5)
        self.assertEqual(data_points[0].data_source, 'fred')
        self.assertEqual(data_points[0].spy_price, 0.0)
    
    def test_unsupported_source(self):
        """測試不支援的數據源"""
        with self.assertRaises(DataValidationError):
            DataModelFactory.create_market_data_from_api({}, 'unsupported')
    
    def test_aggregate_to_periods(self):
        """測試期間聚合"""
        # 創建測試數據
        market_data = []
        for i in range(60):  # 60天數據
            date = f"2024-01-{i+1:02d}" if i < 31 else f"2024-02-{i-30:02d}"
            if i < 31:  # 1月只有31天
                market_data.append(MarketDataPoint(
                    date=date,
                    spy_price=400.0 + i,
                    bond_yield=4.0 + i * 0.01,
                    bond_price=96.0 - i * 0.1,
                    data_source='simulation'
                ))
        
        # 按月聚合，投資1年
        aggregated_data = DataModelFactory.aggregate_to_periods(
            market_data, 'monthly', 1
        )
        
        self.assertEqual(len(aggregated_data), 12)  # 12個月
        self.assertEqual(aggregated_data[0].period, 1)
        self.assertGreater(aggregated_data[0].trading_days, 0)
    
    def test_empty_market_data(self):
        """測試空市場數據"""
        with self.assertRaises(DataQualityError):
            DataModelFactory.aggregate_to_periods([], 'monthly', 1)
    
    def test_unsupported_frequency(self):
        """測試不支援的頻率"""
        market_data = [MarketDataPoint(
            date="2024-01-01",
            spy_price=400.0,
            bond_yield=4.0,
            bond_price=96.0,
            data_source='simulation'
        )]
        
        with self.assertRaises(DataQualityError):
            DataModelFactory.aggregate_to_periods(market_data, 'weekly', 1)
    
    def test_data_integrity_validation(self):
        """測試數據完整性驗證"""
        # 有效數據
        valid_data = [
            MarketDataPoint(
                date="2024-01-01",
                spy_price=400.0,
                bond_yield=4.0,
                bond_price=96.0,
                data_source='simulation'
            ),
            MarketDataPoint(
                date="2024-01-02",
                spy_price=401.0,
                bond_yield=4.1,
                bond_price=95.9,
                data_source='simulation'
            )
        ]
        
        result = DataModelFactory.validate_data_integrity(valid_data)
        self.assertTrue(result.is_valid)
        self.assertEqual(len(result.errors), 0)
        self.assertGreater(result.data_quality_score, 90)
        
        # 空數據
        empty_result = DataModelFactory.validate_data_integrity([])
        self.assertFalse(empty_result.is_valid)
        self.assertEqual(empty_result.severity, ErrorSeverity.CRITICAL)

class TestValidationResult(unittest.TestCase):
    """測試ValidationResult類別"""
    
    def test_validation_result_creation(self):
        """測試驗證結果創建"""
        result = ValidationResult(
            is_valid=False,
            errors=['錯誤1', '錯誤2'],
            warnings=['警告1'],
            data_quality_score=75.0,
            severity=ErrorSeverity.MEDIUM
        )
        
        self.assertFalse(result.is_valid)
        self.assertEqual(len(result.errors), 2)
        self.assertEqual(len(result.warnings), 1)
        self.assertEqual(result.data_quality_score, 75.0)
        self.assertEqual(result.severity, ErrorSeverity.MEDIUM)

if __name__ == '__main__':
    # 設定測試日誌
    setup_application_logging(
        app_name="DataModelsTest",
        log_level="DEBUG",
        enable_file_logging=True,
        log_directory="test_logs"
    )
    
    # 執行測試
    unittest.main(verbosity=2) 