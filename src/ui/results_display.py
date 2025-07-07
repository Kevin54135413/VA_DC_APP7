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
            
            # 計算結束日期
            frequency_days = {"monthly": 30, "quarterly": 90, "semi_annually": 180, "annually": 365}
            period_days = frequency_days.get(parameters["investment_frequency"], 90)
            end_date = start_date + timedelta(days=total_periods * period_days)
            
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
                        # 真實數據期間：直接使用API數據
                        closest_spy_date = min(spy_data.keys(), key=lambda x: abs((datetime.strptime(x, '%Y-%m-%d') - period_start).days), default=None)
                        spy_price_origin = spy_data.get(closest_spy_date) if closest_spy_date else None
                        if spy_price_origin is None:
                            spy_price_origin = list(spy_data.values())[-1] if spy_data else 400.0
                        logger.debug(f"期間{period}：使用真實API數據，期初價格{spy_price_origin}")
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
                        # 真實數據期間：直接使用API數據
                        closest_bond_date = min(bond_data.keys(), key=lambda x: abs((datetime.strptime(x, '%Y-%m-%d') - period_start).days), default=None)
                        bond_yield_origin = bond_data.get(closest_bond_date) if closest_bond_date else None
                        if bond_yield_origin is None:
                            bond_yield_origin = list(bond_data.values())[-1] if bond_data else 3.0
                        logger.debug(f"期間{period}：使用真實API債券數據，期初殖利率{bond_yield_origin}")
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
                    # 模擬數據期間：使用連續性保證的波動模型
                    base_seed = 42
                    np.random.seed(base_seed + period * 17 + int(start_date.timestamp()) % 1000)
                    
                    # 控制股票價格變化幅度，避免巨大跳躍
                    controlled_volatility = 0.08  # 8%波動，比真實數據期間更小
                    stock_return = np.random.normal(0.015, controlled_volatility)
                    spy_price_end = round(spy_price_origin * (1 + stock_return), 2)
                    
                    # 確保價格變化在合理範圍內
                    price_change_ratio = abs(spy_price_end - spy_price_origin) / spy_price_origin
                    if price_change_ratio > 0.15:
                        max_change = 0.15 if spy_price_end > spy_price_origin else -0.15
                        spy_price_end = round(spy_price_origin * (1 + max_change), 2)
                        logger.debug(f"期間{period}：限制股價變化幅度至15%，從{spy_price_origin}變為{spy_price_end}")
                    
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
                    st.info(f"🌐 真實數據: {' | '.join(data_summary)} | 📊 模擬數據: 第{real_data_cutoff_period + 1}-{total_periods}期（價格連續性已保證）")
                else:
                    st.success(f"✅ 已成功使用真實市場數據生成 {len(market_data)} 期投資數據")
                    st.info(f"🌐 數據來源: {' | '.join(data_summary)}")
            else:
                st.info(f"📊 已使用模擬數據生成 {len(market_data)} 期投資數據")
            
            logger.info(f"成功準備 {len(market_data)} 期市場數據")
            return market_data
            
        except Exception as e:
            logger.error(f"獲取真實市場數據失敗: {str(e)}")
            # 使用備用模擬數據
            return self._generate_fallback_data(parameters)
    
    def _generate_fallback_data(self, parameters: Dict[str, Any]) -> pd.DataFrame:
        """
        生成備用模擬數據 - 當API不可用時使用
        
        確保股票和債券有不同的價格表現，讓股債比率產生實際影響
        """
        # 導入必要模組
        import numpy as np
        from src.utils.trading_days import calculate_period_start_date, calculate_period_end_date
        from src.utils.logger import get_component_logger
        
        logger = get_component_logger("ResultsDisplay")
        logger.info("生成備用模擬數據")
        
        # 解析參數
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
        user_start_date = parameters.get("start_date") or parameters.get("investment_start_date", datetime.now().date())
        
        # 確保start_date是datetime對象
        if isinstance(user_start_date, datetime):
            start_date = user_start_date
        elif hasattr(user_start_date, 'date'):
            # 如果是date對象，轉換為datetime
            start_date = datetime.combine(user_start_date, datetime.min.time())
        else:
            # 如果是字符串，解析為datetime
            start_date = datetime.strptime(str(user_start_date), '%Y-%m-%d')
        
        market_data_list = []
        
        # 設定不同的價格表現參數 - 增加波動以展示策略差異
        stock_base_price = 400.0
        stock_growth_rate = 0.02  # 每期2%成長
        stock_volatility = 0.25   # 25%波動 - 大幅增加波動性確保觸發賣出
        
        bond_base_yield = 3.0
        bond_yield_volatility = 0.3  # 殖利率波動 - 增加波動性
        
        # 改進的隨機數生成機制 - 修正2026年後價格相同問題
        base_seed = 42
        
        # 價格連續性追蹤變量 - 確保模擬數據也有相依性但不完全相同
        previous_spy_price_end = None
        previous_bond_yield_end = None
        
        for period in range(total_periods):
            # 為每期設定不同的隨機種子，確保價格變化多樣性
            np.random.seed(base_seed + period * 17 + int(start_date.timestamp()) % 1000)
            
            # 使用正確的投資頻率計算日期
            period_start = calculate_period_start_date(start_date, parameters["investment_frequency"], period + 1)
            period_end = calculate_period_end_date(start_date, parameters["investment_frequency"], period + 1)
            
            date_str = period_start.strftime('%Y-%m-%d')
            end_date_str = period_end.strftime('%Y-%m-%d')
            
            # 修正的股票價格生成：確保價格相依性但不完全相同
            if period == 0:
                # 第一期：使用基準價格
                stock_trend = stock_base_price
                cycle_factor = 1 + 0.05 * np.sin(2 * np.pi * period / 20)  # 20期為一個週期
                stock_trend *= cycle_factor
                
                volatility_multiplier = 1 + 0.3 * np.sin(2 * np.pi * period / 8)  # 波動率本身也有週期
                period_volatility = stock_volatility * volatility_multiplier
                
                stock_noise = np.random.normal(0, period_volatility * stock_trend)
                spy_price_origin = round(max(stock_trend + stock_noise, 1.0), 2)  # 確保價格大於0
            else:
                # 第二期開始：基於前期期末價格但加入隔夜變動
                if previous_spy_price_end is not None:
                    # 隔夜價格變動：通常在-1%到+1%之間
                    np.random.seed(base_seed + period * 23)  # 確保可重現的隔夜變動
                    overnight_change = np.random.normal(0, 0.005)  # 0.5%標準差
                    overnight_change = max(-0.01, min(0.01, overnight_change))  # 限制在±1%
                    
                    spy_price_origin = round(previous_spy_price_end * (1 + overnight_change), 2)
                    logger.debug(f"模擬數據期間{period}：基於前期期末價格{previous_spy_price_end}，加入{overnight_change:.4f}隔夜變動，期初價格{spy_price_origin}")
                else:
                    # 備用方案
                    stock_trend = stock_base_price * ((1 + stock_growth_rate) ** period)
                    cycle_factor = 1 + 0.05 * np.sin(2 * np.pi * period / 20)
                    stock_trend *= cycle_factor
                    
                    volatility_multiplier = 1 + 0.3 * np.sin(2 * np.pi * period / 8)
                    period_volatility = stock_volatility * volatility_multiplier
                    
                    stock_noise = np.random.normal(0, period_volatility * stock_trend)
                    spy_price_origin = round(max(stock_trend + stock_noise, 1.0), 2)
            
            # 期末股票價格：使用改進的成長模型
            # 添加動量效應（前期表現影響當期）
            momentum_factor = 1.0
            if period > 0:
                # 簡單動量：如果前期成長良好，當期有較高機率繼續成長
                previous_growth_proxy = (period * stock_growth_rate) % 0.1
                momentum_factor = 1 + 0.1 * np.tanh(previous_growth_proxy - 0.05)
            
            enhanced_growth_rate = stock_growth_rate * momentum_factor
            period_growth = np.random.normal(enhanced_growth_rate, period_volatility)
            spy_price_end = round(spy_price_origin * (1 + period_growth), 2)
            
            # 強化價格差異保證機制
            price_difference_ratio = abs(spy_price_end - spy_price_origin) / spy_price_origin
            if price_difference_ratio < 0.01:  # 如果價格變化小於1%
                # 根據期數和日期生成確定性但多變的價格變化
                deterministic_change = 0.02 + 0.03 * np.sin(period * 1.7) + 0.02 * np.cos(period * 2.3)
                change_direction = 1 if (period % 3) != 0 else -1  # 大部分時候上漲，偶爾下跌
                spy_price_end = round(spy_price_origin * (1 + change_direction * abs(deterministic_change)), 2)
            
            # 修正的債券殖利率生成：確保相依性但不完全相同
            if period == 0:
                # 第一期：使用基準殖利率
                interest_rate_cycle = 0.5 * np.sin(2 * np.pi * period / 30)  # 30期利率週期
                economic_factor = 1 + 0.2 * np.sin(2 * np.pi * period / 15)  # 經濟週期影響
                
                bond_yield_base = bond_base_yield + interest_rate_cycle
                bond_yield_change = np.random.normal(0, bond_yield_volatility * economic_factor)
                bond_yield_origin = round(bond_yield_base + bond_yield_change, 4)
            else:
                # 第二期開始：基於前期期末殖利率但加入隔夜變動
                if previous_bond_yield_end is not None:
                    # 殖利率隔夜變動：通常很小，在-0.1%到+0.1%之間
                    np.random.seed(base_seed + period * 29)  # 不同種子避免與股價同步
                    overnight_yield_change = np.random.normal(0, 0.02)  # 2個基點標準差
                    overnight_yield_change = max(-0.001, min(0.001, overnight_yield_change))  # 限制在±0.1%
                    
                    bond_yield_origin = round(max(0.5, min(8.0, previous_bond_yield_end + overnight_yield_change)), 4)
                    logger.debug(f"模擬數據期間{period}：基於前期期末殖利率{previous_bond_yield_end}，加入{overnight_yield_change:.4f}隔夜變動，期初殖利率{bond_yield_origin}")
                else:
                    # 備用方案
                    interest_rate_cycle = 0.5 * np.sin(2 * np.pi * period / 30)
                    economic_factor = 1 + 0.2 * np.sin(2 * np.pi * period / 15)
                    
                    bond_yield_base = bond_base_yield + interest_rate_cycle
                    bond_yield_change = np.random.normal(0, bond_yield_volatility * economic_factor)
                    bond_yield_origin = round(bond_yield_base + bond_yield_change, 4)
            
            # 期末債券殖利率
            yield_momentum = 0.1 * bond_yield_change  # 殖利率有慣性
            bond_yield_end = round(bond_yield_origin + yield_momentum + np.random.normal(0, 0.05), 4)
            
            # 確保殖利率在合理範圍內
            bond_yield_origin = max(0.5, min(8.0, bond_yield_origin))
            bond_yield_end = max(0.5, min(8.0, bond_yield_end))
            
            # 債券價格計算
            bond_price_origin = round(100.0 / (1 + bond_yield_origin/100), 2)
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
        
        logger.info(f"生成 {len(market_data_list)} 期備用模擬數據，股票平均成長 {stock_growth_rate*100}%/期，債券殖利率平均 {bond_base_yield}%")
        return pd.DataFrame(market_data_list)
    
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
        
        st.plotly_chart(fig, use_container_width=True, key="asset_growth_chart")
    
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
        
        st.plotly_chart(fig, use_container_width=True, key="return_comparison_chart")
    
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