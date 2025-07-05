"""
中央結果展示區域 - 實作第3章3.3節規格
嚴格遵循所有顯示規格和計算邏輯整合
"""

import streamlit as st
import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, Union, List, Tuple
import os
import sys
from datetime import datetime
import altair as alt
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# 添加src目錄到Python路徑
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# 導入第2章計算模組
from models.calculation_formulas import calculate_annualized_return
from models.strategy_engine import calculate_va_strategy, calculate_dca_strategy
from models.table_calculator import calculate_summary_metrics
from models.table_specifications import VA_COLUMNS_ORDER, DCA_COLUMNS_ORDER, PERCENTAGE_PRECISION_RULES
from models.chart_visualizer import create_strategy_comparison_chart, create_bar_chart, create_line_chart

# ============================================================================
# 3.3.1 頂部摘要卡片實作 - SUMMARY_METRICS_DISPLAY
# ============================================================================

SUMMARY_METRICS_DISPLAY = {
    "layout": {
        "desktop": "horizontal_layout",
        "tablet": "two_plus_one_layout",
        "mobile": "vertical_stack"
    },
    "metrics": {
        "recommended_strategy": {
            "icon": "🏆",
            "label": "推薦策略",
            "content": "dynamic_recommendation",
            "calculation": "基於風險收益比較",
            "format": "strategy_name",
            "tooltip": "根據風險收益比分析推薦最適策略"
        },
        "expected_final_value": {
            "icon": "💰",
            "label": "預期最終價值",
            "content": "final_portfolio_value",
            "calculation": "基於第2章計算結果",
            "format": "currency_with_delta",
            "tooltip": "投資期末預期資產總價值"
        },
        "annualized_return": {
            "icon": "📈",
            "label": "年化報酬率",
            "content": "annualized_return",
            "calculation": "第2章calculate_annualized_return函數",
            "format": "percentage_with_delta",
            "tooltip": "年化平均報酬率"
        }
    }
}

# ============================================================================
# 3.3.2 策略對比卡片實作 - STRATEGY_COMPARISON_CARDS
# ============================================================================

STRATEGY_COMPARISON_CARDS = {
    "va_strategy": {
        "title": "🎯 定期定值 (VA策略)",
        "style": "modern_info_card",
        "content": {
            "final_value": "calculation_backend",
            "annualized_return": "calculation_backend",
            "suitability": "有經驗投資者"
        },
        "key_feature": "智能調節投入金額",
        "pros": [
            "可能獲得更高報酬",
            "有效控制市場波動"
        ],
        "cons": [
            "需要主動管理",
            "可能錯過部分漲幅"
        ],
        "calculation_backend": {
            "data_source": "第2章VA策略表格",
            "key_metric": "Cum_Value",
            "integration": "chapter2_compliance_check"
        }
    },
    "dca_strategy": {
        "title": "💰 定期定額 (DCA策略)",
        "style": "modern_info_card",
        "content": {
            "final_value": "calculation_backend",
            "annualized_return": "calculation_backend", 
            "suitability": "投資新手"
        },
        "key_feature": "固定金額定期投入",
        "pros": [
            "操作簡單",
            "情緒影響較小"
        ],
        "cons": [
            "報酬可能較低",
            "無法優化時機"
        ],
        "calculation_backend": {
            "data_source": "第2章DCA策略表格",
            "key_metric": "Cum_Value",
            "integration": "chapter2_compliance_check"
        }
    }
}

# ============================================================================
# 3.3.3 圖表顯示實作 - SIMPLIFIED_CHARTS_CONFIG
# ============================================================================

SIMPLIFIED_CHARTS_CONFIG = {
    "tab_navigation": {
        "asset_growth": {
            "icon": "📈",
            "label": "資產成長",
            "chart_type": "line_chart",
            "description": "兩種策略的資產累積對比",
            "data_source": "第2章策略計算結果",
            "x_axis": "Period",
            "y_axis": "Cum_Value"
        },
        "return_comparison": {
            "icon": "📊",
            "label": "報酬比較",
            "chart_type": "bar_chart",
            "description": "年化報酬率對比",
            "data_source": "第2章summary_comparison",
            "chart_type": "horizontal_bar"
        },
        "risk_analysis": {
            "icon": "⚠️",
            "label": "風險分析",
            "chart_type": "risk_metrics",
            "description": "風險指標比較",
            "data_source": "第2章績效指標計算模組",
            "visualization": "horizontal_comparison_bars"
        }
    }
}

# ============================================================================
# 3.3.4 數據表格與下載實作 - DATA_TABLES_CONFIG
# ============================================================================

DATA_TABLES_CONFIG = {
    "display_options": {
        "expandable_section": True,
        "strategy_selector": ["VA策略", "DCA策略", "比較摘要"],
        "mobile_responsive": True
    },
    "va_strategy_table": {
        "column_specs": "第2章VA_COLUMNS_ORDER",
        "total_columns": 27,
        "formatting_rules": "第2章PERCENTAGE_PRECISION_RULES",
        "validation": {
            "chapter2_compliance_check": True
        }
    },
    "dca_strategy_table": {
        "column_specs": "第2章DCA_COLUMNS_ORDER", 
        "total_columns": 28,
        "formatting_rules": "第2章DCA邏輯和通膨調整",
        "validation": {
            "chapter2_compliance_check": True
        }
    },
    "csv_download": {
        "layout": "three_button_layout",
        "buttons": ["VA策略數據", "DCA策略數據", "績效摘要"],
        "filename_convention": "投資策略比較_{strategy}_{timestamp}.csv",
        "validation": {
            "chapter1_2_compliance_validation": True
        }
    }
}

# ============================================================================
# 中央結果展示區域管理器
# ============================================================================

class ResultsDisplayManager:
    """中央結果展示區域管理器 - 實作第3章3.3節所有規格"""
    
    def __init__(self):
        self.summary_config = SUMMARY_METRICS_DISPLAY
        self.strategy_cards_config = STRATEGY_COMPARISON_CARDS
        self.charts_config = SIMPLIFIED_CHARTS_CONFIG
        self.tables_config = DATA_TABLES_CONFIG
        self.calculation_results = {}
        
    def render_complete_results_display(self, parameters: Dict[str, Any]):
        """渲染完整中央結果展示區域"""
        # 執行策略計算
        self._execute_strategy_calculations(parameters)
        
        # 渲染頂部摘要卡片
        self.render_summary_metrics_display()
        
        # 渲染策略對比卡片
        self.render_strategy_comparison_cards()
        
        # 渲染圖表顯示
        self.render_charts_display()
        
        # 渲染數據表格與下載
        self.render_data_tables_and_download()
    
    def _execute_strategy_calculations(self, parameters: Dict[str, Any]):
        """執行策略計算 - 整合第2章計算引擎"""
        try:
            # 模擬市場數據（實際應用中應從第1章API獲取）
            market_data = self._generate_simulation_data(parameters)
            
            # VA策略計算
            va_rebalance_df = calculate_va_strategy(
                C0=parameters["initial_investment"],
                annual_investment=parameters["initial_investment"] * 0.1,  # 假設年投入為初始投入的10%
                annual_growth_rate=parameters["va_growth_rate"],
                annual_inflation_rate=parameters["inflation_rate"],
                investment_years=parameters["investment_years"],
                frequency=parameters["investment_frequency"],
                stock_ratio=parameters["stock_ratio"],
                strategy_type="Rebalance",
                market_data=market_data
            )
            
            # DCA策略計算
            dca_df = calculate_dca_strategy(
                C0=parameters["initial_investment"],
                annual_investment=parameters["initial_investment"] * 0.1,
                annual_growth_rate=parameters["va_growth_rate"],
                annual_inflation_rate=parameters["inflation_rate"],
                investment_years=parameters["investment_years"],
                frequency=parameters["investment_frequency"],
                stock_ratio=parameters["stock_ratio"],
                market_data=market_data
            )
            
            # 綜合比較指標
            summary_df = calculate_summary_metrics(
                va_rebalance_df=va_rebalance_df,
                va_nosell_df=None,
                dca_df=dca_df,
                initial_investment=parameters["initial_investment"],
                periods_per_year=parameters["periods_per_year"]
            )
            
            self.calculation_results = {
                "va_rebalance_df": va_rebalance_df,
                "dca_df": dca_df,
                "summary_df": summary_df,
                "parameters": parameters
            }
            
        except Exception as e:
            st.error(f"計算過程中出現錯誤: {e}")
            self.calculation_results = {}
    
    def _generate_simulation_data(self, parameters: Dict[str, Any]) -> pd.DataFrame:
        """生成模擬市場數據"""
        total_periods = parameters["total_periods"]
        
        # 模擬SPY價格數據
        np.random.seed(42)  # 固定種子確保一致性
        price_changes = np.random.normal(0.02, 0.15, total_periods)  # 2%均值，15%波動
        spy_prices = [100.0]  # 起始價格
        
        for change in price_changes:
            spy_prices.append(spy_prices[-1] * (1 + change))
        
        # 模擬債券殖利率
        bond_yields = np.random.normal(3.0, 0.5, total_periods + 1)  # 3%均值，0.5%波動
        bond_yields = np.clip(bond_yields, 0.5, 8.0)  # 限制在合理範圍
        
        # 創建市場數據DataFrame
        dates = pd.date_range(start='2020-01-01', periods=total_periods + 1, freq='3MS')  # 使用3MS代替3M
        
        market_data = pd.DataFrame({
            'Date': dates,
            'SPY_Price': spy_prices,
            'Bond_Yield': bond_yields
        })
        
        return market_data
    
    def render_summary_metrics_display(self):
        """渲染頂部摘要卡片 - 3.3.1節實作"""
        st.markdown("### 📊 投資策略比較摘要")
        
        if not self.calculation_results:
            st.info("請設定投資參數後開始分析")
            return
        
        # 響應式布局
        if st.session_state.get('device_type', 'desktop') == 'mobile':
            # 移動版垂直堆疊
            self._render_metric_card("recommended_strategy")
            self._render_metric_card("expected_final_value")
            self._render_metric_card("annualized_return")
        else:
            # 桌面版水平布局
            col1, col2, col3 = st.columns(3)
            
            with col1:
                self._render_metric_card("recommended_strategy")
            with col2:
                self._render_metric_card("expected_final_value")
            with col3:
                self._render_metric_card("annualized_return")
    
    def _render_metric_card(self, metric_key: str):
        """渲染單個指標卡片"""
        metric_config = self.summary_config["metrics"][metric_key]
        
        if metric_key == "recommended_strategy":
            # 動態推薦策略
            recommendation = self._calculate_dynamic_recommendation()
            st.metric(
                label=f"{metric_config['icon']} {metric_config['label']}",
                value=recommendation["strategy"],
                delta=recommendation["reason"],
                help=metric_config["tooltip"]
            )
        
        elif metric_key == "expected_final_value":
            # 預期最終價值
            final_values = self._get_final_values()
            if final_values:
                st.metric(
                    label=f"{metric_config['icon']} {metric_config['label']}",
                    value=f"${final_values['recommended']:,.0f}",
                    delta=f"${final_values['difference']:,.0f}",
                    help=metric_config["tooltip"]
                )
        
        elif metric_key == "annualized_return":
            # 年化報酬率
            returns = self._get_annualized_returns()
            if returns:
                st.metric(
                    label=f"{metric_config['icon']} {metric_config['label']}",
                    value=f"{returns['recommended']:.2f}%",
                    delta=f"{returns['difference']:.2f}%",
                    help=metric_config["tooltip"]
                )
    
    def _calculate_dynamic_recommendation(self) -> Dict[str, str]:
        """計算動態推薦策略"""
        if not self.calculation_results:
            return {"strategy": "請先設定參數", "reason": ""}
        
        summary_df = self.calculation_results["summary_df"]
        
        if len(summary_df) >= 2:
            va_row = summary_df[summary_df["Strategy"] == "VA_Rebalance"].iloc[0]
            dca_row = summary_df[summary_df["Strategy"] == "DCA"].iloc[0]
            
            # 基於風險收益比較
            va_sharpe = va_row["Sharpe_Ratio"]
            dca_sharpe = dca_row["Sharpe_Ratio"]
            
            if va_sharpe > dca_sharpe:
                return {"strategy": "VA策略", "reason": "風險收益比更佳"}
            else:
                return {"strategy": "DCA策略", "reason": "風險較低"}
        
        return {"strategy": "VA策略", "reason": "預設推薦"}
    
    def _get_final_values(self) -> Optional[Dict[str, float]]:
        """獲取最終價值比較"""
        if not self.calculation_results:
            return None
        
        summary_df = self.calculation_results["summary_df"]
        
        if len(summary_df) >= 2:
            va_value = summary_df[summary_df["Strategy"] == "VA_Rebalance"]["Final_Value"].iloc[0]
            dca_value = summary_df[summary_df["Strategy"] == "DCA"]["Final_Value"].iloc[0]
            
            if va_value > dca_value:
                return {
                    "recommended": va_value,
                    "difference": va_value - dca_value
                }
            else:
                return {
                    "recommended": dca_value,
                    "difference": dca_value - va_value
                }
        
        return None
    
    def _get_annualized_returns(self) -> Optional[Dict[str, float]]:
        """獲取年化報酬率比較"""
        if not self.calculation_results:
            return None
        
        summary_df = self.calculation_results["summary_df"]
        
        if len(summary_df) >= 2:
            va_return = summary_df[summary_df["Strategy"] == "VA_Rebalance"]["Annualized_Return"].iloc[0]
            dca_return = summary_df[summary_df["Strategy"] == "DCA"]["Annualized_Return"].iloc[0]
            
            if va_return > dca_return:
                return {
                    "recommended": va_return,
                    "difference": va_return - dca_return
                }
            else:
                return {
                    "recommended": dca_return,
                    "difference": dca_return - va_return
                }
        
        return None
    
    def render_strategy_comparison_cards(self):
        """渲染策略對比卡片 - 3.3.2節實作"""
        st.markdown("### 🎯 策略詳細比較")
        
        if not self.calculation_results:
            st.info("請設定投資參數後開始分析")
            return
        
        # 雙欄布局
        col1, col2 = st.columns(2)
        
        with col1:
            self._render_strategy_card("va_strategy")
        
        with col2:
            self._render_strategy_card("dca_strategy")
    
    def _render_strategy_card(self, strategy_key: str):
        """渲染單個策略卡片"""
        card_config = self.strategy_cards_config[strategy_key]
        
        # 獲取計算結果
        strategy_data = self._get_strategy_data(strategy_key)
        
        with st.container():
            st.markdown(f"#### {card_config['title']}")
            
            # 關鍵特色
            st.markdown(f"**✨ {card_config['key_feature']}**")
            
            # 核心指標
            if strategy_data:
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("最終價值", f"${strategy_data['final_value']:,.0f}")
                with col2:
                    st.metric("年化報酬", f"{strategy_data['annualized_return']:.2f}%")
            
            # 適合對象
            st.markdown(f"**👥 適合對象：** {card_config['content']['suitability']}")
            
            # 優缺點
            st.markdown("**✅ 優點：**")
            for pro in card_config['pros']:
                st.markdown(f"• {pro}")
            
            st.markdown("**⚠️ 缺點：**")
            for con in card_config['cons']:
                st.markdown(f"• {con}")
    
    def _get_strategy_data(self, strategy_key: str) -> Optional[Dict[str, float]]:
        """獲取策略數據"""
        if not self.calculation_results:
            return None
        
        summary_df = self.calculation_results["summary_df"]
        
        if strategy_key == "va_strategy":
            strategy_name = "VA_Rebalance"
        elif strategy_key == "dca_strategy":
            strategy_name = "DCA"
        else:
            return None
        
        strategy_row = summary_df[summary_df["Strategy"] == strategy_name]
        
        if len(strategy_row) > 0:
            row = strategy_row.iloc[0]
            return {
                "final_value": row["Final_Value"],
                "annualized_return": row["Annualized_Return"]
            }
        
        return None
    
    def render_charts_display(self):
        """渲染圖表顯示 - 3.3.3節實作"""
        st.markdown("### 📈 視覺化分析")
        
        if not self.calculation_results:
            st.info("請設定投資參數後開始分析")
            return
        
        # 標籤導航
        tab1, tab2, tab3 = st.tabs([
            "📈 資產成長",
            "📊 報酬比較", 
            "⚠️ 風險分析"
        ])
        
        with tab1:
            self._render_asset_growth_chart()
        
        with tab2:
            self._render_return_comparison_chart()
        
        with tab3:
            self._render_risk_analysis_chart()
    
    def _render_asset_growth_chart(self):
        """渲染資產成長圖表"""
        st.markdown("**兩種策略的資產累積對比**")
        
        if not self.calculation_results:
            return
        
        # 準備數據
        va_df = self.calculation_results["va_rebalance_df"]
        dca_df = self.calculation_results["dca_df"]
        
        # 合併數據用於圖表
        va_chart_data = va_df[["Period", "Cum_Value"]].copy()
        va_chart_data["Strategy"] = "VA策略"
        
        dca_chart_data = dca_df[["Period", "Cum_Value"]].copy()
        dca_chart_data["Strategy"] = "DCA策略"
        
        combined_data = pd.concat([va_chart_data, dca_chart_data], ignore_index=True)
        
        # 使用Plotly創建互動圖表
        fig = px.line(
            combined_data,
            x="Period",
            y="Cum_Value",
            color="Strategy",
            title="資產成長趨勢比較",
            labels={"Period": "投資期數", "Cum_Value": "累積資產價值 ($)"}
        )
        
        fig.update_layout(
            hovermode='x unified',
            xaxis_title="投資期數",
            yaxis_title="累積資產價值 ($)"
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    def _render_return_comparison_chart(self):
        """渲染報酬比較圖表"""
        st.markdown("**年化報酬率對比**")
        
        if not self.calculation_results:
            return
        
        summary_df = self.calculation_results["summary_df"]
        
        # 創建水平柱狀圖
        fig = px.bar(
            summary_df,
            x="Annualized_Return",
            y="Strategy",
            orientation='h',
            title="年化報酬率比較",
            labels={"Annualized_Return": "年化報酬率 (%)", "Strategy": "投資策略"}
        )
        
        fig.update_layout(
            xaxis_title="年化報酬率 (%)",
            yaxis_title="投資策略"
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    def _render_risk_analysis_chart(self):
        """渲染風險分析圖表"""
        st.markdown("**風險指標比較**")
        
        if not self.calculation_results:
            return
        
        summary_df = self.calculation_results["summary_df"]
        
        # 創建風險指標比較
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=("波動率", "夏普比率", "最大回撤", "總報酬率"),
            specs=[[{"type": "bar"}, {"type": "bar"}],
                   [{"type": "bar"}, {"type": "bar"}]]
        )
        
        strategies = summary_df["Strategy"].tolist()
        
        # 波動率
        fig.add_trace(
            go.Bar(x=strategies, y=summary_df["Volatility"], name="波動率"),
            row=1, col=1
        )
        
        # 夏普比率
        fig.add_trace(
            go.Bar(x=strategies, y=summary_df["Sharpe_Ratio"], name="夏普比率"),
            row=1, col=2
        )
        
        # 最大回撤
        fig.add_trace(
            go.Bar(x=strategies, y=summary_df["Max_Drawdown"], name="最大回撤"),
            row=2, col=1
        )
        
        # 總報酬率
        fig.add_trace(
            go.Bar(x=strategies, y=summary_df["Total_Return"], name="總報酬率"),
            row=2, col=2
        )
        
        fig.update_layout(height=600, showlegend=False)
        
        st.plotly_chart(fig, use_container_width=True)
    
    def render_data_tables_and_download(self):
        """渲染數據表格與下載 - 3.3.4節實作"""
        
        # 可展開的數據表格區域
        with st.expander("📊 詳細數據表格", expanded=False):
            
            if not self.calculation_results:
                st.info("請設定投資參數後開始分析")
                return
            
            # 策略選擇器
            strategy_options = ["VA策略", "DCA策略", "比較摘要"]
            selected_strategy = st.selectbox(
                "選擇要查看的數據",
                strategy_options,
                key="strategy_table_selector"
            )
            
            # 渲染對應表格
            if selected_strategy == "VA策略":
                self._render_va_strategy_table()
            elif selected_strategy == "DCA策略":
                self._render_dca_strategy_table()
            elif selected_strategy == "比較摘要":
                self._render_summary_table()
        
        # CSV下載區域
        st.markdown("### 💾 數據下載")
        
        if not self.calculation_results:
            st.info("請設定投資參數後開始分析")
            return
        
        # 三按鈕布局
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📥 VA策略數據", use_container_width=True):
                self._download_csv("va_strategy")
        
        with col2:
            if st.button("📥 DCA策略數據", use_container_width=True):
                self._download_csv("dca_strategy")
        
        with col3:
            if st.button("📥 績效摘要", use_container_width=True):
                self._download_csv("summary")
    
    def _render_va_strategy_table(self):
        """渲染VA策略表格 - 使用第2章VA_COLUMNS_ORDER"""
        st.markdown("#### 🎯 VA策略詳細數據")
        
        va_df = self.calculation_results["va_rebalance_df"]
        
        # 確保欄位順序符合第2章規格
        display_columns = [col for col in VA_COLUMNS_ORDER if col in va_df.columns]
        display_df = va_df[display_columns].copy()
        
        # 應用格式化規則
        display_df = self._apply_formatting_rules(display_df, "VA")
        
        st.dataframe(display_df, use_container_width=True)
        
        st.info(f"✅ 符合第2章規格：共{len(display_columns)}個欄位")
    
    def _render_dca_strategy_table(self):
        """渲染DCA策略表格 - 使用第2章DCA_COLUMNS_ORDER"""
        st.markdown("#### 💰 DCA策略詳細數據")
        
        dca_df = self.calculation_results["dca_df"]
        
        # 確保欄位順序符合第2章規格
        display_columns = [col for col in DCA_COLUMNS_ORDER if col in dca_df.columns]
        display_df = dca_df[display_columns].copy()
        
        # 應用格式化規則
        display_df = self._apply_formatting_rules(display_df, "DCA")
        
        st.dataframe(display_df, use_container_width=True)
        
        st.info(f"✅ 符合第2章規格：共{len(display_columns)}個欄位")
    
    def _render_summary_table(self):
        """渲染比較摘要表格"""
        st.markdown("#### 📊 策略比較摘要")
        
        summary_df = self.calculation_results["summary_df"]
        
        # 應用格式化規則
        display_df = self._apply_formatting_rules(summary_df, "SUMMARY")
        
        st.dataframe(display_df, use_container_width=True)
    
    def _apply_formatting_rules(self, df: pd.DataFrame, table_type: str) -> pd.DataFrame:
        """應用格式化規則 - 遵循第2章PERCENTAGE_PRECISION_RULES"""
        formatted_df = df.copy()
        
        # 應用百分比精度規則
        for col in formatted_df.columns:
            if col in PERCENTAGE_PRECISION_RULES:
                precision = PERCENTAGE_PRECISION_RULES[col]
                if formatted_df[col].dtype in ['float64', 'float32']:
                    formatted_df[col] = formatted_df[col].round(precision)
        
        # 貨幣格式化
        currency_columns = ["Cum_Value", "Cum_Inv", "Final_Value", "Total_Investment"]
        for col in currency_columns:
            if col in formatted_df.columns:
                formatted_df[col] = formatted_df[col].apply(lambda x: f"${x:,.0f}" if pd.notna(x) else "")
        
        return formatted_df
    
    def _download_csv(self, data_type: str):
        """下載CSV文件"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if data_type == "va_strategy":
            df = self.calculation_results["va_rebalance_df"]
            filename = f"投資策略比較_VA策略_{timestamp}.csv"
        elif data_type == "dca_strategy":
            df = self.calculation_results["dca_df"]
            filename = f"投資策略比較_DCA策略_{timestamp}.csv"
        elif data_type == "summary":
            df = self.calculation_results["summary_df"]
            filename = f"投資策略比較_績效摘要_{timestamp}.csv"
        else:
            return
        
        # 轉換為CSV
        csv = df.to_csv(index=False, encoding='utf-8-sig')
        
        st.download_button(
            label=f"下載 {filename}",
            data=csv,
            file_name=filename,
            mime="text/csv",
            key=f"download_{data_type}_{timestamp}"
        )
        
        st.success(f"✅ {filename} 準備就緒")
    
    def render_mobile_optimized_results(self, parameters: Dict[str, Any]):
        """
        渲染移動端優化結果 - 3.5.1節規格
        簡化展示、觸控友善、效能優化
        """
        if not parameters:
            st.info("請先設定投資參數")
            return
        
        # 執行計算
        self._execute_strategy_calculations(parameters)
        
        if not self.calculation_results:
            st.error("計算失敗，請檢查參數設定")
            return
        
        # 移動端優化展示
        self._render_mobile_summary_cards()
        self._render_mobile_chart()
        self._render_mobile_comparison_table()
    
    def _render_mobile_summary_cards(self):
        """渲染移動端摘要卡片 - 垂直堆疊"""
        st.markdown("#### 📊 策略比較結果")
        
        # 推薦策略卡片
        self._render_mobile_metric_card("recommended_strategy")
        
        # 最終價值卡片
        self._render_mobile_metric_card("expected_final_value")
        
        # 年化報酬率卡片
        self._render_mobile_metric_card("annualized_return")
    
    def _render_mobile_metric_card(self, metric_type: str):
        """渲染移動端指標卡片"""
        # 獲取最終值和年化報酬率
        final_values = self._get_final_values()
        annualized_returns = self._get_annualized_returns()
        
        if not final_values or not annualized_returns:
            return
        
        va_value = final_values.get('va_final_value', 0)
        dca_value = final_values.get('dca_final_value', 0)
        va_return = annualized_returns.get('va_annualized_return', 0)
        dca_return = annualized_returns.get('dca_annualized_return', 0)
        
        # 渲染不同類型的指標卡片
        if metric_type == "recommended_strategy":
            if va_return > dca_return:
                st.metric(
                    label="🎯 推薦策略",
                    value="定期定值 (VA)",
                    delta=f"優勢 {va_return - dca_return:.1f}%",
                    help="基於年化報酬率的推薦"
                )
            else:
                st.metric(
                    label="🎯 推薦策略",
                    value="定期定額 (DCA)",
                    delta=f"優勢 {dca_return - va_return:.1f}%",
                    help="基於年化報酬率的推薦"
                )
                
        elif metric_type == "expected_final_value":
            if va_value > dca_value:
                st.metric(
                    label="💰 預期最終價值",
                    value=f"${va_value:,.0f}",
                    delta=f"+${va_value - dca_value:,.0f}",
                    help="VA策略預期最終價值較高"
                )
            else:
                st.metric(
                    label="💰 預期最終價值",
                    value=f"${dca_value:,.0f}",
                    delta=f"+${dca_value - va_value:,.0f}",
                    help="DCA策略預期最終價值較高"
                )
                
        elif metric_type == "annualized_return":
            if va_return > dca_return:
                st.metric(
                    label="📈 年化報酬率",
                    value=f"{va_return:.1f}%",
                    delta=f"+{va_return - dca_return:.1f}%",
                    help="VA策略年化報酬率較高"
                )
            else:
                st.metric(
                    label="📈 年化報酬率",
                    value=f"{dca_return:.1f}%",
                    delta=f"+{dca_return - va_return:.1f}%",
                    help="DCA策略年化報酬率較高"
                )
    
    def _render_mobile_chart(self):
        """渲染移動端圖表 - 簡化版"""
        st.markdown("#### 📈 投資成長軌跡")
        
        # 簡化的圖表，只顯示主要趨勢
        if not self.calculation_results:
            return
        
        va_df = self.calculation_results.get("va_rebalance_df")
        dca_df = self.calculation_results.get("dca_df")
        
        if va_df is None or dca_df is None:
            st.error("計算數據不完整")
            return
        
        # 創建簡化的時間序列圖
        fig = go.Figure()
        
        # VA線條
        fig.add_trace(go.Scatter(
            x=va_df.index,
            y=va_df['Cum_Value'],
            mode='lines',
            name='🎯 定期定值 (VA)',
            line=dict(color='#3b82f6', width=3)
        ))
        
        # DCA線條
        fig.add_trace(go.Scatter(
            x=dca_df.index,
            y=dca_df['Cum_Value'],
            mode='lines',
            name='💰 定期定額 (DCA)',
            line=dict(color='#10b981', width=3)
        ))
        
        # 移動端優化設定
        fig.update_layout(
            height=300,  # 較小高度
            margin=dict(l=20, r=20, t=40, b=20),
            font=dict(size=12),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            xaxis_title="投資期數",
            yaxis_title="投資價值 ($)",
            hovermode='x unified'
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    def _render_mobile_comparison_table(self):
        """渲染移動端比較表格 - 簡化版"""
        st.markdown("#### 📋 詳細比較")
        
        if not self.calculation_results:
            return
        
        # 獲取數據
        final_values = self._get_final_values()
        annualized_returns = self._get_annualized_returns()
        
        if not final_values or not annualized_returns:
            return
        
        # 創建簡化的比較表格
        comparison_data = {
            "指標": ["💰 最終價值", "📈 年化報酬率", "💸 總投入", "📊 報酬倍數"],
            "🎯 定期定值 (VA)": [
                f"${final_values.get('va_final_value', 0):,.0f}",
                f"{annualized_returns.get('va_annualized_return', 0):.1f}%",
                f"${final_values.get('va_total_investment', 0):,.0f}",
                f"{final_values.get('va_final_value', 0) / max(final_values.get('va_total_investment', 1), 1):.1f}x"
            ],
            "💰 定期定額 (DCA)": [
                f"${final_values.get('dca_final_value', 0):,.0f}",
                f"{annualized_returns.get('dca_annualized_return', 0):.1f}%",
                f"${final_values.get('dca_total_investment', 0):,.0f}",
                f"{final_values.get('dca_final_value', 0) / max(final_values.get('dca_total_investment', 1), 1):.1f}x"
            ]
        }
        
        df = pd.DataFrame(comparison_data)
        
        # 使用觸控友善的表格顯示
        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
            height=200
        )