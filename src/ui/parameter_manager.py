"""
參數管理器 - 實作第3章3.2節左側參數設定區域
嚴格遵循所有參數定義和整合規範
"""

import streamlit as st
from typing import Dict, Any, Optional, Union
import os
from datetime import datetime
import sys

# 添加src目錄到Python路徑
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# 3.2.1 參數設定實作 - PARAMETERS 字典
PARAMETERS = {
    "initial_investment": {
        "component": "slider_with_input",
        "label": "💰 期初投入金額",
        "range": [0, 100000],  # 0-10萬
        "default": 10000,
        "step": 5000,
        "format": "currency",
        "precision": 2,  # 符合第1章價格精確度
        "help": "投資策略的起始資金",
        # 第1章精確度規範集成
        "validation": {
            "chapter1_compliance": True,
            "price_format_check": True
        },
        # 第2章計算邏輯集成
        "chapter1_integration": {
            "price_precision": "第1章價格精確度標準",
            "data_validation": "API數據格式驗證",
            "currency_formatting": "統一貨幣格式"
        },
        "chapter2_integration": {
            "va_initial_investment": "C0參數",
            "dca_initial_component": "DCA策略第1期部分投入",
            "formula_references": ["calculate_va_target_value", "calculate_dca_investment"]
        }
    },
    "annual_investment": {
        "component": "slider_with_input",
        "label": "💳 年度投入金額",
        "range": [0, 100000],  # 0-10萬
        "default": 12000,  # 預設1.2萬/年
        "step": 5000,
        "format": "currency",
        "help": "每年定期投入的金額（不含期初投入）",
        # 第2章計算邏輯集成
        "chapter2_integration": {
            "parameter_conversion": "convert_annual_to_period_parameters",
            "c_period_calculation": "C_period = annual_investment / periods_per_year",
            "va_formula_integration": "calculate_va_target_value",
            "dca_formula_integration": "calculate_dca_investment"
        }
    },
    "investment_start_date": {
        "component": "date_input",
        "label": "📅 投資起始日期",
        "default": "1994_jan_1",  # 預設為1994年1月1日
        "min_date": "current_date",  # 最早為當前日期
        "max_date": "current_date_plus_10_years",  # 最晚為當前日期+10年
        "format": "YYYY-MM-DD",
        "help": "投資策略開始執行的日期，系統會自動調整為最近的交易日",
        # 第1章時間軸生成集成
        "chapter1_integration": {
            "timeline_generation": True,
            "trading_day_adjustment": "adjust_for_trading_days",
            "period_boundary_calculation": True,
            "api_data_start_date": True
        },
        # 第2章計算邏輯集成
        "chapter2_integration": {
            "timeline_parameter": "user_start_date in generate_simulation_timeline",
            "period_calculation_base": "base_start_date for all period calculations",
            "market_data_alignment": "align market data fetch with user timeline"
        }
    },
    "investment_years": {
        "component": "slider",
        "label": "⏱️ 投資年數",
        "range": [10, 40],
        "default": 30,
        "step": 1,
        "format": "integer",
        "help": "投資策略執行的總年數",
        # 第1章時間軸生成集成
        "chapter1_integration": {
            "timeline_generation": True,
            "trading_day_calculation": True,
            "period_boundary_adjustment": True
        },
        # 第2章期數計算集成
        "chapter2_integration": {
            "total_periods_calculation": True,
            "table_rows_preparation": True,
            "frequency_conversion": True
        }
    },
    "investment_frequency": {
        "component": "radio_buttons",
        "label": "📅 投資頻率",
        "options": [
            {"value": "monthly", "label": "每月", "icon": "📅"},
            {"value": "quarterly", "label": "每季", "icon": "📊"},
            {"value": "semi_annually", "label": "每半年", "icon": "📈"},
            {"value": "annually", "label": "每年", "icon": "🗓️"}
        ],
        "default": "annually",
        "layout": "horizontal",
        "help": "投資操作的執行頻率",
        # 第1章交易日調整集成
        "chapter1_integration": {
            "trading_day_rules": True,
            "frequency_aggregation": True,
            "holiday_adjustment": True
        },
        # 第2章參數轉換集成
        "chapter2_integration": {
            "parameter_conversion": "convert_annual_to_period_parameters",
            "periods_per_year_calculation": True,
            "frequency_based_validation": True
        }
    },
    "stock_percentage": {
        "component": "slider",
        "label": "📊 股票比例",
        "range": [0, 100],
        "default": 100,
        "step": 5,
        "format": "percentage",
        "help": "投資組合中股票的分配比例，債券比例自動計算為 100% - 股票比例",
        # 第1章數據源集成
        "chapter1_integration": {
            "stock_data_source": "Tiingo API (SPY)",
            "bond_data_source": "FRED API (DGS1)",
            "pricing_formulas": "第1章債券定價公式"
        },
        # 第2章配置計算集成
        "chapter2_integration": {
            "portfolio_allocation_module": True,
            "asset_value_calculation": True,
            "rebalancing_logic": True
        }
    },
    "data_source": {
        "component": "user_controlled_selection",
        "label": "📊 數據來源",
        "default_mode": "real_data",  # 預設使用真實市場數據
        "user_options": {
            "options": [
                {
                    "value": "real_data",
                    "label": "真實市場數據",
                    "description": "Tiingo API + FRED API",
                    "icon": "🌐",
                    "priority": 1  # 預設選項
                },
                {
                    "value": "simulation",
                    "label": "模擬數據",
                    "description": "基於歷史統計的模擬",
                    "icon": "🎲",
                    "priority": 2
                }
            ]
        },
        "intelligent_fallback": {
            "enabled": True,
            "trigger_condition": "date_range_data_unavailable",  # 當指定日期範圍無API數據時觸發
            "fallback_logic": {
                "step1": "檢查用戶指定的起始日期+投資年數範圍",
                "step2": "驗證該期間內API數據可用性",
                "step3": "若API數據不足，自動啟用模擬數據並通知用戶",
                "step4": "保留用戶原始選擇，僅在必要時臨時切換"
            },
            "user_notification": {
                "message": "指定期間數據不足，已自動切換至模擬數據",
                "type": "warning",
                "display_duration": 5000  # 5秒
            }
        },
        # 第1章API集成
        "chapter1_integration": {
            "tiingo_api": "SPY股票數據",
            "fred_api": "DGS1債券殖利率數據",
            "simulation_fallback": "generate_market_data函數"
        }
    },
    "va_growth_rate": {
        "component": "slider",
        "label": "📈 VA策略目標成長率",
        "range": [0, 100],  # 支援0到100%成長率
        "default": 13,
        "step": 1,
        "format": "percentage",
        "precision": 4,  # 內部計算精度
        "display_precision": 1,  # 用戶界面精度
        "help": "VA策略的年化目標成長率，支援極端市場情境",
        # 第2章VA公式核心集成
        "chapter2_integration": {
            "core_formula": "calculate_va_target_value",
            "parameter_role": "r_period (年化成長率)",
            "validation_logic": "極端情境合理性檢查",
            "extreme_scenarios": True
        }
    },
    "inflation_adjustment": {
        "enable_toggle": {
            "component": "switch",
            "label": "通膨調整",
            "default": True,
            "help": "是否對DCA投入金額進行通膨調整"
        },
        "inflation_rate": {
            "component": "slider",
            "label": "年通膨率",
            "range": [0.0, 15.0],
            "default": 2.0,
            "step": 0.5,
            "format": "percentage",
            "enabled_when": "inflation_adjustment.enable_toggle == True",
            # 第2章DCA投入公式集成
            "chapter2_integration": {
                "formula_impact": "calculate_dca_investment中的g_period參數",
                "cumulative_calculation": "calculate_dca_cumulative_investment",
                "parameter_conversion": "convert_annual_to_period_parameters"
            }
        }
    },
    "strategy_type": {
        "component": "radio_buttons",
        "label": "🎯 VA策略類型",
        "options": [
            {"value": "Rebalance", "label": "Rebalance", "icon": "⚖️", "description": "允許買入和賣出操作"},
            {"value": "No Sell", "label": "No Sell", "icon": "🔒", "description": "僅允許買入，不執行賣出"}
        ],
        "default": "Rebalance",
        "layout": "horizontal",
        "help": "VA策略的執行類型：Rebalance策略允許買賣操作，No Sell策略僅允許買入",
        # 第2章VA策略執行邏輯集成
        "chapter2_integration": {
            "core_function": "execute_va_strategy",
            "parameter_role": "strategy_type參數",
            "rebalance_logic": "investment_gap < 0時允許賣出操作",
            "no_sell_logic": "investment_gap < 0時不執行任何操作",
            "validation_options": ["Rebalance", "No Sell"]
        }
    }
}

# 3.2.2 進階設定實作 - ADVANCED_SETTINGS
ADVANCED_SETTINGS = {
    "expandable_section": {
        "title": "⚙️ 進階設定",
        "expanded": False,
        "description": "調整策略細節參數"
    },
    "va_growth_rate": {
        "component": "slider",
        "label": "📈 VA策略目標成長率",
        "range": [-20, 50],  # 支援負成長率到極高成長率
        "default": 13,
        "step": 1,
        "format": "percentage",
        "precision": 4,  # 內部計算精度
        "display_precision": 1,  # 用戶界面精度
        "help": "VA策略的年化目標成長率，支援極端市場情境",
        # 第2章VA公式核心集成
        "chapter2_integration": {
            "core_formula": "calculate_va_target_value",
            "parameter_role": "r_period (年化成長率)",
            "validation_logic": "極端情境合理性檢查",
            "extreme_scenarios": True
        }
    },
    "inflation_adjustment": {
        "enable_toggle": {
            "component": "switch",
            "label": "通膨調整",
            "default": True,
            "help": "是否對DCA投入金額進行通膨調整"
        },
        "inflation_rate": {
            "component": "slider",
            "label": "年通膨率",
            "range": [0.0, 15.0],
            "default": 2.0,
            "step": 0.5,
            "format": "percentage",
            "enabled_when": "inflation_adjustment.enable_toggle == True",
            # 第2章DCA投入公式集成
            "chapter2_integration": {
                "formula_impact": "calculate_dca_investment中的g_period參數",
                "cumulative_calculation": "calculate_dca_cumulative_investment",
                "parameter_conversion": "convert_annual_to_period_parameters"
            }
        }
    },
    "data_source": {
        "component": "user_controlled_selection",
        "label": "📊 數據來源",
        "default_mode": "real_data",  # 預設使用真實市場數據
        "user_options": {
            "options": [
                {
                    "value": "real_data",
                    "label": "真實市場數據",
                    "description": "Tiingo API + FRED API",
                    "icon": "🌐",
                    "priority": 1  # 預設選項
                },
                {
                    "value": "simulation",
                    "label": "模擬數據",
                    "description": "基於歷史統計的模擬",
                    "icon": "🎲",
                    "priority": 2
                }
            ]
        },
        "intelligent_fallback": {
            "enabled": True,
            "trigger_condition": "date_range_data_unavailable",  # 當指定日期範圍無API數據時觸發
            "fallback_logic": {
                "step1": "檢查用戶指定的起始日期+投資年數範圍",
                "step2": "驗證該期間內API數據可用性",
                "step3": "若API數據不足，自動啟用模擬數據並通知用戶",
                "step4": "保留用戶原始選擇，僅在必要時臨時切換"
            },
            "user_notification": {
                "message": "指定期間數據不足，已自動切換至模擬數據",
                "type": "warning",
                "display_duration": 5000  # 5秒
            }
        },
        # 第1章API集成
        "chapter1_integration": {
            "tiingo_api": "SPY股票數據",
            "fred_api": "DGS1債券殖利率數據",
            "simulation_fallback": "generate_market_data函數"
        }
    },
    "strategy_type": {
        "component": "radio_buttons",
        "label": "🎯 VA策略類型",
        "options": [
            {"value": "Rebalance", "label": "Rebalance", "icon": "⚖️", "description": "允許買入和賣出操作"},
            {"value": "No Sell", "label": "No Sell", "icon": "🔒", "description": "僅允許買入，不執行賣出"}
        ],
        "default": "Rebalance",
        "layout": "horizontal",
        "help": "VA策略的執行類型：Rebalance策略允許買賣操作，No Sell策略僅允許買入",
        # 第2章VA策略執行邏輯集成
        "chapter2_integration": {
            "core_function": "execute_va_strategy",
            "parameter_role": "strategy_type參數",
            "rebalance_logic": "investment_gap < 0時允許賣出操作",
            "no_sell_logic": "investment_gap < 0時不執行任何操作",
            "validation_options": ["Rebalance", "No Sell"]
        }
    }
}

class ParameterManager:
    """參數管理器 - 實作第3章3.2節所有規格"""
    
    def __init__(self):
        self.basic_params = PARAMETERS
        self.advanced_settings = ADVANCED_SETTINGS
        self.current_values = {}
        self._initialize_session_state()
    
    def _initialize_session_state(self):
        """初始化Streamlit會話狀態"""
        # 基本參數預設值
        if 'initial_investment' not in st.session_state:
            st.session_state.initial_investment = self.basic_params["initial_investment"]["default"]
        
        if 'annual_investment' not in st.session_state:
            st.session_state.annual_investment = self.basic_params["annual_investment"]["default"]
        
        if 'investment_start_date' not in st.session_state:
            # 預設為1994年1月1日
            from datetime import datetime
            st.session_state.investment_start_date = datetime(1994, 1, 1).date()
        
        if 'investment_years' not in st.session_state:
            st.session_state.investment_years = self.basic_params["investment_years"]["default"]
        
        if 'investment_frequency' not in st.session_state:
            st.session_state.investment_frequency = self.basic_params["investment_frequency"]["default"]
        
        if 'stock_ratio' not in st.session_state:
            st.session_state.stock_ratio = self.basic_params["stock_percentage"]["default"]
        
        # 其他參數預設值
        if 'va_growth_rate' not in st.session_state:
            st.session_state.va_growth_rate = self.basic_params["va_growth_rate"]["default"]
        
        if 'inflation_adjustment' not in st.session_state:
            st.session_state.inflation_adjustment = self.basic_params["inflation_adjustment"]["enable_toggle"]["default"]
        
        if 'inflation_rate' not in st.session_state:
            st.session_state.inflation_rate = self.basic_params["inflation_adjustment"]["inflation_rate"]["default"]
        
        if 'data_source_mode' not in st.session_state:
            st.session_state.data_source_mode = self.basic_params["data_source"]["default_mode"]
        
        # 修正：添加strategy_type初始化
        if 'strategy_type' not in st.session_state:
            st.session_state.strategy_type = self.basic_params["strategy_type"]["default"]
    
    def render_basic_parameters(self):
        """渲染參數設定區域 - 永遠可見"""
        st.header("🎯 參數設定")
        
        # 按照指定順序排列參數：
        # 1. 期初投入金額
        self._render_initial_investment()
        
        # 2. 年度投入金額
        self._render_annual_investment()
        
        # 3. 投資起始日期
        self._render_investment_start_date()
        
        # 4. 投資年數
        self._render_investment_years()
        
        # 5. 投資頻率
        self._render_investment_frequency()
        
        # 6. 數據來源
        self._render_data_source_selection()
        
        # 7. 股票比例
        self._render_stock_percentage()
        
        # 8. VA策略目標成長率
        self._render_va_growth_rate()
        
        # 9. 通膨調整
        self._render_inflation_adjustment()
        
        # 10. VA策略類型
        self._render_strategy_type()
    
    def _render_initial_investment(self):
        """渲染期初投入金額參數 - 嚴格按照規格"""
        param = self.basic_params["initial_investment"]
        
        # 使用number_input實現slider_with_input效果
        col1, col2 = st.columns([3, 1])
        
        with col1:
            # 主要滑桿
            investment_amount = st.slider(
                param["label"],
                min_value=param["range"][0],
                max_value=param["range"][1],
                value=st.session_state.initial_investment,
                step=param["step"],
                format="$%d",
                help=param["help"],
                key="initial_investment_slider"
            )
        
        with col2:
            # 輔助數字輸入
            investment_input = st.number_input(
                "精確輸入",
                min_value=param["range"][0],
                max_value=param["range"][1],
                value=investment_amount,
                step=param["step"],
                format="%d",
                key="initial_investment_input"
            )
        
        # 同步兩個輸入
        if investment_amount != investment_input:
            st.session_state.initial_investment = investment_input
            st.rerun()
        else:
            st.session_state.initial_investment = investment_amount
        
        # 顯示第1章和第2章整合資訊
        if st.checkbox("🔧 顯示技術整合資訊", key="show_initial_investment_tech_info"):
            st.markdown("**第1章數據源整合**")
            ch1_integration = param['chapter1_integration']
            for key, value in ch1_integration.items():
                st.markdown(f"• **{key}**: {value}")
            
            st.markdown("**第2章計算邏輯整合**")
            ch2_integration = param['chapter2_integration']
            for key, value in ch2_integration.items():
                if isinstance(value, list):
                    st.markdown(f"• **{key}**: {', '.join(value)}")
                else:
                    st.markdown(f"• **{key}**: {value}")
    
    def _render_annual_investment(self):
        """渲染年度投入金額參數 - 嚴格按照規格"""
        param = self.basic_params["annual_investment"]
        
        # 使用number_input實現slider_with_input效果
        col1, col2 = st.columns([3, 1])
        
        with col1:
            # 主要滑桿
            annual_amount = st.slider(
                param["label"],
                min_value=param["range"][0],
                max_value=param["range"][1],
                value=st.session_state.annual_investment,
                step=param["step"],
                format="$%d",
                help=param["help"],
                key="annual_investment_slider"
            )
        
        with col2:
            # 輔助數字輸入
            annual_input = st.number_input(
                "精確輸入",
                min_value=param["range"][0],
                max_value=param["range"][1],
                value=annual_amount,
                step=param["step"],
                format="%d",
                key="annual_investment_input"
            )
        
        # 同步兩個輸入
        if annual_amount != annual_input:
            st.session_state.annual_investment = annual_input
            st.rerun()
        else:
            st.session_state.annual_investment = annual_amount
        
        # 顯示期間投入金額預覽
        frequency_map = {"monthly": 12, "quarterly": 4, "semi_annually": 2, "annually": 1}
        periods_per_year = frequency_map.get(st.session_state.investment_frequency, 1)
        period_amount = st.session_state.annual_investment / periods_per_year
        frequency_labels = {"monthly": "每月", "quarterly": "每季", "semi_annually": "每半年", "annually": "每年"}
        frequency_label = frequency_labels.get(st.session_state.investment_frequency, "每年")
        
        st.info(f"📊 {frequency_label}投入金額: ${period_amount:,.0f}")
        
        # 顯示第2章整合資訊
        if st.checkbox("🔧 顯示技術整合資訊", key="show_annual_investment_tech_info"):
            st.markdown("**第2章計算邏輯整合**")
            ch2_integration = param['chapter2_integration']
            for key, value in ch2_integration.items():
                st.markdown(f"• **{key}**: {value}")
    
    def _render_investment_start_date(self):
        """渲染投資起始日期參數 - 嚴格按照規格"""
        param = self.basic_params["investment_start_date"]
        
        from datetime import datetime, timedelta
        
        # 確保session state已初始化 - 修正：防護機制
        if 'investment_start_date' not in st.session_state:
            st.session_state.investment_start_date = datetime(1994, 1, 1).date()
        
        # 計算日期範圍 - 支援歷史數據分析
        current_date = datetime.now().date()
        min_date = datetime(1994, 1, 1).date()  # SPY ETF成立日期
        max_date = current_date + timedelta(days=365*10)  # 10年後
        
        # 主要日期選擇器
        selected_date = st.date_input(
            param["label"],
            value=st.session_state.investment_start_date,
            min_value=min_date,
            max_value=max_date,
            help=param["help"],
            key="investment_start_date"
        )
        
        # 顯示交易日調整資訊
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # 檢查是否為交易日
            try:
                from src.utils.trading_days import is_trading_day, adjust_for_trading_days
                from datetime import datetime as dt
                
                selected_datetime = dt.combine(selected_date, dt.min.time())
                
                if is_trading_day(selected_datetime):
                    st.success(f"✅ {selected_date} 是交易日")
                else:
                    adjusted_date = adjust_for_trading_days(selected_datetime, 'next')
                    st.warning(f"⚠️ {selected_date} 非交易日，將調整為 {adjusted_date.date()}")
            except Exception as e:
                st.info(f"📅 已選擇日期: {selected_date}")
        
        with col2:
            # 時間軸預覽按鈕
            if st.button("📊 預覽時間軸", key="preview_timeline"):
                self._show_timeline_preview(selected_date)
        
        # 顯示第1章和第2章整合資訊
        if st.checkbox("🔧 顯示技術整合資訊", key="show_start_date_tech_info"):
            st.markdown("**第1章時間軸生成集成**")
            ch1_integration = param['chapter1_integration']
            for key, value in ch1_integration.items():
                st.markdown(f"• **{key}**: {value}")
            
            st.markdown("**第2章計算邏輯集成**")
            ch2_integration = param['chapter2_integration']
            for key, value in ch2_integration.items():
                st.markdown(f"• **{key}**: {value}")
    
    def _show_timeline_preview(self, start_date):
        """顯示時間軸預覽"""
        try:
            from src.utils.trading_days import generate_simulation_timeline
            from datetime import datetime as dt
            
            # 生成預覽時間軸（只顯示前4期）
            start_datetime = dt.combine(start_date, dt.min.time())
            preview_timeline = generate_simulation_timeline(
                investment_years=1,  # 只預覽1年
                frequency=st.session_state.get('investment_frequency', 'quarterly'),
                user_start_date=start_datetime
            )
            
            st.info("📅 **時間軸預覽**（前4期）")
            for i, period in enumerate(preview_timeline[:4]):
                st.markdown(
                    f"**第{period['period']}期**: "
                    f"{period['adjusted_start_date'].strftime('%Y-%m-%d')} ~ "
                    f"{period['adjusted_end_date'].strftime('%Y-%m-%d')} "
                    f"({period['trading_days_count']}個交易日)"
                )
        except Exception as e:
            st.error(f"時間軸預覽失敗: {e}")
    
    def _render_investment_years(self):
        """渲染投資年數參數 - 嚴格按照規格"""
        param = self.basic_params["investment_years"]
        
        years = st.slider(
            param["label"],
            min_value=param["range"][0],
            max_value=param["range"][1],
            step=param["step"],
            help=param["help"],
            key="investment_years"
        )
        
        # 顯示計算的總期數
        frequency_map = {"monthly": 12, "quarterly": 4, "semi_annually": 2, "annually": 1}
        periods_per_year = frequency_map.get(st.session_state.investment_frequency, 1)
        total_periods = years * periods_per_year
        
        st.info(f"📊 總投資期數: {total_periods} 期 ({years} 年 × {periods_per_year} 期/年)")
        
        # 顯示第1章和第2章整合資訊
        if st.checkbox("🔧 顯示技術整合資訊", key="show_investment_years_tech_info"):
            st.markdown("**第1章時間軸整合**")
            ch1_integration = param['chapter1_integration']
            for key, value in ch1_integration.items():
                st.markdown(f"• **{key}**: {value}")
            
            st.markdown("**第2章期數計算整合**")
            ch2_integration = param['chapter2_integration']
            for key, value in ch2_integration.items():
                if isinstance(value, list):
                    st.markdown(f"• **{key}**: {', '.join(value)}")
                else:
                    st.markdown(f"• **{key}**: {value}")
    
    def _render_investment_frequency(self):
        """渲染投資頻率參數 - 嚴格按照規格"""
        param = self.basic_params["investment_frequency"]
        
        # 創建選項標籤
        options = param["options"]
        option_labels = [f"{opt['icon']} {opt['label']}" for opt in options]
        option_values = [opt['value'] for opt in options]
        
        # 找到當前值的索引
        current_index = 0
        try:
            current_index = option_values.index(st.session_state.investment_frequency)
        except ValueError:
            current_index = option_values.index(param["default"])
        
        # 渲染radio buttons
        selected_index = st.radio(
            param["label"],
            range(len(options)),
            index=current_index,
            format_func=lambda x: option_labels[x],
            horizontal=True,
            help=param["help"],
            key="investment_frequency_radio"
        )
        
        # 獲取選中的值（不直接修改session state）
        selected_frequency = option_values[selected_index]
        
        # 顯示頻率說明
        selected_option = options[selected_index]
        st.success(f"✅ 已選擇: {selected_option['icon']} {selected_option['label']}")
        
        # 確保session state同步（只在值確實改變時更新）
        if 'investment_frequency' not in st.session_state or st.session_state.investment_frequency != selected_frequency:
            st.session_state.investment_frequency = selected_frequency
        
        # 顯示第1章和第2章整合資訊
        if st.checkbox("🔧 顯示技術整合資訊", key="show_frequency_tech_info"):
            st.markdown("**第1章交易日整合**")
            ch1_integration = param['chapter1_integration']
            for key, value in ch1_integration.items():
                st.markdown(f"• **{key}**: {value}")
            
            st.markdown("**第2章參數轉換整合**")
            ch2_integration = param['chapter2_integration']
            for key, value in ch2_integration.items():
                if isinstance(value, list):
                    st.markdown(f"• **{key}**: {', '.join(value)}")
                else:
                    st.markdown(f"• **{key}**: {value}")
    
    def _render_stock_percentage(self):
        """渲染股票比例參數 - 債券比例自動計算"""
        param = self.basic_params["stock_percentage"]
        
        # 股票比例滑桿
        stock_ratio = st.slider(
            param["label"],
            min_value=param["range"][0],
            max_value=param["range"][1],
            value=st.session_state.stock_ratio,
            step=param["step"],
            format="%d%%",
            help=param["help"],
            key="stock_ratio_slider"
        )
        
        # 自動計算債券比例
        bond_ratio = 100 - stock_ratio
        
        # 更新會話狀態
        st.session_state.stock_ratio = stock_ratio
        st.session_state.bond_ratio = bond_ratio
        
        # 顯示配置摘要
        st.info(f"📊 投資組合配置: {stock_ratio}% 股票 + {bond_ratio}% 債券")
        
        # 顯示第1章和第2章整合資訊
        if st.checkbox("🔧 顯示技術整合資訊", key="show_stock_percentage_tech_info"):
            st.markdown("**第1章數據源整合**")
            ch1_integration = param['chapter1_integration']
            for key, value in ch1_integration.items():
                st.markdown(f"• **{key}**: {value}")
            
            st.markdown("**第2章計算邏輯整合**")
            ch2_integration = param['chapter2_integration']
            for key, value in ch2_integration.items():
                st.markdown(f"• **{key}**: {value}")
    
    def _render_allocation_pie_chart(self, stock_ratio: int, bond_ratio: int):
        """渲染互動式配置圓餅圖"""
        try:
            import plotly.express as px
            import pandas as pd
            
            # 準備圓餅圖數據
            data = {
                'asset_type': ['股票', '債券'],
                'percentage': [stock_ratio, bond_ratio],
                'colors': ['#3b82f6', '#f59e0b']
            }
            
            df = pd.DataFrame(data)
            
            # 創建圓餅圖
            fig = px.pie(
                df, 
                values='percentage', 
                names='asset_type',
                title="📊 投資組合配置",
                color_discrete_sequence=['#3b82f6', '#f59e0b']
            )
            
            # 優化圖表設定
            fig.update_traces(
                textposition='inside',
                textinfo='percent+label',
                hovertemplate='<b>%{label}</b><br>比例: %{percent}<br>數值: %{value}%<extra></extra>'
            )
            
            fig.update_layout(
                showlegend=True,
                height=300,
                margin=dict(t=50, b=50, l=50, r=50)
            )
            
            st.plotly_chart(fig, use_container_width=True, key="allocation_pie_chart")
            
        except ImportError:
            # 如果沒有plotly，使用簡單的文字顯示
            st.write("📊 投資組合配置:")
            st.write(f"📈 股票: {stock_ratio}%")
            st.write(f"🏦 債券: {bond_ratio}%")
    
    def render_advanced_settings(self):
        """渲染進階設定區域 - 已合併到基本參數中，保留此方法以維持向後兼容性"""
        # 所有進階設定已合併到 render_basic_parameters() 中
        # 此方法保留為空以維持向後兼容性
        pass
    
    def _render_va_growth_rate(self):
        """渲染VA策略目標成長率參數 - 嚴格按照規格"""
        param = self.basic_params["va_growth_rate"]
        
        growth_rate = st.slider(
            param["label"],
            min_value=param["range"][0],
            max_value=param["range"][1],
            step=param["step"],
            format=f"%.{param['display_precision']}f%%",
            help=param["help"],
            key="va_growth_rate"
        )
        
        # 顯示極端情境說明
        if growth_rate < 0:
            st.warning(f"⚠️ 負成長率情境: {growth_rate}% - 適用於經濟衰退分析")
        elif growth_rate > 30:
            st.warning(f"🚀 高成長率情境: {growth_rate}% - 適用於牛市或新興市場分析")
        else:
            st.info(f"📊 標準成長率: {growth_rate}% - 適用於一般市場情境")
        
        # 顯示第2章整合資訊
        if st.checkbox("🔧 顯示技術整合資訊", key="show_va_growth_rate_tech_info"):
            st.markdown("**第2章VA公式核心整合**")
            ch2_integration = param['chapter2_integration']
            for key, value in ch2_integration.items():
                st.markdown(f"• **{key}**: {value}")
            st.markdown(f"• **內部精度**: {param['precision']} 位小數")
            st.markdown(f"• **顯示精度**: {param['display_precision']} 位小數")
    
    def _render_strategy_type(self):
        """渲染VA策略類型參數 - 嚴格按照規格"""
        param = self.basic_params["strategy_type"]
        
        # 創建選項標籤
        options = param["options"]
        option_labels = [f"{opt['icon']} {opt['label']}" for opt in options]
        option_values = [opt['value'] for opt in options]
        
        # 找到當前值的索引
        current_index = 0
        try:
            current_index = option_values.index(st.session_state.strategy_type)
        except ValueError:
            current_index = option_values.index(param["default"])
        
        # 渲染radio buttons
        selected_index = st.radio(
            param["label"],
            range(len(options)),
            index=current_index,
            format_func=lambda x: option_labels[x],
            horizontal=True,
            help=param["help"],
            key="strategy_type_radio"
        )
        
        # 獲取選中的值（不直接修改session state）
        selected_strategy = option_values[selected_index]
        
        # 顯示策略類型說明
        selected_option = options[selected_index]
        st.success(f"✅ 已選擇: {selected_option['icon']} {selected_option['label']}")
        st.info(f"📝 說明: {selected_option['description']}")
        
        # 確保session state同步（只在值確實改變時更新）
        if 'strategy_type' not in st.session_state or st.session_state.strategy_type != selected_strategy:
            st.session_state.strategy_type = selected_strategy
        
        # 修正：移除嵌套expander，改用checkbox控制顯示技術整合資訊
        if st.checkbox("🔧 顯示技術整合資訊", key="show_strategy_type_tech_info"):
            st.markdown("**第2章VA策略執行邏輯整合**")
            ch2_integration = param['chapter2_integration']
            for key, value in ch2_integration.items():
                st.markdown(f"• **{key}**: {value}")
    
    def _render_inflation_adjustment(self):
        """渲染通膨調整參數 - 嚴格按照規格"""
        toggle_config = self.basic_params["inflation_adjustment"]["enable_toggle"]
        rate_config = self.basic_params["inflation_adjustment"]["inflation_rate"]
        
        # 通膨調整開關
        inflation_enabled = st.toggle(
            toggle_config["label"],
            help=toggle_config["help"],
            key="inflation_adjustment"
        )
        
        # 通膨率設定（條件顯示）
        if inflation_enabled:
            inflation_rate = st.slider(
                rate_config["label"],
                min_value=rate_config["range"][0],
                max_value=rate_config["range"][1],
                step=rate_config["step"],
                format="%.1f%%",
                key="inflation_rate"
            )
            
            # 顯示通膨影響說明
            st.info(f"📈 通膨調整: DCA投入金額將每年增加 {inflation_rate}%")
            
            # 顯示第2章整合資訊
            if st.checkbox("🔧 顯示技術整合資訊", key="show_inflation_adjustment_tech_info"):
                st.markdown("**第2章DCA投入公式整合**")
                ch2_integration = rate_config['chapter2_integration']
                for key, value in ch2_integration.items():
                    st.markdown(f"• **{key}**: {value}")
        else:
            st.info("🔒 通膨調整已關閉，DCA投入金額保持固定")
    
    def _render_data_source_selection(self):
        """渲染數據來源選擇 - user_controlled_selection"""
        param = self.basic_params["data_source"]
        
        st.subheader(param["label"])
        
        # 用戶控制的數據源選擇
        options = param["user_options"]["options"]
        
        # 根據priority排序選項
        sorted_options = sorted(options, key=lambda x: x['priority'])
        
        option_labels = [f"{opt['icon']} {opt['label']}" for opt in sorted_options]
        option_values = [opt['value'] for opt in sorted_options]
        
        # 找到預設選項的索引
        default_value = param["default_mode"]
        try:
            default_index = option_values.index(default_value)
        except ValueError:
            default_index = 0
        
        selected_index = st.radio(
            "請選擇數據來源",
            range(len(sorted_options)),
            index=default_index,
            format_func=lambda x: option_labels[x],
            key="data_source_selection",
            help="選擇用於投資分析的數據來源"
        )
        
        selected_option = sorted_options[selected_index]
        st.session_state.data_source_mode = selected_option['value']
        
        # 顯示選擇的數據源資訊
        st.info(f"📊 已選擇: {selected_option['description']}")
        
        # 顯示智能回退機制說明
        if selected_option['value'] == 'real_data':
            fallback_config = param["intelligent_fallback"]
            st.success("✅ 已選擇真實市場數據")
            st.info("💡 智能回退機制：若指定期間API數據不足，系統會自動補充模擬數據並通知您")
            
            # 檢查API金鑰狀態
            tiingo_key = self._get_api_key('TIINGO_API_KEY')
            fred_key = self._get_api_key('FRED_API_KEY')
            
            if tiingo_key and fred_key:
                st.success("🔑 API金鑰已配置完成")
            else:
                missing_keys = []
                if not tiingo_key:
                    missing_keys.append("TIINGO_API_KEY")
                if not fred_key:
                    missing_keys.append("FRED_API_KEY")
                
                # 更友好的API金鑰缺失提示
                with st.expander("⚠️ API金鑰設定指引", expanded=True):
                    st.markdown(f"**缺少API金鑰**: {', '.join(missing_keys)}")
                    st.markdown("**🎯 不用擔心！系統會自動處理：**")
                    st.markdown("• 🔄 自動切換到高品質模擬數據")
                    st.markdown("• 📊 所有功能正常運作")
                    st.markdown("• 🎲 基於真實歷史統計的模擬")
                    
                    st.markdown("**🔑 如需使用真實數據，請設定API金鑰：**")
                    st.markdown("1. **Tiingo API** (股票數據) - [免費註冊](https://api.tiingo.com/)")
                    st.markdown("2. **FRED API** (債券數據) - [免費註冊](https://fred.stlouisfed.org/docs/api/api_key.html)")
                    
                    st.markdown("**📋 Streamlit Cloud設定步驟：**")
                    st.markdown("1. 點擊右下角 'Manage app'")
                    st.markdown("2. 進入 'Secrets' 設定")
                    st.markdown("3. 添加：")
                    st.code('''TIINGO_API_KEY = "your_tiingo_key_here"
FRED_API_KEY = "your_fred_key_here"''', language="toml")
                    
                    st.info("💡 **提示**: 即使沒有API金鑰，系統也能完美運行所有功能！")
        
        elif selected_option['value'] == 'simulation':
            st.success("✅ 已選擇模擬數據")
            st.info("🎲 將使用基於歷史統計的模擬數據進行分析")
        
        # 顯示第1章整合資訊
        if st.checkbox("🔧 顯示技術整合資訊", key="show_data_source_tech_info"):
            st.markdown("**第1章數據源完整整合**")
            integration = param["chapter1_integration"]
            for key, value in integration.items():
                st.markdown(f"• **{key}**: {value}")
    
    def _detect_current_data_source(self) -> str:
        """檢測當前數據源狀態 - 整合第1章API機制"""
        # 檢查API金鑰
        tiingo_key = self._get_api_key('TIINGO_API_KEY')
        fred_key = self._get_api_key('FRED_API_KEY')
        
        if tiingo_key and fred_key:
            return "real_data"
        elif tiingo_key or fred_key:
            return "simulation"
        else:
            return "offline"
    
    def _get_api_key(self, key_name: str) -> Optional[str]:
        """獲取API金鑰 - 多層級策略"""
        # 第1層：Streamlit Secrets
        try:
            if hasattr(st, 'secrets') and key_name in st.secrets:
                return st.secrets[key_name]
        except:
            pass
        
        # 第2層：環境變數
        return os.environ.get(key_name)
    
    def get_all_parameters(self) -> Dict[str, Any]:
        """獲取所有參數值 - 供計算引擎使用"""
        return {
            # 基本參數
            "initial_investment": st.session_state.initial_investment,
            "annual_investment": st.session_state.annual_investment,
            "investment_start_date": st.session_state.investment_start_date,
            "investment_years": st.session_state.investment_years,
            "investment_frequency": st.session_state.investment_frequency,
            "stock_ratio": st.session_state.stock_ratio,
            "bond_ratio": 100 - st.session_state.stock_ratio,
            
            # 進階設定
            "va_growth_rate": st.session_state.va_growth_rate,
            "inflation_adjustment": st.session_state.inflation_adjustment,
            "inflation_rate": st.session_state.inflation_rate if st.session_state.inflation_adjustment else 0,
            "data_source_mode": st.session_state.get("data_source_mode", "real_data"),
            "strategy_type": st.session_state.get("strategy_type", "Rebalance"),
            
            # 計算衍生參數
            "total_periods": self._calculate_total_periods(),
            "periods_per_year": self._get_periods_per_year()
        }
    
    def _calculate_total_periods(self) -> int:
        """計算總投資期數"""
        frequency_map = {"monthly": 12, "quarterly": 4, "semi_annually": 2, "annually": 1}
        periods_per_year = frequency_map.get(st.session_state.investment_frequency, 1)
        return st.session_state.investment_years * periods_per_year
    
    def _get_periods_per_year(self) -> int:
        """獲取每年期數"""
        frequency_map = {"monthly": 12, "quarterly": 4, "semi_annually": 2, "annually": 1}
        return frequency_map.get(st.session_state.investment_frequency, 1)
    
    def render_calculation_button(self):
        """渲染計算按鈕 - 主要計算觸發點"""
        st.markdown("---")
        st.subheader("🚀 開始計算")
        
        # 檢查參數完整性
        params = self.get_all_parameters()
        validation_result = self.validate_parameters()
        
        if validation_result["is_valid"]:
            # 參數有效，顯示計算按鈕
            col1, col2, col3 = st.columns([2, 3, 2])
            
            with col2:
                if st.button(
                    "🎯 執行策略計算",
                    type="primary",
                    use_container_width=True,
                    key="main_calculation_button",
                    help="點擊開始計算VA和DCA策略比較"
                ):
                    # 觸發計算
                    st.session_state.trigger_calculation = True
                    st.session_state.calculation_params = params
                    st.rerun()
            
            # 顯示將要計算的內容預覽
            st.info("📊 將計算以下內容：VA策略表格、DCA策略表格、績效比較分析、投資建議")
            
        else:
            # 參數無效，顯示錯誤信息
            st.error("❌ 參數設定有誤，請檢查以下問題：")
            for error in validation_result["errors"]:
                st.markdown(f"• {error}")
            
            # 顯示禁用的按鈕
            col1, col2, col3 = st.columns([2, 3, 2])
            with col2:
                st.button(
                    "🚫 請先修正參數",
                    disabled=True,
                    use_container_width=True,
                    help="修正上述參數問題後即可開始計算"
                )
        
        # 顯示上次計算時間（如果有）
        if hasattr(st.session_state, 'last_calculation_time') and st.session_state.last_calculation_time:
            st.caption(f"上次計算時間: {st.session_state.last_calculation_time.strftime('%Y-%m-%d %H:%M:%S')}")

    def render_parameter_summary(self):
        """渲染參數摘要卡片"""
        st.subheader("📋 參數摘要")
        
        params = self.get_all_parameters()
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("💰 期初投入", f"${params['initial_investment']:,}")
            st.metric("💳 年度投入", f"${params['annual_investment']:,}")
            st.metric("⏱️ 投資期間", f"{params['investment_years']} 年")
        
        with col2:
            st.metric("📅 投資頻率", params['investment_frequency'])
            st.metric("📈 VA目標成長率", f"{params['va_growth_rate']}%")
            st.metric("📊 股票比例", f"{params['stock_ratio']}%")
    
    def validate_parameters(self) -> Dict[str, Any]:
        """驗證參數有效性"""
        params = self.get_all_parameters()
        validation_result = {
            "is_valid": True,
            "errors": [],
            "warnings": []
        }
        
        # 基本參數驗證
        if params["initial_investment"] < 0:
            validation_result["errors"].append("期初投入金額不能為負數")
            validation_result["is_valid"] = False
        
        if params["investment_years"] < 5:
            validation_result["errors"].append("投資年數不能少於5年")
            validation_result["is_valid"] = False
        
        # 進階參數驗證
        if params["va_growth_rate"] < -20 or params["va_growth_rate"] > 50:
            validation_result["errors"].append("VA成長率超出合理範圍(-20%到50%)")
            validation_result["is_valid"] = False
        
        # 警告檢查
        if params["va_growth_rate"] > 30:
            validation_result["warnings"].append("高成長率可能不符合實際市場情況")
        
        if params["stock_ratio"] > 90:
            validation_result["warnings"].append("股票比例過高可能增加投資風險")
        
        return validation_result
    
    def render_mobile_optimized_parameters(self):
        """
        渲染移動端優化參數 - 3.5.1節規格
        簡化交互、大步長、減少小數精度
        """
        # 獲取設備優化配置
        device_config = st.session_state.get('device_config', {})
        step_size = device_config.get('step_size', 1000)
        decimal_places = device_config.get('decimal_places', 0)
        show_advanced = device_config.get('show_advanced', False)
        
        # 💰 期初投入金額 - 簡化版
        self._render_mobile_initial_investment(step_size)
        
        # ⏱️ 投資年數 - 簡化版
        self._render_mobile_investment_years()
        
        # 📅 投資頻率 - 簡化版
        self._render_mobile_investment_frequency()
        
        # 📊 股債配置 - 簡化版
        self._render_mobile_asset_allocation()
        
        # 進階設定（可選）
        if show_advanced:
            with st.expander("🔧 進階設定"):
                self._render_mobile_advanced_settings()
    
    def _render_mobile_initial_investment(self, step_size: int):
        """渲染移動端期初投入金額 - 大步長"""
        st.markdown("#### 💰 期初投入金額")
        
        # 使用大步長的滑桿
        investment_amount = st.slider(
            "",
            min_value=0,
            max_value=10000000,
            value=st.session_state.initial_investment,
            step=step_size,
            format="$%d",
            help="滑動選擇投資金額",
            key="mobile_initial_investment"
        )
        
        st.session_state.initial_investment = investment_amount
        
        # 顯示格式化金額
        st.success(f"✅ 投資金額: ${investment_amount:,}")
    
    def _render_mobile_investment_years(self):
        """渲染移動端投資年數 - 簡化版"""
        st.markdown("#### ⏱️ 投資年數")
        
        investment_years = st.slider(
            "",
            min_value=5,
            max_value=30,
            value=st.session_state.investment_years,
            step=1,
            format="%d年",
            help="選擇投資期間",
            key="mobile_investment_years"
        )
        
        st.session_state.investment_years = investment_years
        st.success(f"✅ 投資期間: {investment_years} 年")
    
    def _render_mobile_investment_frequency(self):
        """渲染移動端投資頻率 - 簡化版"""
        st.markdown("#### 📅 投資頻率")
        
        # 簡化選項
        frequency_options = {
            "monthly": "📅 每月",
            "quarterly": "📅 每季",
            "annually": "📅 每年"
        }
        
        selected_frequency = st.selectbox(
            "",
            options=list(frequency_options.keys()),
            index=list(frequency_options.keys()).index(st.session_state.investment_frequency),
            format_func=lambda x: frequency_options[x],
            help="選擇投資頻率",
            key="mobile_investment_frequency"
        )
        
        st.session_state.investment_frequency = selected_frequency
        st.success(f"✅ 投資頻率: {frequency_options[selected_frequency]}")
    
    def _render_mobile_asset_allocation(self):
        """渲染移動端股債配置 - 簡化版"""
        st.markdown("#### 📊 股債配置")
        
        # 使用大步長的滑桿
        stock_ratio = st.slider(
            "📈 股票比例",
            min_value=0,
            max_value=100,
            value=st.session_state.stock_ratio,
            step=10,
            format="%d%%",
            help="調整股票投資比例",
            key="mobile_stock_ratio"
        )
        
        st.session_state.stock_ratio = stock_ratio
        bond_ratio = 100 - stock_ratio
        
        # 顯示配置摘要
        col1, col2 = st.columns(2)
        with col1:
            st.metric("📈 股票", f"{stock_ratio}%")
        with col2:
            st.metric("🏦 債券", f"{bond_ratio}%")
    
    def _render_mobile_advanced_settings(self):
        """渲染移動端進階設定 - 簡化版"""
        # VA目標成長率
        va_growth_rate = st.slider(
            "📈 VA目標成長率",
            min_value=0.0,
            max_value=20.0,
            value=float(st.session_state.va_growth_rate),
            step=1.0,
            format="%.0f%%",
            help="VA策略的目標成長率",
            key="mobile_va_growth_rate"
        )
        
        st.session_state.va_growth_rate = va_growth_rate
    
    def render_complete_parameter_panel(self):
        """
        渲染完整參數面板 - 桌面版
        """
        # 渲染參數設定（已合併基本和進階參數）
        self.render_basic_parameters()
        
        # 渲染計算按鈕（主要觸發點）
        self.render_calculation_button()
        
        # 渲染參數摘要
        self.render_parameter_summary() 