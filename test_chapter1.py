"""
測試第一章功能的腳本
驗證數據源與資訊流的完整功能
"""

import sys
import os
import logging
from datetime import datetime, timedelta

# 添加src目錄到Python路徑
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.data_manager import DataManager
from src.utils.trading_days import generate_simulation_timeline, is_trading_day
from src.models.data_models import MarketDataPoint

# 設定日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_api_security():
    """測試API安全機制"""
    print("\n=== 測試API安全機制 ===")
    
    data_manager = DataManager()
    status = data_manager.get_data_source_status()
    
    print(f"API金鑰狀態: {status['api_keys']}")
    print(f"API連通性: {status['connectivity']}")
    print(f"可用數據源: {status['available_sources']}")
    print(f"推薦數據源: {status['recommended_source']}")


def test_trading_days():
    """測試交易日處理功能"""
    print("\n=== 測試交易日處理功能 ===")
    
    # 測試特定日期是否為交易日
    test_dates = [
        datetime(2024, 1, 1),   # 元旦
        datetime(2024, 1, 2),   # 工作日
        datetime(2024, 7, 4),   # 獨立日
        datetime(2024, 12, 25), # 聖誕節
        datetime(2024, 6, 15),  # 普通週六
        datetime(2024, 6, 17),  # 普通週一
    ]
    
    for date in test_dates:
        is_trading = is_trading_day(date)
        print(f"{date.strftime('%Y-%m-%d (%A)')}: {'是' if is_trading else '不是'}交易日")


def test_simulation_timeline():
    """測試模擬時間軸生成"""
    print("\n=== 測試模擬時間軸生成 ===")
    
    timeline = generate_simulation_timeline(investment_years=2, frequency='quarterly')
    
    print(f"生成了 {len(timeline)} 期的時間軸")
    for i, period in enumerate(timeline[:4]):  # 只顯示前4期
        print(f"第{period['period']}期:")
        print(f"  期初日期: {period['adjusted_start_date'].strftime('%Y-%m-%d')}")
        print(f"  期末日期: {period['adjusted_end_date'].strftime('%Y-%m-%d')}")
        print(f"  交易日數量: {period['trading_days_count']}")
        print(f"  日期調整: {period['date_adjustments']}")


def test_simulation_data():
    """測試模擬數據生成"""
    print("\n=== 測試模擬數據生成 ===")
    
    data_manager = DataManager()
    
    try:
        # 生成2年的模擬數據
        market_data = data_manager.get_market_data(
            start_date="2026-01-01",
            end_date="2027-12-31",
            data_source="simulation"
        )
        
        print(f"成功生成 {len(market_data)} 筆模擬數據")
        
        # 顯示前5筆數據
        print("\n前5筆數據:")
        for i, data in enumerate(market_data[:5]):
            print(f"  {i+1}. {data.date}: SPY=${data.spy_price:.2f}, "
                  f"債券殖利率={data.bond_yield:.4f}%, "
                  f"債券價格=${data.bond_price:.2f}")
        
        # 驗證數據品質
        quality_report = data_manager.validate_data_quality(market_data)
        print(f"\n數據品質報告:")
        print(f"  總記錄數: {quality_report['statistics']['total_records']}")
        print(f"  日期範圍: {quality_report['statistics']['date_range']}")
        print(f"  數據完整度: {quality_report['statistics']['data_completeness']}")
        
        if quality_report['warnings']:
            print(f"  警告: {len(quality_report['warnings'])} 項")
            for warning in quality_report['warnings'][:3]:  # 只顯示前3個警告
                print(f"    - {warning}")
                
    except Exception as e:
        print(f"模擬數據生成失敗: {e}")


def test_api_data():
    """測試API數據獲取（如果可用）"""
    print("\n=== 測試API數據獲取 ===")
    
    data_manager = DataManager()
    
    if not data_manager.market_data_provider.is_available():
        print("API數據源不可用，跳過測試")
        return
    
    try:
        # 獲取最近一個月的數據
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        
        market_data = data_manager.get_market_data(
            start_date=start_date,
            end_date=end_date,
            data_source="api"
        )
        
        print(f"成功獲取 {len(market_data)} 筆API數據")
        
        # 顯示最新5筆數據
        print("\n最新5筆數據:")
        for i, data in enumerate(market_data[-5:]):
            bond_info = f"殖利率={data.bond_yield:.4f}%" if data.bond_yield else "無債券數據"
            print(f"  {i+1}. {data.date}: SPY=${data.spy_price:.2f}, {bond_info}")
            
    except Exception as e:
        print(f"API數據獲取失敗: {e}")


def test_period_aggregation():
    """測試期間數據聚合"""
    print("\n=== 測試期間數據聚合 ===")
    
    data_manager = DataManager()
    
    try:
        period_data = data_manager.get_period_data(
            investment_years=1,
            frequency='quarterly',
            data_source='simulation'
        )
        
        print(f"成功聚合 {len(period_data)} 期數據")
        
        for period in period_data:
            return_pct = period.period_return * 100
            print(f"第{period.period}期 ({period.start_date} ~ {period.end_date}):")
            print(f"  期初價格: ${period.spy_price_start:.2f}")
            print(f"  期末價格: ${period.spy_price_end:.2f}")
            print(f"  期間報酬率: {return_pct:+.2f}%")
            print(f"  交易日數: {period.trading_days}")
            print()
            
    except Exception as e:
        print(f"期間數據聚合失敗: {e}")


def main():
    """主測試函數"""
    print("開始測試第一章：數據源與資訊流定義")
    print("=" * 50)
    
    # 執行各項測試
    test_api_security()
    test_trading_days()
    test_simulation_timeline()
    test_simulation_data()
    test_api_data()
    test_period_aggregation()
    
    print("\n" + "=" * 50)
    print("第一章功能測試完成")


if __name__ == "__main__":
    main() 