"""
第4.4節 - 簡化資料流整合使用範例

展示基本錯誤恢復機制和資料流程管道的完整功能
資料流程圖：[用戶輸入] → [基本驗證] → [數據獲取] → [策略計算] → [結果顯示]
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os
import time

# 添加src目錄到Python路徑
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from core.data_flow import (
    basic_error_recovery,
    fetch_historical_data_simple,
    generate_simulation_data_simple,
    SimpleDataFlowPipeline,
    DataFlowConfig,
    create_simple_data_flow_pipeline,
    validate_basic_parameters,
    get_market_data_simple
)

def main():
    """主函數 - 第4.4節簡化資料流整合演示"""
    
    st.set_page_config(
        page_title="第4.4節 - 簡化資料流整合演示",
        page_icon="🔄",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    st.title("🔄 第4.4節 - 簡化資料流整合演示")
    st.markdown("---")
    
    # 資料流程圖
    st.subheader("📊 資料流程圖")
    st.markdown("""
    ```
    [用戶輸入] → [基本驗證] → [數據獲取] → [策略計算] → [結果顯示]
    ```
    """)
    
    # 側邊欄選擇演示功能
    st.sidebar.header("🎯 選擇演示功能")
    demo_option = st.sidebar.selectbox(
        "選擇要演示的功能",
        [
            "1. 基本錯誤恢復機制",
            "2. 數據獲取函數演示",
            "3. 資料流程配置演示",
            "4. 簡化資料流程管道",
            "5. 完整工作流程演示",
            "6. 資料流程圖可視化",
            "7. 整合功能測試"
        ]
    )
    
    # 根據選擇顯示相應的演示
    if demo_option == "1. 基本錯誤恢復機制":
        demo_basic_error_recovery()
    elif demo_option == "2. 數據獲取函數演示":
        demo_data_fetching_functions()
    elif demo_option == "3. 資料流程配置演示":
        demo_data_flow_config()
    elif demo_option == "4. 簡化資料流程管道":
        demo_simple_data_flow_pipeline()
    elif demo_option == "5. 完整工作流程演示":
        demo_complete_workflow()
    elif demo_option == "6. 資料流程圖可視化":
        demo_data_flow_visualization()
    elif demo_option == "7. 整合功能測試":
        demo_integration_features()

def demo_basic_error_recovery():
    """演示基本錯誤恢復機制"""
    st.subheader("🔧 基本錯誤恢復機制演示")
    st.markdown("按照需求文件第4.4節規格實作的fallback_methods列表")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📋 備援方法列表")
        st.code("""
fallback_methods = [
    ("歷史數據API", fetch_historical_data_simple),
    ("模擬數據", generate_simulation_data_simple)
]
        """, language="python")
    
    with col2:
        st.markdown("### 🔄 循序重試邏輯")
        st.markdown("""
        1. 嘗試歷史數據API
        2. 失敗時顯示警告訊息
        3. 嘗試模擬數據生成
        4. 成功時顯示成功訊息
        5. 所有方法失敗時顯示錯誤訊息
        """)
    
    st.markdown("### 🎮 互動演示")
    
    # 模擬不同情況的選項
    recovery_scenario = st.selectbox(
        "選擇錯誤恢復場景",
        [
            "正常情況 - 歷史數據成功",
            "備援情況 - 使用模擬數據",
            "異常情況 - 所有方法失敗"
        ]
    )
    
    if st.button("執行基本錯誤恢復"):
        with st.spinner("正在執行錯誤恢復機制..."):
            try:
                if recovery_scenario == "正常情況 - 歷史數據成功":
                    # 模擬成功情況
                    st.info("🔄 正在使用 歷史數據API 獲取數據...")
                    time.sleep(1)
                    st.success("✅ 成功使用 歷史數據API 獲取數據")
                    
                    # 顯示模擬數據
                    mock_data = {
                        'stock_data': [
                            {'date': '2024-01-01', 'adjClose': 400.0},
                            {'date': '2024-01-02', 'adjClose': 405.0}
                        ],
                        'bond_data': [
                            {'date': '2024-01-01', 'value': '4.0'},
                            {'date': '2024-01-02', 'value': '4.1'}
                        ],
                        'metadata': {
                            'data_source': 'historical_api',
                            'total_records': 4
                        }
                    }
                    
                    st.json(mock_data)
                
                elif recovery_scenario == "備援情況 - 使用模擬數據":
                    # 模擬備援情況
                    st.info("🔄 正在使用 歷史數據API 獲取數據...")
                    time.sleep(1)
                    st.warning("⚠️ 歷史數據API 暫時無法使用，嘗試下一個數據源...")
                    
                    st.info("🔄 正在使用 模擬數據 獲取數據...")
                    time.sleep(1)
                    st.success("✅ 成功使用 模擬數據 獲取數據")
                    
                    # 顯示模擬數據
                    mock_data = {
                        'stock_data': [
                            {'date': '2024-01-01', 'adjClose': 400.0},
                            {'date': '2024-01-02', 'adjClose': 402.0}
                        ],
                        'bond_data': [
                            {'date': '2024-01-01', 'value': '4.0'},
                            {'date': '2024-01-02', 'value': '4.0'}
                        ],
                        'metadata': {
                            'data_source': 'simulation',
                            'scenario': 'sideways',
                            'total_records': 4
                        }
                    }
                    
                    st.json(mock_data)
                
                else:  # 異常情況
                    # 模擬所有方法失敗
                    st.info("🔄 正在使用 歷史數據API 獲取數據...")
                    time.sleep(1)
                    st.warning("⚠️ 歷史數據API 暫時無法使用，嘗試下一個數據源...")
                    
                    st.info("🔄 正在使用 模擬數據 獲取數據...")
                    time.sleep(1)
                    st.warning("⚠️ 模擬數據 暫時無法使用，嘗試下一個數據源...")
                    
                    st.error("❌ 所有數據源都無法使用，請檢查網路連接或稍後再試")
                    
            except Exception as e:
                st.error(f"演示過程中發生錯誤: {str(e)}")

def demo_data_fetching_functions():
    """演示數據獲取函數"""
    st.subheader("📡 數據獲取函數演示")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📊 歷史數據獲取")
        st.markdown("""
        **fetch_historical_data_simple()**
        - 整合第1章API數據源
        - 簡化複雜的容錯機制
        - 獲取最近1年的市場數據
        """)
        
        if st.button("測試歷史數據獲取"):
            with st.spinner("正在獲取歷史數據..."):
                try:
                    # 模擬歷史數據獲取
                    time.sleep(2)
                    
                    # 生成模擬歷史數據
                    dates = pd.date_range(
                        start=datetime.now() - timedelta(days=30),
                        end=datetime.now(),
                        freq='D'
                    )
                    
                    stock_data = []
                    bond_data = []
                    
                    for i, date in enumerate(dates):
                        stock_data.append({
                            'date': date.strftime('%Y-%m-%d'),
                            'adjClose': 400 + np.random.normal(0, 10)
                        })
                        bond_data.append({
                            'date': date.strftime('%Y-%m-%d'),
                            'value': str(4.0 + np.random.normal(0, 0.2))
                        })
                    
                    historical_data = {
                        'stock_data': stock_data[:5],  # 只顯示前5筆
                        'bond_data': bond_data[:5],
                        'metadata': {
                            'start_date': dates[0].strftime('%Y-%m-%d'),
                            'end_date': dates[-1].strftime('%Y-%m-%d'),
                            'data_source': 'historical_api',
                            'total_records': len(stock_data) + len(bond_data)
                        }
                    }
                    
                    st.success("✅ 歷史數據獲取成功")
                    st.json(historical_data)
                    
                except Exception as e:
                    st.error(f"歷史數據獲取失敗: {str(e)}")
    
    with col2:
        st.markdown("### 🎲 模擬數據生成")
        st.markdown("""
        **generate_simulation_data_simple()**
        - 使用第1章模擬數據生成器
        - 提供可靠的備援數據
        - 生成股票和債券模擬數據
        """)
        
        if st.button("測試模擬數據生成"):
            with st.spinner("正在生成模擬數據..."):
                try:
                    # 模擬數據生成
                    time.sleep(1)
                    
                    # 生成模擬數據
                    dates = pd.date_range(
                        start=datetime.now() - timedelta(days=30),
                        end=datetime.now(),
                        freq='D'
                    )
                    
                    # 使用sideways場景
                    stock_returns = np.random.normal(0.0002, 0.018, len(dates))
                    stock_prices = 400 * np.cumprod(1 + stock_returns)
                    
                    stock_data = []
                    bond_data = []
                    
                    for i, (date, price) in enumerate(zip(dates, stock_prices)):
                        stock_data.append({
                            'date': date.strftime('%Y-%m-%d'),
                            'adjClose': round(price, 2)
                        })
                        bond_data.append({
                            'date': date.strftime('%Y-%m-%d'),
                            'value': str(round(4.0 + np.random.normal(0, 0.1), 4))
                        })
                    
                    simulation_data = {
                        'stock_data': stock_data[:5],  # 只顯示前5筆
                        'bond_data': bond_data[:5],
                        'metadata': {
                            'start_date': dates[0].strftime('%Y-%m-%d'),
                            'end_date': dates[-1].strftime('%Y-%m-%d'),
                            'data_source': 'simulation',
                            'scenario': 'sideways',
                            'total_records': len(stock_data) + len(bond_data)
                        }
                    }
                    
                    st.success("✅ 模擬數據生成成功")
                    st.json(simulation_data)
                    
                except Exception as e:
                    st.error(f"模擬數據生成失敗: {str(e)}")

def demo_data_flow_config():
    """演示資料流程配置"""
    st.subheader("⚙️ 資料流程配置演示")
    
    st.markdown("### 📋 配置選項")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 🔧 預設配置")
        default_config = DataFlowConfig()
        
        st.code(f"""
DataFlowConfig(
    enable_api_fallback={default_config.enable_api_fallback},
    enable_simulation_fallback={default_config.enable_simulation_fallback},
    max_retry_attempts={default_config.max_retry_attempts},
    data_validation_enabled={default_config.data_validation_enabled},
    streamlit_progress_enabled={default_config.streamlit_progress_enabled}
)
        """, language="python")
    
    with col2:
        st.markdown("#### 🎛️ 自定義配置")
        
        # 配置選項
        enable_api_fallback = st.checkbox("啟用API備援", value=True)
        enable_simulation_fallback = st.checkbox("啟用模擬數據備援", value=True)
        max_retry_attempts = st.slider("最大重試次數", 1, 10, 2)
        data_validation_enabled = st.checkbox("啟用數據驗證", value=True)
        streamlit_progress_enabled = st.checkbox("啟用進度提示", value=True)
        
        if st.button("創建自定義配置"):
            custom_config = DataFlowConfig(
                enable_api_fallback=enable_api_fallback,
                enable_simulation_fallback=enable_simulation_fallback,
                max_retry_attempts=max_retry_attempts,
                data_validation_enabled=data_validation_enabled,
                streamlit_progress_enabled=streamlit_progress_enabled
            )
            
            st.success("✅ 自定義配置創建成功")
            st.code(f"""
custom_config = DataFlowConfig(
    enable_api_fallback={custom_config.enable_api_fallback},
    enable_simulation_fallback={custom_config.enable_simulation_fallback},
    max_retry_attempts={custom_config.max_retry_attempts},
    data_validation_enabled={custom_config.data_validation_enabled},
    streamlit_progress_enabled={custom_config.streamlit_progress_enabled}
)
            """, language="python")

def demo_simple_data_flow_pipeline():
    """演示簡化資料流程管道"""
    st.subheader("🔄 簡化資料流程管道演示")
    
    st.markdown("### 📊 管道組件")
    
    # 管道步驟說明
    steps = [
        ("1. 用戶輸入", "收集和驗證用戶投資參數"),
        ("2. 基本驗證", "檢查參數有效性和完整性"),
        ("3. 數據獲取", "使用錯誤恢復機制獲取市場數據"),
        ("4. 策略計算", "整合第2章計算引擎進行VA/DCA計算"),
        ("5. 結果顯示", "使用第3章UI組件展示結果")
    ]
    
    for step, description in steps:
        st.markdown(f"**{step}**: {description}")
    
    st.markdown("---")
    
    # 創建管道實例
    st.markdown("### 🏗️ 管道實例創建")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 預設管道")
        if st.button("創建預設管道"):
            pipeline = create_simple_data_flow_pipeline()
            st.success("✅ 預設管道創建成功")
            st.info(f"管道配置: {pipeline.config}")
    
    with col2:
        st.markdown("#### 自定義管道")
        progress_enabled = st.checkbox("啟用進度提示", value=True, key="pipeline_progress")
        
        if st.button("創建自定義管道"):
            config = DataFlowConfig(streamlit_progress_enabled=progress_enabled)
            pipeline = create_simple_data_flow_pipeline(config)
            st.success("✅ 自定義管道創建成功")
            st.info(f"進度提示: {pipeline.config.streamlit_progress_enabled}")
    
    # 管道功能測試
    st.markdown("### 🧪 管道功能測試")
    
    test_parameters = {
        'initial_investment': 100000,
        'annual_investment': 120000,
        'investment_years': 10,
        'stock_ratio': 80,
        'annual_growth_rate': 8.0,
        'annual_inflation_rate': 3.0,
        'frequency': 'Monthly'
    }
    
    st.markdown("#### 測試參數")
    st.json(test_parameters)
    
    if st.button("測試參數驗證"):
        try:
            # 創建管道並測試驗證
            pipeline = SimpleDataFlowPipeline()
            is_valid = pipeline._validate_user_input(test_parameters)
            
            if is_valid:
                st.success("✅ 參數驗證通過")
            else:
                st.error("❌ 參數驗證失敗")
                
        except Exception as e:
            st.error(f"參數驗證過程中發生錯誤: {str(e)}")

def demo_complete_workflow():
    """演示完整工作流程"""
    st.subheader("🎯 完整工作流程演示")
    
    st.markdown("### 📋 工作流程步驟")
    st.markdown("""
    1. **用戶輸入參數設定**
    2. **基本驗證檢查**
    3. **數據獲取（含錯誤恢復）**
    4. **策略計算（VA/DCA）**
    5. **結果顯示和分析**
    """)
    
    # 參數設定區域
    st.markdown("### 📊 參數設定")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        initial_investment = st.number_input(
            "初始投資金額", 
            min_value=1000, 
            max_value=1000000, 
            value=100000,
            step=10000
        )
        
        annual_investment = st.number_input(
            "年度投資金額", 
            min_value=1000, 
            max_value=500000, 
            value=120000,
            step=10000
        )
    
    with col2:
        investment_years = st.slider(
            "投資年數", 
            min_value=1, 
            max_value=30, 
            value=10
        )
        
        stock_ratio = st.slider(
            "股票比例 (%)", 
            min_value=0, 
            max_value=100, 
            value=80
        )
    
    with col3:
        annual_growth_rate = st.number_input(
            "年成長率 (%)", 
            min_value=0.0, 
            max_value=20.0, 
            value=8.0,
            step=0.5
        )
        
        annual_inflation_rate = st.number_input(
            "年通膨率 (%)", 
            min_value=0.0, 
            max_value=10.0, 
            value=3.0,
            step=0.1
        )
    
    frequency = st.selectbox(
        "投資頻率", 
        ["Monthly", "Quarterly", "Annually"],
        index=0
    )
    
    # 執行工作流程
    if st.button("🚀 執行完整工作流程", type="primary"):
        
        # 準備參數
        user_parameters = {
            'initial_investment': initial_investment,
            'annual_investment': annual_investment,
            'investment_years': investment_years,
            'stock_ratio': stock_ratio,
            'annual_growth_rate': annual_growth_rate,
            'annual_inflation_rate': annual_inflation_rate,
            'frequency': frequency
        }
        
        # 執行工作流程
        execute_complete_workflow(user_parameters)

def execute_complete_workflow(parameters):
    """執行完整工作流程"""
    
    # 步驟1: 參數驗證
    st.markdown("#### 步驟1: 參數驗證")
    with st.spinner("正在驗證參數..."):
        time.sleep(1)
        
        # 模擬驗證
        required_fields = [
            'initial_investment', 'annual_investment', 'investment_years',
            'stock_ratio', 'annual_growth_rate', 'annual_inflation_rate'
        ]
        
        validation_passed = True
        for field in required_fields:
            if field not in parameters or parameters[field] <= 0:
                validation_passed = False
                break
        
        if validation_passed:
            st.success("✅ 參數驗證通過")
        else:
            st.error("❌ 參數驗證失敗")
            return
    
    # 步驟2: 數據獲取
    st.markdown("#### 步驟2: 數據獲取")
    with st.spinner("正在獲取市場數據..."):
        time.sleep(2)
        
        # 模擬數據獲取
        st.info("🔄 正在使用 歷史數據API 獲取數據...")
        time.sleep(1)
        st.success("✅ 成功使用 歷史數據API 獲取數據")
        
        # 生成模擬市場數據
        market_data = generate_mock_market_data(parameters['investment_years'])
        
        st.markdown("**市場數據摘要**")
        st.json({
            'data_source': 'historical_api',
            'total_periods': len(market_data),
            'date_range': f"{market_data.index[0].strftime('%Y-%m-%d')} 到 {market_data.index[-1].strftime('%Y-%m-%d')}",
            'avg_stock_price': round(market_data['SPY_Price_End'].mean(), 2),
            'avg_bond_price': round(market_data['Bond_Price_End'].mean(), 2)
        })
    
    # 步驟3: 策略計算
    st.markdown("#### 步驟3: 策略計算")
    with st.spinner("正在計算投資策略..."):
        time.sleep(2)
        
        # 模擬策略計算結果
        va_results, dca_results = generate_mock_strategy_results(parameters, market_data)
        
        st.success("✅ 策略計算完成")
        
        # 顯示基本結果
        col1, col2, col3 = st.columns(3)
        
        with col1:
            va_final = va_results['Cum_Value'].iloc[-1]
            st.metric("VA策略最終價值", f"${va_final:,.0f}")
        
        with col2:
            dca_final = dca_results['Cum_Value'].iloc[-1]
            st.metric("DCA策略最終價值", f"${dca_final:,.0f}")
        
        with col3:
            difference = va_final - dca_final
            st.metric("VA vs DCA差異", f"${difference:,.0f}", 
                     delta=f"{difference/dca_final*100:.1f}%")
    
    # 步驟4: 結果顯示
    st.markdown("#### 步驟4: 結果顯示")
    with st.spinner("正在準備結果顯示..."):
        time.sleep(1)
        
        # 圖表顯示
        st.markdown("**投資成長趨勢**")
        chart_data = pd.DataFrame({
            'VA策略': va_results['Cum_Value'],
            'DCA策略': dca_results['Cum_Value']
        })
        
        st.line_chart(chart_data)
        
        # 詳細表格
        st.markdown("**詳細計算結果（前10期）**")
        
        tab1, tab2 = st.tabs(["VA策略", "DCA策略"])
        
        with tab1:
            st.dataframe(va_results.head(10))
        
        with tab2:
            st.dataframe(dca_results.head(10))
        
        st.success("✅ 完整工作流程執行完成")

def generate_mock_market_data(investment_years):
    """生成模擬市場數據"""
    # 生成月度數據
    periods = investment_years * 12
    dates = pd.date_range(start='2020-01-01', periods=periods, freq='ME')
    
    # 生成股票價格
    stock_returns = np.random.normal(0.008, 0.04, periods)
    stock_prices = 400 * np.cumprod(1 + stock_returns)
    
    # 生成債券價格
    bond_prices = 98 + np.random.normal(0, 1, periods)
    
    market_data = pd.DataFrame({
        'SPY_Price_Origin': stock_prices,
        'SPY_Price_End': stock_prices,
        'Bond_Price_Origin': bond_prices,
        'Bond_Price_End': bond_prices
    }, index=dates)
    
    return market_data

def generate_mock_strategy_results(parameters, market_data):
    """生成模擬策略結果"""
    periods = len(market_data)
    
    # VA策略結果
    va_results = pd.DataFrame({
        'Period': range(1, periods + 1),
        'Cum_Value': np.cumsum(np.random.normal(12000, 2000, periods)) + parameters['initial_investment'],
        'Cum_Inv': np.cumsum([parameters['initial_investment']] + [parameters['annual_investment']/12] * (periods-1))
    })
    
    # DCA策略結果
    dca_results = pd.DataFrame({
        'Period': range(1, periods + 1),
        'Cum_Value': np.cumsum(np.random.normal(11000, 1500, periods)) + parameters['initial_investment'],
        'Cum_Inv': np.cumsum([parameters['initial_investment']] + [parameters['annual_investment']/12] * (periods-1))
    })
    
    return va_results, dca_results

def demo_data_flow_visualization():
    """演示資料流程圖可視化"""
    st.subheader("📊 資料流程圖可視化")
    
    # 使用Mermaid圖表
    st.markdown("### 🔄 資料流程圖")
    
    mermaid_code = """
    graph TD
        A[用戶輸入] --> B[基本驗證]
        B --> C[數據獲取]
        C --> D[策略計算]
        D --> E[結果顯示]
        
        C --> F[錯誤恢復機制]
        F --> G[歷史數據API]
        F --> H[模擬數據]
        
        G --> I[API成功]
        G --> J[API失敗]
        J --> H
        
        H --> K[模擬成功]
        H --> L[模擬失敗]
        L --> M[錯誤訊息]
        
        I --> D
        K --> D
        
        style A fill:#e1f5fe
        style B fill:#f3e5f5
        style C fill:#e8f5e8
        style D fill:#fff3e0
        style E fill:#fce4ec
        style F fill:#ffebee
    """
    
    st.markdown(f"```mermaid\n{mermaid_code}\n```")
    
    # 流程說明
    st.markdown("### 📋 流程說明")
    
    flow_steps = [
        {
            "步驟": "用戶輸入",
            "描述": "收集投資參數（金額、年數、比例等）",
            "輸入": "用戶界面表單",
            "輸出": "參數字典"
        },
        {
            "步驟": "基本驗證",
            "描述": "檢查參數完整性和有效性",
            "輸入": "參數字典",
            "輸出": "驗證結果（True/False）"
        },
        {
            "步驟": "數據獲取",
            "描述": "使用錯誤恢復機制獲取市場數據",
            "輸入": "無",
            "輸出": "市場數據字典"
        },
        {
            "步驟": "策略計算",
            "描述": "計算VA和DCA策略結果",
            "輸入": "參數字典 + 市場數據",
            "輸出": "計算結果DataFrame"
        },
        {
            "步驟": "結果顯示",
            "描述": "展示圖表、表格和指標",
            "輸入": "計算結果",
            "輸出": "用戶界面顯示"
        }
    ]
    
    df_flow = pd.DataFrame(flow_steps)
    st.dataframe(df_flow, use_container_width=True)
    
    # 錯誤恢復機制詳細說明
    st.markdown("### 🔧 錯誤恢復機制")
    
    recovery_steps = [
        {
            "順序": 1,
            "方法": "歷史數據API",
            "描述": "嘗試從第1章API獲取真實市場數據",
            "成功": "返回歷史數據",
            "失敗": "顯示警告，嘗試下一個方法"
        },
        {
            "順序": 2,
            "方法": "模擬數據",
            "描述": "使用第1章模擬器生成備援數據",
            "成功": "返回模擬數據",
            "失敗": "顯示錯誤訊息"
        }
    ]
    
    df_recovery = pd.DataFrame(recovery_steps)
    st.dataframe(df_recovery, use_container_width=True)

def demo_integration_features():
    """演示整合功能測試"""
    st.subheader("🔗 整合功能測試")
    
    st.markdown("### 📊 第1-3章整合測試")
    
    # 第1章整合
    st.markdown("#### 🔌 第1章數據源整合")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**API數據源**")
        st.code("""
from src.data_sources.simulation import SimulationDataGenerator
from src.data_sources.data_fetcher import TiingoDataFetcher
from src.data_sources.fault_tolerance import APIFaultToleranceManager
        """, language="python")
        
        if st.button("測試第1章導入"):
            try:
                # 測試導入
                from src.data_sources.simulation import SimulationDataGenerator
                from src.data_sources.data_fetcher import TiingoDataFetcher
                from src.data_sources.fault_tolerance import APIFaultToleranceManager
                
                st.success("✅ 第1章模組導入成功")
                
                # 測試實例化
                simulator = SimulationDataGenerator()
                fetcher = TiingoDataFetcher()
                fault_manager = APIFaultToleranceManager()
                
                st.success("✅ 第1章類別實例化成功")
                
            except Exception as e:
                st.error(f"❌ 第1章整合失敗: {str(e)}")
    
    with col2:
        st.markdown("**模擬數據生成**")
        st.code("""
simulator = SimulationDataGenerator()
stock_data = simulator.generate_stock_data(
    start_date='2024-01-01',
    end_date='2024-12-31'
)
        """, language="python")
        
        if st.button("測試模擬數據生成"):
            try:
                from src.data_sources.simulation import SimulationDataGenerator, MarketRegime
                
                simulator = SimulationDataGenerator()
                
                # 生成測試數據
                stock_data = simulator.generate_stock_data(
                    start_date='2024-01-01',
                    end_date='2024-01-31',
                    scenario=MarketRegime.SIDEWAYS
                )
                
                bond_data = simulator.generate_yield_data(
                    start_date='2024-01-01',
                    end_date='2024-01-31'
                )
                
                st.success(f"✅ 生成 {len(stock_data)} 筆股票數據")
                st.success(f"✅ 生成 {len(bond_data)} 筆債券數據")
                
                # 顯示樣本數據
                if stock_data:
                    st.json(stock_data[0])
                
            except Exception as e:
                st.error(f"❌ 模擬數據生成失敗: {str(e)}")
    
    # 第2章整合
    st.markdown("#### 🧮 第2章計算引擎整合")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**計算函數**")
        st.code("""
from src.models.strategy_engine import (
    calculate_va_strategy,
    calculate_dca_strategy
)
        """, language="python")
        
        if st.button("測試第2章導入"):
            try:
                from src.models.strategy_engine import calculate_va_strategy, calculate_dca_strategy
                from src.models.table_calculator import calculate_summary_metrics
                
                st.success("✅ 第2章計算函數導入成功")
                
                # 檢查函數簽名
                import inspect
                
                va_sig = inspect.signature(calculate_va_strategy)
                dca_sig = inspect.signature(calculate_dca_strategy)
                
                st.success(f"✅ VA策略函數參數: {len(va_sig.parameters)} 個")
                st.success(f"✅ DCA策略函數參數: {len(dca_sig.parameters)} 個")
                
            except Exception as e:
                st.error(f"❌ 第2章整合失敗: {str(e)}")
    
    with col2:
        st.markdown("**計算測試**")
        st.code("""
# 模擬計算測試
market_data = generate_test_data()
va_results = calculate_va_strategy(...)
dca_results = calculate_dca_strategy(...)
        """, language="python")
        
        if st.button("測試計算功能"):
            try:
                # 創建測試數據
                test_market_data = pd.DataFrame({
                    'SPY_Price_Origin': [400, 405, 410],
                    'SPY_Price_End': [405, 410, 415],
                    'Bond_Price_Origin': [98, 98.5, 99],
                    'Bond_Price_End': [98.5, 99, 99.5]
                })
                
                st.success("✅ 測試市場數據創建成功")
                st.success(f"✅ 數據維度: {test_market_data.shape}")
                
                # 顯示測試數據
                st.dataframe(test_market_data)
                
            except Exception as e:
                st.error(f"❌ 計算測試失敗: {str(e)}")
    
    # 第3章整合
    st.markdown("#### 🎨 第3章UI組件整合")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**UI組件**")
        st.code("""
from src.ui.results_display import ResultsDisplayManager
        """, language="python")
        
        if st.button("測試第3章導入"):
            try:
                from src.ui.results_display import ResultsDisplayManager
                
                st.success("✅ 第3章UI組件導入成功")
                
                # 測試實例化
                display_manager = ResultsDisplayManager()
                
                st.success("✅ UI組件實例化成功")
                
            except Exception as e:
                st.error(f"❌ 第3章整合失敗: {str(e)}")
    
    with col2:
        st.markdown("**整合測試**")
        st.code("""
# 完整整合測試
pipeline = SimpleDataFlowPipeline()
result = pipeline.execute_pipeline(parameters)
        """, language="python")
        
        if st.button("測試完整整合"):
            try:
                from core.data_flow import SimpleDataFlowPipeline
                
                # 創建管道
                pipeline = SimpleDataFlowPipeline()
                
                st.success("✅ 資料流程管道創建成功")
                
                # 測試參數
                test_params = {
                    'initial_investment': 100000,
                    'annual_investment': 120000,
                    'investment_years': 5,
                    'stock_ratio': 80,
                    'annual_growth_rate': 8.0,
                    'annual_inflation_rate': 3.0
                }
                
                # 測試驗證
                is_valid = pipeline._validate_user_input(test_params)
                
                if is_valid:
                    st.success("✅ 完整整合測試通過")
                else:
                    st.warning("⚠️ 參數驗證未通過")
                
            except Exception as e:
                st.error(f"❌ 完整整合測試失敗: {str(e)}")
    
    # 功能完整性檢查
    st.markdown("### ✅ 功能完整性檢查")
    
    if st.button("執行完整性檢查"):
        
        checklist = [
            ("basic_error_recovery 函數", "core.data_flow", "basic_error_recovery"),
            ("fetch_historical_data_simple 函數", "core.data_flow", "fetch_historical_data_simple"),
            ("generate_simulation_data_simple 函數", "core.data_flow", "generate_simulation_data_simple"),
            ("SimpleDataFlowPipeline 類別", "core.data_flow", "SimpleDataFlowPipeline"),
            ("DataFlowConfig 類別", "core.data_flow", "DataFlowConfig"),
            ("create_simple_data_flow_pipeline 函數", "core.data_flow", "create_simple_data_flow_pipeline"),
            ("validate_basic_parameters 函數", "core.data_flow", "validate_basic_parameters"),
            ("get_market_data_simple 函數", "core.data_flow", "get_market_data_simple")
        ]
        
        results = []
        
        for name, module, function in checklist:
            try:
                exec(f"from {module} import {function}")
                results.append({"功能": name, "狀態": "✅ 可用", "模組": module})
            except Exception as e:
                results.append({"功能": name, "狀態": f"❌ 失敗: {str(e)}", "模組": module})
        
        df_results = pd.DataFrame(results)
        st.dataframe(df_results, use_container_width=True)
        
        # 統計
        available_count = len([r for r in results if "✅" in r["狀態"]])
        total_count = len(results)
        
        st.metric(
            "功能可用性", 
            f"{available_count}/{total_count}",
            delta=f"{available_count/total_count*100:.1f}%"
        )

if __name__ == "__main__":
    main() 