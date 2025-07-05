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

# 3.2.1 基本參數實作 - BASIC_PARAMETERS 字典
BASIC_PARAMETERS = {
    "initial_investment": {
        "component": "slider_with_input",
        "label": "💰 期初投入金額",
        "range": [100000, 10000000],  # 10萬-1000萬
        "default": 100000,
        "step": 50000,
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
    "investment_years": {
        "component": "slider",
        "label": "⏱️ 投資年數",
        "range": [5, 40],
        "default": 10,
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
    "asset_allocation": {
        "component": "dual_slider",
        "label": "📊 股債配置",
        "stock_percentage": {
            "label": "股票比例",
            "range": [0, 100],
            "default": 80,
            "color": "#3b82f6"
        },
        "bond_percentage": {
            "label": "債券比例", 
            "range": [0, 100],
            "default": 20,
            "color": "#f59e0b",
            "auto_calculate": True  # 自動計算為100-股票比例
        },
        "visual": "interactive_pie_chart",
        "help": "投資組合的股票與債券分配比例",
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
        "step": 1.0,
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
            "range": [0, 15],
            "default": 2,
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
        "component": "smart_auto_selection",
        "label": "📊 數據來源",
        "auto_mode": True,  # 預設自動選擇
        "manual_override": {
            "options": [
                {
                    "value": "real_data",
                    "label": "真實市場數據",
                    "description": "Tiingo API + FRED API",
                    "icon": "🌐"
                },
                {
                    "value": "simulation",
                    "label": "模擬數據",
                    "description": "基於歷史統計的模擬",
                    "icon": "🎲"
                }
            ]
        },
        "smart_fallback": True,  # 自動切換失敗的數據源
        # 第1章數據源完整集成
        "chapter1_integration": {
            "api_security_mechanisms": True,
            "fault_tolerance_strategy": True,
            "data_quality_validation": True,
            "simulation_model_specs": "幾何布朗運動 + Vasicek模型"
        }
    }
}

class ParameterManager:
    """參數管理器 - 實作第3章3.2節所有規格"""
    
    def __init__(self):
        self.basic_params = BASIC_PARAMETERS
        self.advanced_settings = ADVANCED_SETTINGS
        self.current_values = {}
        self._initialize_session_state()
    
    def _initialize_session_state(self):
        """初始化Streamlit會話狀態"""
        # 基本參數預設值
        if 'initial_investment' not in st.session_state:
            st.session_state.initial_investment = self.basic_params["initial_investment"]["default"]
        
        if 'investment_years' not in st.session_state:
            st.session_state.investment_years = self.basic_params["investment_years"]["default"]
        
        if 'investment_frequency' not in st.session_state:
            st.session_state.investment_frequency = self.basic_params["investment_frequency"]["default"]
        
        if 'stock_ratio' not in st.session_state:
            st.session_state.stock_ratio = self.basic_params["asset_allocation"]["stock_percentage"]["default"]
        
        # 進階設定預設值
        if 'va_growth_rate' not in st.session_state:
            st.session_state.va_growth_rate = self.advanced_settings["va_growth_rate"]["default"]
        
        if 'inflation_adjustment' not in st.session_state:
            st.session_state.inflation_adjustment = self.advanced_settings["inflation_adjustment"]["enable_toggle"]["default"]
        
        if 'inflation_rate' not in st.session_state:
            st.session_state.inflation_rate = self.advanced_settings["inflation_adjustment"]["inflation_rate"]["default"]
        
        if 'data_source_mode' not in st.session_state:
            st.session_state.data_source_mode = "auto"
    
    def render_basic_parameters(self):
        """渲染基本參數區域 - 永遠可見"""
        st.header("🎯 投資設定")
        
        # 💰 期初投入金額 - slider_with_input
        self._render_initial_investment()
        
        # ⏱️ 投資年數 - slider
        self._render_investment_years()
        
        # 📅 投資頻率 - radio_buttons
        self._render_investment_frequency()
        
        # 📊 股債配置 - dual_slider
        self._render_asset_allocation()
    
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
        with st.expander("🔧 技術整合資訊"):
            st.write(f"**第1章整合**: {param['chapter1_integration']}")
            st.write(f"**第2章整合**: {param['chapter2_integration']}")
    
    def _render_investment_years(self):
        """渲染投資年數參數 - 嚴格按照規格"""
        param = self.basic_params["investment_years"]
        
        years = st.slider(
            param["label"],
            min_value=param["range"][0],
            max_value=param["range"][1],
            value=st.session_state.investment_years,
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
        with st.expander("🔧 技術整合資訊"):
            st.write(f"**第1章整合**: {param['chapter1_integration']}")
            st.write(f"**第2章整合**: {param['chapter2_integration']}")
    
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
        
        # 更新會話狀態
        st.session_state.investment_frequency = option_values[selected_index]
        
        # 顯示頻率說明
        selected_option = options[selected_index]
        st.success(f"✅ 已選擇: {selected_option['icon']} {selected_option['label']}")
        
        # 顯示第1章和第2章整合資訊
        with st.expander("🔧 技術整合資訊"):
            st.write(f"**第1章整合**: {param['chapter1_integration']}")
            st.write(f"**第2章整合**: {param['chapter2_integration']}")
    
    def _render_asset_allocation(self):
        """渲染股債配置參數 - dual_slider with interactive_pie_chart"""
        param = self.basic_params["asset_allocation"]
        
        st.subheader(param["label"])
        
        # 股票比例滑桿
        stock_config = param["stock_percentage"]
        stock_ratio = st.slider(
            f"📈 {stock_config['label']}",
            min_value=stock_config["range"][0],
            max_value=stock_config["range"][1],
            value=st.session_state.stock_ratio,
            step=10,
            format="%d%%",
            help=param["help"],
            key="stock_ratio"
        )
        
        # 自動計算債券比例
        bond_ratio = 100 - stock_ratio
        
        # 顯示債券比例（只讀）
        st.slider(
            f"🏦 債券比例",
            min_value=0,
            max_value=100,
            value=bond_ratio,
            step=10,
            format="%d%%",
            disabled=True,
            help="自動計算 = 100% - 股票比例"
        )
        
        # 顯示配置摘要
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric(
                "📈 股票配置",
                f"{stock_ratio}%",
                delta=f"{stock_ratio - stock_config['default']}%" if stock_ratio != stock_config['default'] else None
            )
        
        with col2:
            st.metric(
                "🏦 債券配置", 
                f"{bond_ratio}%",
                delta=f"{bond_ratio - (100 - stock_config['default'])}%" if bond_ratio != (100 - stock_config['default']) else None
            )
        
        # 視覺化配置圓餅圖
        self._render_allocation_pie_chart(stock_ratio, bond_ratio)
        
        # 顯示第1章和第2章整合資訊
        with st.expander("🔧 技術整合資訊"):
            st.write(f"**第1章整合**: {param['chapter1_integration']}")
            st.write(f"**第2章整合**: {param['chapter2_integration']}")
    
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
            
            st.plotly_chart(fig, use_container_width=True)
            
        except ImportError:
            # 如果沒有plotly，使用簡單的文字顯示
            st.write("📊 投資組合配置:")
            st.write(f"📈 股票: {stock_ratio}%")
            st.write(f"🏦 債券: {bond_ratio}%")
    
    def render_advanced_settings(self):
        """渲染進階設定區域 - 可摺疊"""
        expandable_config = self.advanced_settings["expandable_section"]
        
        with st.expander(expandable_config["title"], expanded=expandable_config["expanded"]):
            st.write(expandable_config["description"])
            
            # 📈 VA策略目標成長率
            self._render_va_growth_rate()
            
            # 通膨調整設定
            self._render_inflation_adjustment()
            
            # 📊 數據來源選擇
            self._render_data_source_selection()
    
    def _render_va_growth_rate(self):
        """渲染VA策略目標成長率參數 - 嚴格按照規格"""
        param = self.advanced_settings["va_growth_rate"]
        
        growth_rate = st.slider(
            param["label"],
            min_value=param["range"][0],
            max_value=param["range"][1],
            value=st.session_state.va_growth_rate,
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
        with st.expander("🔧 VA公式整合"):
            st.write(f"**核心公式**: {param['chapter2_integration']['core_formula']}")
            st.write(f"**參數角色**: {param['chapter2_integration']['parameter_role']}")
            st.write(f"**內部精度**: {param['precision']} 位小數")
            st.write(f"**顯示精度**: {param['display_precision']} 位小數")
    
    def _render_inflation_adjustment(self):
        """渲染通膨調整參數 - 嚴格按照規格"""
        toggle_config = self.advanced_settings["inflation_adjustment"]["enable_toggle"]
        rate_config = self.advanced_settings["inflation_adjustment"]["inflation_rate"]
        
        # 通膨調整開關
        inflation_enabled = st.toggle(
            toggle_config["label"],
            value=st.session_state.inflation_adjustment,
            help=toggle_config["help"],
            key="inflation_adjustment"
        )
        
        # 通膨率設定（條件顯示）
        if inflation_enabled:
            inflation_rate = st.slider(
                rate_config["label"],
                min_value=rate_config["range"][0],
                max_value=rate_config["range"][1],
                value=st.session_state.inflation_rate,
                step=rate_config["step"],
                format="%.1f%%",
                key="inflation_rate"
            )
            
            # 顯示通膨影響說明
            st.info(f"📈 通膨調整: DCA投入金額將每年增加 {inflation_rate}%")
            
            # 顯示第2章整合資訊
            with st.expander("🔧 DCA公式整合"):
                st.write(f"**公式影響**: {rate_config['chapter2_integration']['formula_impact']}")
                st.write(f"**累積計算**: {rate_config['chapter2_integration']['cumulative_calculation']}")
        else:
            st.info("🔒 通膨調整已關閉，DCA投入金額保持固定")
    
    def _render_data_source_selection(self):
        """渲染數據來源選擇 - smart_auto_selection"""
        param = self.advanced_settings["data_source"]
        
        st.subheader(param["label"])
        
        # 自動模式開關
        auto_mode = st.toggle(
            "🤖 自動選擇數據源",
            value=param["auto_mode"],
            help="系統自動選擇最佳可用數據源",
            key="data_source_auto_mode"
        )
        
        if auto_mode:
            # 自動模式 - 顯示當前狀態
            current_source = self._detect_current_data_source()
            
            if current_source == "real_data":
                st.success("🌐 正在使用真實市場數據 (Tiingo API + FRED API)")
            elif current_source == "simulation":
                st.warning("🎲 正在使用模擬數據 (API暫時不可用)")
            else:
                st.error("🔴 數據源不可用，請檢查網路連接")
            
            st.session_state.data_source_mode = "auto"
            
        else:
            # 手動模式 - 讓用戶選擇
            options = param["manual_override"]["options"]
            
            option_labels = [f"{opt['icon']} {opt['label']}" for opt in options]
            option_values = [opt['value'] for opt in options]
            
            selected_index = st.radio(
                "選擇數據源",
                range(len(options)),
                format_func=lambda x: option_labels[x],
                key="data_source_manual_selection"
            )
            
            selected_option = options[selected_index]
            st.session_state.data_source_mode = selected_option['value']
            
            # 顯示選擇的數據源資訊
            st.info(f"📊 已選擇: {selected_option['description']}")
        
        # 顯示第1章整合資訊
        with st.expander("🔧 第1章API整合"):
            integration = param["chapter1_integration"]
            st.write(f"**API安全機制**: {integration['api_security_mechanisms']}")
            st.write(f"**容錯策略**: {integration['fault_tolerance_strategy']}")
            st.write(f"**數據品質驗證**: {integration['data_quality_validation']}")
            st.write(f"**模擬模型**: {integration['simulation_model_specs']}")
    
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
            "investment_years": st.session_state.investment_years,
            "investment_frequency": st.session_state.investment_frequency,
            "stock_ratio": st.session_state.stock_ratio,
            "bond_ratio": 100 - st.session_state.stock_ratio,
            
            # 進階設定
            "va_growth_rate": st.session_state.va_growth_rate,
            "inflation_adjustment": st.session_state.inflation_adjustment,
            "inflation_rate": st.session_state.inflation_rate if st.session_state.inflation_adjustment else 0,
            "data_source_mode": st.session_state.get("data_source_mode", "auto"),
            
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
    
    def render_parameter_summary(self):
        """渲染參數摘要卡片"""
        st.subheader("📋 參數摘要")
        
        params = self.get_all_parameters()
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("💰 投資金額", f"${params['initial_investment']:,}")
            st.metric("⏱️ 投資期間", f"{params['investment_years']} 年")
            st.metric("📊 股票比例", f"{params['stock_ratio']}%")
        
        with col2:
            st.metric("📅 投資頻率", params['investment_frequency'])
            st.metric("📈 VA目標成長率", f"{params['va_growth_rate']}%")
            st.metric("🔢 總期數", f"{params['total_periods']} 期")
    
    def validate_parameters(self) -> Dict[str, Any]:
        """驗證參數有效性"""
        params = self.get_all_parameters()
        validation_result = {
            "valid": True,
            "errors": [],
            "warnings": []
        }
        
        # 基本參數驗證
        if params["initial_investment"] < 100000:
            validation_result["errors"].append("期初投入金額不能少於10萬")
            validation_result["valid"] = False
        
        if params["investment_years"] < 5:
            validation_result["errors"].append("投資年數不能少於5年")
            validation_result["valid"] = False
        
        # 進階參數驗證
        if params["va_growth_rate"] < -20 or params["va_growth_rate"] > 50:
            validation_result["errors"].append("VA成長率超出合理範圍(-20%到50%)")
            validation_result["valid"] = False
        
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
            min_value=10000,
            max_value=1000000,
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
        # 渲染基本參數
        self.render_basic_parameters()
        
        # 渲染進階設定
        self.render_advanced_settings()
        
        # 渲染參數摘要
        self.render_parameter_summary() 