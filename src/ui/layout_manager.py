"""
布局管理器 - 實作第3章3.1節設計原則與布局架構
嚴格按照需求文件規格，不得修改任何定義和規格
"""

import streamlit as st
from typing import Dict, Any, Optional
import os
from datetime import datetime

# 3.1.1 核心設計原則實作 - APP_HEADER_SPECS 字典
APP_HEADER_SPECS = {
    "main_title": {
        "text": "投資策略績效比較分析系統",
        "font_size": "2.5rem",
        "font_weight": "bold",
        "color": "#1f2937",
        "text_align": "center",
        "margin_bottom": "0.5rem"
    },
    "subtitle": {
        "text": "VA(定期定值) vs DCA(定期定額) 策略比較",
        "font_size": "1.2rem", 
        "color": "#6b7280",
        "text_align": "center",
        "margin_bottom": "1rem"
    },
    "visual_simplicity": {
        "clean_interface": "移除非必要視覺元素",
        "intuitive_navigation": "符合用戶心理模型的操作流程",
        "friendly_guidance": "使用emoji和簡潔文案提升親和力"
    }
}

# 3.1.2 三欄式響應式布局實作 - RESPONSIVE_LAYOUT_CONFIG
RESPONSIVE_LAYOUT_CONFIG = {
    "desktop_layout": {
        "structure": """
        ┌─────────────────────────────────────────────────┐
        │ 🏠 投資策略比較分析 - 輕鬆比較兩種投資方法 │
        └─────────────────────────────────────────────────┘
        ┌──────────┬─────────────────┬─────────────────┐
        │ 🎯 投資設定│ 📊 即時結果預覽 │ 💡 智能建議 │
        │ (350px) │ (主要區域) │ (300px) │
        └──────────┴─────────────────┴─────────────────┘
        """,
        "implementation": {
            "left_panel": {
                "width": 350,
                "content": "simplified_parameter_inputs",
                "collapsible": False
            },
            "center_panel": {
                "width": "auto",
                "content": "results_visualization",
                "responsive": True
            },
            "right_panel": {
                "width": 300,
                "content": "smart_recommendations",
                "hide_on_tablet": True
            }
        },
        "breakpoint": ">=1024px"
    },
    "mobile_layout": {
        "structure": "tab_navigation",
        "tabs": [
            {
                "name": "🎯 設定",
                "icon": "⚙️",
                "content": "parameter_inputs",
                "priority": 1
            },
            {
                "name": "📊 結果", 
                "icon": "📈",
                "content": "results_display",
                "priority": 2
            },
            {
                "name": "💡 建議",
                "icon": "🎯", 
                "content": "recommendations",
                "priority": 3
            }
        ],
        "navigation_position": "bottom",
        "breakpoint": "<1024px"
    }
}

# 3.1.3 簡潔標題設計實作 - MODERN_HEADER_SPECS
MODERN_HEADER_SPECS = {
    "main_header": {
        "title": "🏠 投資策略比較分析",
        "subtitle": "輕鬆比較兩種投資方法",
        "style": "minimal_centered",
        "mobile_optimized": True
    },
    "smart_status_indicator": {
        # 第1章API狀態整合（背景化、非干擾）
        "data_source_status": {
            "display_mode": "icon_with_tooltip",
            "states": {
                "real_data": {"icon": "🟢", "tooltip": "使用真實市場數據"},
                "simulation": {"icon": "🟡", "tooltip": "使用模擬數據"},
                "offline": {"icon": "🔴", "tooltip": "離線模式"}
            },
            "auto_fallback": True,  # 自動切換數據源
            "user_notification": "minimal"  # 僅必要時提醒
        },
        "chapter1_integration": {
            "multilevel_api_security": "background_processing",
            "fault_tolerance": "automatic",
            "data_quality_monitoring": "silent",
            "backup_strategy": "seamless_switching"
        }
    }
}

class LayoutManager:
    """布局管理器 - 實作第3章3.1節所有規格"""
    
    def __init__(self):
        self.device_type = self._detect_device_type()
        self.layout_config = RESPONSIVE_LAYOUT_CONFIG
        self.header_specs = APP_HEADER_SPECS
        self.modern_header_specs = MODERN_HEADER_SPECS
    
    def _detect_device_type(self) -> str:
        """檢測設備類型"""
        # 使用Streamlit的會話狀態來模擬設備檢測
        # 實際部署時可以通過JavaScript獲取螢幕寬度
        if 'screen_width' not in st.session_state:
            st.session_state.screen_width = 1024  # 預設為桌面
        
        if st.session_state.screen_width >= 1024:
            return "desktop"
        elif st.session_state.screen_width >= 768:
            return "tablet"
        else:
            return "mobile"
    
    def apply_modern_styling(self):
        """應用現代化CSS樣式 - 嚴格按照規格"""
        st.markdown("""
        <style>
        /* 隱藏Streamlit預設元素 */
        .stAppDeployButton {display: none;}
        .stDecoration {display: none;}
        #MainMenu {visibility: hidden;}
        
        /* 主標題樣式 - 嚴格按照APP_HEADER_SPECS */
        .main-title {
            font-size: 2.5rem;
            font-weight: bold;
            color: #1f2937;
            text-align: center;
            margin-bottom: 0.5rem;
        }
        
        /* 副標題樣式 - 嚴格按照APP_HEADER_SPECS */
        .subtitle {
            font-size: 1.2rem;
            color: #6b7280;
            text-align: center;
            margin-bottom: 1rem;
        }
        
        /* 現代化卡片樣式 */
        .metric-card {
            background: white;
            padding: 1.5rem;
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            border: 1px solid #e5e7eb;
            margin-bottom: 1rem;
        }
        
        /* 響應式字體大小 - 斷點<1024px */
        @media (max-width: 1024px) {
            .stMarkdown h1 { font-size: 1.75rem !important; }
            .stMarkdown h2 { font-size: 1.5rem !important; }
            .stMarkdown h3 { font-size: 1.25rem !important; }
            .stSlider > div > div > div { min-height: 48px; }
            .stButton > button { min-height: 48px; font-size: 16px; }
        }
        
        /* 改進的互動元件 */
        .stSlider > div > div > div > div {
            background: #3b82f6;
        }
        
        .stButton > button {
            border-radius: 8px;
            font-weight: 500;
            transition: all 0.2s ease;
        }
        
        .stButton > button:hover {
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        }
        
        /* 智能狀態指示器 */
        .status-indicator {
            display: inline-block;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-right: 8px;
        }
        
        .status-healthy { background: #10b981; }
        .status-warning { background: #f59e0b; }
        .status-error { background: #ef4444; }
        
        /* 三欄布局樣式 - 桌面版 >=1024px */
        @media (min-width: 1024px) {
            .desktop-left-panel {
                width: 350px;
                min-width: 350px;
                max-width: 350px;
            }
            
            .desktop-right-panel {
                width: 300px;
                min-width: 300px;
                max-width: 300px;
            }
            
            .desktop-center-panel {
                flex: 1;
                min-width: 0;
            }
        }
        
        /* 平板隱藏右側面板 */
        @media (max-width: 1023px) and (min-width: 768px) {
            .desktop-right-panel {
                display: none;
            }
        }
        
        /* 移動版標籤導航 - <1024px */
        @media (max-width: 1024px) {
            .mobile-tab-navigation {
                position: fixed;
                bottom: 0;
                left: 0;
                right: 0;
                background: white;
                border-top: 1px solid #e5e7eb;
                z-index: 1000;
            }
        }
        </style>
        """, unsafe_allow_html=True)
    
    def render_modern_header(self):
        """渲染簡潔的現代化標題 - 嚴格按照MODERN_HEADER_SPECS"""
        # 主標題 - 使用APP_HEADER_SPECS的規格
        st.markdown(f"""
        <div class="main-title">{self.header_specs['main_title']['text']}</div>
        """, unsafe_allow_html=True)
        
        # 副標題 - 使用APP_HEADER_SPECS的規格
        st.markdown(f"""
        <div class="subtitle">{self.header_specs['subtitle']['text']}</div>
        """, unsafe_allow_html=True)
        
        # 智能狀態指示器 - 按照MODERN_HEADER_SPECS
        self._render_smart_status_indicator()
        
        st.markdown("---")
    
    def _render_smart_status_indicator(self):
        """渲染智能狀態指示器"""
        status_col1, status_col2, status_col3 = st.columns([1, 1, 8])
        
        # 獲取數據源狀態
        data_status = self._get_data_source_status()
        
        with status_col1:
            status_config = self.modern_header_specs["smart_status_indicator"]["data_source_status"]["states"]
            
            if data_status == "real_data":
                st.markdown(f"{status_config['real_data']['icon']} 真實數據")
            elif data_status == "simulation":
                st.markdown(f"{status_config['simulation']['icon']} 模擬數據")
            else:
                st.markdown(f"{status_config['offline']['icon']} 離線模式")
    
    def _get_data_source_status(self) -> str:
        """獲取數據源狀態 - 整合第1章API狀態"""
        # 檢查API金鑰是否存在
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
    
    def render_layout(self):
        """渲染主布局 - 根據設備類型選擇布局"""
        if self.device_type == "desktop":
            return self.render_desktop_layout()
        else:
            return self.render_mobile_layout()
    
    def render_desktop_layout(self):
        """渲染桌面版三欄布局 - 嚴格按照desktop_layout規格"""
        desktop_config = self.layout_config["desktop_layout"]["implementation"]
        
        # 創建三欄布局 - 嚴格按照width規格
        left_col, center_col, right_col = st.columns([
            desktop_config["left_panel"]["width"],  # 350px
            1000,  # center_panel auto width (用大數值模擬)
            desktop_config["right_panel"]["width"]   # 300px
        ])
        
        # 左側面板 - simplified_parameter_inputs
        with left_col:
            st.markdown('<div class="desktop-left-panel">', unsafe_allow_html=True)
            self._render_simplified_parameter_inputs()
            st.markdown('</div>', unsafe_allow_html=True)
        
        # 中央面板 - results_visualization
        with center_col:
            st.markdown('<div class="desktop-center-panel">', unsafe_allow_html=True)
            self._render_results_visualization()
            st.markdown('</div>', unsafe_allow_html=True)
        
        # 右側面板 - smart_recommendations
        with right_col:
            st.markdown('<div class="desktop-right-panel">', unsafe_allow_html=True)
            self._render_smart_recommendations()
            st.markdown('</div>', unsafe_allow_html=True)
    
    def render_mobile_layout(self):
        """渲染移動版標籤布局 - 嚴格按照mobile_layout規格"""
        mobile_config = self.layout_config["mobile_layout"]
        
        # 創建標籤導航 - 按照priority順序
        tabs = mobile_config["tabs"]
        sorted_tabs = sorted(tabs, key=lambda x: x["priority"])
        
        # 創建標籤
        tab_names = [tab["name"] for tab in sorted_tabs]
        tab_objects = st.tabs(tab_names)
        
        # 渲染各標籤內容
        for i, (tab_obj, tab_config) in enumerate(zip(tab_objects, sorted_tabs)):
            with tab_obj:
                if tab_config["content"] == "parameter_inputs":
                    self._render_parameter_inputs()
                elif tab_config["content"] == "results_display":
                    self._render_results_display()
                elif tab_config["content"] == "recommendations":
                    self._render_recommendations()
    
    def _render_simplified_parameter_inputs(self):
        """渲染簡化參數輸入區域 - 整合第3章3.2節參數管理器"""
        from .parameter_manager import ParameterManager
        
        # 創建參數管理器實例
        if not hasattr(self, '_parameter_manager'):
            self._parameter_manager = ParameterManager()
        
        # 渲染參數設定（已合併基本和進階參數）
        self._parameter_manager.render_basic_parameters()
        
        # 渲染參數摘要
        self._parameter_manager.render_parameter_summary()
    
    def _render_results_visualization(self):
        """渲染結果視覺化區域 - 整合第3章3.3節中央結果展示區域"""
        from .results_display import ResultsDisplayManager
        
        # 創建結果展示管理器
        if not hasattr(self, '_results_display_manager'):
            self._results_display_manager = ResultsDisplayManager()
        
        # 獲取參數管理器的參數
        if hasattr(self, '_parameter_manager'):
            parameters = self._parameter_manager.get_all_parameters()
            
            # 渲染完整的中央結果展示區域
            self._results_display_manager.render_complete_results_display(parameters)
        else:
            st.info("請先設定投資參數")
    
    def _render_smart_recommendations(self):
        """渲染智能建議區域 - 整合第3章3.4節智能建議系統"""
        from .smart_recommendations import SmartRecommendationsManager
        
        # 創建智能建議管理器
        if not hasattr(self, '_smart_recommendations_manager'):
            self._smart_recommendations_manager = SmartRecommendationsManager()
        
        # 獲取參數和計算結果
        parameters = {}
        calculation_results = {}
        
        if hasattr(self, '_parameter_manager'):
            parameters = self._parameter_manager.get_all_parameters()
        
        if hasattr(self, '_results_display_manager') and hasattr(self._results_display_manager, 'calculation_results'):
            calculation_results = self._results_display_manager.calculation_results
        
        # 渲染完整智能建議區域
        self._smart_recommendations_manager.render_complete_smart_recommendations(
            parameters, calculation_results
        )
    
    def _render_parameter_inputs(self):
        """渲染參數輸入區域（移動版）"""
        self._render_simplified_parameter_inputs()
    
    def _render_results_display(self):
        """渲染結果顯示區域（移動版）"""
        self._render_results_visualization()
    
    def _render_recommendations(self):
        """渲染建議區域（移動版）"""
        self._render_smart_recommendations()
    
    def initialize_layout(self):
        """初始化完整布局 - 整合響應式設計"""
        # 導入響應式設計管理器
        from .responsive_design import ResponsiveDesignManager
        
        # 創建響應式設計管理器
        if not hasattr(self, '_responsive_manager'):
            self._responsive_manager = ResponsiveDesignManager()
        
        # 初始化響應式設計
        device_info = self._responsive_manager.initialize_responsive_design()
        
        # 渲染現代化標題
        self.render_modern_header()
        
        # 顯示設備資訊（可選）
        if st.session_state.get('show_device_info', False):
            st.info(f"設備類型: {device_info['device']} | 螢幕寬度: {device_info['screen_width']}px | 布局模式: {device_info['layout_mode']}")
        
        # 注意：不需要再調用 render_layout()，因為響應式管理器已經處理了布局 