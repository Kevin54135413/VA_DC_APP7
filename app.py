"""
投資策略績效比較分析系統 - 完整Streamlit應用實現
嚴格實作第3章3.6節規格，整合第1-2章所有技術規範
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import time
import sys
import os
import logging
from typing import Dict, Any, Optional, Union, List

# 添加src目錄到Python路徑
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# 頁面配置（必須在任何其他Streamlit命令之前）
st.set_page_config(
    page_title="投資策略比較分析",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 第1章模組導入（保持不變）
try:
    from src.data_sources.tiingo_client import TiingoDataFetcher
    from src.data_sources.fred_client import FREDDataFetcher
    from src.data_sources.simulation import SimulationDataGenerator
    from src.data_sources.cache_manager import IntelligentCacheManager
    from src.utils.api_security import get_api_key, validate_api_key_format
    from src.data_sources.fault_tolerance import APIFaultToleranceManager
except ImportError as e:
    st.error(f"第1章模組導入失敗: {e}")

# 第2章模組導入（保持不變）
try:
    from src.models.calculation_formulas import (
        calculate_va_target_value, 
        calculate_dca_investment,
        calculate_annualized_return,
        convert_annual_to_period_parameters
    )
    from src.models.strategy_engine import calculate_va_strategy, calculate_dca_strategy
    from src.models.performance_metrics import calculate_irr, calculate_sharpe_ratio
    from src.models.table_calculator import calculate_summary_metrics
except ImportError as e:
    st.error(f"第2章模組導入失敗: {e}")

# 第3章UI模組導入
try:
    from src.ui.parameter_manager import ParameterManager
    from src.ui.results_display import ResultsDisplayManager
    from src.ui.smart_recommendations import SmartRecommendationsManager
    from src.ui.responsive_design import ResponsiveDesignManager
except ImportError as e:
    st.error(f"第3章UI模組導入失敗: {e}")

# 第1章技術規範集成確認
CHAPTER1_INTEGRATION_CHECKLIST = {
    "data_precision": {
        "price_precision": "小數點後2位",
        "yield_precision": "小數點後4位", 
        "percentage_precision": "小數點後2位",
        "implementation": "所有UI組件強制精確度驗證"
    },
    "api_security": {
        "multilevel_keys": "背景自動管理",
        "fault_tolerance": "無縫自動切換",
        "retry_mechanism": "智能重試策略",
        "backup_strategy": "模擬數據降級",
        "user_experience": "零感知切換"
    },
    "data_sources": {
        "tiingo_api": "SPY股票數據",
        "fred_api": "債券殖利率數據", 
        "simulation_engine": "幾何布朗運動+Vasicek模型",
        "quality_validation": "數據品質評分系統"
    },
    "trading_days": {
        "us_market_rules": "美股交易日規則",
        "holiday_adjustment": "假期調整機制",
        "period_calculation": "期初期末日期計算"
    }
}

# 第2章技術規範集成確認
CHAPTER2_INTEGRATION_CHECKLIST = {
    "core_formulas": {
        "va_target_value": "calculate_va_target_value函數保持不變",
        "dca_investment": "calculate_dca_investment函數保持不變",
        "parameter_conversion": "convert_annual_to_period_parameters保持不變",
        "ui_integration": "UI參數直接對應公式參數"
    },
    "table_structures": {
        "va_strategy": "27個欄位，VA_COLUMNS_ORDER",
        "dca_strategy": "28個欄位，DCA_COLUMNS_ORDER", 
        "summary_comparison": "8個欄位，SUMMARY_COLUMNS_ORDER",
        "csv_export": "格式一致性保證機制"
    },
    "performance_metrics": {
        "irr_calculation": "calculate_irr函數",
        "annualized_return": "calculate_annualized_return函數",
        "sharpe_ratio": "3位小數精度",
        "max_drawdown": "calculate_max_drawdown函數"
    },
    "execution_logic": {
        "va_timing": "期末執行，第1期期初投入C0",
        "dca_timing": "期初執行，每期固定投入",
        "investment_sequence": "符合2.1.3.1投資時機規定"
    }
}

def main():
    """
    主應用程式函數 - 3.6.1節規格
    """
    # 注意：st.set_page_config() 只能在腳本開始時調用一次
    
    # 應用程式初始化（整合第1章）
    simple_app_initialization()
    
    # 應用現代化樣式
    apply_modern_styling()
    
    # 渲染現代化標題
    render_modern_header()
    
    # 狀態管理
    simple_state_management()
    
    # 檢測設備並渲染對應布局
    detect_device_and_layout()

def simple_app_initialization():
    """
    應用程式初始化（整合第1章） - 3.6.1節規格
    """
    # 設定日誌配置
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 初始化session_state
    if 'app_initialized' not in st.session_state:
        st.session_state.app_initialized = True
        st.session_state.data_source_status = "checking"
        st.session_state.last_calculation_params = None
        st.session_state.calculation_results = None
        st.session_state.api_health_status = "unknown"
    
    # 檢查API金鑰（背景執行）
    try:
        tiingo_key = get_api_key("TIINGO_API_KEY")
        fred_key = get_api_key("FRED_API_KEY")
        
        if tiingo_key and fred_key:
            st.session_state.api_health_status = "healthy"
            st.session_state.data_source_status = "real_data"
        else:
            st.session_state.api_health_status = "partial"
            st.session_state.data_source_status = "simulation"
    except Exception as e:
        st.session_state.api_health_status = "error"
        st.session_state.data_source_status = "offline"
        logging.error(f"API初始化失敗: {e}")
    
    # 執行基本健康檢查
    if st.session_state.data_source_status == "real_data":
        # 背景測試API連接
        try:
            # 這裡可以添加快速API測試
            pass
        except Exception as e:
            st.session_state.data_source_status = "simulation"
            logging.warning(f"API連接測試失敗，切換到模擬模式: {e}")
    
    # 配置Streamlit設定
    st.session_state.streamlit_config = {
        "theme": "light",
        "responsive_mode": True,
        "cache_enabled": True
    }

def apply_modern_styling():
    """
    現代化CSS樣式 - 3.6.2節規格
    """
    st.markdown("""
    <style>
    /* 隱藏Streamlit預設元素 */
    .stAppDeployButton {display: none !important;}
    .stDecoration {display: none !important;}
    #MainMenu {visibility: hidden !important;}
    .stFooter {visibility: hidden !important;}
    header {visibility: hidden !important;}
    
    /* 現代化卡片樣式 */
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        border: 1px solid #e5e7eb;
        margin-bottom: 1rem;
        transition: all 0.2s ease;
    }
    
    .metric-card:hover {
        box-shadow: 0 4px 16px rgba(0,0,0,0.15);
        transform: translateY(-2px);
    }
    
    /* 響應式字體大小 */
    @media (max-width: 768px) {
        .stMarkdown h1 { font-size: 1.75rem !important; }
        .stMarkdown h2 { font-size: 1.5rem !important; }
        .stMarkdown h3 { font-size: 1.25rem !important; }
        .stSlider > div > div > div { min-height: 48px !important; }
        .stButton > button { min-height: 48px !important; font-size: 16px !important; }
    }
    
    @media (min-width: 769px) and (max-width: 1023px) {
        .stMarkdown h1 { font-size: 2rem !important; }
        .stMarkdown h2 { font-size: 1.75rem !important; }
        .stMarkdown h3 { font-size: 1.5rem !important; }
    }
    
    @media (min-width: 1024px) {
        .stMarkdown h1 { font-size: 2.5rem !important; }
        .stMarkdown h2 { font-size: 2rem !important; }
        .stMarkdown h3 { font-size: 1.75rem !important; }
    }
    
    /* 改進的互動元件 */
    .stSlider > div > div > div > div {
        background: #3b82f6 !important;
    }
    
    .stButton > button {
        border-radius: 8px !important;
        font-weight: 500 !important;
        transition: all 0.2s ease !important;
        border: 1px solid #d1d5db !important;
    }
    
    .stButton > button:hover {
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15) !important;
    }
    
    .stButton > button[kind="primary"] {
        background: #3b82f6 !important;
        color: white !important;
        border: none !important;
    }
    
    .stButton > button[kind="primary"]:hover {
        background: #2563eb !important;
    }
    
    /* 智能狀態指示器 */
    .status-indicator {
        display: inline-block;
        width: 12px;
        height: 12px;
        border-radius: 50%;
        margin-right: 8px;
        animation: pulse 2s infinite;
    }
    
    .status-healthy { 
        background: #10b981; 
    }
    
    .status-warning { 
        background: #f59e0b; 
    }
    
    .status-error { 
        background: #ef4444; 
    }
    
    @keyframes pulse {
        0% { opacity: 1; }
        50% { opacity: 0.5; }
        100% { opacity: 1; }
    }
    
    /* 進度條樣式 */
    .stProgress .st-bo {
        background: #3b82f6 !important;
    }
    
    /* 表格樣式 */
    .stDataFrame {
        border-radius: 8px !important;
        overflow: hidden !important;
    }
    
    /* 圖表容器 */
    .stPlotlyChart {
        background: white;
        border-radius: 8px;
        padding: 1rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    
    /* 輸入元件樣式 */
    .stNumberInput > div > div > input {
        border-radius: 6px !important;
        border: 1px solid #d1d5db !important;
    }
    
    .stSelectbox > div > div > div {
        border-radius: 6px !important;
        border: 1px solid #d1d5db !important;
    }
    
    /* 標籤樣式 */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px 8px 0 0;
        padding: 12px 24px;
        font-weight: 500;
    }
    
    /* 警告和成功訊息 */
    .stAlert {
        border-radius: 8px !important;
        border: none !important;
    }
    
    .stSuccess {
        background: #f0fdf4 !important;
        color: #166534 !important;
        border-left: 4px solid #10b981 !important;
    }
    
    .stWarning {
        background: #fffbeb !important;
        color: #92400e !important;
        border-left: 4px solid #f59e0b !important;
    }
    
    .stError {
        background: #fef2f2 !important;
        color: #991b1b !important;
        border-left: 4px solid #ef4444 !important;
    }
    
    .stInfo {
        background: #eff6ff !important;
        color: #1e40af !important;
        border-left: 4px solid #3b82f6 !important;
    }
    </style>
    """, unsafe_allow_html=True)

def render_modern_header():
    """
    渲染現代化標題 - 3.6.1節規格
    """
    # 主標題和副標題
    st.markdown("# 🏠 投資策略比較分析")
    st.markdown("##### 輕鬆比較定期定值(VA) vs 定期定額(DCA)策略")
    
    # 智能狀態指示器（整合第1章數據源狀態）
    col1, col2, col3, col4 = st.columns([2, 2, 2, 6])
    
    with col1:
        data_status = st.session_state.get("data_source_status", "checking")
        if data_status == "real_data":
            st.markdown('<span class="status-indicator status-healthy"></span>🟢 真實數據', unsafe_allow_html=True)
        elif data_status == "simulation":
            st.markdown('<span class="status-indicator status-warning"></span>🟡 模擬數據', unsafe_allow_html=True)
        else:
            st.markdown('<span class="status-indicator status-error"></span>🔴 離線模式', unsafe_allow_html=True)
    
    with col2:
        api_status = st.session_state.get("api_health_status", "unknown")
        if api_status == "healthy":
            st.markdown("🔗 API正常")
        elif api_status == "partial":
            st.markdown("⚠️ 部分API")
        else:
            st.markdown("❌ API離線")
    
    with col3:
        # 顯示計算狀態
        if st.session_state.get("calculation_results"):
            st.markdown("✅ 已完成計算")
        else:
            st.markdown("⏳ 等待計算")
    
    st.markdown("---")

def simple_state_management():
    """
    狀態管理 - 3.6.1節規格
    """
    # 初始化狀態變數
    if 'calculation_results' not in st.session_state:
        st.session_state.calculation_results = None
    
    if 'last_calculation_params' not in st.session_state:
        st.session_state.last_calculation_params = None
    
    if 'parameter_changed' not in st.session_state:
        st.session_state.parameter_changed = False
    
    # 檢測參數變更的輔助函數
    def check_parameter_change(current_params):
        """檢測參數是否變更"""
        if st.session_state.last_calculation_params is None:
            return True
        
        # 比較關鍵參數
        key_params = ['initial_investment', 'investment_years', 'investment_frequency', 
                     'stock_allocation', 'bond_allocation', 'expected_stock_return', 
                     'expected_bond_return']
        
        for param in key_params:
            if current_params.get(param) != st.session_state.last_calculation_params.get(param):
                return True
        
        return False
    
    # 存儲檢測函數到session_state
    st.session_state.check_parameter_change = check_parameter_change

def detect_device_and_layout():
    """
    檢測設備並渲染對應布局 - 整合響應式設計
    """
    # 創建響應式設計管理器
    if 'responsive_manager' not in st.session_state:
        st.session_state.responsive_manager = ResponsiveDesignManager()
    
    # 檢測設備並調整布局
    st.session_state.responsive_manager.detect_device_and_layout()

def collect_user_parameters():
    """
    收集用戶參數 - 3.6.1節規格
    """
    # 創建參數管理器
    if 'parameter_manager' not in st.session_state:
        st.session_state.parameter_manager = ParameterManager()
    
    # 根據設備類型選擇參數收集方式
    device_type = st.session_state.get('layout_mode', 'desktop')
    
    if device_type == 'mobile':
        # 移動端簡化參數收集
        return st.session_state.parameter_manager.get_mobile_parameters()
    elif device_type == 'tablet':
        # 平板端中等複雜度參數收集
        return st.session_state.parameter_manager.get_tablet_parameters()
    else:
        # 桌面端完整參數收集
        return st.session_state.parameter_manager.get_all_parameters()

def simplified_calculation_flow(user_params):
    """
    簡化版計算流程 - 3.6.1節規格
    """
    if not user_params:
        return None
    
    # 檢查參數是否變更
    if st.session_state.check_parameter_change(user_params):
        st.session_state.parameter_changed = True
        
        # 顯示計算進度
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            # 階段1：數據獲取（整合第1章）
            status_text.text("🔄 階段1/4：獲取市場數據...")
            progress_bar.progress(25)
            
            # 根據數據源狀態選擇數據獲取方式
            if st.session_state.data_source_status == "real_data":
                # 使用真實API數據
                market_data = fetch_real_market_data(user_params)
            else:
                # 使用模擬數據
                market_data = generate_simulation_data(user_params)
            
            # 階段2：參數轉換
            status_text.text("⚙️ 階段2/4：轉換投資參數...")
            progress_bar.progress(50)
            
            # 使用第2章的參數轉換函數
            period_params = convert_annual_to_period_parameters(
                user_params['investment_frequency'],
                user_params['expected_stock_return'],
                user_params['expected_bond_return'],
                user_params['stock_volatility'],
                user_params['bond_volatility']
            )
            
            # 階段3：策略計算（整合第2章）
            status_text.text("📊 階段3/4：執行策略計算...")
            progress_bar.progress(75)
            
            # VA策略計算
            va_results = calculate_va_strategy(user_params, market_data)
            
            # DCA策略計算
            dca_results = calculate_dca_strategy(user_params, market_data)
            
            # 階段4：結果整理
            status_text.text("✅ 階段4/4：整理計算結果...")
            progress_bar.progress(100)
            
            # 計算摘要指標
            summary_metrics = calculate_summary_metrics(va_results, dca_results)
            
            # 整理最終結果
            calculation_results = {
                'va_results': va_results,
                'dca_results': dca_results,
                'summary_metrics': summary_metrics,
                'market_data': market_data,
                'parameters': user_params,
                'calculation_time': datetime.now()
            }
            
            # 更新狀態
            st.session_state.calculation_results = calculation_results
            st.session_state.last_calculation_params = user_params.copy()
            st.session_state.parameter_changed = False
            
            # 清除進度顯示
            progress_bar.empty()
            status_text.empty()
            
            return calculation_results
            
        except Exception as e:
            progress_bar.empty()
            status_text.empty()
            st.error(f"計算過程發生錯誤: {str(e)}")
            return None
    
    # 參數未變更，返回已有結果
    return st.session_state.calculation_results

def fetch_real_market_data(user_params):
    """
    獲取真實市場數據（整合第1章）
    """
    try:
        # 使用第1章的數據獲取器
        tiingo_fetcher = TiingoDataFetcher()
        fred_fetcher = FREDDataFetcher()
        
        # 獲取股票數據
        stock_data = tiingo_fetcher.fetch_stock_data(
            symbol="SPY",
            start_date=datetime.now() - timedelta(days=365*5),
            end_date=datetime.now()
        )
        
        # 獲取債券數據
        bond_data = fred_fetcher.fetch_bond_data(
            series_id="DGS10",
            start_date=datetime.now() - timedelta(days=365*5),
            end_date=datetime.now()
        )
        
        return {
            'stock_data': stock_data,
            'bond_data': bond_data,
            'data_source': 'real_api'
        }
        
    except Exception as e:
        st.warning(f"真實數據獲取失敗，切換到模擬數據: {str(e)}")
        return generate_simulation_data(user_params)

def generate_simulation_data(user_params):
    """
    生成模擬數據（整合第1章）
    """
    try:
        # 使用第1章的模擬數據生成器
        simulator = SimulationDataGenerator()
        
        # 生成模擬市場數據
        simulation_data = simulator.generate_market_simulation(
            periods=user_params['investment_years'] * user_params['investment_frequency'],
            stock_return=user_params['expected_stock_return'],
            bond_return=user_params['expected_bond_return'],
            stock_volatility=user_params.get('stock_volatility', 0.15),
            bond_volatility=user_params.get('bond_volatility', 0.05)
        )
        
        return {
            'stock_data': simulation_data['stock_data'],
            'bond_data': simulation_data['bond_data'],
            'data_source': 'simulation'
        }
        
    except Exception as e:
        st.error(f"模擬數據生成失敗: {str(e)}")
        return None

if __name__ == "__main__":
    main() 