"""
第4.6節 - 主應用程式架構（簡化版）

實作簡化的主應用程式架構，整合第1-4章所有功能。
包含完整的Streamlit頁面配置、控件實作和計算流程。
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import logging
import io
from functools import wraps

# 導入第1章數據獲取機制
from src.data_sources.simulation import SimulationDataGenerator, MarketRegime
from src.data_sources.data_fetcher import TiingoDataFetcher, FREDDataFetcher
from src.data_sources.fault_tolerance import APIFaultToleranceManager

# 導入第2章核心計算函數
from src.models.strategy_engine import calculate_va_strategy, calculate_dca_strategy
from src.models.table_calculator import calculate_summary_metrics
from src.models.calculation_formulas import (
    calculate_va_target_value, 
    calculate_dca_investment,
    convert_annual_to_period_parameters
)

# 導入第3章UI組件
from src.ui.parameter_manager import ParameterManager
from src.ui.results_display import ResultsDisplayManager
from src.ui.smart_recommendations import SmartRecommendationsManager

# 導入第4章功能模組
from src.core.app_initialization import simple_app_initialization
from src.core.data_flow import basic_error_recovery, SimpleDataFlowPipeline
from src.core.deployment import quick_deployment_check

# 設置日誌
logger = logging.getLogger(__name__)

# ============================================================================
# 錯誤處理裝飾器
# ============================================================================

def simple_error_handler(func):
    """
    簡單錯誤處理裝飾器
    
    用於simplified_calculation_flow函數的錯誤處理
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"計算流程錯誤: {str(e)}")
            st.error(f"❌ 計算過程發生錯誤: {str(e)}")
            return None
    return wrapper

# ============================================================================
# 第4.6節核心函數
# ============================================================================

def main() -> None:
    """
    主應用程式函數
    
    按照需求文件第4.6節規格實作：
    - 調用simple_app_initialization()
    - 調用render_sidebar_controls()
    - 調用render_main_content()
    - 調用simple_state_management()
    """
    logger.info("啟動主應用程式")
    
    # 頁面配置
    st.set_page_config(
        page_title="投資策略比較分析",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # 應用程式初始化
    simple_app_initialization()
    
    # 狀態管理
    simple_state_management()
    
    # 渲染側邊欄控件
    render_sidebar_controls()
    
    # 渲染主要內容
    render_main_content()
    
    logger.info("主應用程式渲染完成")

def render_sidebar_controls() -> None:
    """
    渲染側邊欄控件
    
    實作所有需求文件中指定的控件：
    - initial_investment: number_input, min=1000, max=1000000, value=10000, step=1000
    - monthly_investment: number_input, min=100, max=50000, value=1000, step=100
    - investment_years: slider, min=1, max=30, value=10, step=1
    - stock_ratio: slider, min=0.0, max=1.0, value=0.8, step=0.1
    - scenario: selectbox, options=['historical', 'bull_market', 'bear_market']
    """
    logger.info("渲染側邊欄控件")
    
    with st.sidebar:
        st.title("📊 投資參數設定")
        st.markdown("---")
        
        # 初始投資金額
        st.subheader("💰 投資金額")
        initial_investment = st.number_input(
            "初始投資金額 (元)",
            min_value=1000,
            max_value=1000000,
            value=10000,
            step=1000,
            help="一次性投入的初始金額"
        )
        
        monthly_investment = st.number_input(
            "每月投資金額 (元)",
            min_value=100,
            max_value=50000,
            value=1000,
            step=100,
            help="每月定期投入的金額"
        )
        
        # 投資期間
        st.subheader("📅 投資期間")
        investment_years = st.slider(
            "投資年數",
            min_value=1,
            max_value=30,
            value=10,
            step=1,
            help="投資的總年數"
        )
        
        # 資產配置
        st.subheader("📈 資產配置")
        stock_ratio = st.slider(
            "股票比例",
            min_value=0.0,
            max_value=1.0,
            value=0.8,
            step=0.1,
            format="%.1f",
            help="投資組合中股票的比例，其餘為債券"
        )
        
        # 市場情境
        st.subheader("🌍 市場情境")
        scenario = st.selectbox(
            "選擇市場情境",
            options=['historical', 'bull_market', 'bear_market'],
            index=0,
            help="選擇不同的市場情境進行分析"
        )
        
        # 儲存參數到session_state
        st.session_state.user_params = {
            'initial_investment': initial_investment,
            'monthly_investment': monthly_investment,
            'investment_years': investment_years,
            'stock_ratio': stock_ratio,
            'scenario': scenario
        }
        
        st.markdown("---")
        
        # 計算按鈕
        if st.button("🚀 開始計算", type="primary", use_container_width=True):
            st.session_state.trigger_calculation = True
            st.rerun()
        
        # 顯示當前參數
        with st.expander("📋 當前參數預覽"):
            st.write(f"初始投資: {initial_investment:,} 元")
            st.write(f"每月投資: {monthly_investment:,} 元")
            st.write(f"投資年數: {investment_years} 年")
            st.write(f"股票比例: {stock_ratio:.1%}")
            st.write(f"市場情境: {scenario}")

def render_main_content() -> None:
    """
    渲染主要內容區域
    """
    logger.info("渲染主要內容")
    
    # 應用CSS樣式
    _apply_custom_styles()
    
    # 主標題
    st.title("📊 投資策略績效比較分析系統")
    st.markdown("### 比較價值平均法 (VA) 與定期定額 (DCA) 策略的投資績效")
    
    # 系統狀態指示
    _display_system_status()
    
    st.markdown("---")
    
    # 檢查是否需要執行計算
    if st.session_state.get('trigger_calculation', False):
        user_params = st.session_state.get('user_params', {})
        
        if user_params:
            # 執行計算流程
            results = simplified_calculation_flow(user_params)
            
            if results:
                # 顯示結果
                display_results_simple(results)
                
                # 儲存結果
                st.session_state.calculation_results = results
            
        # 重置觸發標誌
        st.session_state.trigger_calculation = False
    
    # 如果有之前的計算結果，顯示它們
    elif 'calculation_results' in st.session_state:
        display_results_simple(st.session_state.calculation_results)
    
    else:
        # 顯示歡迎信息
        _display_welcome_message()

def display_results_simple(results: Dict[str, Any]) -> None:
    """
    顯示計算結果（簡化版）
    
    - 三欄指標卡片：VA最終價值、DCA最終價值、差異比較
    - 使用st.metric()顯示指標
    - 實作line_chart顯示成長趨勢
    - 實作CSV下載功能
    
    Args:
        results: 計算結果字典
    """
    logger.info("顯示計算結果")
    
    if not results:
        st.error("❌ 沒有可顯示的結果")
        return
    
    st.subheader("📈 計算結果")
    
    # 提取關鍵指標
    va_results = results.get('va_strategy', {})
    dca_results = results.get('dca_strategy', {})
    summary = results.get('summary_metrics', {})
    
    # 三欄指標卡片
    col1, col2, col3 = st.columns(3)
    
    with col1:
        va_final_value = va_results.get('final_portfolio_value', 0) if va_results else 0
        st.metric(
            label="💎 VA策略最終價值",
            value=f"{va_final_value:,.0f} 元",
            help="價值平均法策略的最終投資組合價值"
        )
    
    with col2:
        dca_final_value = dca_results.get('final_portfolio_value', 0) if dca_results else 0
        st.metric(
            label="📊 DCA策略最終價值",
            value=f"{dca_final_value:,.0f} 元",
            help="定期定額策略的最終投資組合價值"
        )
    
    with col3:
        if va_final_value > 0 and dca_final_value > 0:
            difference = va_final_value - dca_final_value
            difference_pct = (difference / dca_final_value) * 100
            st.metric(
                label="🔄 策略差異",
                value=f"{difference:,.0f} 元",
                delta=f"{difference_pct:+.2f}%",
                help="VA策略相對於DCA策略的績效差異"
            )
        else:
            st.metric(
                label="🔄 策略差異",
                value="計算中...",
                help="策略比較結果"
            )
    
    st.markdown("---")
    
    # 成長趨勢圖表
    _display_growth_chart(results)
    
    st.markdown("---")
    
    # 詳細績效指標
    _display_performance_metrics(summary)
    
    st.markdown("---")
    
    # CSV下載功能
    _display_download_section(results)

@simple_error_handler
def simplified_calculation_flow(user_params: Dict[str, Any]) -> Optional[Dict]:
    """
    簡化計算流程
    
    實作@simple_error_handler裝飾器
    四個步驟：參數驗證→數據獲取→策略計算→績效分析
    每個步驟使用st.spinner()顯示進度
    
    Args:
        user_params: 用戶參數字典
        
    Returns:
        Optional[Dict]: 計算結果字典
    """
    logger.info("開始簡化計算流程")
    
    # 步驟1: 參數驗證
    with st.spinner("🔍 正在驗證參數..."):
        if not _validate_parameters(user_params):
            st.error("❌ 參數驗證失敗")
            return None
        st.success("✅ 參數驗證通過")
    
    # 步驟2: 數據獲取
    with st.spinner("📊 正在獲取市場數據..."):
        market_data = _fetch_market_data(user_params)
        if not market_data:
            st.error("❌ 數據獲取失敗")
            return None
        st.success("✅ 數據獲取完成")
    
    # 步驟3: 策略計算
    with st.spinner("⚙️ 正在計算投資策略..."):
        calculation_results = _calculate_strategies(user_params, market_data)
        if not calculation_results:
            st.error("❌ 策略計算失敗")
            return None
        st.success("✅ 策略計算完成")
    
    # 步驟4: 績效分析
    with st.spinner("📈 正在分析績效指標..."):
        performance_results = _analyze_performance(calculation_results)
        if not performance_results:
            st.error("❌ 績效分析失敗")
            return None
        st.success("✅ 績效分析完成")
    
    # 整合結果
    final_results = {
        **calculation_results,
        **performance_results,
        'user_params': user_params,
        'market_data_info': {
            'data_source': market_data.get('metadata', {}).get('data_source', 'unknown'),
            'start_date': market_data.get('metadata', {}).get('start_date', ''),
            'end_date': market_data.get('metadata', {}).get('end_date', ''),
            'total_records': market_data.get('metadata', {}).get('total_records', 0)
        }
    }
    
    logger.info("簡化計算流程完成")
    return final_results

def simple_state_management() -> None:
    """
    簡單狀態管理
    
    初始化和管理Streamlit session state
    """
    logger.info("初始化狀態管理")
    
    # 初始化session state
    if 'app_initialized' not in st.session_state:
        st.session_state.app_initialized = True
        st.session_state.calculation_results = None
        st.session_state.user_params = {}
        st.session_state.trigger_calculation = False
        st.session_state.last_calculation_time = None
        st.session_state.system_status = 'ready'
    
    # 檢查系統狀態
    if 'system_health' not in st.session_state:
        st.session_state.system_health = _check_system_health()

# ============================================================================
# 輔助函數
# ============================================================================

def _apply_custom_styles():
    """應用自定義CSS樣式"""
    st.markdown("""
    <style>
    /* 隱藏Streamlit預設元素 */
    .stAppDeployButton {display: none !important;}
    .stDecoration {display: none !important;}
    #MainMenu {visibility: hidden !important;}
    .stFooter {visibility: hidden !important;}
    header {visibility: hidden !important;}
    
    /* 自定義樣式 */
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 4px solid #667eea;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin-bottom: 1rem;
    }
    
    .status-indicator {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-size: 0.9rem;
        font-weight: 500;
    }
    
    .status-healthy {
        background-color: #d4edda;
        color: #155724;
        border: 1px solid #c3e6cb;
    }
    
    .status-warning {
        background-color: #fff3cd;
        color: #856404;
        border: 1px solid #ffeaa7;
    }
    
    .status-error {
        background-color: #f8d7da;
        color: #721c24;
        border: 1px solid #f5c6cb;
    }
    
    /* 響應式設計 */
    @media (max-width: 768px) {
        .main-header {
            padding: 1rem;
        }
        
        .metric-card {
            padding: 1rem;
        }
    }
    </style>
    """, unsafe_allow_html=True)

def _display_system_status():
    """顯示系統狀態"""
    health = st.session_state.get('system_health', {})
    
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        if health.get('overall_status') == 'healthy':
            st.markdown('<div class="status-indicator status-healthy">🟢 系統運行正常</div>', 
                       unsafe_allow_html=True)
        elif health.get('overall_status') == 'warning':
            st.markdown('<div class="status-indicator status-warning">🟡 系統部分功能受限</div>', 
                       unsafe_allow_html=True)
        else:
            st.markdown('<div class="status-indicator status-error">🔴 系統異常</div>', 
                       unsafe_allow_html=True)
    
    with col2:
        if health.get('data_sources_available', 0) > 0:
            st.write(f"📊 數據源: {health.get('data_sources_available', 0)}/2")
        else:
            st.write("📊 數據源: 模擬模式")
    
    with col3:
        if 'last_calculation_time' in st.session_state and st.session_state.last_calculation_time:
            st.write(f"⏰ 上次計算: {st.session_state.last_calculation_time.strftime('%H:%M')}")

def _display_welcome_message():
    """顯示歡迎信息"""
    st.markdown("""
    <div class="main-header">
        <h2>🎯 歡迎使用投資策略比較分析系統</h2>
        <p>請在左側設定投資參數，然後點擊「開始計算」按鈕</p>
    </div>
    """, unsafe_allow_html=True)
    
    # 功能介紹
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        ### 💎 價值平均法 (VA)
        - 根據目標價值調整投資金額
        - 市場下跌時增加投資
        - 市場上漲時減少投資
        - 可能獲得更好的長期報酬
        """)
    
    with col2:
        st.markdown("""
        ### 📊 定期定額 (DCA)
        - 每期投入固定金額
        - 不受市場波動影響
        - 操作簡單易執行
        - 適合長期投資策略
        """)
    
    # 使用指南
    with st.expander("📖 使用指南"):
        st.markdown("""
        1. **設定參數**: 在左側邊欄設定初始投資金額、每月投資金額等參數
        2. **選擇情境**: 選擇歷史數據、牛市或熊市情境
        3. **開始計算**: 點擊「開始計算」按鈕執行分析
        4. **查看結果**: 系統將顯示兩種策略的比較結果
        5. **下載報告**: 可下載詳細的CSV報告
        """)

def _display_growth_chart(results: Dict[str, Any]):
    """顯示成長趨勢圖表"""
    st.subheader("📈 投資組合成長趨勢")
    
    va_data = results.get('va_strategy', {})
    dca_data = results.get('dca_strategy', {})
    
    if not va_data or not dca_data:
        st.warning("⚠️ 圖表數據不完整")
        return
    
    # 創建趨勢圖
    fig = go.Figure()
    
    # 假設我們有時間序列數據
    periods = list(range(1, len(va_data.get('portfolio_values', [])) + 1))
    
    if periods:
        # VA策略線
        fig.add_trace(go.Scatter(
            x=periods,
            y=va_data.get('portfolio_values', []),
            mode='lines+markers',
            name='價值平均法 (VA)',
            line=dict(color='#667eea', width=3),
            marker=dict(size=6)
        ))
        
        # DCA策略線
        fig.add_trace(go.Scatter(
            x=periods,
            y=dca_data.get('portfolio_values', []),
            mode='lines+markers',
            name='定期定額 (DCA)',
            line=dict(color='#764ba2', width=3),
            marker=dict(size=6)
        ))
        
        fig.update_layout(
            title="投資組合價值成長趨勢",
            xaxis_title="投資期數",
            yaxis_title="投資組合價值 (元)",
            hovermode='x unified',
            template='plotly_white',
            height=500
        )
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        # 簡化版本：使用Streamlit內建圖表
        chart_data = pd.DataFrame({
            'VA策略': [va_data.get('final_portfolio_value', 0)],
            'DCA策略': [dca_data.get('final_portfolio_value', 0)]
        })
        
        st.bar_chart(chart_data)

def _display_performance_metrics(summary: Dict[str, Any]):
    """顯示詳細績效指標"""
    st.subheader("📊 詳細績效指標")
    
    if not summary:
        st.warning("⚠️ 績效指標數據不可用")
        return
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        va_return = summary.get('va_annualized_return', 0)
        st.metric(
            "VA年化報酬率",
            f"{va_return:.2%}",
            help="價值平均法策略的年化報酬率"
        )
    
    with col2:
        dca_return = summary.get('dca_annualized_return', 0)
        st.metric(
            "DCA年化報酬率",
            f"{dca_return:.2%}",
            help="定期定額策略的年化報酬率"
        )
    
    with col3:
        va_sharpe = summary.get('va_sharpe_ratio', 0)
        st.metric(
            "VA夏普比率",
            f"{va_sharpe:.3f}",
            help="價值平均法策略的風險調整報酬"
        )
    
    with col4:
        dca_sharpe = summary.get('dca_sharpe_ratio', 0)
        st.metric(
            "DCA夏普比率",
            f"{dca_sharpe:.3f}",
            help="定期定額策略的風險調整報酬"
        )

def _display_download_section(results: Dict[str, Any]):
    """顯示下載區域"""
    st.subheader("📥 下載報告")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # 生成CSV數據
        csv_data = _generate_csv_data(results)
        
        if csv_data:
            st.download_button(
                label="📊 下載詳細報告 (CSV)",
                data=csv_data,
                file_name=f"investment_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                help="下載包含所有計算結果的CSV文件"
            )
    
    with col2:
        # 生成摘要報告
        summary_data = _generate_summary_report(results)
        
        if summary_data:
            st.download_button(
                label="📋 下載摘要報告 (TXT)",
                data=summary_data,
                file_name=f"investment_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                mime="text/plain",
                help="下載投資分析摘要報告"
            )

def _validate_parameters(user_params: Dict[str, Any]) -> bool:
    """驗證用戶參數"""
    required_params = ['initial_investment', 'monthly_investment', 'investment_years', 'stock_ratio', 'scenario']
    
    for param in required_params:
        if param not in user_params:
            logger.error(f"缺少必要參數: {param}")
            return False
    
    # 參數範圍檢查
    if not (1000 <= user_params['initial_investment'] <= 1000000):
        logger.error("初始投資金額超出範圍")
        return False
    
    if not (100 <= user_params['monthly_investment'] <= 50000):
        logger.error("每月投資金額超出範圍")
        return False
    
    if not (1 <= user_params['investment_years'] <= 30):
        logger.error("投資年數超出範圍")
        return False
    
    if not (0.0 <= user_params['stock_ratio'] <= 1.0):
        logger.error("股票比例超出範圍")
        return False
    
    if user_params['scenario'] not in ['historical', 'bull_market', 'bear_market']:
        logger.error("無效的市場情境")
        return False
    
    return True

def _fetch_market_data(user_params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """獲取市場數據"""
    try:
        # 使用第4章的基本錯誤恢復機制
        return basic_error_recovery()
    except Exception as e:
        logger.error(f"數據獲取失敗: {str(e)}")
        return None

def _calculate_strategies(user_params: Dict[str, Any], market_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """計算投資策略"""
    try:
        # 準備計算參數
        C0 = user_params['initial_investment']
        monthly_amount = user_params['monthly_investment']
        years = user_params['investment_years']
        stock_ratio = user_params['stock_ratio']
        
        # 轉換參數
        periods = years * 12  # 月度投資
        annual_stock_return = 0.08  # 預設股票年報酬率
        annual_bond_return = 0.03   # 預設債券年報酬率
        annual_stock_volatility = 0.15  # 預設股票波動率
        
        # 計算組合報酬率
        portfolio_return = stock_ratio * annual_stock_return + (1 - stock_ratio) * annual_bond_return
        portfolio_volatility = stock_ratio * annual_stock_volatility
        
        # 轉換為月度參數
        monthly_params = convert_annual_to_period_parameters(
            annual_return=portfolio_return,
            annual_volatility=portfolio_volatility,
            periods_per_year=12
        )
        
        # 計算VA策略
        va_results = calculate_va_strategy(
            C0=C0,
            target_monthly_amount=monthly_amount,
            periods=periods,
            expected_return=monthly_params['period_return'],
            volatility=monthly_params['period_volatility']
        )
        
        # 計算DCA策略
        dca_results = calculate_dca_strategy(
            monthly_investment=monthly_amount,
            periods=periods,
            expected_return=monthly_params['period_return'],
            volatility=monthly_params['period_volatility'],
            initial_investment=C0
        )
        
        return {
            'va_strategy': va_results,
            'dca_strategy': dca_results
        }
        
    except Exception as e:
        logger.error(f"策略計算失敗: {str(e)}")
        return None

def _analyze_performance(calculation_results: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """分析績效指標"""
    try:
        va_results = calculation_results.get('va_strategy', {})
        dca_results = calculation_results.get('dca_strategy', {})
        
        # 計算摘要指標
        summary_metrics = calculate_summary_metrics(
            va_results=va_results,
            dca_results=dca_results
        )
        
        return {
            'summary_metrics': summary_metrics
        }
        
    except Exception as e:
        logger.error(f"績效分析失敗: {str(e)}")
        return None

def _check_system_health() -> Dict[str, Any]:
    """檢查系統健康狀態"""
    health = {
        'overall_status': 'healthy',
        'data_sources_available': 0,
        'modules_loaded': True,
        'errors': []
    }
    
    try:
        # 檢查數據源
        from src.data_sources.data_fetcher import TiingoDataFetcher, FREDDataFetcher
        
        # 檢查API金鑰
        import os
        if os.getenv('TIINGO_API_KEY'):
            health['data_sources_available'] += 1
        if os.getenv('FRED_API_KEY'):
            health['data_sources_available'] += 1
        
        if health['data_sources_available'] == 0:
            health['overall_status'] = 'warning'
            health['errors'].append('無API金鑰，將使用模擬數據')
        
    except Exception as e:
        health['overall_status'] = 'error'
        health['errors'].append(f'模組載入錯誤: {str(e)}')
    
    return health

def _generate_csv_data(results: Dict[str, Any]) -> str:
    """生成CSV數據"""
    try:
        # 創建DataFrame
        data = []
        
        va_results = results.get('va_strategy', {})
        dca_results = results.get('dca_strategy', {})
        summary = results.get('summary_metrics', {})
        user_params = results.get('user_params', {})
        
        # 基本信息
        data.append(['參數設定', '', ''])
        data.append(['初始投資金額', f"{user_params.get('initial_investment', 0):,}", '元'])
        data.append(['每月投資金額', f"{user_params.get('monthly_investment', 0):,}", '元'])
        data.append(['投資年數', user_params.get('investment_years', 0), '年'])
        data.append(['股票比例', f"{user_params.get('stock_ratio', 0):.1%}", ''])
        data.append(['市場情境', user_params.get('scenario', ''), ''])
        data.append(['', '', ''])
        
        # 計算結果
        data.append(['計算結果', '', ''])
        data.append(['VA最終價值', f"{va_results.get('final_portfolio_value', 0):,.0f}", '元'])
        data.append(['DCA最終價值', f"{dca_results.get('final_portfolio_value', 0):,.0f}", '元'])
        data.append(['績效差異', f"{(va_results.get('final_portfolio_value', 0) - dca_results.get('final_portfolio_value', 0)):,.0f}", '元'])
        data.append(['', '', ''])
        
        # 績效指標
        data.append(['績效指標', '', ''])
        data.append(['VA年化報酬率', f"{summary.get('va_annualized_return', 0):.2%}", ''])
        data.append(['DCA年化報酬率', f"{summary.get('dca_annualized_return', 0):.2%}", ''])
        data.append(['VA夏普比率', f"{summary.get('va_sharpe_ratio', 0):.3f}", ''])
        data.append(['DCA夏普比率', f"{summary.get('dca_sharpe_ratio', 0):.3f}", ''])
        
        # 轉換為CSV
        df = pd.DataFrame(data, columns=['項目', '數值', '單位'])
        
        return df.to_csv(index=False, encoding='utf-8-sig')
        
    except Exception as e:
        logger.error(f"CSV生成失敗: {str(e)}")
        return ""

def _generate_summary_report(results: Dict[str, Any]) -> str:
    """生成摘要報告"""
    try:
        user_params = results.get('user_params', {})
        va_results = results.get('va_strategy', {})
        dca_results = results.get('dca_strategy', {})
        summary = results.get('summary_metrics', {})
        
        report = f"""
投資策略比較分析報告
生成時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

=== 參數設定 ===
初始投資金額: {user_params.get('initial_investment', 0):,} 元
每月投資金額: {user_params.get('monthly_investment', 0):,} 元
投資年數: {user_params.get('investment_years', 0)} 年
股票比例: {user_params.get('stock_ratio', 0):.1%}
市場情境: {user_params.get('scenario', '')}

=== 計算結果 ===
價值平均法 (VA) 最終價值: {va_results.get('final_portfolio_value', 0):,.0f} 元
定期定額 (DCA) 最終價值: {dca_results.get('final_portfolio_value', 0):,.0f} 元
績效差異: {(va_results.get('final_portfolio_value', 0) - dca_results.get('final_portfolio_value', 0)):,.0f} 元

=== 績效指標 ===
VA年化報酬率: {summary.get('va_annualized_return', 0):.2%}
DCA年化報酬率: {summary.get('dca_annualized_return', 0):.2%}
VA夏普比率: {summary.get('va_sharpe_ratio', 0):.3f}
DCA夏普比率: {summary.get('dca_sharpe_ratio', 0):.3f}

=== 建議 ===
"""
        
        # 添加分析建議
        va_final = va_results.get('final_portfolio_value', 0)
        dca_final = dca_results.get('final_portfolio_value', 0)
        
        if va_final > dca_final:
            report += "在此參數設定下，價值平均法策略表現較佳。\n"
        elif dca_final > va_final:
            report += "在此參數設定下，定期定額策略表現較佳。\n"
        else:
            report += "兩種策略表現相當。\n"
        
        report += "\n注意: 此分析基於歷史數據和假設，實際投資結果可能有所不同。\n"
        
        return report
        
    except Exception as e:
        logger.error(f"摘要報告生成失敗: {str(e)}")
        return ""

# ============================================================================
# 主程式入口
# ============================================================================

if __name__ == "__main__":
    main() 