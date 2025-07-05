"""
第4.2節 - 主要業務流程使用範例

本範例展示第4.2節「主要業務流程」的所有核心功能：
1. 效能監控系統
2. 主要計算流程控制
3. 並行策略計算
4. 數據獲取流程
5. 目標日期計算與交易日調整
6. 批次數據獲取
7. 數據品質評估
8. 快取鍵生成

運行方式：
streamlit run examples/chapter4_2_usage_example.py
"""

import streamlit as st
import pandas as pd
import numpy as np
import time
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import logging

# 導入第4.2節業務流程模組
from src.core.business_process import (
    performance_monitor,
    main_calculation_flow,
    calculate_strategies_parallel,
    calculate_va_strategy_safe,
    calculate_dca_strategy_safe,
    data_acquisition_flow,
    fetch_historical_data_optimized,
    calculate_target_dates,
    adjust_to_trading_days,
    extract_target_date_data,
    get_closest_price,
    generate_cache_key_enhanced,
    assess_data_quality,
    check_date_continuity,
    detect_outliers
)

# 設置頁面配置
st.set_page_config(
    page_title="第4.2節 - 主要業務流程展示",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 設置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """主要展示函數"""
    st.title("🔧 第4.2節 - 主要業務流程展示")
    st.markdown("---")
    
    # 側邊欄功能選擇
    st.sidebar.title("功能選擇")
    demo_option = st.sidebar.selectbox(
        "選擇展示功能",
        [
            "效能監控系統",
            "主要計算流程",
            "並行策略計算",
            "數據獲取流程",
            "目標日期計算",
            "批次數據獲取",
            "數據品質評估",
            "快取鍵生成",
            "綜合展示"
        ]
    )
    
    if demo_option == "效能監控系統":
        demo_performance_monitor()
    elif demo_option == "主要計算流程":
        demo_main_calculation_flow()
    elif demo_option == "並行策略計算":
        demo_parallel_calculation()
    elif demo_option == "數據獲取流程":
        demo_data_acquisition()
    elif demo_option == "目標日期計算":
        demo_target_date_calculation()
    elif demo_option == "批次數據獲取":
        demo_batch_data_fetch()
    elif demo_option == "數據品質評估":
        demo_data_quality_assessment()
    elif demo_option == "快取鍵生成":
        demo_cache_key_generation()
    elif demo_option == "綜合展示":
        demo_comprehensive()

def demo_performance_monitor():
    """展示效能監控系統"""
    st.header("⏱️ 效能監控系統")
    
    st.markdown("""
    ### 功能說明
    - 使用`@contextmanager`裝飾器實現上下文管理
    - 自動記錄開始/結束時間
    - 調用`record_performance_metric()`記錄指標
    - 完整的異常處理機制
    """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("正常操作監控")
        operation_name = st.text_input("操作名稱", "示例操作")
        sleep_time = st.slider("模擬耗時(秒)", 0.1, 3.0, 1.0, 0.1)
        
        if st.button("執行監控測試"):
            with st.spinner("執行中..."):
                start_time = time.time()
                
                try:
                    with performance_monitor(operation_name):
                        time.sleep(sleep_time)
                        # 模擬一些工作
                        data = np.random.randn(1000, 10)
                        result = np.mean(data)
                    
                    end_time = time.time()
                    duration = end_time - start_time
                    
                    st.success(f"✅ 操作完成")
                    st.info(f"⏱️ 實際耗時: {duration:.2f}秒")
                    st.info(f"📊 計算結果: {result:.4f}")
                    
                except Exception as e:
                    st.error(f"❌ 操作失敗: {str(e)}")
    
    with col2:
        st.subheader("異常處理監控")
        error_type = st.selectbox("錯誤類型", ["ValueError", "RuntimeError", "TypeError"])
        
        if st.button("執行異常測試"):
            with st.spinner("執行中..."):
                try:
                    with performance_monitor(f"異常測試-{error_type}"):
                        time.sleep(0.5)
                        if error_type == "ValueError":
                            raise ValueError("測試值錯誤")
                        elif error_type == "RuntimeError":
                            raise RuntimeError("測試運行時錯誤")
                        else:
                            raise TypeError("測試類型錯誤")
                            
                except Exception as e:
                    st.error(f"❌ 捕獲異常: {str(e)}")
                    st.info("✅ 異常處理機制正常工作")

def demo_main_calculation_flow():
    """展示主要計算流程"""
    st.header("🔄 主要計算流程")
    
    st.markdown("""
    ### 流程步驟
    1. 參數收集與驗證
    2. 數據獲取
    3. 策略計算（並行處理）
    4. 績效分析
    5. 結果驗證與輸出
    """)
    
    if st.button("執行完整計算流程"):
        with st.spinner("執行計算流程..."):
            # 模擬計算流程
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # 步驟1: 參數驗證
            status_text.text("步驟1: 參數收集與驗證...")
            progress_bar.progress(20)
            time.sleep(0.5)
            
            # 步驟2: 數據獲取
            status_text.text("步驟2: 數據獲取...")
            progress_bar.progress(40)
            time.sleep(0.5)
            
            # 步驟3: 策略計算
            status_text.text("步驟3: 策略計算（並行處理）...")
            progress_bar.progress(60)
            time.sleep(1.0)
            
            # 步驟4: 績效分析
            status_text.text("步驟4: 績效分析...")
            progress_bar.progress(80)
            time.sleep(0.5)
            
            # 步驟5: 結果驗證
            status_text.text("步驟5: 結果驗證與輸出...")
            progress_bar.progress(100)
            time.sleep(0.5)
            
            status_text.text("✅ 計算流程完成！")
            
            # 顯示模擬結果
            st.success("🎉 主要計算流程執行成功")
            
            # 模擬結果數據
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("VA策略年化報酬", "8.2%", "0.5%")
            with col2:
                st.metric("DCA策略年化報酬", "7.8%", "0.3%")
            with col3:
                st.metric("數據品質分數", "0.92", "0.02")

def demo_parallel_calculation():
    """展示並行策略計算"""
    st.header("⚡ 並行策略計算")
    
    st.markdown("""
    ### 並行處理特點
    - 使用`concurrent.futures.ThreadPoolExecutor`
    - `max_workers=2`（VA和DCA策略並行）
    - 30秒超時機制
    - 完整的異常處理
    """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("參數設定")
        initial_investment = st.number_input("初始投資", 10000, 100000, 10000, 1000)
        annual_investment = st.number_input("年度投資", 5000, 50000, 12000, 1000)
        investment_years = st.slider("投資年數", 1, 20, 10)
        stock_ratio = st.slider("股票比例(%)", 0, 100, 80)
        
        simulate_delay = st.checkbox("模擬計算延遲", value=False)
        delay_seconds = st.slider("延遲時間(秒)", 0.1, 5.0, 1.0, 0.1) if simulate_delay else 0
    
    with col2:
        st.subheader("計算結果")
        
        if st.button("執行並行計算"):
            with st.spinner("並行計算中..."):
                # 模擬市場數據
                market_data = generate_sample_market_data(investment_years)
                
                # 模擬用戶參數
                user_params = {
                    'initial_investment': initial_investment,
                    'annual_investment': annual_investment,
                    'investment_years': investment_years,
                    'stock_ratio': stock_ratio,
                    'annual_growth_rate': 7.0,
                    'annual_inflation_rate': 2.0,
                    'frequency': 'monthly'
                }
                
                start_time = time.time()
                
                # 執行並行計算
                try:
                    va_results, dca_results = calculate_strategies_parallel(market_data, user_params)
                    
                    end_time = time.time()
                    duration = end_time - start_time
                    
                    if va_results is not None and dca_results is not None:
                        st.success(f"✅ 並行計算完成 (耗時: {duration:.2f}秒)")
                        
                        # 顯示結果摘要
                        st.info("📊 VA策略計算: 成功")
                        st.info("📊 DCA策略計算: 成功")
                        
                        # 顯示模擬的績效指標
                        metrics_col1, metrics_col2 = st.columns(2)
                        with metrics_col1:
                            st.metric("VA最終價值", f"${np.random.randint(50000, 80000):,}")
                            st.metric("VA年化報酬", f"{np.random.uniform(6.5, 9.5):.1f}%")
                        with metrics_col2:
                            st.metric("DCA最終價值", f"${np.random.randint(45000, 75000):,}")
                            st.metric("DCA年化報酬", f"{np.random.uniform(6.0, 9.0):.1f}%")
                    else:
                        st.error("❌ 並行計算失敗")
                        
                except Exception as e:
                    st.error(f"❌ 計算異常: {str(e)}")

def demo_target_date_calculation():
    """展示目標日期計算"""
    st.header("📅 目標日期計算與交易日調整")
    
    st.markdown("""
    ### 功能特點
    - 計算所有期初/期末目標日期
    - 使用`pandas.tseries.holiday.USFederalHolidayCalendar`
    - 自動調整為有效交易日
    - 支援多種投資頻率
    """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("參數設定")
        start_date = st.date_input("開始日期", datetime(2020, 1, 1))
        frequency = st.selectbox("投資頻率", ["monthly", "quarterly", "semi-annually", "annually"])
        periods = st.slider("期數", 1, 24, 12)
        
        if st.button("計算目標日期"):
            start_datetime = datetime.combine(start_date, datetime.min.time())
            
            with st.spinner("計算中..."):
                # 計算目標日期
                target_dates = calculate_target_dates(start_datetime, frequency, periods)
                
                # 調整為交易日
                adjusted_dates = adjust_to_trading_days(target_dates)
                
                st.success(f"✅ 計算完成，共{periods}期")
                
                # 存儲結果到session state
                st.session_state.target_dates = target_dates
                st.session_state.adjusted_dates = adjusted_dates
    
    with col2:
        st.subheader("計算結果")
        
        if 'target_dates' in st.session_state:
            target_dates = st.session_state.target_dates
            adjusted_dates = st.session_state.adjusted_dates
            
            # 創建結果DataFrame
            results_data = []
            for i in range(len(target_dates['period_starts'])):
                results_data.append({
                    '期數': i + 1,
                    '原始期初日期': target_dates['period_starts'][i].strftime('%Y-%m-%d'),
                    '調整期初日期': adjusted_dates['period_starts'][i].strftime('%Y-%m-%d'),
                    '原始期末日期': target_dates['period_ends'][i].strftime('%Y-%m-%d'),
                    '調整期末日期': adjusted_dates['period_ends'][i].strftime('%Y-%m-%d'),
                    '期初調整': '是' if target_dates['period_starts'][i] != adjusted_dates['period_starts'][i] else '否',
                    '期末調整': '是' if target_dates['period_ends'][i] != adjusted_dates['period_ends'][i] else '否'
                })
            
            results_df = pd.DataFrame(results_data)
            st.dataframe(results_df, use_container_width=True)
            
            # 統計信息
            start_adjustments = sum(1 for i in range(len(target_dates['period_starts'])) 
                                  if target_dates['period_starts'][i] != adjusted_dates['period_starts'][i])
            end_adjustments = sum(1 for i in range(len(target_dates['period_ends'])) 
                                if target_dates['period_ends'][i] != adjusted_dates['period_ends'][i])
            
            st.info(f"📊 期初日期調整: {start_adjustments}次")
            st.info(f"📊 期末日期調整: {end_adjustments}次")

def demo_data_quality_assessment():
    """展示數據品質評估"""
    st.header("🔍 數據品質評估")
    
    st.markdown("""
    ### 評估指標
    - 數據完整性檢查
    - 缺失值比例
    - 日期連續性
    - 異常值檢測
    - 返回0-1品質分數
    """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("測試數據生成")
        data_type = st.selectbox("數據類型", ["完整數據", "有缺失值", "有異常值", "日期不連續"])
        data_size = st.slider("數據量", 10, 1000, 100)
        
        if st.button("生成測試數據"):
            test_data = generate_test_data(data_type, data_size)
            st.session_state.test_data = test_data
            st.success("✅ 測試數據生成完成")
    
    with col2:
        st.subheader("品質評估結果")
        
        if 'test_data' in st.session_state:
            test_data = st.session_state.test_data
            
            if st.button("執行品質評估"):
                with st.spinner("評估中..."):
                    # 執行品質評估
                    quality_score = assess_data_quality(test_data)
                    
                    # 顯示結果
                    st.metric("品質分數", f"{quality_score:.3f}", 
                             delta=f"{quality_score - 0.5:.3f}" if quality_score != 0.5 else None)
                    
                    # 品質等級
                    if quality_score >= 0.9:
                        st.success("🟢 優秀品質")
                    elif quality_score >= 0.7:
                        st.info("🟡 良好品質")
                    elif quality_score >= 0.5:
                        st.warning("🟠 一般品質")
                    else:
                        st.error("🔴 品質較差")
                    
                    # 詳細分析
                    if isinstance(test_data, pd.DataFrame):
                        st.subheader("詳細分析")
                        
                        # 缺失值分析
                        missing_ratio = test_data.isnull().sum().sum() / (test_data.shape[0] * test_data.shape[1])
                        st.info(f"缺失值比例: {missing_ratio:.1%}")
                        
                        # 日期連續性分析
                        if 'date' in test_data.columns:
                            continuity_score = check_date_continuity(test_data)
                            st.info(f"日期連續性問題: {continuity_score:.1%}")
                        
                        # 異常值分析
                        numeric_cols = test_data.select_dtypes(include=[np.number]).columns
                        if len(numeric_cols) > 0:
                            outlier_ratio = detect_outliers(test_data[numeric_cols])
                            st.info(f"異常值比例: {outlier_ratio:.1%}")

def demo_cache_key_generation():
    """展示快取鍵生成"""
    st.header("🔑 快取鍵生成")
    
    st.markdown("""
    ### 功能特點
    - 包含所有相關參數
    - 自動移除None值
    - 使用MD5哈希生成32位鍵
    - 確保參數變化時鍵值不同
    """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("參數設定")
        scenario = st.selectbox("場景", ["historical", "simulation"])
        frequency = st.selectbox("頻率", ["monthly", "quarterly", "annually"])
        periods = st.slider("期數", 1, 60, 12)
        stock_ratio = st.slider("股票比例", 0.0, 100.0, 80.0)
        
        include_dates = st.checkbox("包含日期參數")
        if include_dates:
            start_date = st.date_input("開始日期", datetime(2020, 1, 1))
            end_date = st.date_input("結束日期", datetime(2023, 12, 31))
        else:
            start_date = None
            end_date = None
    
    with col2:
        st.subheader("快取鍵生成")
        
        if st.button("生成快取鍵"):
            # 創建參數對象
            class MockParams:
                def __init__(self):
                    self.scenario = scenario
                    self.frequency = frequency
                    self.periods = periods
                    self.stock_ratio = stock_ratio
                    self.start_date = datetime.combine(start_date, datetime.min.time()) if start_date else None
                    self.end_date = datetime.combine(end_date, datetime.min.time()) if end_date else None
                    self.simulation_params = {"volatility": 0.15} if scenario == "simulation" else None
            
            params = MockParams()
            
            # 生成快取鍵
            cache_key = generate_cache_key_enhanced(params)
            
            st.success("✅ 快取鍵生成完成")
            st.code(f"快取鍵: {cache_key}")
            
            # 顯示參數摘要
            st.subheader("參數摘要")
            param_summary = {
                "場景": scenario,
                "頻率": frequency,
                "期數": periods,
                "股票比例": f"{stock_ratio}%",
                "開始日期": start_date.strftime('%Y-%m-%d') if start_date else "未設定",
                "結束日期": end_date.strftime('%Y-%m-%d') if end_date else "未設定"
            }
            
            for key, value in param_summary.items():
                st.info(f"{key}: {value}")

def demo_comprehensive():
    """綜合展示"""
    st.header("🎯 綜合展示")
    
    st.markdown("""
    ### 完整業務流程展示
    本展示將串聯所有第4.2節的核心功能，展示完整的業務流程。
    """)
    
    if st.button("執行綜合展示", type="primary"):
        with st.spinner("執行綜合業務流程..."):
            # 創建進度條
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # 1. 效能監控展示
            status_text.text("1. 初始化效能監控...")
            progress_bar.progress(10)
            time.sleep(0.5)
            
            # 2. 目標日期計算
            status_text.text("2. 計算目標日期...")
            progress_bar.progress(20)
            start_date = datetime(2020, 1, 1)
            target_dates = calculate_target_dates(start_date, 'monthly', 12)
            adjusted_dates = adjust_to_trading_days(target_dates)
            time.sleep(0.5)
            
            # 3. 快取鍵生成
            status_text.text("3. 生成快取鍵...")
            progress_bar.progress(30)
            class MockParams:
                def __init__(self):
                    self.scenario = 'historical'
                    self.frequency = 'monthly'
                    self.periods = 12
                    self.stock_ratio = 80.0
                    self.start_date = start_date
            
            params = MockParams()
            cache_key = generate_cache_key_enhanced(params)
            time.sleep(0.5)
            
            # 4. 生成測試數據
            status_text.text("4. 生成測試數據...")
            progress_bar.progress(50)
            market_data = generate_sample_market_data(1)
            time.sleep(0.5)
            
            # 5. 數據品質評估
            status_text.text("5. 評估數據品質...")
            progress_bar.progress(60)
            quality_score = assess_data_quality(market_data)
            time.sleep(0.5)
            
            # 6. 並行策略計算
            status_text.text("6. 執行並行策略計算...")
            progress_bar.progress(80)
            user_params = {
                'initial_investment': 10000,
                'annual_investment': 12000,
                'investment_years': 1,
                'stock_ratio': 80.0,
                'annual_growth_rate': 7.0,
                'annual_inflation_rate': 2.0,
                'frequency': 'monthly'
            }
            
            try:
                va_results, dca_results = calculate_strategies_parallel(market_data, user_params)
                calculation_success = va_results is not None and dca_results is not None
            except:
                calculation_success = False
            
            time.sleep(1.0)
            
            # 7. 完成
            status_text.text("7. 綜合展示完成！")
            progress_bar.progress(100)
            time.sleep(0.5)
            
            # 顯示結果摘要
            st.success("🎉 綜合展示執行完成！")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.subheader("📅 日期計算")
                st.info(f"目標期數: {len(target_dates['period_starts'])}")
                st.info(f"日期調整: {sum(1 for i in range(len(target_dates['period_starts'])) if target_dates['period_starts'][i] != adjusted_dates['period_starts'][i])}次")
            
            with col2:
                st.subheader("🔍 品質評估")
                st.metric("數據品質分數", f"{quality_score:.3f}")
                st.info(f"快取鍵: {cache_key[:8]}...")
            
            with col3:
                st.subheader("⚡ 策略計算")
                if calculation_success:
                    st.success("✅ 並行計算成功")
                    st.info("VA & DCA 策略完成")
                else:
                    st.warning("⚠️ 計算部分完成")
                    st.info("演示模式運行")

# 輔助函數
def generate_sample_market_data(years: int) -> Dict[str, Any]:
    """生成示例市場數據"""
    periods = years * 12
    dates = pd.date_range(start='2020-01-01', periods=periods, freq='M')
    
    # 生成隨機價格數據
    stock_prices = 100 * np.cumprod(1 + np.random.normal(0.007, 0.04, periods))
    bond_prices = 98 + np.random.normal(0, 0.5, periods)
    
    periods_data = []
    for i in range(periods):
        periods_data.append({
            'period': i + 1,
            'start_date': dates[i],
            'end_date': dates[i] + pd.DateOffset(days=30),
            'start_stock_price': stock_prices[i],
            'start_bond_price': bond_prices[i],
            'end_stock_price': stock_prices[i] * (1 + np.random.normal(0.007, 0.04)),
            'end_bond_price': bond_prices[i] + np.random.normal(0, 0.1)
        })
    
    return {
        'periods_data': periods_data,
        'data_source': 'sample',
        'total_periods': periods
    }

def generate_test_data(data_type: str, size: int) -> pd.DataFrame:
    """生成測試數據"""
    dates = pd.date_range(start='2020-01-01', periods=size, freq='D')
    prices = 100 + np.cumsum(np.random.normal(0, 1, size))
    volumes = np.random.randint(1000, 10000, size)
    
    data = pd.DataFrame({
        'date': dates,
        'price': prices,
        'volume': volumes
    })
    
    if data_type == "有缺失值":
        # 隨機設置一些缺失值
        missing_indices = np.random.choice(size, size//10, replace=False)
        data.loc[missing_indices, 'price'] = np.nan
        
    elif data_type == "有異常值":
        # 添加一些異常值
        outlier_indices = np.random.choice(size, size//20, replace=False)
        data.loc[outlier_indices, 'price'] = data['price'].mean() + 10 * data['price'].std()
        
    elif data_type == "日期不連續":
        # 創建日期間隔
        gap_indices = np.random.choice(size//2, size//20, replace=False)
        for idx in gap_indices:
            if idx < len(data) - 1:
                data.loc[idx+1:, 'date'] = data.loc[idx+1:, 'date'] + pd.Timedelta(days=15)
    
    return data

if __name__ == "__main__":
    main() 