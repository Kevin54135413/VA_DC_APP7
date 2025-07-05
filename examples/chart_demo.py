"""
圖表視覺化模組演示腳本

展示所有8個核心圖表函數的實際效果：
1. create_line_chart() - 線圖
2. create_bar_chart() - 柱狀圖
3. create_scatter_chart() - 散點圖
4. create_strategy_comparison_chart() - 策略比較圖
5. create_drawdown_chart() - 回撤分析圖
6. create_risk_return_scatter() - 風險收益散點圖
7. create_investment_flow_chart() - 投資流圖
8. create_allocation_pie_chart() - 資產配置圓餅圖
"""

import sys
import os
import pandas as pd
import numpy as np

# 添加src路徑以便導入模組
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from models.chart_visualizer import (
    create_line_chart, create_bar_chart, create_scatter_chart,
    create_strategy_comparison_chart, create_drawdown_chart,
    create_risk_return_scatter, create_investment_flow_chart,
    create_allocation_pie_chart, CHART_TYPES, CHART_GLOBAL_CONFIG
)

def create_demo_data():
    """創建演示用的投資策略數據"""
    # 設定隨機種子以確保結果可重現
    np.random.seed(42)
    
    periods = 24  # 2年的月度數據
    
    # VA Rebalance策略數據
    va_rebalance = {
        "Period": range(periods),
        "Cum_Value": np.cumsum(np.random.normal(2000, 1500, periods)) + 100000,
        "Cum_Inv": np.cumsum(np.random.normal(1000, 800, periods)) + 100000,
        "Invested": np.random.normal(1000, 800, periods),
        "Period_Return": np.random.normal(1.2, 2.5, periods),
        "Cumulative_Return": None,  # 稍後計算
        "Annualized_Return": None   # 稍後計算
    }
    
    # 計算衍生欄位
    va_rebalance["Cumulative_Return"] = [
        ((v / i - 1) * 100) if i > 0 else 0 
        for v, i in zip(va_rebalance["Cum_Value"], va_rebalance["Cum_Inv"])
    ]
    
    va_rebalance_df = pd.DataFrame(va_rebalance)
    
    # VA NoSell策略數據（類似但稍有不同）
    va_nosell_df = va_rebalance_df.copy()
    va_nosell_df["Cum_Value"] = va_nosell_df["Cum_Value"] * 0.95  # 較低報酬
    va_nosell_df["Period_Return"] = va_nosell_df["Period_Return"] * 0.9
    va_nosell_df["Cumulative_Return"] = [
        ((v / i - 1) * 100) if i > 0 else 0 
        for v, i in zip(va_nosell_df["Cum_Value"], va_nosell_df["Cum_Inv"])
    ]
    
    # DCA策略數據
    dca_df = va_rebalance_df.copy()
    dca_df["Cum_Value"] = np.cumsum(np.random.normal(1800, 1200, periods)) + 100000
    dca_df["Cum_Inv"] = [100000 + i * 2000 for i in range(periods)]  # 定額投資
    dca_df["Invested"] = [2000] * periods  # 每期固定投資2000
    dca_df["Period_Return"] = np.random.normal(0.8, 2.0, periods)
    dca_df["Cumulative_Return"] = [
        ((v / i - 1) * 100) if i > 0 else 0 
        for v, i in zip(dca_df["Cum_Value"], dca_df["Cum_Inv"])
    ]
    
    # 摘要數據
    summary_data = {
        "Strategy": ["VA_Rebalance", "VA_NoSell", "DCA"],
        "Final_Value": [va_rebalance_df["Cum_Value"].iloc[-1], 
                       va_nosell_df["Cum_Value"].iloc[-1], 
                       dca_df["Cum_Value"].iloc[-1]],
        "Total_Investment": [va_rebalance_df["Cum_Inv"].iloc[-1], 
                           va_nosell_df["Cum_Inv"].iloc[-1], 
                           dca_df["Cum_Inv"].iloc[-1]],
        "Annualized_Return": [8.5, 6.8, 7.2],
        "Volatility": [15.2, 18.5, 12.8],
        "Sharpe_Ratio": [0.42, 0.25, 0.38],
        "Max_Drawdown": [-12.5, -18.2, -8.9]
    }
    summary_df = pd.DataFrame(summary_data)
    summary_df["Total_Return"] = [
        ((fv / ti - 1) * 100) if ti > 0 else 0 
        for fv, ti in zip(summary_df["Final_Value"], summary_df["Total_Investment"])
    ]
    
    return va_rebalance_df, va_nosell_df, dca_df, summary_df

def demo_all_charts():
    """演示所有圖表函數"""
    print("🎨 圖表視覺化模組演示")
    print("=" * 50)
    
    # 準備演示數據
    va_rebalance, va_nosell, dca, summary = create_demo_data()
    print("✓ 演示數據準備完成")
    
    charts_created = []
    
    # 1. 線圖演示
    print("\n📈 1. 線圖演示 (create_line_chart)")
    line_chart = create_line_chart(
        va_rebalance, 
        "Period", 
        "Cum_Value", 
        title="累積資產價值趨勢"
    )
    charts_created.append(("線圖", line_chart))
    print("✓ 累積資產價值線圖創建完成")
    
    # 2. 柱狀圖演示
    print("\n📊 2. 柱狀圖演示 (create_bar_chart)")
    bar_chart = create_bar_chart(
        va_rebalance.head(12),  # 只顯示前12期
        "Period", 
        "Period_Return", 
        title="期間報酬率分析"
    )
    charts_created.append(("柱狀圖", bar_chart))
    print("✓ 期間報酬率柱狀圖創建完成")
    
    # 3. 散點圖演示
    print("\n🔍 3. 散點圖演示 (create_scatter_chart)")
    scatter_chart = create_scatter_chart(
        summary, 
        "Volatility", 
        "Annualized_Return",
        size_field="Final_Value",
        color_field="Strategy",
        title="風險收益關係分析"
    )
    charts_created.append(("散點圖", scatter_chart))
    print("✓ 風險收益散點圖創建完成")
    
    # 4. 策略比較圖演示
    print("\n🔄 4. 策略比較圖演示 (create_strategy_comparison_chart)")
    comparison_chart = create_strategy_comparison_chart(
        va_rebalance_df=va_rebalance,
        va_nosell_df=va_nosell,
        dca_df=dca,
        chart_type="cumulative_value"
    )
    charts_created.append(("策略比較圖", comparison_chart))
    print("✓ 累積資產價值策略比較圖創建完成")
    
    # 5. 回撤分析圖演示
    print("\n📉 5. 回撤分析圖演示 (create_drawdown_chart)")
    # 創建有明顯回撤的數據
    drawdown_data = va_rebalance.copy()
    # 在期間10-15製造一個回撤
    for i in range(10, 16):
        drawdown_data.loc[i, "Cum_Value"] = drawdown_data.loc[i, "Cum_Value"] * (0.85 + (i-10)*0.03)
    
    drawdown_chart = create_drawdown_chart(drawdown_data, "VA Rebalance")
    charts_created.append(("回撤分析圖", drawdown_chart))
    print("✓ 回撤分析圖創建完成")
    
    # 6. 風險收益散點圖演示
    print("\n⚖️ 6. 風險收益散點圖演示 (create_risk_return_scatter)")
    risk_return_chart = create_risk_return_scatter(summary)
    charts_created.append(("風險收益散點圖", risk_return_chart))
    print("✓ 策略風險收益散點圖創建完成")
    
    # 7. 投資流圖演示
    print("\n💰 7. 投資流圖演示 (create_investment_flow_chart)")
    flow_chart = create_investment_flow_chart(va_rebalance.head(12))
    charts_created.append(("投資流圖", flow_chart))
    print("✓ VA策略投資流圖創建完成")
    
    # 8. 資產配置圓餅圖演示
    print("\n🥧 8. 資產配置圓餅圖演示 (create_allocation_pie_chart)")
    allocation_chart = create_allocation_pie_chart(0.6, 0.4)
    charts_created.append(("資產配置圓餅圖", allocation_chart))
    print("✓ 60/40資產配置圓餅圖創建完成")
    
    # 演示結果總結
    print("\n" + "=" * 50)
    print("🎉 圖表演示完成！")
    print(f"✅ 成功創建 {len(charts_created)} 個不同類型的圖表")
    
    print("\n📋 創建的圖表類型：")
    for i, (chart_type, chart) in enumerate(charts_created, 1):
        print(f"  {i}. {chart_type}")
    
    print("\n🎯 技術特點展示：")
    print("  ✓ 使用Altair建立互動式圖表")
    print("  ✓ 支援縮放、平移、tooltip等互動功能")
    print("  ✓ 移動端友善的響應式設計")
    print("  ✓ 完整的錯誤處理和數據驗證")
    print("  ✓ 統一的視覺化風格和配色方案")
    print("  ✓ 多策略數據比較功能")
    print("  ✓ 專業的金融圖表類型支援")
    
    return charts_created

def demo_configuration():
    """演示圖表配置功能"""
    print("\n⚙️ 圖表配置演示")
    print("-" * 30)
    
    print(f"📊 支援的圖表類型 ({len(CHART_TYPES)} 種):")
    for chart_type, config in CHART_TYPES.items():
        print(f"  • {chart_type}: {config['title']}")
    
    print(f"\n🎨 全域配置 ({len(CHART_GLOBAL_CONFIG)} 項):")
    for key, value in CHART_GLOBAL_CONFIG.items():
        print(f"  • {key}: {value}")

def demo_chart_types():
    """演示不同的圖表類型比較"""
    print("\n🔍 不同圖表類型比較演示")
    print("-" * 40)
    
    va_rebalance, va_nosell, dca, summary = create_demo_data()
    
    # 演示相同數據的不同圖表類型
    chart_types = ["cumulative_value", "cumulative_return", "period_return"]
    
    for chart_type in chart_types:
        print(f"\n📈 {chart_type} 比較圖:")
        chart = create_strategy_comparison_chart(
            va_rebalance_df=va_rebalance,
            va_nosell_df=va_nosell,
            dca_df=dca,
            chart_type=chart_type
        )
        print(f"✓ {CHART_TYPES[chart_type]['title']} 創建完成")

if __name__ == "__main__":
    print("🚀 開始圖表視覺化模組演示")
    print("此演示將展示所有8個核心圖表函數的功能")
    print("=" * 60)
    
    try:
        # 主要演示
        charts = demo_all_charts()
        
        # 配置演示
        demo_configuration()
        
        # 圖表類型比較演示
        demo_chart_types()
        
        print("\n" + "=" * 60)
        print("🎊 演示完成！圖表視覺化模組功能展示結束")
        print("💡 提示: 在Streamlit或Jupyter環境中，這些圖表將顯示為完全互動式的視覺化元件")
        
    except Exception as e:
        print(f"\n❌ 演示過程中出現錯誤: {e}")
        print("請檢查依賴項和模組路徑是否正確") 