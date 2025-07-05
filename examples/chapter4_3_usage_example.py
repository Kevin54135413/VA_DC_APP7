"""
第4.3節使用範例 - 狀態管理與快取策略 (State Management & Cache Strategy)

本範例展示第4.3節所有核心功能的實際應用：
1. CacheManager類別使用
2. 狀態管理演示
3. Streamlit快取函數演示
4. 智能快取管理演示
5. 快取統計監控
6. 綜合展示

運行方式：
streamlit run examples/chapter4_3_usage_example.py
"""

import streamlit as st
import pandas as pd
import numpy as np
import time
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# 添加項目根目錄到Python路徑
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# 導入第4.3節核心功能
from src.core.state_cache import (
    CacheManager,
    get_cache_manager,
    state_management,
    cached_market_data,
    cached_strategy_calculation,
    cached_performance_metrics,
    intelligent_cache_invalidation,
    cache_warming,
    get_cache_statistics
)

def main():
    """主函數"""
    st.set_page_config(
        page_title="第4.3節 - 狀態管理與快取策略演示",
        page_icon="🗄️",
        layout="wide"
    )
    
    st.title("🗄️ 第4.3節 - 狀態管理與快取策略演示")
    st.markdown("---")
    
    # 側邊欄選單
    demo_option = st.sidebar.selectbox(
        "選擇演示功能",
        [
            "1. CacheManager類別演示",
            "2. 狀態管理演示", 
            "3. Streamlit快取函數演示",
            "4. 智能快取管理演示",
            "5. 快取統計監控演示",
            "6. 快取預熱演示",
            "7. 綜合展示"
        ]
    )
    
    # 根據選擇顯示對應演示
    if demo_option.startswith("1."):
        demo_cache_manager()
    elif demo_option.startswith("2."):
        demo_state_management()
    elif demo_option.startswith("3."):
        demo_streamlit_cache_functions()
    elif demo_option.startswith("4."):
        demo_intelligent_cache_management()
    elif demo_option.startswith("5."):
        demo_cache_statistics()
    elif demo_option.startswith("6."):
        demo_cache_warming()
    elif demo_option.startswith("7."):
        demo_comprehensive()

def demo_cache_manager():
    """演示CacheManager類別"""
    st.header("1. CacheManager類別演示")
    st.markdown("展示CacheManager的初始化、統計記錄和命中率計算功能")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🔧 CacheManager操作")
        
        # 獲取快取管理器
        cache_manager = get_cache_manager()
        
        # 操作按鈕
        if st.button("記錄快取命中", key="hit"):
            cache_manager.record_hit()
            st.success("已記錄快取命中")
        
        if st.button("記錄快取未命中", key="miss"):
            cache_manager.record_miss()
            st.warning("已記錄快取未命中")
        
        if st.button("記錄快取驅逐", key="evict"):
            cache_manager.record_eviction()
            st.info("已記錄快取驅逐")
        
        # 更新快取大小
        cache_size = st.slider("設置快取大小 (MB)", 0.0, 500.0, 100.0, 5.0)
        if st.button("更新快取大小"):
            cache_manager.update_cache_size(cache_size)
            st.success(f"快取大小已更新為 {cache_size} MB")
        
        if st.button("重設統計"):
            cache_manager.reset_stats()
            st.success("統計已重設")
    
    with col2:
        st.subheader("📊 實時統計")
        
        # 顯示當前統計
        stats = cache_manager.cache_stats
        hit_ratio = cache_manager.get_cache_hit_ratio()
        
        # 創建指標卡片
        metric_col1, metric_col2, metric_col3 = st.columns(3)
        
        with metric_col1:
            st.metric("命中率", f"{hit_ratio:.1%}")
        
        with metric_col2:
            st.metric("總請求數", stats['total_requests'])
        
        with metric_col3:
            st.metric("快取大小", f"{stats['cache_size_mb']:.1f} MB")
        
        # 詳細統計表格
        st.markdown("**詳細統計**")
        stats_df = pd.DataFrame([
            {"指標": "命中數", "值": stats['hits']},
            {"指標": "未命中數", "值": stats['misses']},
            {"指標": "驅逐數", "值": stats['evictions']},
            {"指標": "總請求數", "值": stats['total_requests']},
            {"指標": "命中率", "值": f"{hit_ratio:.3f}"},
            {"指標": "最後清理時間", "值": stats['last_cleanup'][:19]}
        ])
        st.dataframe(stats_df, use_container_width=True)
        
        # 命中率圖表
        if stats['total_requests'] > 0:
            fig = go.Figure(data=go.Pie(
                labels=['命中', '未命中'],
                values=[stats['hits'], stats['misses']],
                hole=0.4
            ))
            fig.update_layout(title="快取命中率分布", height=300)
            st.plotly_chart(fig, use_container_width=True)

def demo_state_management():
    """演示狀態管理"""
    st.header("2. 狀態管理演示")
    st.markdown("展示Streamlit狀態管理和參數變更檢測功能")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("⚙️ 投資參數設置")
        
        # 投資參數輸入
        initial_investment = st.number_input(
            "期初投資金額", 
            min_value=1000, 
            max_value=1000000, 
            value=100000, 
            step=1000
        )
        
        annual_investment = st.number_input(
            "年度投資金額", 
            min_value=0, 
            max_value=100000, 
            value=12000, 
            step=1000
        )
        
        annual_growth_rate = st.slider(
            "年化成長率 (%)", 
            0.0, 
            20.0, 
            7.0, 
            0.1
        )
        
        investment_years = st.slider(
            "投資年數", 
            1, 
            30, 
            10
        )
        
        frequency = st.selectbox(
            "投資頻率",
            ["monthly", "quarterly", "annually"]
        )
        
        scenario = st.selectbox(
            "市場場景",
            ["historical", "bull_market", "bear_market", "sideways"]
        )
        
        # 觸發狀態管理
        if st.button("執行狀態管理檢查"):
            with st.spinner("檢查狀態管理..."):
                try:
                    # 模擬狀態管理
                    current_params = {
                        'initial_investment': initial_investment,
                        'annual_investment': annual_investment,
                        'annual_growth_rate': annual_growth_rate,
                        'investment_years': investment_years,
                        'frequency': frequency,
                        'scenario': scenario
                    }
                    
                    # 檢查參數變更
                    last_params = st.session_state.get('demo_last_params', None)
                    
                    if last_params != current_params:
                        st.success("✅ 檢測到參數變更")
                        st.session_state['demo_last_params'] = current_params
                        st.session_state['demo_calculation_results'] = {
                            'timestamp': datetime.now().isoformat(),
                            'params': current_params,
                            'status': 'calculated'
                        }
                    else:
                        st.info("ℹ️ 參數未變更，使用快取結果")
                        
                except Exception as e:
                    st.error(f"狀態管理錯誤: {str(e)}")
    
    with col2:
        st.subheader("📋 狀態信息")
        
        # 顯示當前會話狀態
        if 'demo_last_params' in st.session_state:
            st.markdown("**上次參數:**")
            last_params_df = pd.DataFrame([
                {"參數": k, "值": v} 
                for k, v in st.session_state['demo_last_params'].items()
            ])
            st.dataframe(last_params_df, use_container_width=True)
        
        if 'demo_calculation_results' in st.session_state:
            st.markdown("**計算結果:**")
            results = st.session_state['demo_calculation_results']
            st.json(results)
        
        # 顯示所有session_state鍵
        st.markdown("**Session State 鍵:**")
        state_keys = list(st.session_state.keys())
        st.write(f"共 {len(state_keys)} 個鍵: {', '.join(state_keys)}")

def demo_streamlit_cache_functions():
    """演示Streamlit快取函數"""
    st.header("3. Streamlit快取函數演示")
    st.markdown("展示cached_market_data、cached_strategy_calculation、cached_performance_metrics函數")
    
    tab1, tab2, tab3 = st.tabs(["市場數據快取", "策略計算快取", "績效指標快取"])
    
    with tab1:
        st.subheader("📈 市場數據快取演示")
        
        col1, col2 = st.columns([1, 2])
        
        with col1:
            start_date = st.date_input("開始日期", value=datetime(2023, 1, 1))
            end_date = st.date_input("結束日期", value=datetime(2023, 12, 31))
            scenario = st.selectbox("場景", ["historical", "bull_market", "bear_market"], key="market_scenario")
            
            if st.button("獲取市場數據", key="get_market_data"):
                with st.spinner("正在獲取市場數據..."):
                    start_time = time.time()
                    
                    # 調用快取函數
                    result = cached_market_data(
                        start_date.strftime('%Y-%m-%d'),
                        end_date.strftime('%Y-%m-%d'),
                        scenario
                    )
                    
                    end_time = time.time()
                    
                    if result:
                        st.success(f"✅ 數據獲取成功 (耗時: {end_time - start_time:.2f}秒)")
                        st.session_state['market_data_result'] = result
                    else:
                        st.error("❌ 數據獲取失敗")
        
        with col2:
            if 'market_data_result' in st.session_state:
                result = st.session_state['market_data_result']
                
                # 顯示基本信息
                st.markdown("**數據信息:**")
                info_df = pd.DataFrame([
                    {"項目": "數據來源", "值": result['data_source']},
                    {"項目": "快取時間", "值": result['cached_at'][:19]},
                    {"項目": "品質分數", "值": f"{result['quality_score']:.3f}"},
                    {"項目": "記錄數", "值": result['total_records']},
                    {"項目": "日期範圍", "值": result['date_range']}
                ])
                st.dataframe(info_df, use_container_width=True)
                
                # 繪製價格圖表
                if 'data' in result and 'stock_data' in result['data']:
                    stock_data = result['data']['stock_data']
                    dates = stock_data['dates'][:100]  # 限制顯示數量
                    prices = stock_data['prices'][:100]
                    
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(
                        x=dates, 
                        y=prices, 
                        mode='lines',
                        name='股票價格'
                    ))
                    fig.update_layout(
                        title="股票價格走勢",
                        xaxis_title="日期",
                        yaxis_title="價格",
                        height=300
                    )
                    st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        st.subheader("🎯 策略計算快取演示")
        
        col1, col2 = st.columns([1, 2])
        
        with col1:
            market_hash = st.text_input("市場數據哈希", value="market_hash_123", key="market_hash")
            params_hash = st.text_input("參數哈希", value="params_hash_456", key="params_hash")
            calc_type = st.selectbox("計算類型", ["va", "dca"], key="calc_type")
            
            if st.button("計算策略", key="calc_strategy"):
                with st.spinner("正在計算策略..."):
                    start_time = time.time()
                    
                    result = cached_strategy_calculation(
                        market_hash,
                        params_hash,
                        calc_type
                    )
                    
                    end_time = time.time()
                    
                    if result:
                        st.success(f"✅ 策略計算成功 (耗時: {end_time - start_time:.2f}秒)")
                        st.session_state['strategy_result'] = result
                    else:
                        st.error("❌ 策略計算失敗")
        
        with col2:
            if 'strategy_result' in st.session_state:
                result = st.session_state['strategy_result']
                
                # 顯示計算信息
                st.markdown("**計算信息:**")
                calc_info_df = pd.DataFrame([
                    {"項目": "計算類型", "值": result['calculation_type']},
                    {"項目": "計算時間", "值": result['calculated_at'][:19]},
                    {"項目": "計算耗時", "值": f"{result['calculation_duration']:.3f}秒"},
                    {"項目": "數據哈希", "值": result['data_hash'][:16] + "..."},
                    {"項目": "參數哈希", "值": result['params_hash'][:16] + "..."}
                ])
                st.dataframe(calc_info_df, use_container_width=True)
                
                # 顯示結果摘要
                if 'result_summary' in result and result['result_summary']:
                    st.markdown("**結果摘要:**")
                    summary = result['result_summary']
                    summary_df = pd.DataFrame([
                        {"指標": "策略類型", "值": summary['strategy_type']},
                        {"指標": "最終價值", "值": f"${summary['final_value']:,.2f}"},
                        {"指標": "總回報率", "值": f"{summary['total_return']:.2%}"},
                        {"指標": "期數", "值": summary['periods_count']}
                    ])
                    st.dataframe(summary_df, use_container_width=True)
    
    with tab3:
        st.subheader("📊 績效指標快取演示")
        
        col1, col2 = st.columns([1, 2])
        
        with col1:
            va_hash = st.text_input("VA策略哈希", value="va_hash_789", key="va_hash")
            dca_hash = st.text_input("DCA策略哈希", value="dca_hash_012", key="dca_hash")
            
            if st.button("計算績效指標", key="calc_metrics"):
                with st.spinner("正在計算績效指標..."):
                    start_time = time.time()
                    
                    result = cached_performance_metrics(va_hash, dca_hash)
                    
                    end_time = time.time()
                    
                    if result:
                        st.success(f"✅ 績效指標計算成功 (耗時: {end_time - start_time:.2f}秒)")
                        st.session_state['metrics_result'] = result
                    else:
                        st.error("❌ 績效指標計算失敗")
        
        with col2:
            if 'metrics_result' in st.session_state:
                result = st.session_state['metrics_result']
                
                # 顯示基本信息
                st.markdown("**計算信息:**")
                metrics_info_df = pd.DataFrame([
                    {"項目": "計算時間", "值": result['calculated_at'][:19]},
                    {"項目": "VA哈希", "值": result['va_hash'][:16] + "..."},
                    {"項目": "DCA哈希", "值": result['dca_hash'][:16] + "..."}
                ])
                st.dataframe(metrics_info_df, use_container_width=True)
                
                # 顯示績效比較
                if 'comparison_summary' in result and result['comparison_summary']:
                    st.markdown("**比較摘要:**")
                    comparison = result['comparison_summary']
                    comparison_df = pd.DataFrame([
                        {"指標": "較佳策略", "值": comparison['better_strategy']},
                        {"指標": "回報優勢", "值": f"{comparison['return_advantage']:.2%}"},
                        {"指標": "風險差異", "值": f"{comparison['risk_difference']:.2%}"}
                    ])
                    st.dataframe(comparison_df, use_container_width=True)

def demo_intelligent_cache_management():
    """演示智能快取管理"""
    st.header("4. 智能快取管理演示")
    st.markdown("展示intelligent_cache_invalidation功能")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🧹 快取清理操作")
        
        if st.button("執行智能快取失效", key="invalidate_cache"):
            with st.spinner("正在執行智能快取失效..."):
                start_time = time.time()
                
                try:
                    intelligent_cache_invalidation()
                    end_time = time.time()
                    
                    st.success(f"✅ 智能快取失效完成 (耗時: {end_time - start_time:.2f}秒)")
                    
                    # 記錄操作
                    if 'cache_operations' not in st.session_state:
                        st.session_state['cache_operations'] = []
                    
                    st.session_state['cache_operations'].append({
                        'operation': '智能快取失效',
                        'timestamp': datetime.now().isoformat(),
                        'duration': end_time - start_time,
                        'status': '成功'
                    })
                    
                except Exception as e:
                    st.error(f"❌ 智能快取失效失敗: {str(e)}")
                    
                    if 'cache_operations' not in st.session_state:
                        st.session_state['cache_operations'] = []
                    
                    st.session_state['cache_operations'].append({
                        'operation': '智能快取失效',
                        'timestamp': datetime.now().isoformat(),
                        'duration': 0,
                        'status': f'失敗: {str(e)}'
                    })
        
        # 手動清理特定快取
        st.markdown("**手動清理選項:**")
        
        if st.button("清理Streamlit快取"):
            if hasattr(st, 'cache_data'):
                st.cache_data.clear()
                st.success("Streamlit快取已清理")
        
        if st.button("重設快取管理器"):
            cache_manager = get_cache_manager()
            cache_manager.reset_stats()
            st.success("快取管理器已重設")
    
    with col2:
        st.subheader("📋 操作歷史")
        
        if 'cache_operations' in st.session_state:
            operations = st.session_state['cache_operations']
            
            if operations:
                # 顯示最近的操作
                st.markdown("**最近操作:**")
                recent_ops = operations[-5:]  # 顯示最近5次操作
                
                for i, op in enumerate(reversed(recent_ops)):
                    status_icon = "✅" if op['status'] == '成功' else "❌"
                    st.write(f"{status_icon} {op['operation']} - {op['timestamp'][:19]}")
                    if op['duration'] > 0:
                        st.write(f"   耗時: {op['duration']:.3f}秒")
                
                # 操作統計
                st.markdown("**操作統計:**")
                total_ops = len(operations)
                successful_ops = len([op for op in operations if op['status'] == '成功'])
                
                stats_df = pd.DataFrame([
                    {"指標": "總操作數", "值": total_ops},
                    {"指標": "成功操作數", "值": successful_ops},
                    {"指標": "成功率", "值": f"{successful_ops/total_ops:.1%}" if total_ops > 0 else "N/A"}
                ])
                st.dataframe(stats_df, use_container_width=True)
            else:
                st.info("暫無操作記錄")
        else:
            st.info("暫無操作記錄")

def demo_cache_statistics():
    """演示快取統計監控"""
    st.header("5. 快取統計監控演示")
    st.markdown("展示get_cache_statistics功能和實時監控")
    
    # 自動刷新選項
    auto_refresh = st.sidebar.checkbox("自動刷新 (5秒)", value=False)
    
    if auto_refresh:
        # 使用empty容器實現自動刷新
        placeholder = st.empty()
        
        # 刷新計數器
        if 'refresh_count' not in st.session_state:
            st.session_state['refresh_count'] = 0
        
        st.session_state['refresh_count'] += 1
        
        with placeholder.container():
            display_cache_statistics()
        
        # 5秒後重新運行
        time.sleep(5)
        st.rerun()
    else:
        display_cache_statistics()

def display_cache_statistics():
    """顯示快取統計"""
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 實時快取統計")
        
        if st.button("刷新統計", key="refresh_stats"):
            st.rerun()
        
        try:
            # 獲取快取統計
            stats = get_cache_statistics()
            
            # 關鍵指標
            metric_col1, metric_col2, metric_col3 = st.columns(3)
            
            with metric_col1:
                st.metric("命中率", f"{stats.get('hit_ratio', 0):.1%}")
            
            with metric_col2:
                st.metric("總請求數", stats.get('total_requests', 0))
            
            with metric_col3:
                st.metric("快取大小", f"{stats.get('cache_size_mb', 0):.1f} MB")
            
            # 詳細統計表格
            st.markdown("**詳細統計:**")
            detailed_stats = [
                {"指標": "總命中數", "值": stats.get('total_hits', 0)},
                {"指標": "總未命中數", "值": stats.get('total_misses', 0)},
                {"指標": "驅逐次數", "值": stats.get('evictions', 0)},
                {"指標": "記憶體條目數", "值": stats.get('memory_entries', 0)},
                {"指標": "磁碟條目數", "值": stats.get('disk_entries', 0)},
                {"指標": "總條目數", "值": stats.get('total_entries', 0)},
                {"指標": "快取使用率", "值": f"{stats.get('cache_usage_ratio', 0):.1%}"},
                {"指標": "快取效率", "值": f"{stats.get('cache_efficiency', 0):.3f}"},
                {"指標": "健康狀態", "值": stats.get('health_status', 'unknown')}
            ]
            
            stats_df = pd.DataFrame(detailed_stats)
            st.dataframe(stats_df, use_container_width=True)
            
        except Exception as e:
            st.error(f"獲取統計失敗: {str(e)}")
    
    with col2:
        st.subheader("📈 視覺化統計")
        
        try:
            stats = get_cache_statistics()
            
            # 命中率餅圖
            if stats.get('total_requests', 0) > 0:
                fig_pie = go.Figure(data=go.Pie(
                    labels=['命中', '未命中'],
                    values=[stats.get('total_hits', 0), stats.get('total_misses', 0)],
                    hole=0.4
                ))
                fig_pie.update_layout(title="快取命中率分布", height=300)
                st.plotly_chart(fig_pie, use_container_width=True)
            
            # 快取使用情況條形圖
            cache_usage_data = {
                '記憶體條目': stats.get('memory_entries', 0),
                '磁碟條目': stats.get('disk_entries', 0)
            }
            
            fig_bar = go.Figure(data=go.Bar(
                x=list(cache_usage_data.keys()),
                y=list(cache_usage_data.values())
            ))
            fig_bar.update_layout(title="快取條目分布", height=300)
            st.plotly_chart(fig_bar, use_container_width=True)
            
            # 健康狀態指示器
            health_status = stats.get('health_status', 'unknown')
            health_colors = {
                'excellent': 'green',
                'good': 'blue', 
                'fair': 'orange',
                'poor': 'red',
                'unknown': 'gray'
            }
            
            st.markdown(f"**快取健康狀態:** <span style='color: {health_colors.get(health_status, 'gray')}'>{health_status.upper()}</span>", unsafe_allow_html=True)
            
        except Exception as e:
            st.error(f"視覺化統計失敗: {str(e)}")

def demo_cache_warming():
    """演示快取預熱"""
    st.header("6. 快取預熱演示")
    st.markdown("展示cache_warming功能")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🔥 快取預熱操作")
        
        st.markdown("**預設預熱場景:**")
        scenarios = [
            ("2020-01-01", "2023-12-31", "historical"),
            ("2018-01-01", "2023-12-31", "historical")
        ]
        
        for i, (start, end, scenario) in enumerate(scenarios):
            st.write(f"{i+1}. {scenario}: {start} 到 {end}")
        
        if st.button("執行快取預熱", key="warm_cache"):
            with st.spinner("正在執行快取預熱..."):
                start_time = time.time()
                
                try:
                    # 執行快取預熱
                    cache_warming()
                    
                    end_time = time.time()
                    duration = end_time - start_time
                    
                    st.success(f"✅ 快取預熱完成 (耗時: {duration:.2f}秒)")
                    
                    # 記錄預熱操作
                    if 'warming_history' not in st.session_state:
                        st.session_state['warming_history'] = []
                    
                    st.session_state['warming_history'].append({
                        'timestamp': datetime.now().isoformat(),
                        'duration': duration,
                        'scenarios_count': len(scenarios),
                        'status': '成功'
                    })
                    
                except Exception as e:
                    st.error(f"❌ 快取預熱失敗: {str(e)}")
                    
                    if 'warming_history' not in st.session_state:
                        st.session_state['warming_history'] = []
                    
                    st.session_state['warming_history'].append({
                        'timestamp': datetime.now().isoformat(),
                        'duration': 0,
                        'scenarios_count': len(scenarios),
                        'status': f'失敗: {str(e)}'
                    })
        
        # 手動預熱選項
        st.markdown("**手動預熱:**")
        manual_start = st.date_input("開始日期", value=datetime(2022, 1, 1), key="manual_start")
        manual_end = st.date_input("結束日期", value=datetime(2022, 12, 31), key="manual_end")
        manual_scenario = st.selectbox("場景", ["historical", "bull_market", "bear_market"], key="manual_scenario")
        
        if st.button("手動預熱", key="manual_warm"):
            with st.spinner("正在手動預熱..."):
                try:
                    result = cached_market_data(
                        manual_start.strftime('%Y-%m-%d'),
                        manual_end.strftime('%Y-%m-%d'),
                        manual_scenario
                    )
                    
                    if result:
                        st.success("✅ 手動預熱成功")
                    else:
                        st.error("❌ 手動預熱失敗")
                        
                except Exception as e:
                    st.error(f"❌ 手動預熱失敗: {str(e)}")
    
    with col2:
        st.subheader("📋 預熱歷史")
        
        if 'warming_history' in st.session_state:
            history = st.session_state['warming_history']
            
            if history:
                # 顯示最近預熱記錄
                st.markdown("**最近預熱記錄:**")
                recent_history = history[-5:]
                
                for i, record in enumerate(reversed(recent_history)):
                    status_icon = "✅" if record['status'] == '成功' else "❌"
                    st.write(f"{status_icon} {record['timestamp'][:19]}")
                    st.write(f"   場景數: {record['scenarios_count']}")
                    if record['duration'] > 0:
                        st.write(f"   耗時: {record['duration']:.2f}秒")
                
                # 預熱統計
                st.markdown("**預熱統計:**")
                total_warmings = len(history)
                successful_warmings = len([h for h in history if h['status'] == '成功'])
                
                if successful_warmings > 0:
                    avg_duration = np.mean([h['duration'] for h in history if h['duration'] > 0])
                else:
                    avg_duration = 0
                
                warming_stats_df = pd.DataFrame([
                    {"指標": "總預熱次數", "值": total_warmings},
                    {"指標": "成功次數", "值": successful_warmings},
                    {"指標": "成功率", "值": f"{successful_warmings/total_warmings:.1%}" if total_warmings > 0 else "N/A"},
                    {"指標": "平均耗時", "值": f"{avg_duration:.2f}秒" if avg_duration > 0 else "N/A"}
                ])
                st.dataframe(warming_stats_df, use_container_width=True)
                
                # 預熱時間趨勢圖
                if len([h for h in history if h['duration'] > 0]) > 1:
                    durations = [h['duration'] for h in history if h['duration'] > 0]
                    timestamps = [h['timestamp'][:19] for h in history if h['duration'] > 0]
                    
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(
                        x=timestamps,
                        y=durations,
                        mode='lines+markers',
                        name='預熱耗時'
                    ))
                    fig.update_layout(
                        title="預熱耗時趨勢",
                        xaxis_title="時間",
                        yaxis_title="耗時 (秒)",
                        height=250
                    )
                    st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("暫無預熱記錄")
        else:
            st.info("暫無預熱記錄")

def demo_comprehensive():
    """綜合展示"""
    st.header("7. 綜合展示")
    st.markdown("展示第4.3節所有功能的完整工作流程")
    
    # 工作流程步驟
    steps = [
        "1. 初始化快取管理器",
        "2. 設置投資參數",
        "3. 執行狀態管理",
        "4. 獲取市場數據 (快取)",
        "5. 計算投資策略 (快取)",
        "6. 計算績效指標 (快取)",
        "7. 執行智能快取管理",
        "8. 顯示統計報告"
    ]
    
    st.markdown("**工作流程步驟:**")
    for step in steps:
        st.write(f"- {step}")
    
    if st.button("🚀 執行完整工作流程", key="comprehensive_demo"):
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            # 步驟1: 初始化快取管理器
            status_text.text("步驟1: 初始化快取管理器...")
            cache_manager = get_cache_manager()
            progress_bar.progress(12.5)
            time.sleep(0.5)
            
            # 步驟2: 設置投資參數
            status_text.text("步驟2: 設置投資參數...")
            params = {
                'initial_investment': 100000,
                'annual_investment': 12000,
                'annual_growth_rate': 7.0,
                'investment_years': 10,
                'frequency': 'monthly',
                'scenario': 'historical'
            }
            progress_bar.progress(25)
            time.sleep(0.5)
            
            # 步驟3: 執行狀態管理
            status_text.text("步驟3: 執行狀態管理...")
            st.session_state['comprehensive_params'] = params
            progress_bar.progress(37.5)
            time.sleep(0.5)
            
            # 步驟4: 獲取市場數據
            status_text.text("步驟4: 獲取市場數據...")
            market_data = cached_market_data("2020-01-01", "2023-12-31", "historical")
            progress_bar.progress(50)
            time.sleep(0.5)
            
            # 步驟5: 計算投資策略
            status_text.text("步驟5: 計算投資策略...")
            va_result = cached_strategy_calculation("market_hash", "params_hash", "va")
            dca_result = cached_strategy_calculation("market_hash", "params_hash", "dca")
            progress_bar.progress(62.5)
            time.sleep(0.5)
            
            # 步驟6: 計算績效指標
            status_text.text("步驟6: 計算績效指標...")
            metrics = cached_performance_metrics("va_hash", "dca_hash")
            progress_bar.progress(75)
            time.sleep(0.5)
            
            # 步驟7: 執行智能快取管理
            status_text.text("步驟7: 執行智能快取管理...")
            intelligent_cache_invalidation()
            progress_bar.progress(87.5)
            time.sleep(0.5)
            
            # 步驟8: 顯示統計報告
            status_text.text("步驟8: 生成統計報告...")
            stats = get_cache_statistics()
            progress_bar.progress(100)
            
            status_text.text("✅ 工作流程完成!")
            
            # 顯示結果摘要
            st.success("🎉 綜合展示完成!")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("快取命中率", f"{stats.get('hit_ratio', 0):.1%}")
            
            with col2:
                st.metric("總請求數", stats.get('total_requests', 0))
            
            with col3:
                st.metric("快取效率", f"{stats.get('cache_efficiency', 0):.3f}")
            
            # 詳細結果
            with st.expander("查看詳細結果"):
                tab1, tab2, tab3, tab4 = st.tabs(["參數", "市場數據", "策略結果", "快取統計"])
                
                with tab1:
                    st.json(params)
                
                with tab2:
                    if market_data:
                        st.write(f"數據來源: {market_data.get('data_source', 'N/A')}")
                        st.write(f"品質分數: {market_data.get('quality_score', 0):.3f}")
                        st.write(f"記錄數: {market_data.get('total_records', 0)}")
                
                with tab3:
                    if va_result and dca_result:
                        st.write("**VA策略:**")
                        st.write(f"計算類型: {va_result.get('calculation_type', 'N/A')}")
                        st.write(f"計算耗時: {va_result.get('calculation_duration', 0):.3f}秒")
                        
                        st.write("**DCA策略:**")
                        st.write(f"計算類型: {dca_result.get('calculation_type', 'N/A')}")
                        st.write(f"計算耗時: {dca_result.get('calculation_duration', 0):.3f}秒")
                
                with tab4:
                    st.json(stats)
            
        except Exception as e:
            status_text.text(f"❌ 工作流程失敗: {str(e)}")
            st.error(f"綜合展示失敗: {str(e)}")

if __name__ == "__main__":
    main() 