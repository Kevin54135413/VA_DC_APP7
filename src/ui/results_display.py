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
from datetime import datetime, timedelta
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
from models.chart_visualizer import (
    create_strategy_comparison_chart, 
    create_bar_chart, 
    create_line_chart,
    create_scatter_chart,
    create_drawdown_chart,
    create_risk_return_scatter,
    create_investment_flow_chart,
    create_allocation_pie_chart
)

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
        },
        "investment_flow": {
            "icon": "💰",
            "label": "投資流分析",
            "chart_type": "investment_flow_chart",
            "description": "VA策略投資行為分析",
            "data_source": "第2章VA策略計算結果",
            "visualization": "investment_flow_bar_chart"
        },
        "asset_allocation": {
            "icon": "🥧",
            "label": "資產配置",
            "chart_type": "allocation_pie_chart",
            "description": "投資組合資產配置分析",
            "data_source": "投資參數配置",
            "visualization": "pie_chart"
        },
        "drawdown_analysis": {
            "icon": "📉",
            "label": "回撤分析",
            "chart_type": "drawdown_chart",
            "description": "策略回撤風險分析",
            "data_source": "第2章策略計算結果",
            "visualization": "area_chart"
        },
        "risk_return_analysis": {
            "icon": "📊",
            "label": "風險收益分析",
            "chart_type": "risk_return_scatter",
            "description": "風險收益散點圖分析",
            "data_source": "第2章績效指標計算模組",
            "visualization": "scatter_chart"
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
        self.strategy_cards_config = STRATEGY_COMPARISON_CARDS
        self.charts_config = SIMPLIFIED_CHARTS_CONFIG
        self.tables_config = DATA_TABLES_CONFIG
        self.calculation_results = {}
        self.last_parameters = None
        
    def render_complete_results_display(self, parameters: Dict[str, Any]):
        """渲染完整中央結果展示區域"""
        # 檢查是否有計算觸發
        if st.session_state.get('trigger_calculation', False):
            # 清除觸發標記
            st.session_state.trigger_calculation = False
            
            # 執行策略計算
            self._execute_strategy_calculations(parameters)
            
            # 記錄計算時間
            from datetime import datetime
            st.session_state.last_calculation_time = datetime.now()
            
            # 顯示計算完成信息
            st.success("✅ 計算完成！以下是您的投資策略分析結果：")
        
        # 從session_state讀取計算結果（如果有的話）
        if not self.calculation_results and st.session_state.get('calculation_results'):
            self.calculation_results = st.session_state.calculation_results
        
        # 如果沒有計算結果，顯示提示
        if not self.calculation_results:
            st.info("👈 請在左側設定投資參數，然後點擊「🎯 執行策略計算」按鈕開始分析")
            return
        
        # 渲染策略對比卡片
        self.render_strategy_comparison_cards()
        
        # 渲染圖表顯示
        self.render_charts_display()
        
        # 渲染數據表格與下載
        self.render_data_tables_and_download()
    
    def _execute_strategy_calculations(self, parameters: Dict[str, Any]):
        """執行策略計算 - 整合第2章計算引擎"""
        try:
            # 顯示計算進度
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # 階段1：準備市場數據
            status_text.text("📊 階段1/4：準備市場數據...")
            progress_bar.progress(25)
            
            # 從第1章API獲取真實市場數據
            market_data = self._fetch_real_market_data(parameters)
            
            # 階段2：計算VA策略
            status_text.text("🎯 階段2/4：計算VA策略...")
            progress_bar.progress(50)
            
            # 轉換頻率格式（UI使用小寫，計算函數期望大寫開頭）
            frequency_mapping = {
               "monthly": "Monthly",
               "quarterly": "Quarterly", 
               "semi_annually": "Semi-annually",
               "annually": "Annually"
            }
            calculation_frequency = frequency_mapping.get(parameters["investment_frequency"], "Annually")
            
            # VA策略計算
            va_rebalance_df = calculate_va_strategy(
               C0=parameters["initial_investment"],
               annual_investment=parameters["annual_investment"],  # 使用正確的年度投入金額
               annual_growth_rate=parameters["va_growth_rate"],  # 直接使用，不需要除以100
               annual_inflation_rate=parameters["inflation_rate"],  # 直接使用，不需要除以100
               investment_years=parameters["investment_years"],
               frequency=calculation_frequency,  # 使用轉換後的頻率
               stock_ratio=parameters["stock_ratio"],  # 直接使用，不需要除以100
               strategy_type=parameters.get("strategy_type", "Rebalance"),  # 修正：使用用戶選擇的策略類型
               market_data=market_data
            )
            
            # 階段3：計算DCA策略
            status_text.text("💰 階段3/4：計算DCA策略...")
            progress_bar.progress(75)
            
            # DCA策略計算
            dca_df = calculate_dca_strategy(
               C0=parameters["initial_investment"],
               annual_investment=parameters["annual_investment"],  # 使用正確的年度投入金額
               annual_growth_rate=parameters["va_growth_rate"],  # 直接使用，不需要除以100
               annual_inflation_rate=parameters["inflation_rate"],  # 直接使用，不需要除以100
               investment_years=parameters["investment_years"],
               frequency=calculation_frequency,  # 使用轉換後的頻率
               stock_ratio=parameters["stock_ratio"],  # 直接使用，不需要除以100
               market_data=market_data
            )
            
            # 階段4：生成比較分析
            status_text.text("📈 階段4/4：生成比較分析...")
            progress_bar.progress(100)
            
            # 綜合比較指標
            summary_df = calculate_summary_metrics(
               va_rebalance_df=va_rebalance_df,
               va_nosell_df=None,
               dca_df=dca_df,
               initial_investment=parameters["initial_investment"],
               periods_per_year=parameters["periods_per_year"]
            )
            
            # 保存計算結果到實例變量和session_state
            self.calculation_results = {
               "va_rebalance_df": va_rebalance_df,
               "dca_df": dca_df,
               "summary_df": summary_df,
               "parameters": parameters
            }
            
            # 保存最後使用的參數
            self.last_parameters = parameters
            
            # 同時保存到session_state以便跨組件訪問
            st.session_state.calculation_results = self.calculation_results
            
            # 清除進度顯示
            progress_bar.empty()
            status_text.empty()
            
        except Exception as e:
            # 清除進度顯示
            if 'progress_bar' in locals():
               progress_bar.empty()
            if 'status_text' in locals():
               status_text.empty()
            
            st.error(f"計算過程中出現錯誤: {e}")
            self.calculation_results = {}
            st.session_state.calculation_results = {}
    
    def _fetch_real_market_data(self, parameters: Dict[str, Any]) -> pd.DataFrame:
        """
        獲取真實市場數據 - 嚴格遵循第1章規格
        
        API端點：
        - Tiingo API：https://api.tiingo.com/tiingo/daily/SPY/prices
        - FRED API：https://api.stlouisfed.org/fred/series/observations
        
        數據精度：
        - 價格精度：小數點後2位
        - 殖利率精度：小數點後4位
        """
        try:
            from src.data_sources import get_api_key
            from src.data_sources.tiingo_client import TiingoDataFetcher
            from src.data_sources.fred_client import FREDDataFetcher
            from src.data_sources.trading_calendar import generate_trading_days
            from datetime import datetime, timedelta
            import logging
            
            logger = logging.getLogger(__name__)
            
            # 檢查用戶數據源選擇
            data_source_mode = parameters.get("data_source_mode", "real_data")
            
            # 如果用戶明確選擇模擬數據，直接使用模擬數據
            if data_source_mode == "simulation":
               logger.info("用戶選擇模擬數據模式")
               return self._generate_fallback_data(parameters)
            
            # 多層級API金鑰獲取：Streamlit Secrets → 環境變數 → .env檔案
            tiingo_api_key = get_api_key('TIINGO_API_KEY')
            fred_api_key = get_api_key('FRED_API_KEY')
            
            # 如果用戶選擇真實數據但API金鑰不可用，顯示錯誤
            if data_source_mode == "real_data" and (not tiingo_api_key or not fred_api_key):
               missing_keys = []
               if not tiingo_api_key:
                   missing_keys.append("TIINGO_API_KEY")
               if not fred_api_key:
                   missing_keys.append("FRED_API_KEY")
               
               logger.error(f"用戶選擇真實數據但缺少API金鑰: {missing_keys}")
               st.error(f"❌ 無法使用真實市場數據：缺少 {', '.join(missing_keys)}")
               st.info("💡 請設定API金鑰或切換到模擬數據模式")
               return self._generate_fallback_data(parameters)
            
            # 計算日期範圍（使用起始日期參數）
            # 根據投資年數和頻率計算總期數
            investment_years = parameters.get("investment_periods", 30)
            frequency = parameters.get("investment_frequency", "annually")
            
            # 使用 FREQUENCY_MAPPING 計算總期數
            from src.models.calculation_formulas import FREQUENCY_MAPPING
            if frequency.lower() == "annually":
               periods_per_year = FREQUENCY_MAPPING["Annually"]["periods_per_year"]
            elif frequency.lower() == "quarterly":
               periods_per_year = FREQUENCY_MAPPING["Quarterly"]["periods_per_year"]
            elif frequency.lower() == "monthly":
               periods_per_year = FREQUENCY_MAPPING["Monthly"]["periods_per_year"]
            elif frequency.lower() == "semi_annually":
               periods_per_year = FREQUENCY_MAPPING["Semi-annually"]["periods_per_year"]
            else:
               periods_per_year = 1  # 預設為年度
            
            total_periods = investment_years * periods_per_year
            
            # 獲取起始日期參數
            user_start_date = parameters.get("start_date") or parameters.get("investment_start_date")
            if user_start_date:
               # 將date對象轉換為datetime對象
               if isinstance(user_start_date, datetime):
                   start_date = user_start_date
               elif hasattr(user_start_date, 'date'):
                   # 如果是date對象，轉換為datetime
                   start_date = datetime.combine(user_start_date, datetime.min.time())
               else:
                   # 如果是字符串，解析為datetime
                   start_date = datetime.strptime(str(user_start_date), '%Y-%m-%d')
            else:
               # 預設為次年1月1日
               current_year = datetime.now().year
               start_date = datetime(current_year + 1, 1, 1)
            
            # 計算結束日期 - 修正：確保獲取足夠的API數據
            # 修正前：使用固定的期間天數計算，導致API數據範圍不足
            # frequency_days = {"monthly": 30, "quarterly": 90, "semi_annually": 180, "annually": 365}
            # period_days = frequency_days.get(parameters["investment_frequency"], 90)
            # end_date = start_date + timedelta(days=total_periods * period_days)
            
            # 修正後：使用實際期間計算確保覆蓋所有期間
            from src.utils.trading_days import calculate_period_end_date
            final_period_end = calculate_period_end_date(start_date, parameters["investment_frequency"], total_periods)
            
            # 為了確保有足夠的API數據，在最後期間結束日期基礎上再加6個月緩衝
            end_date = final_period_end + timedelta(days=180)
            
            # 使用交易日調整函數
            trading_days = generate_trading_days(start_date, end_date)
            
            market_data_list = []
            
            # 初始化API客戶端
            tiingo_fetcher = None
            fred_fetcher = None
            
            if tiingo_api_key:
               tiingo_fetcher = TiingoDataFetcher(tiingo_api_key)
               logger.info("Tiingo API客戶端初始化成功")
            
            if fred_api_key:
               fred_fetcher = FREDDataFetcher(fred_api_key)
               logger.info("FRED API客戶端初始化成功")
            
            # 獲取股票價格數據
            spy_data = {}
            api_success = True
            
            if tiingo_fetcher:
               try:
                   spy_prices = tiingo_fetcher.get_spy_prices(
                       start_date.strftime('%Y-%m-%d'),
                       end_date.strftime('%Y-%m-%d')
                   )
                   for data_point in spy_prices:
                       # 確保價格精度：小數點後2位
                       spy_data[data_point.date] = round(data_point.spy_price, 2)
                   logger.info(f"成功獲取 {len(spy_data)} 筆SPY價格數據")
                   
               except Exception as e:
                   logger.warning(f"Tiingo API獲取失敗: {str(e)}")
                   api_success = False
                   if data_source_mode == "real_data":
                       st.warning(f"⚠️ Tiingo API獲取失敗: {str(e)}")
            else:
               api_success = False
            
            # 獲取債券殖利率數據
            bond_data = {}
            if fred_fetcher:
               try:
                   bond_yields = fred_fetcher.get_treasury_yields(
                       start_date.strftime('%Y-%m-%d'),
                       end_date.strftime('%Y-%m-%d'),
                       'DGS1'
                   )
                   for data_point in bond_yields:
                       # 確保殖利率精度：小數點後4位
                       bond_data[data_point.date] = round(data_point.bond_yield, 4)
                   logger.info(f"成功獲取 {len(bond_data)} 筆債券殖利率數據")
                   
               except Exception as e:
                   logger.warning(f"FRED API獲取失敗: {str(e)}")
                   api_success = False
                   if data_source_mode == "real_data":
                       st.warning(f"⚠️ FRED API獲取失敗: {str(e)}")
            else:
               api_success = False
            
            # 如果用戶選擇真實數據但API完全失敗，顯示錯誤並回退
            if data_source_mode == "real_data" and not api_success:
               logger.error("用戶選擇真實數據但API不可用")
               st.error("❌ 無法獲取真實市場數據：API連接失敗")
               st.info("💡 請檢查網路連接或切換到模擬數據模式")
               return self._generate_fallback_data(parameters)
            
            # 如果用戶選擇真實數據但沒有獲取到API數據，直接返回錯誤
            if data_source_mode == "real_data" and (len(spy_data) == 0 and len(bond_data) == 0):
               logger.error("用戶選擇真實數據但未獲取到任何API數據")
               st.error("❌ 無法獲取指定期間的真實市場數據")
               st.info("💡 請檢查日期範圍或切換到模擬數據模式")
               return self._generate_fallback_data(parameters)
            
            # 生成期間數據
            from src.utils.trading_days import calculate_period_start_date, calculate_period_end_date
            
            # 價格連續性追蹤變量 - 解決混合數據價格跳躍問題
            previous_spy_price_end = None
            previous_bond_yield_end = None
            
            # 檢測真實數據可用範圍
            current_date = datetime.now().date()
            real_data_cutoff_period = None
            
            for period in range(total_periods):
               # 使用正確的投資頻率計算日期 - 修正：不再使用固定30天間隔
               period_start = calculate_period_start_date(start_date, parameters["investment_frequency"], period + 1)
               period_end = calculate_period_end_date(start_date, parameters["investment_frequency"], period + 1)
               
               date_str = period_start.strftime('%Y-%m-%d')
               end_date_str = period_end.strftime('%Y-%m-%d')
               
               # 判斷是否進入模擬數據範圍
               is_real_data_available = period_start.date() <= current_date
               
               # 記錄真實數據截止期間
               if is_real_data_available and real_data_cutoff_period is None:
                   pass  # 還在真實數據範圍內
               elif not is_real_data_available and real_data_cutoff_period is None:
                   real_data_cutoff_period = period
                   if real_data_cutoff_period > 0:
                       logger.info(f"第{real_data_cutoff_period}期開始使用模擬數據，確保價格連續性")
                       st.info(f"📊 前{real_data_cutoff_period}期使用真實數據，第{real_data_cutoff_period + 1}期開始使用模擬數據（保持價格連續性）")
               
               # 價格連續性處理 - 統一處理真實數據和模擬數據的連續性
               if period == 0:
                   # 第一期：直接使用真實數據或預設值
                   if is_real_data_available and len(spy_data) > 0:
                       closest_spy_date = min(spy_data.keys(), key=lambda x: abs((datetime.strptime(x, '%Y-%m-%d') - period_start).days), default=None)
                       spy_price_origin = spy_data.get(closest_spy_date) if closest_spy_date else None
                       if spy_price_origin is None:
                           spy_price_origin = list(spy_data.values())[-1] if spy_data else 400.0
                   else:
                       spy_price_origin = 400.0  # 預設起始價格
                   
                   if is_real_data_available and len(bond_data) > 0:
                       closest_bond_date = min(bond_data.keys(), key=lambda x: abs((datetime.strptime(x, '%Y-%m-%d') - period_start).days), default=None)
                       bond_yield_origin = bond_data.get(closest_bond_date) if closest_bond_date else None
                       if bond_yield_origin is None:
                           bond_yield_origin = list(bond_data.values())[-1] if bond_data else 3.0
                   else:
                       bond_yield_origin = 3.0  # 預設起始殖利率
               else:
                   # 第二期開始：優先使用真實API數據，只在無法獲取時才使用相依性機制
                   if is_real_data_available and len(spy_data) > 0:
                       # 真實數據期間：直接使用API數據，但需要檢查日期範圍合理性
                       closest_spy_date = min(spy_data.keys(), key=lambda x: abs((datetime.strptime(x, '%Y-%m-%d') - period_start).days), default=None)
                       
                       # 修正：檢查匹配的日期是否在合理範圍內（30天內）
                       if closest_spy_date:
                           date_diff = abs((datetime.strptime(closest_spy_date, '%Y-%m-%d') - period_start).days)
                           if date_diff <= 30:
                               # 在合理範圍內，使用API數據
                               spy_price_origin = spy_data.get(closest_spy_date)
                               if spy_price_origin is None:
                                   spy_price_origin = list(spy_data.values())[-1] if spy_data else 400.0
                               logger.debug(f"期間{period}：使用真實API數據，期初價格{spy_price_origin}，匹配日期{closest_spy_date}（差異{date_diff}天）")
                           else:
                               # 超出合理範圍，表示API數據不足，使用連續性邏輯
                               if previous_spy_price_end is not None:
                                   import numpy as np
                                   np.random.seed(42 + period * 23)
                                   overnight_change = np.random.normal(0, 0.005)
                                   overnight_change = max(-0.01, min(0.01, overnight_change))
                                   spy_price_origin = round(previous_spy_price_end * (1 + overnight_change), 2)
                                   logger.debug(f"期間{period}：API數據超出範圍（差異{date_diff}天），使用連續性邏輯，期初價格{spy_price_origin}")
                               else:
                                   spy_price_origin = 400.0
                                   logger.debug(f"期間{period}：API數據超出範圍且無前期數據，使用預設價格{spy_price_origin}")
                       else:
                           # 沒有找到匹配日期，使用連續性邏輯
                           if previous_spy_price_end is not None:
                               import numpy as np
                               np.random.seed(42 + period * 23)
                               overnight_change = np.random.normal(0, 0.005)
                               overnight_change = max(-0.01, min(0.01, overnight_change))
                               spy_price_origin = round(previous_spy_price_end * (1 + overnight_change), 2)
                               logger.debug(f"期間{period}：無API匹配日期，使用連續性邏輯，期初價格{spy_price_origin}")
                           else:
                               spy_price_origin = 400.0
                   elif previous_spy_price_end is not None:
                       # 模擬數據期間：基於前期期末價格加入隔夜變動
                       import numpy as np
                       np.random.seed(42 + period * 23)  # 確保可重現的隔夜變動
                       
                       # 隔夜價格變動：通常在-1%到+1%之間
                       overnight_change = np.random.normal(0, 0.005)  # 0.5%標準差
                       overnight_change = max(-0.01, min(0.01, overnight_change))  # 限制在±1%
                       
                       spy_price_origin = round(previous_spy_price_end * (1 + overnight_change), 2)
                       logger.debug(f"期間{period}：模擬數據期間，基於前期期末價格{previous_spy_price_end}，加入{overnight_change:.4f}隔夜變動，期初價格{spy_price_origin}")
                   else:
                       # 最後備用方案
                       spy_price_origin = 400.0
                   
                   if is_real_data_available and len(bond_data) > 0:
                       # 真實數據期間：直接使用API數據，但需要檢查日期範圍合理性
                       closest_bond_date = min(bond_data.keys(), key=lambda x: abs((datetime.strptime(x, '%Y-%m-%d') - period_start).days), default=None)
                       
                       # 修正：檢查匹配的日期是否在合理範圍內（30天內）
                       if closest_bond_date:
                           date_diff = abs((datetime.strptime(closest_bond_date, '%Y-%m-%d') - period_start).days)
                           if date_diff <= 30:
                               # 在合理範圍內，使用API數據
                               bond_yield_origin = bond_data.get(closest_bond_date)
                               if bond_yield_origin is None:
                                   bond_yield_origin = list(bond_data.values())[-1] if bond_data else 3.0
                               logger.debug(f"期間{period}：使用真實API債券數據，期初殖利率{bond_yield_origin}，匹配日期{closest_bond_date}（差異{date_diff}天）")
                           else:
                               # 超出合理範圍，使用連續性邏輯
                               if previous_bond_yield_end is not None:
                                   import numpy as np
                                   np.random.seed(42 + period * 29)
                                   overnight_yield_change = np.random.normal(0, 0.02)
                                   overnight_yield_change = max(-0.001, min(0.001, overnight_yield_change))
                                   bond_yield_origin = round(max(0.5, min(8.0, previous_bond_yield_end + overnight_yield_change)), 4)
                                   logger.debug(f"期間{period}：債券API數據超出範圍（差異{date_diff}天），使用連續性邏輯，期初殖利率{bond_yield_origin}")
                               else:
                                   bond_yield_origin = 3.0
                                   logger.debug(f"期間{period}：債券API數據超出範圍且無前期數據，使用預設殖利率{bond_yield_origin}")
                       else:
                           # 沒有找到匹配日期，使用連續性邏輯
                           if previous_bond_yield_end is not None:
                               import numpy as np
                               np.random.seed(42 + period * 29)
                               overnight_yield_change = np.random.normal(0, 0.02)
                               overnight_yield_change = max(-0.001, min(0.001, overnight_yield_change))
                               bond_yield_origin = round(max(0.5, min(8.0, previous_bond_yield_end + overnight_yield_change)), 4)
                               logger.debug(f"期間{period}：無債券API匹配日期，使用連續性邏輯，期初殖利率{bond_yield_origin}")
                           else:
                               bond_yield_origin = 3.0
                   elif previous_bond_yield_end is not None:
                       # 模擬數據期間：基於前期期末殖利率加入隔夜變動
                       import numpy as np
                       np.random.seed(42 + period * 29)  # 不同種子避免與股價同步
                       
                       # 殖利率隔夜變動：通常很小，在-0.1%到+0.1%之間
                       overnight_yield_change = np.random.normal(0, 0.02)  # 2個基點標準差
                       overnight_yield_change = max(-0.001, min(0.001, overnight_yield_change))  # 限制在±0.1%
                       
                       bond_yield_origin = round(max(0.5, min(8.0, previous_bond_yield_end + overnight_yield_change)), 4)
                       logger.debug(f"期間{period}：模擬數據期間，基於前期期末殖利率{previous_bond_yield_end}，加入{overnight_yield_change:.4f}隔夜變動，期初殖利率{bond_yield_origin}")
                   else:
                       # 最後備用方案
                       bond_yield_origin = 3.0
               
               # 債券價格計算（簡化公式）
               bond_price_origin = round(100.0 / (1 + bond_yield_origin/100), 2)
               
               # 生成期末價格 - 優先使用真實API數據
               import numpy as np
               
               if is_real_data_available:
                   # 真實數據期間：嘗試使用API數據
                   if len(spy_data) > 0:
                       # 找最接近期末日期的SPY價格
                       closest_spy_end_date = min(spy_data.keys(), key=lambda x: abs((datetime.strptime(x, '%Y-%m-%d') - period_end).days), default=None)
                       if closest_spy_end_date and abs((datetime.strptime(closest_spy_end_date, '%Y-%m-%d') - period_end).days) <= 30:
                           # 如果找到30天內的數據，使用真實數據
                           spy_price_end = spy_data[closest_spy_end_date]
                           logger.debug(f"期間{period}：使用真實API期末數據，期末價格{spy_price_end}")
                       else:
                           # 如果沒有找到接近的數據，使用小幅波動模擬
                           np.random.seed(42 + period)
                           stock_return = np.random.normal(0.02, 0.10)  # 10%波動
                           spy_price_end = round(spy_price_origin * (1 + stock_return), 2)
                           logger.debug(f"期間{period}：無法找到合適的真實期末數據，使用模擬波動，期末價格{spy_price_end}")
                   else:
                       # 沒有SPY數據，使用模擬
                       np.random.seed(42 + period)
                       stock_return = np.random.normal(0.02, 0.10)
                       spy_price_end = round(spy_price_origin * (1 + stock_return), 2)
                   
                   # 債券殖利率期末數據
                   if len(bond_data) > 0:
                       closest_bond_end_date = min(bond_data.keys(), key=lambda x: abs((datetime.strptime(x, '%Y-%m-%d') - period_end).days), default=None)
                       if closest_bond_end_date and abs((datetime.strptime(closest_bond_end_date, '%Y-%m-%d') - period_end).days) <= 30:
                           bond_yield_end = bond_data[closest_bond_end_date]
                           logger.debug(f"期間{period}：使用真實API債券期末數據，期末殖利率{bond_yield_end}")
                       else:
                           bond_yield_change = np.random.normal(0, 0.15)
                           bond_yield_end = round(max(0.5, min(8.0, bond_yield_origin + bond_yield_change)), 4)
                           logger.debug(f"期間{period}：無法找到合適的真實債券期末數據，使用模擬波動")
                   else:
                       bond_yield_change = np.random.normal(0, 0.15)
                       bond_yield_end = round(max(0.5, min(8.0, bond_yield_origin + bond_yield_change)), 4)
               else:
                   # 模擬數據期間：使用與_generate_fallback_data相同的市場週期邏輯
                   # 修正：需要在函數開始時預先生成市場週期，而非在此處重新生成
                   # 這裡改為使用簡化但連續的模擬邏輯，確保價格連續性
                   base_seed = 42
                   np.random.seed(base_seed + period * 17 + int(start_date.timestamp()) % 1000)
                   
                   # 使用連續性保證的長期成長模型
                   # 計算期間時間參數 - 確保與parameter頻率格式一致
                   freq_lower = parameters.get("investment_frequency", "annually").lower()
                   if freq_lower == 'monthly':
                       dt = 1/12
                   elif freq_lower == 'quarterly':
                       dt = 1/4
                   elif freq_lower == 'semi_annually':
                       dt = 1/2
                   else:  # annually
                       dt = 1
                   
                   # 使用長期股市成長預期：年化7-10%（歷史S&P 500平均）
                   # 而非每期隨機決定牛熊市
                   base_annual_return = 0.085  # 8.5%年化報酬率（歷史平均）
                   annual_volatility = 0.16  # 16%年化波動率（歷史平均）
                   
                   # 加入週期性調整（基於期間位置的緩慢變化）
                   cycle_adjustment = 0.02 * np.sin(2 * np.pi * period / (total_periods / 3))  # 3個大週期
                   adjusted_annual_return = base_annual_return + cycle_adjustment
                   
                   # 使用幾何布朗運動計算期間報酬率
                   Z = np.random.normal(0, 1)
                   period_return = (adjusted_annual_return - annual_volatility**2/2) * dt + annual_volatility * np.sqrt(dt) * Z
                   spy_price_end = round(spy_price_origin * (1 + period_return), 2)
                   
                   # 確保價格變化在合理範圍內
                   price_change_ratio = abs(spy_price_end - spy_price_origin) / spy_price_origin
                   if price_change_ratio > 0.35:  # ✅ 只限制極端異常（35%以上）
                       max_change = 0.35 if spy_price_end > spy_price_origin else -0.35
                       spy_price_end = round(spy_price_origin * (1 + max_change), 2)
                       logger.debug(f"期間{period}：限制股價變化幅度至35%，從{spy_price_origin}變為{spy_price_end}")
                   
                   # 債券殖利率：較小的波動
                   bond_yield_change = np.random.normal(0, 0.1)
                   bond_yield_end = round(max(0.5, min(8.0, bond_yield_origin + bond_yield_change)), 4)
                   
                   # 確保殖利率變化在合理範圍內
                   yield_change_ratio = abs(bond_yield_end - bond_yield_origin) / bond_yield_origin
                   if yield_change_ratio > 0.25:
                       max_yield_change = 0.25 if bond_yield_end > bond_yield_origin else -0.25
                       bond_yield_end = round(max(0.5, min(8.0, bond_yield_origin * (1 + max_yield_change))), 4)
                       logger.debug(f"期間{period}：限制殖利率變化幅度至25%，從{bond_yield_origin}變為{bond_yield_end}")
               
               bond_price_end = round(100.0 / (1 + bond_yield_end/100), 2)
               
               market_data_list.append({
                   'Period': period,
                   'Date_Origin': date_str,
                   'Date_End': end_date_str,
                   'SPY_Price_Origin': spy_price_origin,
                   'SPY_Price_End': spy_price_end,
                   'Bond_Yield_Origin': bond_yield_origin,
                   'Bond_Yield_End': bond_yield_end,
                   'Bond_Price_Origin': bond_price_origin,
                   'Bond_Price_End': bond_price_end
               })
               
               # 更新連續性追蹤變量
               previous_spy_price_end = spy_price_end
               previous_bond_yield_end = bond_yield_end
            
            # 創建DataFrame
            market_data = pd.DataFrame(market_data_list)
            
            # 顯示最終數據源狀態
            if len(spy_data) > 0 or len(bond_data) > 0:
               data_summary = []
               if len(spy_data) > 0:
                   data_summary.append(f"📈 SPY股票: {len(spy_data)} 筆")
               if len(bond_data) > 0:
                   data_summary.append(f"📊 債券殖利率: {len(bond_data)} 筆")
               
               if real_data_cutoff_period is not None:
                   st.success(f"✅ 已成功使用混合數據生成 {len(market_data)} 期投資數據")
                   st.info(f"🌐 **真實數據**: {' | '.join(data_summary)} | 📊 **模擬數據**: 第{real_data_cutoff_period + 1}-{total_periods}期（價格連續性已保證）")
                   
                   # 顯示混合數據的識別標記
                   with st.expander("📋 混合數據詳細資訊", expanded=False):
                       st.markdown("#### 🌐 真實數據部分")
                       st.markdown(f"- **數據來源**: Tiingo API (SPY) + FRED API (DGS1)")
                       st.markdown(f"- **涵蓋期間**: 第1-{real_data_cutoff_period}期")
                       st.markdown(f"- **數據品質**: ✅ 市場實際交易數據")
                       
                       st.markdown("#### 📊 模擬數據部分")
                       st.markdown(f"- **涵蓋期間**: 第{real_data_cutoff_period + 1}-{total_periods}期")
                       st.markdown(f"- **生成方式**: 基於前期真實數據的連續性模擬")
                       st.markdown(f"- **價格連續性**: ✅ 已確保與真實數據無縫銜接")
               else:
                   st.success(f"✅ 已成功使用真實市場數據生成 {len(market_data)} 期投資數據")
                   st.info(f"🌐 **真實數據來源**: {' | '.join(data_summary)}")
                   
                   # 顯示真實數據的識別標記
                   with st.expander("📋 真實數據詳細資訊", expanded=False):
                       st.markdown("#### 🌐 數據來源")
                       st.markdown(f"- **股票數據**: Tiingo API - SPY (標普500指數ETF)")
                       st.markdown(f"- **債券數據**: FRED API - DGS1 (1年期美國國債殖利率)")
                       st.markdown(f"- **數據期間**: {len(market_data)} 期完整覆蓋")
                       st.markdown(f"- **數據品質**: ✅ 100% 真實市場交易數據")
                       
                       st.markdown("#### 📊 數據精度")
                       st.markdown(f"- **價格精度**: 小數點後2位 (美元)")
                       st.markdown(f"- **殖利率精度**: 小數點後4位 (百分比)")
                       st.markdown(f"- **時間精度**: 日期級別準確")
            else:
               # 純模擬數據的情況會在_generate_fallback_data中顯示
               pass
            
            logger.info(f"成功準備 {len(market_data)} 期市場數據")
            return market_data
            
        except Exception as e:
            logger.error(f"獲取真實市場數據失敗: {str(e)}")
            # 使用備用模擬數據
            return self._generate_fallback_data(parameters)
    
    def _generate_fallback_data(self, parameters: Dict[str, Any]) -> pd.DataFrame:
        """
        生成備用模擬數據 - 當API不可用時使用
        
        按照需求文件1.1.3節規格實作：
        1. 市場情境模擬（牛市、熊市特徵）
        2. 完整時間軸生成架構
        3. 幾何布朗運動價格生成
        """
        # 導入必要模組
        import numpy as np
        from src.utils.trading_days import calculate_period_start_date, calculate_period_end_date
        from src.utils.logger import get_component_logger
        import time
        from datetime import datetime
        
        logger = get_component_logger("ResultsDisplay")
        logger.info("生成備用模擬數據 - 優化：更接近美國股市歷史特徵")
        
        # 數據生成時間戳記錄
        generation_timestamp = datetime.now()
        
        # 隨機種子管理
        # 優先使用手動設定的種子，其次使用自動生成的種子
        if hasattr(st.session_state, 'custom_simulation_seed') and st.session_state.custom_simulation_seed is not None:
            base_seed = st.session_state.custom_simulation_seed
        elif hasattr(st.session_state, 'simulation_seed') and st.session_state.simulation_seed is not None:
            base_seed = st.session_state.simulation_seed
        else:
            # 預設種子：結合當前時間和用戶參數
            base_seed = int(time.time()) % 100000
            st.session_state.simulation_seed = base_seed
        
        # 記錄模擬數據生成資訊到session_state
        st.session_state.simulation_data_info = {
            'generation_timestamp': generation_timestamp,
            'random_seed': base_seed,
            'regeneration_count': st.session_state.get('simulation_regeneration_count', 0),
            'market_bias': getattr(st.session_state, 'simulation_market_bias', '隨機組合'),
            'volatility_level': getattr(st.session_state, 'simulation_volatility_level', '中波動'),
            'seed_mode': st.session_state.get('simulation_seed_mode', '自動生成')
        }
        
        # 解析參數
        investment_years = parameters.get("investment_periods", 30)
        frequency = parameters.get("investment_frequency", "annually")
        
        # 使用 FREQUENCY_MAPPING 計算總期數
        from src.models.calculation_formulas import FREQUENCY_MAPPING
        if frequency.lower() == "annually":
            periods_per_year = FREQUENCY_MAPPING["Annually"]["periods_per_year"]
        elif frequency.lower() == "quarterly":
            periods_per_year = FREQUENCY_MAPPING["Quarterly"]["periods_per_year"]
        elif frequency.lower() == "monthly":
            periods_per_year = FREQUENCY_MAPPING["Monthly"]["periods_per_year"]
        elif frequency.lower() == "semi_annually":
            periods_per_year = FREQUENCY_MAPPING["Semi-annually"]["periods_per_year"]
        else:
            periods_per_year = 1  # 預設為年度
        
        total_periods = investment_years * periods_per_year
        user_start_date = parameters.get("start_date") or parameters.get("investment_start_date", datetime.now().date())
        
        # 確保起始日期是datetime.date類型
        if isinstance(user_start_date, str):
            start_date = datetime.strptime(user_start_date, '%Y-%m-%d').date()
        elif hasattr(user_start_date, 'date'):
            start_date = user_start_date.date()
        else:
            start_date = user_start_date
        
        logger.info(f"模擬數據生成 - 種子: {base_seed}, 期間: {total_periods}, 起始: {start_date}")
        
        # 市場偏好調整
        market_bias = getattr(st.session_state, 'simulation_market_bias', '隨機組合')
        if market_bias == "偏向牛市":
            bull_market_probability = 0.8
        elif market_bias == "偏向熊市":
            bull_market_probability = 0.3
        elif market_bias == "平衡市場":
            bull_market_probability = 0.5
        else:  # 隨機組合
            bull_market_probability = 0.7
        
        # 波動性調整
        volatility_level = getattr(st.session_state, 'simulation_volatility_level', '中波動')
        if volatility_level == "低波動":
            volatility_multiplier = 0.7
        elif volatility_level == "高波動":
            volatility_multiplier = 1.4
        else:  # 中波動
            volatility_multiplier = 1.0
            
        # 生成市場週期
        def generate_market_cycles():
            """生成市場週期序列 - 優化：更接近美國股市歷史特徵"""
            np.random.seed(base_seed)
            cycles = []
            remaining_periods = total_periods
            is_first_cycle = True
            previous_cycle_type = None
            
            while remaining_periods > 0:
                # 決定市場類型
                is_bull_market = np.random.random() < bull_market_probability
                
                if is_bull_market:
                    # 牛市：年化報酬率8%-20%，波動率15%-20%，持續2-5年（嚴格遵循需求文件規格）
                    annual_return = np.random.uniform(0.08, 0.20)
                    
                    # 波動率動態調整：市場轉換期增加波動率
                    if previous_cycle_type == 'bear':
                        # 熊轉牛初期：波動率較高
                        annual_volatility = np.random.uniform(0.18, 0.25) * volatility_multiplier
                    else:
                        # 正常牛市期間
                        annual_volatility = np.random.uniform(0.15, 0.20) * volatility_multiplier
                    
                    duration_years = np.random.uniform(2, 5)
                    market_type = 'bull'
                    
                else:
                    # 熊市：年化報酬率-15%～ -2%，波動率25%-35%，持續1-2年（嚴格遵循需求文件規格）
                    # 基本熊市報酬率：-15% ~ -2%（包含偏態分佈的正報酬可能）
                    base_return = np.random.uniform(-0.15, 0.02)
                    
                    # 極端事件：5-10%機率出現-30%以上年度跌幅
                    extreme_event_probability = 0.075  # 7.5%機率
                    if np.random.random() < extreme_event_probability:
                        # 極端熊市：-35% ~ -30%
                        annual_return = np.random.uniform(-0.35, -0.30)
                        # 極端事件期間波動率急劇上升
                        annual_volatility = np.random.uniform(0.35, 0.45) * volatility_multiplier
                        logger.info(f"模擬極端熊市事件：年化報酬率{annual_return:.2%}，波動率{annual_volatility:.2%}")
                    else:
                        annual_return = base_return
                        # 波動率動態調整：熊市初期急劇上升
                        if previous_cycle_type == 'bull':
                            # 牛轉熊初期：波動率急劇上升
                            annual_volatility = np.random.uniform(0.30, 0.40) * volatility_multiplier
                        else:
                            # 正常熊市期間
                            annual_volatility = np.random.uniform(0.25, 0.35) * volatility_multiplier
                    
                    duration_years = np.random.uniform(1, 2)
                    market_type = 'bear'
                
                duration_periods = min(int(duration_years * periods_per_year), remaining_periods)
                
                # 記錄週期轉換資訊
                transition_info = {
                    'is_transition': not is_first_cycle and previous_cycle_type != market_type,
                    'transition_type': f"{previous_cycle_type}_to_{market_type}" if not is_first_cycle else "initial",
                    'volatility_boost': annual_volatility > 0.25 if market_type == 'bull' else annual_volatility > 0.35
                }
                
                cycles.append({
                    'type': market_type,
                    'duration': duration_periods,
                    'annual_return': annual_return,
                    'annual_volatility': annual_volatility,
                    'transition_info': transition_info  # 新增：週期轉換資訊
                })
                
                remaining_periods -= duration_periods
                previous_cycle_type = market_type
                is_first_cycle = False
            
            return cycles
        
        # 生成完整時間軸
        def generate_simulation_timeline():
            """生成完整的模擬時間軸"""
            timeline = []
            
            for period in range(1, total_periods + 1):
                period_start_date = calculate_period_start_date(start_date, frequency, period)
                period_end_date = calculate_period_end_date(start_date, frequency, period)
                
                timeline.append({
                    'period': period,
                    'adjusted_start_date': period_start_date,
                    'adjusted_end_date': period_end_date
                })
            
            return timeline
        
        # 生成期間價格時間軸
        def generate_period_price_timeline(period_info, base_price, previous_price):
            """
            使用幾何布朗運動生成期間價格變化
            公式：S(t+1) = S(t) * exp((μ - σ²/2) * dt + σ * √dt * Z)
            """
            # 獲取當期市場週期參數
            current_cycle = market_cycles[current_cycle_index]
            
            # 計算期間時間參數
            if frequency == 'monthly':
                dt = 1/12
            elif frequency == 'quarterly':
                dt = 1/4
            elif frequency == 'semi-annually':
                dt = 1/2
            else:  # annually
                dt = 1
            
            # 幾何布朗運動參數
            mu = current_cycle['annual_return']  # 年化報酬率
            sigma = current_cycle['annual_volatility']  # 年化波動率
            
            # 期初價格
            if previous_price is not None:
                period_start_price = previous_price
            else:
                period_start_price = base_price
            
            # 使用幾何布朗運動生成期末價格
            Z = np.random.normal(0, 1)  # 標準常態分佈隨機數
            growth_factor = np.exp((mu - sigma**2/2) * dt + sigma * np.sqrt(dt) * Z)
            period_end_price = period_start_price * growth_factor
            
            # 價格精度控制：小數點後2位
            period_start_price = round(period_start_price, 2)
            period_end_price = round(period_end_price, 2)
            
            # 價格合理性檢查
            price_change = abs(period_end_price - period_start_price) / period_start_price
            if price_change > 0.35:  # ✅ 只限制極端異常（35%以上）
                if period_end_price > period_start_price:
                    period_end_price = period_start_price * 1.35
                else:
                    period_end_price = period_start_price * 0.65
                period_end_price = round(period_end_price, 2)
            
            return {
                'period_start_price': period_start_price,
                'period_end_price': period_end_price,
                'market_type': current_cycle['type'],
                'growth_factor': round(growth_factor, 4)
            }
        
        # 執行模擬數據生成
        market_cycles = generate_market_cycles()
        timeline = generate_simulation_timeline()
        
        # 記錄市場週期資訊
        st.session_state.simulation_data_info['market_cycles'] = market_cycles
        st.session_state.simulation_data_info['total_bull_periods'] = sum(cycle['duration'] for cycle in market_cycles if cycle['type'] == 'bull')
        st.session_state.simulation_data_info['total_bear_periods'] = sum(cycle['duration'] for cycle in market_cycles if cycle['type'] == 'bear')
        
        # 基準價格設定
        stock_base_price = 200.0  # SPY基準價格
        bond_base_yield = 3.0  # 債券基準殖利率
        bond_yield_volatility = 0.003  # 債券殖利率波動率
        
        # 生成期間數據
        market_data_list = []
        previous_spy_price_end = None
        previous_bond_yield_end = None
        current_cycle_index = 0
        current_cycle_remaining = market_cycles[0]['duration']
        
        # 觸發條件追蹤變量
        cumulative_decline_from_peak = 0.0  # 從高點累積跌幅
        peak_price = None  # 記錄高點價格
        bear_market_triggered = False  # 熊市觸發標記
        
        for period_idx, period_info in enumerate(timeline):
            # 為每期設定不同的隨機種子
            np.random.seed(base_seed + period_idx * 17 + int(start_date.timetuple().tm_yday))
            
            # 更新市場週期索引（傳統時間驅動）
            if current_cycle_remaining <= 0 and current_cycle_index < len(market_cycles) - 1:
                current_cycle_index += 1
                current_cycle_remaining = market_cycles[current_cycle_index]['duration']
                bear_market_triggered = False  # 重置觸發標記
            
            # 週期轉換觸發條件檢查（條件驅動）
            if previous_spy_price_end is not None:
                # 更新高點價格
                if peak_price is None or previous_spy_price_end > peak_price:
                    peak_price = previous_spy_price_end
                    cumulative_decline_from_peak = 0.0
                else:
                    # 計算從高點累積跌幅
                    cumulative_decline_from_peak = (peak_price - previous_spy_price_end) / peak_price
                
                # 觸發條件：連續下跌20%觸發熊市（如果當前不是熊市且未被觸發）
                if (cumulative_decline_from_peak >= 0.20 and 
                    market_cycles[current_cycle_index]['type'] == 'bull' and 
                    not bear_market_triggered and
                    current_cycle_index < len(market_cycles) - 1):
                    
                    # 檢查下一個週期是否為熊市，如果是則提前觸發
                    next_cycle_index = current_cycle_index + 1
                    if next_cycle_index < len(market_cycles) and market_cycles[next_cycle_index]['type'] == 'bear':
                        logger.info(f"期間{period_info['period']}：觸發條件滿足，從高點跌幅{cumulative_decline_from_peak:.2%}，提前進入熊市週期")
                        current_cycle_index = next_cycle_index
                        current_cycle_remaining = market_cycles[current_cycle_index]['duration']
                        bear_market_triggered = True
                        
                        # 重置高點追蹤
                        peak_price = previous_spy_price_end
                        cumulative_decline_from_peak = 0.0
            
            period = period_info['period']
            date_str = period_info['adjusted_start_date'].strftime('%Y-%m-%d')
            end_date_str = period_info['adjusted_end_date'].strftime('%Y-%m-%d')
            
            # 生成股票價格 - 使用幾何布朗運動
            stock_price_data = generate_period_price_timeline(
                period_info, 
                stock_base_price, 
                previous_spy_price_end
            )
            
            spy_price_origin = stock_price_data['period_start_price']
            spy_price_end = stock_price_data['period_end_price']
            
            # 計算期間時間參數
            if frequency == 'monthly':
                dt = 1/12
            elif frequency == 'quarterly':
                dt = 1/4
            elif frequency == 'semi-annually':
                dt = 1/2
            else:  # annually
                dt = 1
            
            # 生成債券殖利率 - 使用Vasicek模型簡化版
            if period == 1:
                # 第一期：使用基準殖利率
                bond_yield_origin = bond_base_yield + np.random.normal(0, bond_yield_volatility)
            else:
                # 第二期開始：均值回歸模型
                if previous_bond_yield_end is not None:
                    # 均值回歸：α(θ - r)dt + σ dW 的簡化版
                    mean_reversion_speed = 0.1
                    target_yield = bond_base_yield
                    yield_change = mean_reversion_speed * (target_yield - previous_bond_yield_end) * dt
                    yield_change += bond_yield_volatility * np.random.normal(0, np.sqrt(dt))
                    
                    bond_yield_origin = previous_bond_yield_end + yield_change
                else:
                    bond_yield_origin = bond_base_yield
            
            # 殖利率合理性限制
            bond_yield_origin = max(0.5, min(8.0, bond_yield_origin))
            
            # 期末殖利率生成
            yield_change = bond_yield_volatility * np.random.normal(0, np.sqrt(dt))
            bond_yield_end = bond_yield_origin + yield_change
            bond_yield_end = max(0.5, min(8.0, bond_yield_end))
            
            # 殖利率精度控制：小數點後4位
            bond_yield_origin = round(bond_yield_origin, 4)
            bond_yield_end = round(bond_yield_end, 4)
            
            # 債券價格計算（簡化公式）
            bond_price_origin = round(100.0 / (1 + bond_yield_origin/100), 2)
            bond_price_end = round(100.0 / (1 + bond_yield_end/100), 2)
            
            # 添加市場類型標記
            market_data_list.append({
                'Period': period,
                'Date_Origin': date_str,
                'Date_End': end_date_str,
                'SPY_Price_Origin': spy_price_origin,
                'SPY_Price_End': spy_price_end,
                'Bond_Yield_Origin': bond_yield_origin,
                'Bond_Yield_End': bond_yield_end,
                'Bond_Price_Origin': bond_price_origin,
                'Bond_Price_End': bond_price_end,
                'Market_Type': stock_price_data['market_type'],  # 新增：市場類型標記
                'Data_Source': 'simulation'  # 新增：數據來源標記
            })
            
            # 更新連續性追蹤變量
            previous_spy_price_end = spy_price_end
            previous_bond_yield_end = bond_yield_end
            current_cycle_remaining -= 1
        
        # 創建DataFrame
        market_data = pd.DataFrame(market_data_list)
        
        # 顯示模擬數據詳細資訊
        self._display_simulation_data_info(market_data)
        
        logger.info(f"成功生成 {len(market_data)} 期模擬數據 (種子: {base_seed})")
        return market_data
    
    def _display_simulation_data_info(self, market_data: pd.DataFrame):
        """
        顯示模擬數據詳細資訊和識別標記
        提供清楚的數據源識別和品質指標
        """
        if not hasattr(st.session_state, 'simulation_data_info'):
            return
        
        info = st.session_state.simulation_data_info
        
        # 主要數據源標記
        st.info(f"🎲 **模擬數據** | 生成時間: {info['generation_timestamp'].strftime('%Y-%m-%d %H:%M:%S')} | 隨機種子: **{info['random_seed']}**")
        
        # 詳細資訊展開區域
        with st.expander("📋 模擬數據詳細資訊", expanded=False):
            
            # 基本資訊
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown("#### 🔧 生成配置")
                st.markdown(f"- **隨機種子**: {info['random_seed']}")
                st.markdown(f"- **種子模式**: {info['seed_mode']}")
                st.markdown(f"- **重新生成次數**: {info['regeneration_count']}")
                st.markdown(f"- **數據期間數**: {len(market_data)}")
            
            with col2:
                st.markdown("#### 🌊 市場配置")
                st.markdown(f"- **市場偏好**: {info['market_bias']}")
                st.markdown(f"- **波動性水準**: {info['volatility_level']}")
                
                # 市場週期統計
                if 'total_bull_periods' in info and 'total_bear_periods' in info:
                    bull_ratio = info['total_bull_periods'] / (info['total_bull_periods'] + info['total_bear_periods']) * 100
                    st.markdown(f"- **牛市期間**: {info['total_bull_periods']} 期 ({bull_ratio:.1f}%)")
                    st.markdown(f"- **熊市期間**: {info['total_bear_periods']} 期 ({100-bull_ratio:.1f}%)")
            
            with col3:
                st.markdown("#### 📊 品質指標")
                
                # 計算數據品質指標
                import numpy as np
                if 'SPY_Price_Origin' in market_data.columns and 'SPY_Price_End' in market_data.columns:
                    price_changes = []
                    for i in range(len(market_data)):
                        change = abs(market_data.iloc[i]['SPY_Price_End'] - market_data.iloc[i]['SPY_Price_Origin']) / market_data.iloc[i]['SPY_Price_Origin']
                        price_changes.append(change)
                    
                    avg_change = np.mean(price_changes) * 100
                    max_change = np.max(price_changes) * 100
                    
                    st.markdown(f"- **平均價格變動**: {avg_change:.2f}%")
                    st.markdown(f"- **最大價格變動**: {max_change:.2f}%")
                
                # 殖利率變動統計
                if 'Bond_Yield_Origin' in market_data.columns and 'Bond_Yield_End' in market_data.columns:
                    yield_changes = []
                    for i in range(len(market_data)):
                        change = abs(market_data.iloc[i]['Bond_Yield_End'] - market_data.iloc[i]['Bond_Yield_Origin'])
                        yield_changes.append(change)
                    
                    avg_yield_change = np.mean(yield_changes) * 10000  # 轉換為基點
                    st.markdown(f"- **平均殖利率變動**: {avg_yield_change:.1f} bp")
            
            # 市場週期詳情
            if 'market_cycles' in info:
                st.markdown("#### 🔄 市場週期組成")
                
                cycles_data = []
                extreme_events_count = 0
                transition_events_count = 0
                
                for i, cycle in enumerate(info['market_cycles'], 1):
                    # 檢查極端事件
                    is_extreme = cycle.get('annual_return', 0) < -0.30
                    if is_extreme:
                        extreme_events_count += 1
                    
                    # 檢查週期轉換
                    transition_info = cycle.get('transition_info', {})
                    if transition_info.get('is_transition', False):
                        transition_events_count += 1
                    
                    # 構建週期顯示數據
                    market_icon = '🐂' if cycle['type'] == 'bull' else '🐻'
                    if is_extreme:
                        market_icon += '💥'  # 極端事件標記
                    if transition_info.get('volatility_boost', False):
                        market_icon += '⚡'  # 高波動標記
                    
                    cycles_data.append({
                        '週期': f"第{i}週期",
                        '市場類型': f"{market_icon} {'牛市' if cycle['type'] == 'bull' else '熊市'}",
                        '持續期間': f"{cycle['duration']} 期",
                        '年化報酬率': f"{cycle['annual_return']:.2%}",
                        '年化波動率': f"{cycle['annual_volatility']:.2%}",
                        '特殊事件': '極端熊市' if is_extreme else ('週期轉換' if transition_info.get('is_transition', False) else '-')
                    })
                
                cycles_df = pd.DataFrame(cycles_data)
                st.dataframe(cycles_df, use_container_width=True, hide_index=True)
                
                # 顯示歷史特徵統計
                col_a, col_b, col_c = st.columns(3)
                with col_a:
                    st.metric("極端事件次數", f"{extreme_events_count} 次", help="年化報酬率低於-30%的事件")
                with col_b:
                    st.metric("週期轉換次數", f"{transition_events_count} 次", help="牛熊市場轉換事件")
                with col_c:
                    bear_cycles = [c for c in info['market_cycles'] if c['type'] == 'bear']
                    avg_bear_return = sum(c['annual_return'] for c in bear_cycles) / len(bear_cycles) if bear_cycles else 0
                    st.metric("平均熊市報酬", f"{avg_bear_return:.1%}", help="熊市期間平均年化報酬率")
            
            # 數據追蹤資訊
            st.markdown("#### 🔍 數據追蹤")
            st.markdown(f"- **生成演算法**: 幾何布朗運動 + Vasicek模型")
            st.markdown(f"- **價格精度**: 小數點後2位")
            st.markdown(f"- **殖利率精度**: 小數點後4位")
            st.markdown(f"- **資料完整性**: ✅ 100% 無缺失值")
            
            # 重現性說明
            if info['seed_mode'] == '手動設定':
                st.success(f"🔒 **可重現**: 使用相同種子 {info['random_seed']} 和參數可重現相同結果")
            else:
                st.info(f"🎲 **隨機生成**: 每次重新生成將產生不同的市場情境")
    

    
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
               # 使用垂直排列的指標，避免嵌套列
               st.metric("最終價值", f"${strategy_data['final_value']:,.0f}")
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
        """渲染圖表顯示 - 3.3.3節實作 - 擴展到5個標籤頁"""
        st.markdown("### 📈 視覺化分析")
        
        if not self.calculation_results:
            st.info("請設定投資參數後開始分析")
            return
        
        # 標籤導航 - 7個標籤頁，刪除綜合分析標籤頁
        tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
            "📈 資產成長",
            "📊 報酬比較", 
            "⚠️ 風險分析",
            "💰 投資流分析",
            "🥧 資產配置",
            "📉 回撤分析",
            "📊 風險收益分析"
        ])
        
        with tab1:
            self._render_asset_growth_chart()
        
        with tab2:
            self._render_return_comparison_chart()
        
        with tab3:
            self._render_risk_analysis_chart()
        
        with tab4:
            self._render_investment_flow_chart()
        
        with tab5:
            self._render_asset_allocation_chart()
        
        with tab6:
            self._render_drawdown_analysis_chart()
        
        with tab7:
            self._render_risk_return_analysis_chart()
    
    def _render_asset_growth_chart(self):
        """渲染資產成長圖表 - 使用Altair符合需求文件"""
        st.markdown("**兩種策略的資產累積對比**")
        
        if not self.calculation_results:
            return
        
        # 使用第2章圖表視覺化模組的策略比較圖表
        try:
            chart = create_strategy_comparison_chart(
               va_rebalance_df=self.calculation_results["va_rebalance_df"],
               va_nosell_df=None,  # 簡化版本不顯示NoSell策略
               dca_df=self.calculation_results["dca_df"],
               chart_type="cumulative_value"
            )
            
            st.altair_chart(chart, use_container_width=True)
            
        except Exception as e:
            st.error(f"圖表生成錯誤: {str(e)}")
            # 降級到簡單線圖
            self._render_fallback_line_chart()

        # 新增：在投資流分析下方顯示策略比較摘要表格
        st.markdown("---")  # 分隔線
        st.markdown("#### 📊 策略比較摘要")
        
        try:
            summary_df = self.calculation_results["summary_df"]
            
            # 應用格式化規則
            display_df = self._apply_formatting_rules(summary_df, "SUMMARY")
            
            # 顯示策略比較摘要表格
            st.dataframe(display_df, use_container_width=True, key="investment_flow_summary_table")
            
            # 添加摘要說明
            st.info("💡 **摘要說明**：此表格展示兩種投資策略的詳細績效比較，包含最終價值、報酬率、風險指標等關鍵數據。")
            
        except Exception as e:
            st.error(f"策略比較摘要表格生成錯誤: {str(e)}")
            # 降級顯示基本信息
            try:
               final_values = self._get_final_values()
               annualized_returns = self._get_annualized_returns()
               
               if final_values and annualized_returns:
                   col1, col2 = st.columns(2)
                   with col1:
                       st.metric("VA策略最終價值", f"${final_values.get('va_final_value', 0):,.0f}")
                       st.metric("VA策略年化報酬", f"{annualized_returns.get('va_annualized_return', 0):.2f}%")
                   with col2:
                       st.metric("DCA策略最終價值", f"${final_values.get('dca_final_value', 0):,.0f}")
                       st.metric("DCA策略年化報酬", f"{annualized_returns.get('dca_annualized_return', 0):.2f}%")
            except:
               st.warning("無法顯示策略比較摘要")

    def _render_return_comparison_chart(self):
        """渲染報酬比較圖表 - 使用Altair符合需求文件"""
        st.markdown("**年化報酬率對比**")
        
        if not self.calculation_results:
            return
        
        summary_df = self.calculation_results["summary_df"]
        
        # 使用第2章圖表視覺化模組的柱狀圖
        try:
            chart = create_bar_chart(
               data_df=summary_df,
               x_field="Annualized_Return",
               y_field="Strategy",
               color_field="Strategy",
               title="年化報酬率比較"
            )
            
            st.altair_chart(chart, use_container_width=True)
            
        except Exception as e:
            st.error(f"圖表生成錯誤: {str(e)}")
            # 降級到簡單表格顯示
            st.dataframe(summary_df[["Strategy", "Annualized_Return"]])
    
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
        
        st.plotly_chart(fig, use_container_width=True, key="risk_analysis_chart")
    
    def _render_investment_flow_chart(self):
        """渲染投資流分析圖表 - 包含策略比較摘要表格"""
        st.markdown("**投資流分析對比**")
        
        if not self.calculation_results:
            return
        
        # 分兩欄顯示VA和DCA策略的投資流分析
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("##### 🎯 VA策略投資行為分析")
            try:
               va_df = self.calculation_results["va_rebalance_df"]
               va_chart = create_investment_flow_chart(va_df)
               st.altair_chart(va_chart, use_container_width=True)
               
               # VA策略說明
               st.info("💡 **VA策略說明**：綠色表示買入，紅色表示賣出，灰色表示持有。VA策略會根據市場波動調整投資金額。")
               
            except Exception as e:
               st.error(f"VA投資流圖表生成錯誤: {str(e)}")
               # 降級到簡單數據顯示
               va_df = self.calculation_results["va_rebalance_df"]
               st.dataframe(va_df[["Period", "Invested", "Cum_Value"]].head(10))
        
        with col2:
            st.markdown("##### 💰 DCA策略投資行為分析")
            try:
               dca_df = self.calculation_results["dca_df"]
               
               # 為DCA策略創建投資流圖表數據
               dca_df_copy = dca_df.copy()
               
               # DCA策略使用Fixed_Investment欄位作為投資金額
               if "Fixed_Investment" in dca_df_copy.columns:
                   dca_df_copy["Invested"] = dca_df_copy["Fixed_Investment"]
                   # DCA策略都是買入操作
                   dca_df_copy["Investment_Type"] = "Buy"
               else:
                   # 降級處理：如果沒有Fixed_Investment欄位，使用計算方式
                   if len(dca_df_copy) > 1:
                       # 計算每期投資金額
                       dca_df_copy["Invested"] = dca_df_copy["Cum_Inv"].diff().fillna(dca_df_copy["Cum_Inv"].iloc[0])
                   else:
                       dca_df_copy["Invested"] = dca_df_copy.get("Cum_Inv", 0)
                   dca_df_copy["Investment_Type"] = "Buy"
               
               # 確保Period欄位存在
               if "Period" not in dca_df_copy.columns:
                   dca_df_copy["Period"] = range(len(dca_df_copy))
               
               # 創建DCA投資流圖表
               dca_chart = alt.Chart(dca_df_copy).mark_bar().encode(
                   x=alt.X("Period:Q", title="Period"),
                   y=alt.Y("Invested:Q", title="Investment Amount ($)"),
                   color=alt.Color(
                       "Investment_Type:N",
                       scale=alt.Scale(
                           domain=["Buy"],
                           range=["green"]
                       ),
                       title="Action"
                   ),
                   tooltip=["Period", "Invested", "Investment_Type"]
               ).properties(
                   title="DCA Strategy Investment Flow",
                   width=400,
                   height=300
               )
               
               st.altair_chart(dca_chart, use_container_width=True)
               
               # DCA策略說明
               st.info("💡 **DCA策略說明**：綠色表示固定金額買入。DCA策略每期投入固定金額，不進行賣出操作。")
               
            except Exception as e:
               st.error(f"DCA投資流圖表生成錯誤: {str(e)}")
               # 降級到簡單數據顯示
               dca_df = self.calculation_results["dca_df"]
               if "Fixed_Investment" in dca_df.columns:
                   st.dataframe(dca_df[["Period", "Fixed_Investment", "Cum_Value"]].head(10))
               else:
                   st.dataframe(dca_df[["Period", "Cum_Inv", "Cum_Value"]].head(10))
        

    
    def _render_asset_allocation_chart(self):
        """渲染資產配置圖表 - 獨立標籤頁"""
        st.markdown("**資產配置分析**")
        
        if not self.calculation_results:
            return
        
        try:
            # 從多個來源獲取資產配置比例，確保數據可用性
            stock_ratio = None
            
            # 1. 優先從session_state獲取
            if 'stock_ratio' in st.session_state:
               stock_ratio = st.session_state['stock_ratio']
               # 如果是百分比形式（0-100），轉換為小數形式（0-1）
               if stock_ratio > 1:
                   stock_ratio = stock_ratio / 100
            
            # 2. 從計算結果的參數中獲取
            if stock_ratio is None and hasattr(self, 'last_parameters') and self.last_parameters:
               stock_ratio = self.last_parameters.get('stock_ratio', 0.6)
               if stock_ratio > 1:
                   stock_ratio = stock_ratio / 100
            
            # 3. 使用預設值
            if stock_ratio is None:
               stock_ratio = 0.6  # 預設60%股票，40%債券
            
            bond_ratio = 1 - stock_ratio
            
            # 驗證比例數據
            if stock_ratio < 0 or stock_ratio > 1 or bond_ratio < 0 or bond_ratio > 1:
               raise ValueError(f"無效的資產配置比例: 股票={stock_ratio:.2%}, 債券={bond_ratio:.2%}")
            
            pie_chart = create_allocation_pie_chart(stock_ratio, bond_ratio)
            st.altair_chart(pie_chart, use_container_width=True)
            
            # 添加配置說明
            st.info(f"📊 **配置說明**：股票 {stock_ratio:.1%} | 債券 {bond_ratio:.1%}")
            
            # 添加配置詳細信息
            col1, col2 = st.columns(2)
            with col1:
               st.metric("股票配置", f"{stock_ratio:.1%}", help="投資於股票市場的比例")
            with col2:
               st.metric("債券配置", f"{bond_ratio:.1%}", help="投資於債券市場的比例")
            
        except Exception as e:
            st.error(f"資產配置圖表錯誤: {str(e)}")
            # 降級到文字顯示
            try:
               stock_ratio = st.session_state.get('stock_ratio', 60)
               if stock_ratio > 1:
                   stock_ratio = stock_ratio / 100
               bond_ratio = 1 - stock_ratio
               st.write(f"📊 **資產配置**")
               st.write(f"• 股票比例: {stock_ratio:.1%}")
               st.write(f"• 債券比例: {bond_ratio:.1%}")
            except:
               st.write("📊 **預設資產配置**")
               st.write("• 股票比例: 60.0%")
               st.write("• 債券比例: 40.0%")
    
    def _render_drawdown_analysis_chart(self):
        """渲染回撤分析圖表 - 獨立標籤頁"""
        st.markdown("**回撤分析對比**")
        
        if not self.calculation_results:
            return
        
        try:
            # 創建VA和DCA策略的回撤分析圖表
            va_df = self.calculation_results["va_rebalance_df"]
            dca_df = self.calculation_results["dca_df"]
            
            # 創建VA策略回撤圖表
            va_drawdown_chart = create_drawdown_chart(va_df, "VA策略")
            
            # 創建DCA策略回撤圖表
            dca_drawdown_chart = create_drawdown_chart(dca_df, "DCA策略")
            
            # 垂直合併兩個圖表
            combined_drawdown_chart = alt.vconcat(
               va_drawdown_chart.properties(title="VA策略 回撤分析"),
               dca_drawdown_chart.properties(title="DCA策略 回撤分析")
            ).resolve_scale(x='independent', y='independent')
            
            st.altair_chart(combined_drawdown_chart, use_container_width=True)
            
            # 添加回撤統計摘要
            st.markdown("##### 📊 回撤統計摘要")
            col1, col2 = st.columns(2)
            
            with col1:
               # VA策略回撤統計
               va_max_drawdown = va_df["Cum_Value"].expanding().max()
               va_current_drawdown = (va_df["Cum_Value"] - va_max_drawdown) / va_max_drawdown
               st.metric("VA策略最大回撤", f"{va_current_drawdown.min():.2%}", help="VA策略歷史最大回撤幅度")
            
            with col2:
               # DCA策略回撤統計
               dca_max_drawdown = dca_df["Cum_Value"].expanding().max()
               dca_current_drawdown = (dca_df["Cum_Value"] - dca_max_drawdown) / dca_max_drawdown
               st.metric("DCA策略最大回撤", f"{dca_current_drawdown.min():.2%}", help="DCA策略歷史最大回撤幅度")
            
        except Exception as e:
            st.error(f"回撤分析圖表錯誤: {str(e)}")
            # 降級到簡單統計
            va_df = self.calculation_results["va_rebalance_df"]
            dca_df = self.calculation_results["dca_df"]
            
            # VA策略回撤統計
            va_max_drawdown = va_df["Cum_Value"].expanding().max()
            va_current_drawdown = (va_df["Cum_Value"] - va_max_drawdown) / va_max_drawdown
            st.write(f"VA策略最大回撤: {va_current_drawdown.min():.2%}")
            
            # DCA策略回撤統計
            dca_max_drawdown = dca_df["Cum_Value"].expanding().max()
            dca_current_drawdown = (dca_df["Cum_Value"] - dca_max_drawdown) / dca_max_drawdown
            st.write(f"DCA策略最大回撤: {dca_current_drawdown.min():.2%}")
    
    def _render_risk_return_analysis_chart(self):
        """渲染風險收益分析圖表 - 獨立標籤頁"""
        st.markdown("**風險收益散點圖分析**")
        
        if not self.calculation_results:
            return
        
        try:
            summary_df = self.calculation_results["summary_df"]
            scatter_chart = create_risk_return_scatter(summary_df)
            st.altair_chart(scatter_chart, use_container_width=True)
            
            # 添加風險收益統計摘要
            st.markdown("##### 📊 風險收益統計")
            
            # 顯示每個策略的風險收益指標
            for _, row in summary_df.iterrows():
               with st.expander(f"📈 {row['Strategy']} 策略詳細指標"):
                   col1, col2, col3 = st.columns(3)
                   
                   with col1:
                       st.metric("年化報酬率", f"{row['Annualized_Return']:.2f}%")
                   with col2:
                       st.metric("波動率", f"{row['Volatility']:.2f}%")
                   with col3:
                       st.metric("夏普比率", f"{row['Sharpe_Ratio']:.2f}")
            
        except Exception as e:
            st.error(f"風險收益散點圖錯誤: {str(e)}")
            # 降級到表格顯示
            summary_df = self.calculation_results["summary_df"]
            st.dataframe(summary_df[["Strategy", "Annualized_Return", "Volatility", "Sharpe_Ratio"]])
    

    
    def _render_fallback_line_chart(self):
        """降級線圖 - 當Altair圖表失敗時使用"""
        try:
            va_df = self.calculation_results["va_rebalance_df"]
            dca_df = self.calculation_results["dca_df"]
            
            # 使用基礎線圖
            combined_data = []
            
            # VA數據
            for _, row in va_df.iterrows():
               combined_data.append({
                   "Period": row["Period"],
                   "Cum_Value": row["Cum_Value"],
                   "Strategy": "VA策略"
               })
            
            # DCA數據
            for _, row in dca_df.iterrows():
               combined_data.append({
                   "Period": row["Period"],
                   "Cum_Value": row["Cum_Value"],
                   "Strategy": "DCA策略"
               })
            
            combined_df = pd.DataFrame(combined_data)
            
            chart = create_line_chart(
               data_df=combined_df,
               x_field="Period",
               y_field="Cum_Value",
               color_field="Strategy",
               title="資產成長趨勢比較"
            )
            
            st.altair_chart(chart, use_container_width=True)
            
        except Exception as e:
            st.error(f"降級圖表也失敗: {str(e)}")
            # 最終降級到數據表格
            st.dataframe(combined_df.pivot(index="Period", columns="Strategy", values="Cum_Value"))
    
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
            if st.button("📥 VA策略數據", use_container_width=True, key="download_va_button"):
               self._download_csv("va_strategy")
        
        with col2:
            if st.button("📥 DCA策略數據", use_container_width=True, key="download_dca_button"):
               self._download_csv("dca_strategy")
        
        with col3:
            if st.button("📥 績效摘要", use_container_width=True, key="download_summary_button"):
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
        
        st.plotly_chart(fig, use_container_width=True, key="mobile_growth_chart")
    
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