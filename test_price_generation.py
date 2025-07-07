"""
測試價格生成修正效果 - 檢查2026年後價格變化
"""

import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# 添加項目根目錄到Python路徑
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.ui.results_display import ResultsDisplayManager
from src.utils.logger import get_component_logger

def test_price_generation_fix():
    """測試價格生成修正效果"""
    logger = get_component_logger("TestPriceGeneration")
    logger.info("開始測試2026年後價格生成修正效果")
    
    # 創建測試參數 - 設定長期投資（包含2026年後）
    test_parameters = {
        "investment_start_date": datetime(2020, 1, 1),
        "investment_frequency": "annually",
        "total_periods": 30,  # 30年投資期間，會超過2026年
        "initial_investment": 10000,
        "annual_investment": 12000,
        "va_growth_rate": 8.0,
        "inflation_rate": 3.0,
        "investment_years": 30,
        "stock_ratio": 80
    }
    
    # 創建結果顯示管理器並生成備用數據
    display_manager = ResultsDisplayManager()
    
    print("=== 測試價格生成修正效果 ===")
    print(f"投資期間：{test_parameters['investment_start_date'].year} - {test_parameters['investment_start_date'].year + 30}")
    print(f"投資頻率：{test_parameters['investment_frequency']}")
    print(f"總期數：{test_parameters['total_periods']}")
    
    # 生成數據
    market_data = display_manager._generate_fallback_data(test_parameters)
    
    print(f"\n=== 生成的市場數據概況 ===")
    print(f"數據期數：{len(market_data)}")
    print(f"數據欄位：{list(market_data.columns)}")
    
    # 檢查價格變化
    print(f"\n=== 股票價格變化分析 ===")
    
    # 計算期初期末價格差異
    market_data['SPY_Price_Change'] = market_data['SPY_Price_End'] - market_data['SPY_Price_Origin']
    market_data['SPY_Price_Change_Pct'] = (market_data['SPY_Price_Change'] / market_data['SPY_Price_Origin'] * 100).round(2)
    
    # 檢查是否有相同價格
    same_price_periods = market_data[market_data['SPY_Price_Change'] == 0]
    print(f"期初期末價格完全相同的期數：{len(same_price_periods)}")
    
    if len(same_price_periods) > 0:
        print("⚠️  發現價格相同的期間：")
        for idx, row in same_price_periods.iterrows():
            print(f"  期間 {row['Period']}: {row['Date_Origin']} - 價格 ${row['SPY_Price_Origin']}")
    else:
        print("✅ 所有期間都有價格變化")
    
    # 檢查小幅變化（小於1%）
    small_change_periods = market_data[abs(market_data['SPY_Price_Change_Pct']) < 1.0]
    print(f"價格變化小於1%的期數：{len(small_change_periods)} / {len(market_data)}")
    
    # 統計價格變化分布
    price_changes = market_data['SPY_Price_Change_Pct']
    print(f"\n=== 價格變化統計 ===")
    print(f"平均變化：{price_changes.mean():.2f}%")
    print(f"標準差：{price_changes.std():.2f}%")
    print(f"最大漲幅：{price_changes.max():.2f}%")
    print(f"最大跌幅：{price_changes.min():.2f}%")
    
    # 檢查特定年份的價格變化（重點關注2026年後）
    market_data['Year'] = pd.to_datetime(market_data['Date_Origin']).dt.year
    
    print(f"\n=== 按年份分析價格變化 ===")
    yearly_stats = market_data.groupby('Year')['SPY_Price_Change_Pct'].agg(['count', 'mean', 'std', 'min', 'max'])
    
    for year in range(2020, 2030):  # 重點檢查2020-2030年
        if year in yearly_stats.index:
            stats = yearly_stats.loc[year]
            print(f"{year}年：期數={stats['count']}, 平均變化={stats['mean']:.2f}%, 標準差={stats['std']:.2f}%")
    
    # 檢查2026年後的特殊情況
    post_2026_data = market_data[market_data['Year'] >= 2026]
    if len(post_2026_data) > 0:
        print(f"\n=== 2026年後數據分析 ===")
        print(f"2026年後期數：{len(post_2026_data)}")
        
        post_2026_same_price = post_2026_data[post_2026_data['SPY_Price_Change'] == 0]
        print(f"2026年後價格相同期數：{len(post_2026_same_price)}")
        
        if len(post_2026_same_price) == 0:
            print("✅ 2026年後價格相同問題已修正")
        else:
            print("⚠️  2026年後仍有價格相同問題")
            
        # 檢查價格變化多樣性
        unique_changes = len(post_2026_data['SPY_Price_Change_Pct'].unique())
        total_periods = len(post_2026_data)
        diversity_ratio = unique_changes / total_periods
        print(f"2026年後價格變化多樣性：{unique_changes}/{total_periods} = {diversity_ratio:.2%}")
    
    # 輸出前10期和後10期的詳細數據供檢視
    print(f"\n=== 前10期數據樣本 ===")
    sample_columns = ['Period', 'Date_Origin', 'SPY_Price_Origin', 'SPY_Price_End', 'SPY_Price_Change_Pct']
    print(market_data[sample_columns].head(10).to_string(index=False))
    
    print(f"\n=== 後10期數據樣本 ===")
    print(market_data[sample_columns].tail(10).to_string(index=False))
    
    # 債券數據檢查
    print(f"\n=== 債券殖利率變化分析 ===")
    market_data['Bond_Yield_Change'] = market_data['Bond_Yield_End'] - market_data['Bond_Yield_Origin']
    bond_changes = market_data['Bond_Yield_Change']
    
    print(f"債券殖利率變化統計：")
    print(f"  平均變化：{bond_changes.mean():.4f}")
    print(f"  標準差：{bond_changes.std():.4f}")
    print(f"  最大變化：{bond_changes.max():.4f}")
    print(f"  最小變化：{bond_changes.min():.4f}")
    
    same_bond_yield = market_data[market_data['Bond_Yield_Change'] == 0]
    print(f"  殖利率無變化期數：{len(same_bond_yield)}")
    
    print(f"\n=== 測試總結 ===")
    issues_found = []
    
    if len(same_price_periods) > 0:
        issues_found.append(f"股票價格相同問題：{len(same_price_periods)}期")
    
    if len(same_bond_yield) > 0:
        issues_found.append(f"債券殖利率相同問題：{len(same_bond_yield)}期")
    
    if len(issues_found) == 0:
        print("✅ 所有檢查通過，價格生成修正成功！")
        return True
    else:
        print("⚠️  發現以下問題：")
        for issue in issues_found:
            print(f"  - {issue}")
        return False

if __name__ == "__main__":
    success = test_price_generation_fix()
    if success:
        print("\n🎉 價格生成修正測試通過！")
    else:
        print("\n❌ 價格生成修正測試失敗，需要進一步調整。") 