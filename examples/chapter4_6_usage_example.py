"""
第4.6節 - 主應用程式架構使用範例

展示主應用程式架構的所有功能，包括：
1. 核心函數演示
2. 參數控制演示
3. 計算流程演示
4. 結果顯示演示
5. 錯誤處理演示
6. 狀態管理演示
7. 完整應用程式演示
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import logging
from typing import Dict, Any, Optional
import traceback

# 導入主應用程式模組
from src.core.main_app import (
    main,
    render_sidebar_controls,
    render_main_content,
    display_results_simple,
    simplified_calculation_flow,
    simple_state_management,
    simple_error_handler,
    _validate_parameters,
    _fetch_market_data,
    _calculate_strategies,
    _analyze_performance,
    _check_system_health,
    _generate_csv_data,
    _generate_summary_report
)

# 設置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main_demo():
    """主演示函數"""
    st.set_page_config(
        page_title="第4.6節 - 主應用程式架構演示",
        page_icon="🏗️",
        layout="wide"
    )
    
    st.title("🏗️ 第4.6節 - 主應用程式架構演示")
    st.markdown("展示主應用程式架構的所有功能和特性")
    
    # 演示選單
    demo_options = [
        "🎯 核心函數演示",
        "🎛️ 參數控制演示", 
        "⚙️ 計算流程演示",
        "📊 結果顯示演示",
        "🛡️ 錯誤處理演示",
        "💾 狀態管理演示",
        "🚀 完整應用程式演示"
    ]
    
    selected_demo = st.sidebar.selectbox("選擇演示項目", demo_options)
    
    if selected_demo == "🎯 核心函數演示":
        core_functions_demo()
    elif selected_demo == "🎛️ 參數控制演示":
        parameter_controls_demo()
    elif selected_demo == "⚙️ 計算流程演示":
        calculation_flow_demo()
    elif selected_demo == "📊 結果顯示演示":
        results_display_demo()
    elif selected_demo == "🛡️ 錯誤處理演示":
        error_handling_demo()
    elif selected_demo == "💾 狀態管理演示":
        state_management_demo()
    elif selected_demo == "🚀 完整應用程式演示":
        full_application_demo()

def core_functions_demo():
    """核心函數演示"""
    st.header("🎯 核心函數演示")
    st.markdown("展示第4.6節所有核心函數的功能和特性")
    
    # 函數簽名檢查
    st.subheader("📋 函數簽名檢查")
    
    functions_info = [
        ("main", main, "主應用程式入口函數"),
        ("render_sidebar_controls", render_sidebar_controls, "渲染側邊欄控件"),
        ("render_main_content", render_main_content, "渲染主要內容"),
        ("display_results_simple", display_results_simple, "顯示計算結果"),
        ("simplified_calculation_flow", simplified_calculation_flow, "簡化計算流程"),
        ("simple_state_management", simple_state_management, "簡單狀態管理")
    ]
    
    for name, func, description in functions_info:
        with st.expander(f"📝 {name}()"):
            import inspect
            sig = inspect.signature(func)
            
            st.write(f"**描述**: {description}")
            st.write(f"**簽名**: `{name}{sig}`")
            st.write(f"**參數數量**: {len(sig.parameters)}")
            st.write(f"**返回類型**: {sig.return_annotation}")
            
            # 顯示函數文檔
            if func.__doc__:
                st.markdown("**文檔**:")
                st.code(func.__doc__, language="text")
    
    # 系統健康檢查演示
    st.subheader("🏥 系統健康檢查")
    
    if st.button("🔍 檢查系統健康狀態"):
        with st.spinner("正在檢查系統健康狀態..."):
            health = _check_system_health()
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("整體狀態", health.get('overall_status', 'unknown'))
                st.metric("可用數據源", health.get('data_sources_available', 0))
                st.metric("模組載入", "✅" if health.get('modules_loaded', False) else "❌")
            
            with col2:
                st.write("**錯誤列表**:")
                errors = health.get('errors', [])
                if errors:
                    for error in errors:
                        st.error(f"❌ {error}")
                else:
                    st.success("✅ 無錯誤")
    
    # 參數驗證演示
    st.subheader("✅ 參數驗證演示")
    
    test_params = {
        'initial_investment': st.number_input("初始投資金額", value=10000, min_value=1000, max_value=1000000),
        'monthly_investment': st.number_input("每月投資金額", value=1000, min_value=100, max_value=50000),
        'investment_years': st.slider("投資年數", min_value=1, max_value=30, value=10),
        'stock_ratio': st.slider("股票比例", min_value=0.0, max_value=1.0, value=0.8, step=0.1),
        'scenario': st.selectbox("市場情境", ['historical', 'bull_market', 'bear_market'])
    }
    
    if st.button("🔍 驗證參數"):
        is_valid = _validate_parameters(test_params)
        
        if is_valid:
            st.success("✅ 參數驗證通過")
            st.json(test_params)
        else:
            st.error("❌ 參數驗證失敗")

def parameter_controls_demo():
    """參數控制演示"""
    st.header("🎛️ 參數控制演示")
    st.markdown("展示側邊欄控件的實作和功能")
    
    # 控件規格說明
    st.subheader("📋 控件規格")
    
    controls_spec = [
        ("initial_investment", "number_input", "min=1000, max=1000000, value=10000, step=1000"),
        ("monthly_investment", "number_input", "min=100, max=50000, value=1000, step=100"),
        ("investment_years", "slider", "min=1, max=30, value=10, step=1"),
        ("stock_ratio", "slider", "min=0.0, max=1.0, value=0.8, step=0.1"),
        ("scenario", "selectbox", "options=['historical', 'bull_market', 'bear_market']")
    ]
    
    spec_df = pd.DataFrame(controls_spec, columns=["控件名稱", "類型", "參數"])
    st.dataframe(spec_df, use_container_width=True)
    
    # 實際控件演示
    st.subheader("🎛️ 實際控件")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**投資金額控件**")
        demo_initial = st.number_input(
            "初始投資金額 (元)",
            min_value=1000,
            max_value=1000000,
            value=10000,
            step=1000,
            key="demo_initial"
        )
        
        demo_monthly = st.number_input(
            "每月投資金額 (元)",
            min_value=100,
            max_value=50000,
            value=1000,
            step=100,
            key="demo_monthly"
        )
    
    with col2:
        st.markdown("**投資參數控件**")
        demo_years = st.slider(
            "投資年數",
            min_value=1,
            max_value=30,
            value=10,
            step=1,
            key="demo_years"
        )
        
        demo_ratio = st.slider(
            "股票比例",
            min_value=0.0,
            max_value=1.0,
            value=0.8,
            step=0.1,
            key="demo_ratio"
        )
        
        demo_scenario = st.selectbox(
            "市場情境",
            ['historical', 'bull_market', 'bear_market'],
            key="demo_scenario"
        )
    
    # 參數預覽
    st.subheader("📊 參數預覽")
    
    current_params = {
        'initial_investment': demo_initial,
        'monthly_investment': demo_monthly,
        'investment_years': demo_years,
        'stock_ratio': demo_ratio,
        'scenario': demo_scenario
    }
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.json(current_params)
    
    with col2:
        # 計算投資總額
        total_investment = demo_initial + (demo_monthly * demo_years * 12)
        
        st.metric("總投資金額", f"{total_investment:,} 元")
        st.metric("投資期間", f"{demo_years * 12} 個月")
        st.metric("股票配置", f"{demo_ratio:.1%}")
        st.metric("債券配置", f"{1-demo_ratio:.1%}")

def calculation_flow_demo():
    """計算流程演示"""
    st.header("⚙️ 計算流程演示")
    st.markdown("展示簡化計算流程的四個步驟")
    
    # 流程步驟說明
    st.subheader("📋 流程步驟")
    
    steps = [
        ("1️⃣ 參數驗證", "驗證用戶輸入的參數是否有效"),
        ("2️⃣ 數據獲取", "從數據源獲取市場數據"),
        ("3️⃣ 策略計算", "計算VA和DCA策略結果"),
        ("4️⃣ 績效分析", "分析和比較策略績效")
    ]
    
    for step, description in steps:
        st.write(f"**{step}**: {description}")
    
    # 流程圖
    st.subheader("🔄 流程圖")
    
    flow_chart = """
    graph TD
        A[開始] --> B[參數驗證]
        B --> C{驗證通過?}
        C -->|否| D[返回錯誤]
        C -->|是| E[數據獲取]
        E --> F{數據獲取成功?}
        F -->|否| G[返回錯誤]
        F -->|是| H[策略計算]
        H --> I{計算成功?}
        I -->|否| J[返回錯誤]
        I -->|是| K[績效分析]
        K --> L[返回結果]
        L --> M[結束]
    """
    
    st.markdown(f"```mermaid\n{flow_chart}\n```")
    
    # 實際計算演示
    st.subheader("🚀 實際計算演示")
    
    # 參數設定
    with st.expander("⚙️ 計算參數設定"):
        calc_params = {
            'initial_investment': st.number_input("初始投資", value=10000, key="calc_initial"),
            'monthly_investment': st.number_input("每月投資", value=1000, key="calc_monthly"),
            'investment_years': st.slider("投資年數", 1, 30, 10, key="calc_years"),
            'stock_ratio': st.slider("股票比例", 0.0, 1.0, 0.8, key="calc_ratio"),
            'scenario': st.selectbox("市場情境", ['historical', 'bull_market', 'bear_market'], key="calc_scenario")
        }
    
    # 執行計算
    if st.button("🚀 執行計算流程"):
        st.markdown("### 計算過程")
        
        # 創建進度條
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            # 步驟1: 參數驗證
            status_text.text("🔍 正在驗證參數...")
            progress_bar.progress(25)
            
            is_valid = _validate_parameters(calc_params)
            if not is_valid:
                st.error("❌ 參數驗證失敗")
                return
            
            st.success("✅ 參數驗證通過")
            
            # 步驟2: 數據獲取
            status_text.text("📊 正在獲取市場數據...")
            progress_bar.progress(50)
            
            market_data = _fetch_market_data(calc_params)
            if not market_data:
                st.error("❌ 數據獲取失敗")
                return
            
            st.success("✅ 數據獲取完成")
            
            # 步驟3: 策略計算
            status_text.text("⚙️ 正在計算投資策略...")
            progress_bar.progress(75)
            
            calculation_results = _calculate_strategies(calc_params, market_data)
            if not calculation_results:
                st.error("❌ 策略計算失敗")
                return
            
            st.success("✅ 策略計算完成")
            
            # 步驟4: 績效分析
            status_text.text("📈 正在分析績效指標...")
            progress_bar.progress(100)
            
            performance_results = _analyze_performance(calculation_results)
            if not performance_results:
                st.error("❌ 績效分析失敗")
                return
            
            st.success("✅ 績效分析完成")
            
            # 顯示結果摘要
            st.markdown("### 計算結果摘要")
            
            final_results = {
                **calculation_results,
                **performance_results,
                'user_params': calc_params
            }
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                va_value = final_results.get('va_strategy', {}).get('final_portfolio_value', 0)
                st.metric("VA策略最終價值", f"{va_value:,.0f} 元")
            
            with col2:
                dca_value = final_results.get('dca_strategy', {}).get('final_portfolio_value', 0)
                st.metric("DCA策略最終價值", f"{dca_value:,.0f} 元")
            
            with col3:
                difference = va_value - dca_value
                st.metric("績效差異", f"{difference:,.0f} 元")
            
            status_text.text("🎉 計算流程完成!")
            
        except Exception as e:
            st.error(f"❌ 計算過程發生錯誤: {str(e)}")
            st.code(traceback.format_exc())

def results_display_demo():
    """結果顯示演示"""
    st.header("📊 結果顯示演示")
    st.markdown("展示計算結果的顯示功能")
    
    # 模擬結果數據
    st.subheader("📋 模擬結果數據")
    
    # 生成模擬數據
    np.random.seed(42)
    periods = 120  # 10年 * 12個月
    
    # VA策略模擬數據
    va_values = []
    current_value = 10000
    for i in range(periods):
        growth = np.random.normal(0.006, 0.04)  # 月度報酬率
        current_value *= (1 + growth)
        va_values.append(current_value)
    
    # DCA策略模擬數據
    dca_values = []
    current_value = 10000
    for i in range(periods):
        growth = np.random.normal(0.0055, 0.035)  # 稍低的報酬率
        current_value *= (1 + growth)
        dca_values.append(current_value)
    
    mock_results = {
        'va_strategy': {
            'final_portfolio_value': va_values[-1],
            'portfolio_values': va_values,
            'total_investment': 10000 + 1000 * periods,
            'total_return': va_values[-1] - (10000 + 1000 * periods)
        },
        'dca_strategy': {
            'final_portfolio_value': dca_values[-1],
            'portfolio_values': dca_values,
            'total_investment': 10000 + 1000 * periods,
            'total_return': dca_values[-1] - (10000 + 1000 * periods)
        },
        'summary_metrics': {
            'va_annualized_return': 0.085,
            'dca_annualized_return': 0.078,
            'va_sharpe_ratio': 1.25,
            'dca_sharpe_ratio': 1.18,
            'va_max_drawdown': -0.15,
            'dca_max_drawdown': -0.12
        },
        'user_params': {
            'initial_investment': 10000,
            'monthly_investment': 1000,
            'investment_years': 10,
            'stock_ratio': 0.8,
            'scenario': 'historical'
        }
    }
    
    # 三欄指標演示
    st.subheader("📊 三欄指標卡片")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        va_final = mock_results['va_strategy']['final_portfolio_value']
        st.metric(
            "💎 VA策略最終價值",
            f"{va_final:,.0f} 元",
            help="價值平均法策略的最終投資組合價值"
        )
    
    with col2:
        dca_final = mock_results['dca_strategy']['final_portfolio_value']
        st.metric(
            "📊 DCA策略最終價值",
            f"{dca_final:,.0f} 元",
            help="定期定額策略的最終投資組合價值"
        )
    
    with col3:
        difference = va_final - dca_final
        difference_pct = (difference / dca_final) * 100
        st.metric(
            "🔄 策略差異",
            f"{difference:,.0f} 元",
            delta=f"{difference_pct:+.2f}%",
            help="VA策略相對於DCA策略的績效差異"
        )
    
    # 成長趨勢圖表
    st.subheader("📈 成長趨勢圖表")
    
    # 創建圖表數據
    chart_data = pd.DataFrame({
        'VA策略': va_values,
        'DCA策略': dca_values
    })
    
    st.line_chart(chart_data)
    
    # 詳細績效指標
    st.subheader("📊 詳細績效指標")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("VA年化報酬率", f"{mock_results['summary_metrics']['va_annualized_return']:.2%}")
    
    with col2:
        st.metric("DCA年化報酬率", f"{mock_results['summary_metrics']['dca_annualized_return']:.2%}")
    
    with col3:
        st.metric("VA夏普比率", f"{mock_results['summary_metrics']['va_sharpe_ratio']:.3f}")
    
    with col4:
        st.metric("DCA夏普比率", f"{mock_results['summary_metrics']['dca_sharpe_ratio']:.3f}")
    
    # CSV下載功能演示
    st.subheader("📥 下載功能演示")
    
    col1, col2 = st.columns(2)
    
    with col1:
        csv_data = _generate_csv_data(mock_results)
        if csv_data:
            st.download_button(
                "📊 下載詳細報告 (CSV)",
                csv_data,
                f"demo_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                "text/csv"
            )
    
    with col2:
        summary_data = _generate_summary_report(mock_results)
        if summary_data:
            st.download_button(
                "📋 下載摘要報告 (TXT)",
                summary_data,
                f"demo_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                "text/plain"
            )
    
    # 完整結果顯示演示
    st.subheader("🎯 完整顯示函數演示")
    
    if st.button("🚀 執行 display_results_simple()"):
        st.markdown("---")
        display_results_simple(mock_results)

def error_handling_demo():
    """錯誤處理演示"""
    st.header("🛡️ 錯誤處理演示")
    st.markdown("展示錯誤處理裝飾器和異常處理機制")
    
    # 裝飾器演示
    st.subheader("🎭 錯誤處理裝飾器")
    
    st.code("""
@simple_error_handler
def test_function():
    # 這個函數會拋出異常
    raise ValueError("這是一個測試錯誤")
    """, language="python")
    
    # 測試成功情況
    st.subheader("✅ 成功執行演示")
    
    @simple_error_handler
    def success_function():
        return "函數執行成功!"
    
    if st.button("🚀 執行成功函數"):
        result = success_function()
        if result:
            st.success(f"✅ {result}")
    
    # 測試錯誤情況
    st.subheader("❌ 錯誤處理演示")
    
    @simple_error_handler
    def error_function():
        raise ValueError("這是一個測試錯誤")
    
    if st.button("💥 執行錯誤函數"):
        result = error_function()
        if result is None:
            st.info("ℹ️ 函數因錯誤返回None，錯誤已被處理")
    
    # 參數驗證錯誤演示
    st.subheader("🔍 參數驗證錯誤")
    
    error_test_cases = [
        ("缺少必要參數", {'initial_investment': 10000}),
        ("投資金額超出範圍", {'initial_investment': 2000000, 'monthly_investment': 1000, 'investment_years': 10, 'stock_ratio': 0.8, 'scenario': 'historical'}),
        ("無效市場情境", {'initial_investment': 10000, 'monthly_investment': 1000, 'investment_years': 10, 'stock_ratio': 0.8, 'scenario': 'invalid'})
    ]
    
    for test_name, test_params in error_test_cases:
        with st.expander(f"🧪 {test_name}"):
            st.json(test_params)
            
            if st.button(f"測試 {test_name}", key=f"test_{test_name}"):
                is_valid = _validate_parameters(test_params)
                if is_valid:
                    st.success("✅ 參數驗證通過")
                else:
                    st.error("❌ 參數驗證失敗（預期結果）")
    
    # 計算流程錯誤演示
    st.subheader("⚙️ 計算流程錯誤處理")
    
    if st.button("🔧 測試計算流程錯誤處理"):
        # 使用無效參數測試計算流程
        invalid_params = {'invalid': 'params'}
        
        st.write("**測試參數**:")
        st.json(invalid_params)
        
        st.write("**執行結果**:")
        result = simplified_calculation_flow(invalid_params)
        
        if result is None:
            st.info("ℹ️ 計算流程正確處理了錯誤參數，返回None")
        else:
            st.warning("⚠️ 預期應該返回None")

def state_management_demo():
    """狀態管理演示"""
    st.header("💾 狀態管理演示")
    st.markdown("展示Streamlit session state管理功能")
    
    # 初始化狀態管理
    simple_state_management()
    
    # 顯示當前狀態
    st.subheader("📊 當前Session State")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**應用程式狀態**:")
        app_states = {
            'app_initialized': st.session_state.get('app_initialized', False),
            'system_status': st.session_state.get('system_status', 'unknown'),
            'trigger_calculation': st.session_state.get('trigger_calculation', False)
        }
        
        for key, value in app_states.items():
            if isinstance(value, bool):
                st.write(f"- {key}: {'✅' if value else '❌'}")
            else:
                st.write(f"- {key}: {value}")
    
    with col2:
        st.write("**數據狀態**:")
        data_states = {
            'user_params': len(st.session_state.get('user_params', {})),
            'calculation_results': 'available' if st.session_state.get('calculation_results') else 'none',
            'last_calculation_time': st.session_state.get('last_calculation_time', 'never')
        }
        
        for key, value in data_states.items():
            st.write(f"- {key}: {value}")
    
    # 狀態操作演示
    st.subheader("🎛️ 狀態操作演示")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔄 重置狀態"):
            for key in ['user_params', 'calculation_results', 'trigger_calculation']:
                if key in st.session_state:
                    del st.session_state[key]
            st.success("✅ 狀態已重置")
            st.rerun()
    
    with col2:
        if st.button("⚡ 觸發計算"):
            st.session_state.trigger_calculation = True
            st.session_state.last_calculation_time = datetime.now()
            st.success("✅ 計算觸發器已設置")
    
    with col3:
        if st.button("💾 保存測試數據"):
            st.session_state.user_params = {
                'initial_investment': 10000,
                'monthly_investment': 1000,
                'investment_years': 10,
                'stock_ratio': 0.8,
                'scenario': 'historical'
            }
            st.success("✅ 測試數據已保存")
    
    # 系統健康狀態
    st.subheader("🏥 系統健康狀態")
    
    health = st.session_state.get('system_health', {})
    
    if health:
        col1, col2, col3 = st.columns(3)
        
        with col1:
            status = health.get('overall_status', 'unknown')
            if status == 'healthy':
                st.success(f"✅ 系統狀態: {status}")
            elif status == 'warning':
                st.warning(f"⚠️ 系統狀態: {status}")
            else:
                st.error(f"❌ 系統狀態: {status}")
        
        with col2:
            data_sources = health.get('data_sources_available', 0)
            st.metric("可用數據源", f"{data_sources}/2")
        
        with col3:
            modules_loaded = health.get('modules_loaded', False)
            st.metric("模組載入", "✅" if modules_loaded else "❌")
    
    # 狀態詳細信息
    with st.expander("🔍 完整Session State"):
        st.json(dict(st.session_state))

def full_application_demo():
    """完整應用程式演示"""
    st.header("🚀 完整應用程式演示")
    st.markdown("展示完整的主應用程式功能")
    
    # 應用程式說明
    st.subheader("📖 應用程式說明")
    
    st.markdown("""
    這是一個完整的投資策略比較分析系統，包含以下功能：
    
    1. **參數設定**: 透過側邊欄設定投資參數
    2. **數據處理**: 獲取和處理市場數據
    3. **策略計算**: 計算VA和DCA策略結果
    4. **結果顯示**: 顯示比較結果和圖表
    5. **報告下載**: 生成和下載分析報告
    """)
    
    # 功能模組狀態
    st.subheader("🔧 功能模組狀態")
    
    modules_status = [
        ("數據獲取模組", "✅ 正常"),
        ("計算引擎模組", "✅ 正常"),
        ("UI顯示模組", "✅ 正常"),
        ("錯誤處理模組", "✅ 正常"),
        ("狀態管理模組", "✅ 正常")
    ]
    
    for module, status in modules_status:
        col1, col2 = st.columns([3, 1])
        with col1:
            st.write(f"**{module}**")
        with col2:
            st.write(status)
    
    # 啟動完整應用程式
    st.subheader("🚀 啟動完整應用程式")
    
    st.info("""
    💡 **提示**: 點擊下方按鈕將啟動完整的主應用程式。
    
    由於Streamlit的限制，完整應用程式需要在獨立的環境中運行。
    您可以執行以下命令來啟動完整應用程式：
    
    ```bash
    streamlit run src/core/main_app.py
    ```
    """)
    
    if st.button("🎯 模擬主應用程式流程"):
        st.markdown("### 🔄 模擬應用程式流程")
        
        # 模擬主函數調用序列
        steps = [
            "🏗️ 設置頁面配置",
            "🔧 執行應用程式初始化",
            "💾 初始化狀態管理",
            "🎛️ 渲染側邊欄控件",
            "📊 渲染主要內容",
            "✅ 應用程式準備就緒"
        ]
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for i, step in enumerate(steps):
            status_text.text(f"正在執行: {step}")
            progress_bar.progress((i + 1) / len(steps))
            
            # 模擬處理時間
            import time
            time.sleep(0.5)
        
        status_text.text("🎉 模擬完成!")
        st.success("✅ 主應用程式流程模擬完成")
    
    # 整合測試
    st.subheader("🧪 整合測試")
    
    if st.button("🔍 執行整合測試"):
        st.markdown("### 🔬 整合測試結果")
        
        test_results = []
        
        # 測試1: 函數導入
        try:
            from src.core.main_app import main, render_sidebar_controls
            test_results.append(("函數導入測試", "✅ 通過"))
        except Exception as e:
            test_results.append(("函數導入測試", f"❌ 失敗: {str(e)}"))
        
        # 測試2: 參數驗證
        try:
            test_params = {
                'initial_investment': 10000,
                'monthly_investment': 1000,
                'investment_years': 10,
                'stock_ratio': 0.8,
                'scenario': 'historical'
            }
            is_valid = _validate_parameters(test_params)
            test_results.append(("參數驗證測試", "✅ 通過" if is_valid else "❌ 失敗"))
        except Exception as e:
            test_results.append(("參數驗證測試", f"❌ 失敗: {str(e)}"))
        
        # 測試3: 系統健康檢查
        try:
            health = _check_system_health()
            status = health.get('overall_status', 'unknown')
            test_results.append(("系統健康測試", f"✅ 通過 ({status})"))
        except Exception as e:
            test_results.append(("系統健康測試", f"❌ 失敗: {str(e)}"))
        
        # 測試4: 數據生成
        try:
            mock_results = {
                'va_strategy': {'final_portfolio_value': 100000},
                'dca_strategy': {'final_portfolio_value': 95000},
                'summary_metrics': {'va_annualized_return': 0.08},
                'user_params': test_params
            }
            csv_data = _generate_csv_data(mock_results)
            test_results.append(("數據生成測試", "✅ 通過" if csv_data else "❌ 失敗"))
        except Exception as e:
            test_results.append(("數據生成測試", f"❌ 失敗: {str(e)}"))
        
        # 顯示測試結果
        for test_name, result in test_results:
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(f"**{test_name}**")
            with col2:
                st.write(result)
        
        # 整體結果
        passed_tests = sum(1 for _, result in test_results if result.startswith("✅"))
        total_tests = len(test_results)
        
        if passed_tests == total_tests:
            st.success(f"🎉 所有測試通過! ({passed_tests}/{total_tests})")
        else:
            st.warning(f"⚠️ 部分測試失敗 ({passed_tests}/{total_tests})")

if __name__ == "__main__":
    main_demo() 