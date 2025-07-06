"""
圖表視覺化模組 (Chart Visualizer Module)

本模組提供投資策略比較系統的圖表視覺化功能，包括：
- 基礎圖表生成 (create_line_chart, create_bar_chart, create_scatter_chart)
- 策略比較圖表 (create_strategy_comparison_chart)
- 專業分析圖表 (create_drawdown_chart, create_risk_return_scatter)
- 投資流分析圖表 (create_investment_flow_chart, create_allocation_pie_chart)

嚴格遵循需求文件第2章第2.3節的規格要求，使用Altair建立互動式圖表。
"""

import altair as alt
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Union
import logging

# 設置日誌
logger = logging.getLogger(__name__)

# ============================================================================
# 2.3 圖表架構與視覺化模組 - 配置定義
# ============================================================================

# 主要圖表類型定義
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

# 圖表全域配置
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

# ============================================================================
# 2.3.2 Altair圖表生成模組 - 基礎圖表生成器
# ============================================================================

def create_line_chart(data_df: pd.DataFrame, 
                     x_field: str, 
                     y_field: str, 
                     color_field: Optional[str] = None, 
                     title: str = "") -> alt.Chart:
    """
    創建線圖
    
    Args:
        data_df: 數據DataFrame
        x_field: X軸欄位名
        y_field: Y軸欄位名
        color_field: 分組顏色欄位
        title: 圖表標題
    
    Returns:
        alt.Chart: Altair線圖對象
    """
    logger.info(f"創建線圖: {title}, 數據行數: {len(data_df)}")
    
    if data_df is None or len(data_df) == 0:
        logger.warning("數據為空，返回空圖表")
        return alt.Chart().mark_text(text="No data available")
    
    try:
        # 確保必要欄位存在
        if x_field not in data_df.columns or y_field not in data_df.columns:
            logger.error(f"缺少必要欄位: {x_field}, {y_field}")
            return alt.Chart().mark_text(text=f"Missing fields: {x_field}, {y_field}")
        
        # 創建基礎圖表
        chart = alt.Chart(data_df).mark_line(
            point=True,
            strokeWidth=2
        ).add_selection(
            alt.selection_interval(bind='scales')
        ).encode(
            x=alt.X(f"{x_field}:Q", title=x_field.replace("_", " ").title()),
            y=alt.Y(f"{y_field}:Q", title=y_field.replace("_", " ").title()),
            color=alt.Color(f"{color_field}:N") if color_field and color_field in data_df.columns else alt.value("steelblue"),
            tooltip=[x_field, y_field] + ([color_field] if color_field and color_field in data_df.columns else [])
        ).properties(
            title=title,
            width=CHART_GLOBAL_CONFIG["width"],
            height=CHART_GLOBAL_CONFIG["height"]
        )
        
        logger.info("線圖創建成功")
        return chart
        
    except Exception as e:
        logger.error(f"創建線圖時出現錯誤: {e}")
        return alt.Chart().mark_text(text=f"Chart error: {str(e)}")

def create_bar_chart(data_df: pd.DataFrame, 
                    x_field: str, 
                    y_field: str, 
                    color_field: Optional[str] = None, 
                    title: str = "") -> alt.Chart:
    """
    創建柱狀圖
    
    Args:
        data_df: 數據DataFrame
        x_field: X軸欄位名
        y_field: Y軸欄位名
        color_field: 分組顏色欄位
        title: 圖表標題
    
    Returns:
        alt.Chart: Altair柱狀圖對象
    """
    logger.info(f"創建柱狀圖: {title}, 數據行數: {len(data_df)}")
    
    if data_df is None or len(data_df) == 0:
        logger.warning("數據為空，返回空圖表")
        return alt.Chart().mark_text(text="No data available")
    
    try:
        # 確保必要欄位存在
        if x_field not in data_df.columns or y_field not in data_df.columns:
            logger.error(f"缺少必要欄位: {x_field}, {y_field}")
            return alt.Chart().mark_text(text=f"Missing fields: {x_field}, {y_field}")
        
        # 創建基礎圖表 - 修正顏色可讀性
        base_chart = alt.Chart(data_df).mark_bar(
            opacity=0.8,
            stroke='white',
            strokeWidth=1
        ).encode(
            x=alt.X(f"{x_field}:Q", title=x_field.replace("_", " ").title()),
            y=alt.Y(f"{y_field}:Q", title=y_field.replace("_", " ").title()),
            color=alt.Color(f"{color_field}:N", scale=alt.Scale(range=['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728'])) if color_field and color_field in data_df.columns else alt.value("#4c78a8"),
            tooltip=[x_field, y_field] + ([color_field] if color_field and color_field in data_df.columns else [])
        ).properties(
            title=title,
            width=CHART_GLOBAL_CONFIG["width"], 
            height=CHART_GLOBAL_CONFIG["height"]
        )
        
        # 添加數值標籤 - 確保文字可見性
        text_chart = alt.Chart(data_df).mark_text(
            align='center',
            baseline='middle',
            dy=-10,  # 文字位置稍微上移
            fontSize=12,
            fontWeight='bold',
            color='black'  # 強制使用黑色文字確保可見
        ).encode(
            x=alt.X(f"{x_field}:Q"),
            y=alt.Y(f"{y_field}:Q"),
            text=alt.Text(f"{y_field}:Q", format='.1f')
        )
        
        # 組合圖表和文字標籤
        chart = base_chart + text_chart
        
        logger.info("柱狀圖創建成功")
        return chart
        
    except Exception as e:
        logger.error(f"創建柱狀圖時出現錯誤: {e}")
        return alt.Chart().mark_text(text=f"Chart error: {str(e)}")

def create_scatter_chart(data_df: pd.DataFrame, 
                        x_field: str, 
                        y_field: str, 
                        size_field: Optional[str] = None, 
                        color_field: Optional[str] = None, 
                        title: str = "") -> alt.Chart:
    """
    創建散點圖
    
    Args:
        data_df: 數據DataFrame
        x_field: X軸欄位名
        y_field: Y軸欄位名
        size_field: 點大小欄位
        color_field: 點顏色欄位
        title: 圖表標題
    
    Returns:
        alt.Chart: Altair散點圖對象
    """
    logger.info(f"創建散點圖: {title}, 數據行數: {len(data_df)}")
    
    if data_df is None or len(data_df) == 0:
        logger.warning("數據為空，返回空圖表")
        return alt.Chart().mark_text(text="No data available")
    
    try:
        # 確保必要欄位存在
        if x_field not in data_df.columns or y_field not in data_df.columns:
            logger.error(f"缺少必要欄位: {x_field}, {y_field}")
            return alt.Chart().mark_text(text=f"Missing fields: {x_field}, {y_field}")
        
        # 構建編碼配置
        encoding = {
            "x": alt.X(f"{x_field}:Q", title=x_field.replace("_", " ").title()),
            "y": alt.Y(f"{y_field}:Q", title=y_field.replace("_", " ").title()),
            "tooltip": [x_field, y_field]
        }
        
        if size_field and size_field in data_df.columns:
            encoding["size"] = alt.Size(f"{size_field}:Q", title=size_field.replace("_", " ").title())
            encoding["tooltip"].append(size_field)
        
        if color_field and color_field in data_df.columns:
            encoding["color"] = alt.Color(f"{color_field}:N")
            encoding["tooltip"].append(color_field)
        
        # 創建散點圖
        chart = alt.Chart(data_df).mark_circle(
            size=100,
            opacity=0.7
        ).encode(**encoding).properties(
            title=title,
            width=CHART_GLOBAL_CONFIG["width"],
            height=CHART_GLOBAL_CONFIG["height"] 
        )
        
        logger.info("散點圖創建成功")
        return chart
        
    except Exception as e:
        logger.error(f"創建散點圖時出現錯誤: {e}")
        return alt.Chart().mark_text(text=f"Chart error: {str(e)}")

# ============================================================================
# 2.3.2 策略比較圖表生成器
# ============================================================================

def create_strategy_comparison_chart(va_rebalance_df: Optional[pd.DataFrame] = None,
                                   va_nosell_df: Optional[pd.DataFrame] = None, 
                                   dca_df: Optional[pd.DataFrame] = None, 
                                   chart_type: str = "cumulative_value") -> alt.Chart:
    """
    創建策略比較圖表
    
    Args:
        va_rebalance_df: VA Rebalance策略數據
        va_nosell_df: VA NoSell策略數據
        dca_df: DCA策略數據
        chart_type: 圖表類型（來自CHART_TYPES）
    
    Returns:
        alt.Chart: Altair圖表對象
    """
    logger.info(f"創建策略比較圖表: {chart_type}")
    
    # 驗證圖表類型
    if chart_type not in CHART_TYPES:
        logger.error(f"未支援的圖表類型: {chart_type}")
        return alt.Chart().mark_text(text=f"Unsupported chart type: {chart_type}")
    
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
            # 確保必要欄位存在
            if chart_config["x_field"] in df.columns and chart_config["y_field"] in df.columns:
                strategy_data = df.copy()
                strategy_data["Strategy"] = strategy_name
                comparison_data.append(strategy_data)
                logger.info(f"添加策略數據: {strategy_name}, 行數: {len(strategy_data)}")
    
    if not comparison_data:
        logger.warning("沒有可用的策略數據")
        return alt.Chart().mark_text(text="No strategy data available")
    
    # 合併所有策略數據
    combined_df = pd.concat(comparison_data, ignore_index=True)
    logger.info(f"合併後數據行數: {len(combined_df)}")
    
    try:
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
        else:
            logger.warning(f"圖表類型 {chart_config['chart_type']} 在策略比較中不受支援")
            return create_line_chart(
                combined_df,
                chart_config["x_field"],
                chart_config["y_field"],
                "Strategy",
                chart_config["title"]
            )
    
    except Exception as e:
        logger.error(f"創建策略比較圖表時出現錯誤: {e}")
        return alt.Chart().mark_text(text=f"Strategy comparison error: {str(e)}")

# ============================================================================
# 2.3.3 進階圖表功能模組
# ============================================================================

def create_drawdown_chart(strategy_df: pd.DataFrame, 
                         strategy_name: str) -> alt.Chart:
    """
    創建回撤分析圖表
    
    Args:
        strategy_df: 策略數據DataFrame
        strategy_name: 策略名稱
    
    Returns:
        alt.Chart: 回撤分析圖表
    """
    logger.info(f"創建回撤分析圖表: {strategy_name}")
    
    if strategy_df is None or len(strategy_df) < 2:
        logger.warning("數據不足，無法進行回撤分析")
        return alt.Chart().mark_text(text="Insufficient data for drawdown analysis")
    
    try:
        # 確保Cum_Value欄位存在
        if "Cum_Value" not in strategy_df.columns:
            logger.error("缺少Cum_Value欄位")
            return alt.Chart().mark_text(text="Missing Cum_Value field")
        
        # 計算回撤序列
        cumulative_values = strategy_df["Cum_Value"].values
        running_max = np.maximum.accumulate(cumulative_values)
        drawdown = (cumulative_values - running_max) / running_max * 100
        
        # 創建回撤數據框
        drawdown_df = pd.DataFrame({
            "Period": strategy_df["Period"] if "Period" in strategy_df.columns else range(len(strategy_df)),
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
        
        # 合併圖表
        combined_chart = (drawdown_chart + zero_line).properties(
            title=f"{strategy_name} Drawdown Analysis",
            width=CHART_GLOBAL_CONFIG["width"],
            height=CHART_GLOBAL_CONFIG["height"]
        )
        
        logger.info("回撤分析圖表創建成功")
        return combined_chart
        
    except Exception as e:
        logger.error(f"創建回撤分析圖表時出現錯誤: {e}")
        return alt.Chart().mark_text(text=f"Drawdown chart error: {str(e)}")

def create_risk_return_scatter(summary_df: pd.DataFrame) -> alt.Chart:
    """
    創建風險收益散點圖
    
    Args:
        summary_df: 綜合比較摘要DataFrame
    
    Returns:
        alt.Chart: 風險收益散點圖
    """
    logger.info("創建風險收益散點圖")
    
    if summary_df is None or len(summary_df) == 0:
        logger.warning("摘要數據為空")
        return alt.Chart().mark_text(text="No summary data available")
    
    try:
        # 確保必要欄位存在
        required_fields = ["Volatility", "Annualized_Return", "Strategy"]
        missing_fields = [field for field in required_fields if field not in summary_df.columns]
        
        if missing_fields:
            logger.error(f"缺少必要欄位: {missing_fields}")
            return alt.Chart().mark_text(text=f"Missing fields: {', '.join(missing_fields)}")
        
        # 創建散點圖
        chart = alt.Chart(summary_df).mark_circle(
            size=200,
            opacity=0.8
        ).encode(
            x=alt.X("Volatility:Q", title="Volatility (%)"),
            y=alt.Y("Annualized_Return:Q", title="Annualized Return (%)"),
            color=alt.Color("Strategy:N", title="Strategy"),
            size=alt.Size("Final_Value:Q", title="Final Value ($)") if "Final_Value" in summary_df.columns else alt.value(200),
            tooltip=["Strategy", "Volatility", "Annualized_Return"] + 
                   (["Final_Value"] if "Final_Value" in summary_df.columns else []) +
                   (["Sharpe_Ratio"] if "Sharpe_Ratio" in summary_df.columns else [])
        ).properties(
            title="Risk vs Return Analysis",
            width=CHART_GLOBAL_CONFIG["width"],
            height=CHART_GLOBAL_CONFIG["height"]
        )
        
        logger.info("風險收益散點圖創建成功")
        return chart
        
    except Exception as e:
        logger.error(f"創建風險收益散點圖時出現錯誤: {e}")
        return alt.Chart().mark_text(text=f"Risk-return chart error: {str(e)}")

# ============================================================================
# 投資流分析圖表
# ============================================================================

def create_investment_flow_chart(va_df: pd.DataFrame) -> alt.Chart:
    """
    創建VA策略投資流圖表（顯示買入/賣出）
    
    Args:
        va_df: VA策略數據DataFrame
    
    Returns:
        alt.Chart: 投資流圖表
    """
    logger.info("創建VA策略投資流圖表")
    
    if va_df is None or len(va_df) == 0:
        logger.warning("VA數據為空")
        return alt.Chart().mark_text(text="No VA data available")
    
    try:
        # 確保Invested欄位存在
        if "Invested" not in va_df.columns:
            logger.error("缺少Invested欄位")
            return alt.Chart().mark_text(text="Missing Invested field")
        
        # 為正負投資額設置不同顏色
        va_df_copy = va_df.copy()
        va_df_copy["Investment_Type"] = va_df_copy["Invested"].apply(
            lambda x: "Buy" if x > 0 else "Sell" if x < 0 else "Hold"
        )
        
        # 確保Period欄位存在
        if "Period" not in va_df_copy.columns:
            va_df_copy["Period"] = range(len(va_df_copy))
        
        # 創建投資流圖表
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
        
        logger.info("投資流圖表創建成功")
        return chart
        
    except Exception as e:
        logger.error(f"創建投資流圖表時出現錯誤: {e}")
        return alt.Chart().mark_text(text=f"Investment flow chart error: {str(e)}")

def create_allocation_pie_chart(stock_ratio: float, bond_ratio: float) -> alt.Chart:
    """
    創建資產配置圓餅圖
    
    Args:
        stock_ratio: 股票比例 (0-1)
        bond_ratio: 債券比例 (0-1)
    
    Returns:
        alt.Chart: 圓餅圖
    """
    logger.info(f"創建資產配置圓餅圖: 股票={stock_ratio:.2%}, 債券={bond_ratio:.2%}")
    
    try:
        # 驗證比例數據
        if stock_ratio < 0 or bond_ratio < 0 or (stock_ratio + bond_ratio) <= 0:
            logger.error("無效的資產配置比例")
            return alt.Chart().mark_text(text="Invalid allocation ratios")
        
        # 標準化比例（確保總和為100%）
        total_ratio = stock_ratio + bond_ratio
        stock_pct = (stock_ratio / total_ratio) * 100
        bond_pct = (bond_ratio / total_ratio) * 100
        
        # 創建配置數據
        allocation_data = pd.DataFrame({
            "Asset": ["Stock (SPY)", "Bond"], 
            "Ratio": [stock_pct, bond_pct],
            "Color": ["#1f77b4", "#ff7f0e"]
        })
        
        # 創建圓餅圖
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
        
        logger.info("資產配置圓餅圖創建成功")
        return chart
        
    except Exception as e:
        logger.error(f"創建資產配置圓餅圖時出現錯誤: {e}")
        return alt.Chart().mark_text(text=f"Allocation chart error: {str(e)}")

# ============================================================================
# 工具函數
# ============================================================================

def validate_chart_data(data_df: pd.DataFrame, required_fields: List[str]) -> bool:
    """
    驗證圖表數據完整性
    
    Args:
        data_df: 數據DataFrame
        required_fields: 必要欄位列表
    
    Returns:
        bool: 數據是否有效
    """
    if data_df is None or len(data_df) == 0:
        return False
    
    missing_fields = [field for field in required_fields if field not in data_df.columns]
    if missing_fields:
        logger.warning(f"缺少欄位: {missing_fields}")
        return False
    
    return True

def get_available_chart_types() -> List[str]:
    """
    獲取可用的圖表類型列表
    
    Returns:
        List[str]: 圖表類型列表
    """
    return list(CHART_TYPES.keys())

def get_chart_config(chart_type: str) -> Dict[str, Any]:
    """
    獲取圖表配置
    
    Args:
        chart_type: 圖表類型
    
    Returns:
        Dict: 圖表配置字典
    """
    return CHART_TYPES.get(chart_type, {})

# ============================================================================
# 測試函數
# ============================================================================

def test_chart_visualizer():
    """測試圖表視覺化模組的基本功能"""
    print("🔍 測試圖表視覺化模組")
    
    try:
        # 測試圖表配置
        assert len(CHART_TYPES) == 7
        assert "cumulative_value" in CHART_TYPES
        assert CHART_GLOBAL_CONFIG["width"] == 700
        print("✓ 圖表配置測試通過")
        
        # 測試工具函數
        chart_types = get_available_chart_types()
        assert len(chart_types) == 7
        
        config = get_chart_config("cumulative_value")
        assert config["title"] == "Cumulative Asset Value Comparison"
        print("✓ 工具函數測試通過")
        
        # 測試數據驗證
        test_df = pd.DataFrame({"Period": [1, 2, 3], "Cum_Value": [100, 110, 120]})
        assert validate_chart_data(test_df, ["Period", "Cum_Value"]) == True
        assert validate_chart_data(test_df, ["Period", "Missing_Field"]) == False
        print("✓ 數據驗證測試通過")
        
        print("✅ 圖表視覺化模組測試完成！")
        
    except Exception as e:
        print(f"❌ 圖表視覺化模組測試失敗: {e}")
        raise

if __name__ == "__main__":
    test_chart_visualizer()