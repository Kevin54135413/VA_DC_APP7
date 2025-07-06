"""
響應式設計管理器 - 實作第3章第3.5節響應式設計
嚴格按照需求文件規格，不得修改任何斷點數值和設備適配邏輯
"""

import streamlit as st
from typing import Dict, Any, Optional, Tuple
import json

# 3.5.1 設備檢測與適配實作
DEVICE_BREAKPOINTS = {
    "desktop": 1024,  # screen_width >= 1024px
    "tablet": 768,    # screen_width >= 768px
    "mobile": 0       # screen_width < 768px
}

# 3.5.2 移動端優化實作
MOBILE_OPTIMIZED_COMPONENTS = {
    "touch_friendly_controls": {
        "min_touch_target": "44px",
        "slider_thumb_size": "24px",
        "button_min_height": "48px",
        "tap_feedback": True
    },
    "readable_typography": {
        "min_font_size": "16px",
        "line_height": "1.6",
        "contrast_ratio": "4.5:1",
        "readable_color_scheme": True
    },
    "simplified_interactions": {
        "reduce_decimal_precision": True,
        "larger_step_sizes": True,
        "preset_value_shortcuts": True,
        "swipe_gestures": True
    },
    "performance_optimization": {
        "lazy_loading": True,
        "image_compression": True,
        "minimal_animations": True,
        "efficient_rendering": True
    }
}

# 響應式CSS實作
RESPONSIVE_CSS = """
<style>
/* 基礎響應式樣式 */
.responsive-container {
    width: 100%;
    max-width: 1200px;
    margin: 0 auto;
    padding: 0 1rem;
}

/* 桌面版布局 - screen_width >= 1024px */
@media (min-width: 1024px) {
    .desktop-layout {
        display: grid;
        grid-template-columns: 350px 1fr 300px;
        gap: 1.5rem;
        min-height: 100vh;
    }
    
    .desktop-left-panel {
        background: #f8fafc;
        padding: 1.5rem;
        border-radius: 12px;
        border: 1px solid #e2e8f0;
        height: fit-content;
        position: sticky;
        top: 1rem;
    }
    
    .desktop-center-panel {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        border: 1px solid #e2e8f0;
        min-height: 600px;
    }
    
    .desktop-right-panel {
        background: #f8fafc;
        padding: 1.5rem;
        border-radius: 12px;
        border: 1px solid #e2e8f0;
        height: fit-content;
        position: sticky;
        top: 1rem;
    }
}

/* 平板版布局 - screen_width >= 768px and < 1024px */
@media (min-width: 768px) and (max-width: 1023px) {
    .tablet-layout {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 1rem;
    }
    
    .tablet-left-panel {
        background: #f8fafc;
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid #e2e8f0;
    }
    
    .tablet-main-panel {
        background: white;
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid #e2e8f0;
    }
    
    /* 隱藏右側建議面板 */
    .desktop-right-panel {
        display: none;
    }
}

/* 移動版布局 - screen_width < 768px */
@media (max-width: 767px) {
    .mobile-layout {
        padding: 0.5rem;
    }
    
    .mobile-tab-container {
        background: white;
        border-radius: 8px;
        border: 1px solid #e2e8f0;
        overflow: hidden;
    }
    
    .mobile-tab-content {
        padding: 1rem;
        min-height: 400px;
    }
    
    /* 移動端字體大小調整 */
    .stMarkdown h1 { 
        font-size: 1.75rem !important; 
        line-height: 1.3 !important;
    }
    
    .stMarkdown h2 { 
        font-size: 1.5rem !important; 
        line-height: 1.4 !important;
    }
    
    .stMarkdown h3 { 
        font-size: 1.25rem !important; 
        line-height: 1.5 !important;
    }
    
    /* 觸控友善控件 */
    .stSlider > div > div > div { 
        min-height: 48px !important; 
    }
    
    .stSlider > div > div > div > div > div {
        height: 24px !important;
        width: 24px !important;
    }
    
    .stButton > button { 
        min-height: 48px !important; 
        font-size: 16px !important;
        padding: 0.75rem 1.5rem !important;
        border-radius: 8px !important;
        font-weight: 500 !important;
    }
    
    .stSelectbox > div > div > div {
        min-height: 48px !important;
        font-size: 16px !important;
    }
    
    .stNumberInput > div > div > input {
        min-height: 48px !important;
        font-size: 16px !important;
    }
    
    /* 可讀性優化 */
    .stMarkdown p {
        font-size: 16px !important;
        line-height: 1.6 !important;
    }
    
    .stMarkdown li {
        font-size: 16px !important;
        line-height: 1.6 !important;
    }
    
    /* 對比度優化 */
    .stMarkdown {
        color: #1a202c !important;
    }
    
    /* 簡化交互 */
    .mobile-preset-buttons {
        display: flex;
        flex-wrap: wrap;
        gap: 0.5rem;
        margin-bottom: 1rem;
    }
    
    .mobile-preset-button {
        background: #e2e8f0;
        border: 1px solid #cbd5e0;
        border-radius: 6px;
        padding: 0.5rem 1rem;
        font-size: 14px;
        cursor: pointer;
        transition: all 0.2s ease;
    }
    
    .mobile-preset-button:hover {
        background: #cbd5e0;
        border-color: #a0aec0;
    }
    
    .mobile-preset-button.active {
        background: #3182ce;
        border-color: #3182ce;
        color: white;
    }
}

/* 通用響應式元件 */
.responsive-metric-card {
    background: white;
    padding: 1.5rem;
    border-radius: 8px;
    border: 1px solid #e2e8f0;
    margin-bottom: 1rem;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

@media (max-width: 767px) {
    .responsive-metric-card {
        padding: 1rem;
        margin-bottom: 0.75rem;
    }
}

/* 效能優化 */
.lazy-load-container {
    min-height: 200px;
    display: flex;
    align-items: center;
    justify-content: center;
}

.minimal-animation {
    transition: opacity 0.2s ease;
}

/* 觸控反饋 */
.touch-feedback:active {
    transform: scale(0.98);
    opacity: 0.8;
}

/* 滑動手勢支援 */
.swipe-container {
    touch-action: pan-x;
    overflow-x: auto;
    -webkit-overflow-scrolling: touch;
}

/* 無障礙優化 */
.sr-only {
    position: absolute;
    width: 1px;
    height: 1px;
    padding: 0;
    margin: -1px;
    overflow: hidden;
    clip: rect(0, 0, 0, 0);
    white-space: nowrap;
    border: 0;
}

/* 焦點樣式 */
.stButton > button:focus,
.stSelectbox > div > div:focus,
.stNumberInput > div > div > input:focus,
.stSlider > div > div > div:focus {
    outline: 2px solid #3182ce !important;
    outline-offset: 2px !important;
}
</style>
"""

class ResponsiveDesignManager:
    """響應式設計管理器 - 實作第3章3.5節所有規格"""
    
    def __init__(self):
        self.device_breakpoints = DEVICE_BREAKPOINTS
        self.mobile_components = MOBILE_OPTIMIZED_COMPONENTS
        self.current_device = self._detect_device_type()
        self.screen_width = self._get_screen_width()
        
    def _get_screen_width(self) -> int:
        """獲取螢幕寬度"""
        # 使用JavaScript檢測螢幕寬度
        screen_width_js = """
        <script>
        function getScreenWidth() {
            return window.innerWidth;
        }
        
        // 將螢幕寬度存儲到sessionStorage
        sessionStorage.setItem('screen_width', window.innerWidth);
        
        // 監聽窗口大小變化
        window.addEventListener('resize', function() {
            sessionStorage.setItem('screen_width', window.innerWidth);
        });
        </script>
        """
        
        # 注入JavaScript
        st.components.v1.html(screen_width_js, height=0)
        
        # 從session_state獲取螢幕寬度，預設為1024（桌面）
        return st.session_state.get("screen_width", 1024)
    
    def _detect_device_type(self) -> str:
        """檢測設備類型 - 嚴格按照斷點規格"""
        # 使用當前螢幕寬度（可能已被測試設置）
        screen_width = getattr(self, 'screen_width', self._get_screen_width())
        
        if screen_width >= self.device_breakpoints["desktop"]:  # >= 1024px
            return "desktop"
        elif screen_width >= self.device_breakpoints["tablet"]:  # >= 768px
            return "tablet"
        else:  # < 768px
            return "mobile"
    
    def detect_device_and_layout(self):
        """
        檢測設備類型並調整布局 - 嚴格按照3.5.1節規格
        """
        screen_width = self._get_screen_width()
        
        # 更新session_state
        st.session_state.screen_width = screen_width
        
        # 根據螢幕寬度選擇布局模式
        if screen_width >= 1024:
            st.session_state.layout_mode = "desktop"
            return self.render_desktop_layout()
        elif screen_width >= 768:
            st.session_state.layout_mode = "tablet"
            return self.render_tablet_layout()
        else:
            st.session_state.layout_mode = "mobile"
            return self.render_mobile_layout()
    
    def render_mobile_layout(self):
        """
        手機版標籤式導航布局 - 嚴格按照3.5.1節規格
        """
        # 必須使用st.tabs()創建標籤導航
        tab1, tab2, tab3 = st.tabs(["🎯 設定", "📊 結果", "💡 建議"])
        
        with tab1:
            # 調用render_simplified_parameters()
            self.render_simplified_parameters()
        
        with tab2:
            # 調用render_mobile_optimized_results()
            self.render_mobile_optimized_results()
            
        with tab3:
            # 調用render_compact_recommendations()
            self.render_compact_recommendations()
    
    def render_desktop_layout(self):
        """
        桌面版三欄布局 - 嚴格按照3.5.1節規格
        """
        # 使用比例分配創建三欄布局：左欄固定350px等效，中欄自適應，右欄固定300px等效
        left_col, center_col, right_col = st.columns([2, 3, 2])
        
        with left_col:
            # 調用render_full_parameter_panel()
            self.render_full_parameter_panel()
        
        with center_col:
            # 調用render_main_results_area()
            self.render_main_results_area()
            
        with right_col:
            # 調用render_smart_suggestions_panel()
            self.render_smart_suggestions_panel()
    
    def render_tablet_layout(self):
        """
        平板版兩欄布局
        """
        left_col, right_col = st.columns([1, 1])
        
        with left_col:
            self.render_simplified_parameters()
        
        with right_col:
            self.render_mobile_optimized_results()
    
    def render_simplified_parameters(self):
        """
        渲染簡化參數設定 - 移動端優化
        """
        from .parameter_manager import ParameterManager
        
        st.markdown("### 🎯 投資參數設定")
        
        # 創建參數管理器
        if not hasattr(self, '_parameter_manager'):
            self._parameter_manager = ParameterManager()
        
        # 移動端優化：使用預設值快捷按鈕
        self._render_mobile_preset_buttons()
        
        # 渲染簡化的參數輸入
        self._parameter_manager.render_mobile_optimized_parameters()
    
    def render_mobile_optimized_results(self):
        """
        渲染移動端優化結果 - 3.5.1節規格
        """
        from .results_display import ResultsDisplayManager
        
        st.markdown("### 📊 策略比較結果")
        
        # 創建結果展示管理器
        if not hasattr(self, '_results_display_manager'):
            self._results_display_manager = ResultsDisplayManager()
        
        # 獲取參數
        if hasattr(self, '_parameter_manager'):
            parameters = self._parameter_manager.get_all_parameters()
            
            # 渲染移動端優化的結果
            self._results_display_manager.render_mobile_optimized_results(parameters)
        else:
            st.info("請先在「🎯 設定」標籤中設定投資參數")
    
    def render_compact_recommendations(self):
        """
        渲染緊湊建議 - 3.5.1節規格
        """
        from .smart_recommendations import SmartRecommendationsManager
        
        st.markdown("### 💡 智能投資建議")
        
        # 創建智能建議管理器
        if not hasattr(self, '_smart_recommendations_manager'):
            self._smart_recommendations_manager = SmartRecommendationsManager()
        
        # 獲取參數和結果
        parameters = {}
        calculation_results = {}
        
        if hasattr(self, '_parameter_manager'):
            parameters = self._parameter_manager.get_all_parameters()
        
        if hasattr(self, '_results_display_manager') and hasattr(self._results_display_manager, 'calculation_results'):
            calculation_results = self._results_display_manager.calculation_results
        
        # 渲染緊湊版建議
        self._smart_recommendations_manager.render_compact_recommendations(
            parameters, calculation_results
        )
    
    def render_full_parameter_panel(self):
        """
        渲染完整參數面板 - 桌面版
        """
        from .parameter_manager import ParameterManager
        
        # 創建參數管理器
        if not hasattr(self, '_parameter_manager'):
            self._parameter_manager = ParameterManager()
        
        # 渲染完整參數面板
        self._parameter_manager.render_complete_parameter_panel()
    
    def render_main_results_area(self):
        """
        渲染主結果區域 - 桌面版
        """
        from .results_display import ResultsDisplayManager
        
        # 創建結果展示管理器
        if not hasattr(self, '_results_display_manager'):
            self._results_display_manager = ResultsDisplayManager()
        
        # 獲取參數
        if hasattr(self, '_parameter_manager'):
            parameters = self._parameter_manager.get_all_parameters()
            
            # 檢查是否有計算觸發
            if st.session_state.get('trigger_calculation', False):
                # 確保結果顯示管理器知道計算觸發
                st.session_state.trigger_calculation = True
            
            # 渲染完整結果區域
            self._results_display_manager.render_complete_results_display(parameters)
        else:
            st.info("請先設定投資參數")
    
    def render_smart_suggestions_panel(self):
        """
        渲染智能建議面板 - 桌面版
        """
        from .smart_recommendations import SmartRecommendationsManager
        
        # 創建智能建議管理器
        if not hasattr(self, '_smart_recommendations_manager'):
            self._smart_recommendations_manager = SmartRecommendationsManager()
        
        # 獲取參數和結果
        parameters = {}
        calculation_results = {}
        
        if hasattr(self, '_parameter_manager'):
            parameters = self._parameter_manager.get_all_parameters()
        
        if hasattr(self, '_results_display_manager') and hasattr(self._results_display_manager, 'calculation_results'):
            calculation_results = self._results_display_manager.calculation_results
        
        # 渲染完整智能建議
        self._smart_recommendations_manager.render_complete_smart_recommendations(
            parameters, calculation_results
        )
    
    def _render_mobile_preset_buttons(self):
        """
        渲染移動端預設值快捷按鈕 - 簡化交互
        """
        st.markdown("#### 快速設定")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🎯 保守型", key="preset_conservative", use_container_width=True):
                self._apply_preset("conservative")
        
        with col2:
            if st.button("⚖️ 平衡型", key="preset_balanced", use_container_width=True):
                self._apply_preset("balanced")
        
        with col3:
            if st.button("🚀 積極型", key="preset_aggressive", use_container_width=True):
                self._apply_preset("aggressive")
    
    def _apply_preset(self, preset_type: str):
        """
        應用預設參數 - 大步長、減少小數精度
        """
        presets = {
            "conservative": {
                "initial_investment": 10000,
                "investment_frequency": "quarterly",
                "investment_periods": 20,
                "monthly_investment": 1000
            },
            "balanced": {
                "initial_investment": 50000,
                "investment_frequency": "monthly",
                "investment_periods": 60,
                "monthly_investment": 3000
            },
            "aggressive": {
                "initial_investment": 10000,
                "investment_frequency": "monthly",
                "investment_periods": 120,
                "monthly_investment": 5000
            }
        }
        
        if preset_type in presets:
            for key, value in presets[preset_type].items():
                st.session_state[key] = value
    
    def apply_responsive_styling(self):
        """
        應用響應式CSS樣式 - 完整實作3.5.2節規格
        """
        # 注入響應式CSS
        st.markdown(RESPONSIVE_CSS, unsafe_allow_html=True)
        
        # 根據設備類型應用特定樣式
        if self.current_device == "mobile":
            self._apply_mobile_optimizations()
        elif self.current_device == "tablet":
            self._apply_tablet_optimizations()
        else:
            self._apply_desktop_optimizations()
    
    def _apply_mobile_optimizations(self):
        """
        應用移動端優化 - 嚴格按照MOBILE_OPTIMIZED_COMPONENTS規格
        """
        mobile_css = """
        <style>
        /* 觸控友善控件 - touch_friendly_controls */
        .stButton > button {
            min-height: 48px !important;
            padding: 12px 24px !important;
            font-size: 16px !important;
            border-radius: 8px !important;
            font-weight: 500 !important;
            transition: all 0.2s ease !important;
        }
        
        .stButton > button:active {
            transform: scale(0.98) !important;
            opacity: 0.8 !important;
        }
        
        .stSlider > div > div > div {
            min-height: 48px !important;
        }
        
        .stSlider > div > div > div > div > div {
            height: 24px !important;
            width: 24px !important;
        }
        
        /* 可讀性排版 - readable_typography */
        .stMarkdown p,
        .stMarkdown li,
        .stMarkdown span {
            font-size: 16px !important;
            line-height: 1.6 !important;
            color: #1a202c !important;
        }
        
        .stMarkdown h1 {
            font-size: 1.75rem !important;
            line-height: 1.3 !important;
            color: #1a202c !important;
        }
        
        .stMarkdown h2 {
            font-size: 1.5rem !important;
            line-height: 1.4 !important;
            color: #1a202c !important;
        }
        
        .stMarkdown h3 {
            font-size: 1.25rem !important;
            line-height: 1.5 !important;
            color: #1a202c !important;
        }
        
        /* 簡化交互 - simplified_interactions */
        .stNumberInput > div > div > input {
            font-size: 16px !important;
            padding: 12px !important;
            border-radius: 6px !important;
        }
        
        .stSelectbox > div > div > div {
            font-size: 16px !important;
            padding: 12px !important;
        }
        
        /* 效能優化 - performance_optimization */
        .stPlotlyChart {
            opacity: 0;
            animation: fadeIn 0.3s ease-in-out forwards;
        }
        
        @keyframes fadeIn {
            to { opacity: 1; }
        }
        
        /* 最小動畫 */
        * {
            animation-duration: 0.2s !important;
            transition-duration: 0.2s !important;
        }
        </style>
        """
        
        st.markdown(mobile_css, unsafe_allow_html=True)
    
    def _apply_tablet_optimizations(self):
        """
        應用平板端優化
        """
        tablet_css = """
        <style>
        .stButton > button {
            min-height: 44px !important;
            font-size: 15px !important;
        }
        
        .stMarkdown h1 {
            font-size: 2rem !important;
        }
        
        .stMarkdown h2 {
            font-size: 1.75rem !important;
        }
        
        .stMarkdown h3 {
            font-size: 1.5rem !important;
        }
        </style>
        """
        
        st.markdown(tablet_css, unsafe_allow_html=True)
    
    def _apply_desktop_optimizations(self):
        """
        應用桌面端優化
        """
        desktop_css = """
        <style>
        .stButton > button {
            transition: all 0.2s ease !important;
        }
        
        .stButton > button:hover {
            transform: translateY(-1px) !important;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15) !important;
        }
        
        .desktop-layout {
            display: grid;
            grid-template-columns: 350px 1fr 300px;
            gap: 1.5rem;
        }
        </style>
        """
        
        st.markdown(desktop_css, unsafe_allow_html=True)
    
    def get_current_device(self) -> str:
        """獲取當前設備類型"""
        return self.current_device
    
    def get_screen_width(self) -> int:
        """獲取當前螢幕寬度"""
        return self.screen_width
    
    def is_mobile(self) -> bool:
        """判斷是否為移動設備"""
        return self.current_device == "mobile"
    
    def is_tablet(self) -> bool:
        """判斷是否為平板設備"""
        return self.current_device == "tablet"
    
    def is_desktop(self) -> bool:
        """判斷是否為桌面設備"""
        return self.current_device == "desktop"
    
    def get_optimized_parameters(self) -> Dict[str, Any]:
        """
        獲取設備優化的參數配置
        """
        if self.is_mobile():
            return {
                "decimal_places": 0,  # 減少小數精度
                "step_size": 1000,    # 較大步長
                "show_advanced": False,  # 隱藏進階選項
                "use_presets": True   # 使用預設值
            }
        elif self.is_tablet():
            return {
                "decimal_places": 1,
                "step_size": 500,
                "show_advanced": True,
                "use_presets": False
            }
        else:
            return {
                "decimal_places": 2,
                "step_size": 100,
                "show_advanced": True,
                "use_presets": False
            }
    
    def initialize_responsive_design(self):
        """
        初始化響應式設計 - 完整流程
        """
        # 1. 應用響應式樣式
        self.apply_responsive_styling()
        
        # 2. 檢測設備並選擇布局
        self.detect_device_and_layout()
        
        # 3. 設置設備特定的配置
        device_config = self.get_optimized_parameters()
        st.session_state.device_config = device_config
        
        # 4. 返回設備資訊
        return {
            "device": self.current_device,
            "screen_width": self.screen_width,
            "layout_mode": st.session_state.get("layout_mode", "desktop"),
            "config": device_config
        } 