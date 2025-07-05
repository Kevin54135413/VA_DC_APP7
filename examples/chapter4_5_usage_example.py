"""
第4.5節使用範例
展示如何正確使用部署配置（簡化版）的所有核心函數
"""

import streamlit as st
import sys
import os
import json
from pathlib import Path
from datetime import datetime

# 添加源代碼路徑
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from core.deployment import (
    quick_deployment_check,
    generate_requirements_txt,
    generate_streamlit_config,
    generate_deployment_files,
    prepare_for_deployment,
    get_deployment_status,
    validate_deployment_readiness,
    REQUIRED_FILES,
    REQUIRED_PACKAGES,
    REQUIREMENTS_CONTENT,
    STREAMLIT_CONFIG_CONTENT,
    API_KEY_VARS
)

def main():
    """主函數：展示第4.5節的完整使用流程"""
    
    st.title("🚀 第4.5節：部署配置（簡化版）展示")
    st.markdown("---")
    
    # 創建選項卡
    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
        "📋 快速部署檢查", 
        "📁 配置文件生成", 
        "🔍 部署狀態監控", 
        "⚙️ 部署準備", 
        "📊 整合測試",
        "📚 配置文件預覽",
        "🎯 實際部署指南"
    ])
    
    with tab1:
        demonstrate_quick_deployment_check()
    
    with tab2:
        demonstrate_config_file_generation()
    
    with tab3:
        demonstrate_deployment_status()
    
    with tab4:
        demonstrate_deployment_preparation()
    
    with tab5:
        demonstrate_integration_test()
    
    with tab6:
        demonstrate_config_preview()
    
    with tab7:
        demonstrate_deployment_guide()

def demonstrate_quick_deployment_check():
    """展示快速部署檢查功能"""
    st.header("📋 快速部署檢查")
    
    st.markdown("""
    **核心函數：** `quick_deployment_check() → List[str]`
    
    **功能說明：**
    - 檢查必要文件：app.py, requirements.txt
    - 檢查基本套件導入：streamlit, pandas, numpy, requests
    - 檢查API金鑰設定（警告但不阻止）
    - 檢查項目結構和部署相容性
    """)
    
    # 基本檢查演示
    st.subheader("🔍 執行部署檢查")
    
    if st.button("執行快速部署檢查", key="quick_check_button"):
        with st.spinner("正在執行部署檢查..."):
            try:
                # 執行檢查
                results = quick_deployment_check()
                
                st.success(f"✅ 檢查完成！共執行 {len(results)} 項檢查")
                
                # 分類顯示結果
                col1, col2, col3 = st.columns(3)
                
                passed = [r for r in results if r.startswith('✅')]
                failed = [r for r in results if r.startswith('❌')]
                warnings = [r for r in results if r.startswith('⚠️')]
                
                with col1:
                    st.metric("✅ 通過", len(passed))
                with col2:
                    st.metric("❌ 失敗", len(failed))
                with col3:
                    st.metric("⚠️ 警告", len(warnings))
                
                # 詳細結果
                st.subheader("詳細檢查結果")
                
                if passed:
                    with st.expander("✅ 通過的檢查項目", expanded=True):
                        for result in passed:
                            st.write(result)
                
                if failed:
                    with st.expander("❌ 失敗的檢查項目", expanded=True):
                        for result in failed:
                            st.error(result)
                
                if warnings:
                    with st.expander("⚠️ 警告的檢查項目", expanded=True):
                        for result in warnings:
                            st.warning(result)
                
            except Exception as e:
                st.error(f"❌ 檢查執行失敗: {str(e)}")
                st.exception(e)
    
    # 檢查項目說明
    st.subheader("📝 檢查項目說明")
    
    with st.expander("必要文件檢查"):
        st.write("**檢查項目：**")
        for file in REQUIRED_FILES:
            st.write(f"- {file}")
        st.info("這些文件是部署到Streamlit Cloud的基本要求")
    
    with st.expander("基本套件檢查"):
        st.write("**檢查項目：**")
        for package in REQUIRED_PACKAGES:
            st.write(f"- {package}")
        st.info("這些套件是應用程式運行的基本依賴")
    
    with st.expander("API金鑰檢查"):
        st.write("**檢查項目：**")
        for key in API_KEY_VARS:
            st.write(f"- {key}")
        st.info("API金鑰缺失時會使用模擬數據，不會阻止部署")

def demonstrate_config_file_generation():
    """展示配置文件生成功能"""
    st.header("📁 配置文件生成")
    
    st.markdown("""
    **功能說明：**
    - 自動生成 requirements.txt 文件
    - 自動生成 .streamlit/config.toml 配置文件
    - 確保所有必要依賴都包含在內
    """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📄 生成 requirements.txt")
        
        if st.button("生成 requirements.txt", key="gen_requirements"):
            with st.spinner("正在生成 requirements.txt..."):
                try:
                    success = generate_requirements_txt()
                    
                    if success:
                        st.success("✅ requirements.txt 生成成功！")
                        
                        # 顯示文件內容
                        if Path('requirements.txt').exists():
                            with open('requirements.txt', 'r', encoding='utf-8') as f:
                                content = f.read()
                            st.code(content, language='text')
                    else:
                        st.error("❌ requirements.txt 生成失敗")
                        
                except Exception as e:
                    st.error(f"❌ 生成過程發生錯誤: {str(e)}")
    
    with col2:
        st.subheader("⚙️ 生成 Streamlit 配置")
        
        if st.button("生成 Streamlit 配置", key="gen_streamlit_config"):
            with st.spinner("正在生成 Streamlit 配置..."):
                try:
                    success = generate_streamlit_config()
                    
                    if success:
                        st.success("✅ Streamlit 配置生成成功！")
                        
                        # 顯示文件內容
                        config_path = Path('.streamlit/config.toml')
                        if config_path.exists():
                            with open(config_path, 'r', encoding='utf-8') as f:
                                content = f.read()
                            st.code(content, language='toml')
                    else:
                        st.error("❌ Streamlit 配置生成失敗")
                        
                except Exception as e:
                    st.error(f"❌ 生成過程發生錯誤: {str(e)}")
    
    # 一鍵生成所有文件
    st.subheader("🚀 一鍵生成所有配置文件")
    
    if st.button("生成所有配置文件", key="gen_all_configs"):
        with st.spinner("正在生成所有配置文件..."):
            try:
                results = generate_deployment_files()
                
                st.success("✅ 配置文件生成完成！")
                
                # 顯示結果
                col1, col2 = st.columns(2)
                
                with col1:
                    st.metric("requirements.txt", "✅ 成功" if results.get('requirements.txt') else "❌ 失敗")
                
                with col2:
                    st.metric("streamlit config", "✅ 成功" if results.get('streamlit_config') else "❌ 失敗")
                
                # 顯示詳細結果
                st.json(results)
                
            except Exception as e:
                st.error(f"❌ 生成過程發生錯誤: {str(e)}")

def demonstrate_deployment_status():
    """展示部署狀態監控功能"""
    st.header("🔍 部署狀態監控")
    
    st.markdown("""
    **功能說明：**
    - 實時監控部署準備狀態
    - 提供詳細的統計信息
    - 自動判斷是否準備就緒
    """)
    
    # 實時狀態監控
    st.subheader("📊 實時狀態監控")
    
    if st.button("獲取部署狀態", key="get_status"):
        with st.spinner("正在獲取部署狀態..."):
            try:
                status = get_deployment_status()
                
                # 顯示狀態指標
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("總檢查項目", status['total_checks'])
                with col2:
                    st.metric("✅ 通過", status['passed'])
                with col3:
                    st.metric("❌ 失敗", status['failed'])
                with col4:
                    st.metric("⚠️ 警告", status['warnings'])
                
                # 部署準備狀態
                if status['ready_for_deployment']:
                    st.success("🎉 系統已準備就緒，可以開始部署！")
                else:
                    st.warning("⚠️ 系統尚未準備就緒，請修復錯誤後再部署")
                
                # 詳細狀態信息
                with st.expander("詳細狀態信息"):
                    st.json(status)
                
            except Exception as e:
                st.error(f"❌ 獲取狀態失敗: {str(e)}")
    
    # 部署準備狀態驗證
    st.subheader("✅ 部署準備狀態驗證")
    
    if st.button("驗證部署準備狀態", key="validate_readiness"):
        with st.spinner("正在驗證部署準備狀態..."):
            try:
                is_ready = validate_deployment_readiness()
                
                if is_ready:
                    st.success("🎉 驗證通過！系統已準備就緒")
                    st.balloons()
                else:
                    st.error("❌ 驗證失敗！請修復所有錯誤後再試")
                
            except Exception as e:
                st.error(f"❌ 驗證過程發生錯誤: {str(e)}")

def demonstrate_deployment_preparation():
    """展示部署準備功能"""
    st.header("⚙️ 部署準備")
    
    st.markdown("""
    **功能說明：**
    - 執行完整的部署準備流程
    - 自動生成所有必要文件
    - 提供個性化的部署建議
    """)
    
    st.subheader("🚀 執行完整部署準備")
    
    if st.button("執行完整部署準備", key="prepare_deployment"):
        with st.spinner("正在執行部署準備..."):
            try:
                result = prepare_for_deployment()
                
                st.success("✅ 部署準備完成！")
                
                # 顯示檢查結果摘要
                col1, col2, col3 = st.columns(3)
                
                checks = result['checks']
                passed = len([c for c in checks if c.startswith('✅')])
                failed = len([c for c in checks if c.startswith('❌')])
                warnings = len([c for c in checks if c.startswith('⚠️')])
                
                with col1:
                    st.metric("✅ 通過", passed)
                with col2:
                    st.metric("❌ 失敗", failed)
                with col3:
                    st.metric("⚠️ 警告", warnings)
                
                # 文件生成結果
                st.subheader("📁 文件生成結果")
                files_generated = result['files_generated']
                
                for file_name, success in files_generated.items():
                    if success:
                        st.success(f"✅ {file_name} 生成成功")
                    else:
                        st.error(f"❌ {file_name} 生成失敗")
                
                # 部署建議
                st.subheader("💡 部署建議")
                recommendations = result['recommendations']
                
                for i, recommendation in enumerate(recommendations, 1):
                    st.write(f"{i}. {recommendation}")
                
                # 完整結果
                with st.expander("完整部署準備結果"):
                    st.json(result)
                
            except Exception as e:
                st.error(f"❌ 部署準備失敗: {str(e)}")
                st.exception(e)

def demonstrate_integration_test():
    """展示整合測試功能"""
    st.header("📊 整合測試")
    
    st.markdown("""
    **功能說明：**
    - 測試與第1-3章的整合
    - 驗證所有功能的相容性
    - 確保部署後正常運作
    """)
    
    st.subheader("🔗 章節整合測試")
    
    # 第1章整合測試
    with st.expander("第1章 - 數據源整合測試"):
        st.write("**測試項目：**")
        st.write("- API數據源可用性")
        st.write("- 模擬數據生成器")
        st.write("- 容錯機制")
        
        if st.button("執行第1章整合測試", key="test_chapter1"):
            with st.spinner("正在測試第1章整合..."):
                try:
                    # 測試數據源導入
                    from src.data_sources.simulation import SimulationDataGenerator
                    from src.data_sources.data_fetcher import TiingoDataFetcher, FREDDataFetcher
                    
                    st.success("✅ 第1章模組導入成功")
                    
                    # 測試基本功能
                    simulator = SimulationDataGenerator()
                    st.success("✅ 模擬數據生成器初始化成功")
                    
                except Exception as e:
                    st.error(f"❌ 第1章整合測試失敗: {str(e)}")
    
    # 第2章整合測試
    with st.expander("第2章 - 計算引擎整合測試"):
        st.write("**測試項目：**")
        st.write("- 策略計算函數")
        st.write("- 績效指標計算")
        st.write("- 表格生成器")
        
        if st.button("執行第2章整合測試", key="test_chapter2"):
            with st.spinner("正在測試第2章整合..."):
                try:
                    # 測試計算引擎導入
                    from src.models.strategy_engine import calculate_va_strategy, calculate_dca_strategy
                    from src.models.table_calculator import calculate_summary_metrics
                    
                    st.success("✅ 第2章模組導入成功")
                    
                except Exception as e:
                    st.error(f"❌ 第2章整合測試失敗: {str(e)}")
    
    # 第3章整合測試
    with st.expander("第3章 - UI組件整合測試"):
        st.write("**測試項目：**")
        st.write("- 參數管理器")
        st.write("- 結果顯示管理器")
        st.write("- 智能推薦系統")
        
        if st.button("執行第3章整合測試", key="test_chapter3"):
            with st.spinner("正在測試第3章整合..."):
                try:
                    # 測試UI組件導入
                    from src.ui.parameter_manager import ParameterManager
                    from src.ui.results_display import ResultsDisplayManager
                    
                    st.success("✅ 第3章模組導入成功")
                    
                except Exception as e:
                    st.error(f"❌ 第3章整合測試失敗: {str(e)}")
    
    # 完整整合測試
    st.subheader("🎯 完整整合測試")
    
    if st.button("執行完整整合測試", key="full_integration_test"):
        with st.spinner("正在執行完整整合測試..."):
            try:
                # 執行部署檢查
                checks = quick_deployment_check()
                
                # 檢查結果
                failed_checks = [c for c in checks if c.startswith('❌')]
                
                if not failed_checks:
                    st.success("🎉 完整整合測試通過！所有章節功能正常")
                    st.balloons()
                else:
                    st.warning(f"⚠️ 發現 {len(failed_checks)} 個問題，建議修復後再部署")
                    
                    for check in failed_checks:
                        st.error(check)
                
            except Exception as e:
                st.error(f"❌ 完整整合測試失敗: {str(e)}")

def demonstrate_config_preview():
    """展示配置文件預覽功能"""
    st.header("📚 配置文件預覽")
    
    st.markdown("""
    **功能說明：**
    - 預覽將要生成的配置文件內容
    - 了解各項配置的作用
    - 自定義配置選項
    """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📄 requirements.txt 預覽")
        
        st.write("**文件內容：**")
        st.code(REQUIREMENTS_CONTENT, language='text')
        
        st.write("**說明：**")
        st.write("- streamlit>=1.28.0: 主要框架")
        st.write("- pandas>=1.5.0: 數據處理")
        st.write("- numpy>=1.21.0: 數值計算")
        st.write("- requests>=2.25.0: HTTP請求")
        st.write("- plotly>=5.0.0: 圖表繪製")
        st.write("- yfinance>=0.2.0: 金融數據")
        st.write("- fredapi>=0.5.0: 經濟數據")
    
    with col2:
        st.subheader("⚙️ config.toml 預覽")
        
        st.write("**文件內容：**")
        st.code(STREAMLIT_CONFIG_CONTENT, language='toml')
        
        st.write("**說明：**")
        st.write("- [server]: 服務器配置")
        st.write("- [browser]: 瀏覽器配置")
        st.write("- [theme]: 主題配置")
        st.write("- headless=true: 無頭模式")
        st.write("- port=$PORT: 動態端口")

def demonstrate_deployment_guide():
    """展示實際部署指南"""
    st.header("🎯 實際部署指南")
    
    st.markdown("""
    **完整部署流程：**
    """)
    
    # 部署步驟
    st.subheader("📋 部署步驟")
    
    steps = [
        {
            "title": "1. 準備代碼",
            "description": "確保所有代碼已提交到Git倉庫",
            "action": "git add . && git commit -m 'Ready for deployment'"
        },
        {
            "title": "2. 執行部署檢查",
            "description": "運行quick_deployment_check()確認所有檢查通過",
            "action": "python -c \"from src.core.deployment import quick_deployment_check; print(quick_deployment_check())\""
        },
        {
            "title": "3. 生成配置文件",
            "description": "確保requirements.txt和config.toml存在",
            "action": "python -c \"from src.core.deployment import generate_deployment_files; generate_deployment_files()\""
        },
        {
            "title": "4. 設定環境變數",
            "description": "在Streamlit Cloud中設定API金鑰",
            "action": "TIINGO_API_KEY=your_key, FRED_API_KEY=your_key"
        },
        {
            "title": "5. 部署到Streamlit Cloud",
            "description": "連接GitHub倉庫並部署",
            "action": "https://share.streamlit.io/"
        }
    ]
    
    for step in steps:
        with st.expander(step["title"]):
            st.write(step["description"])
            st.code(step["action"], language='bash')
    
    # 部署檢查清單
    st.subheader("✅ 部署檢查清單")
    
    checklist = [
        "app.py 文件存在",
        "requirements.txt 文件存在",
        "所有必要套件可正常導入",
        ".streamlit/config.toml 配置文件存在",
        "項目結構完整",
        "Python版本符合要求",
        "API金鑰已設定（可選）",
        "代碼已提交到Git倉庫"
    ]
    
    for item in checklist:
        st.checkbox(item, key=f"checklist_{item}")
    
    # 常見問題
    st.subheader("❓ 常見問題")
    
    with st.expander("Q: 部署後無法訪問API數據怎麼辦？"):
        st.write("A: 檢查API金鑰是否正確設定，系統會自動切換到模擬數據模式")
    
    with st.expander("Q: 部署後頁面載入緩慢怎麼辦？"):
        st.write("A: 檢查依賴套件版本，確保使用最新穩定版本")
    
    with st.expander("Q: 如何更新部署後的應用？"):
        st.write("A: 提交新代碼到Git倉庫，Streamlit Cloud會自動重新部署")
    
    # 部署狀態檢查
    st.subheader("🔍 最終部署狀態檢查")
    
    if st.button("執行最終部署檢查", key="final_check"):
        with st.spinner("正在執行最終檢查..."):
            try:
                # 執行完整檢查
                result = prepare_for_deployment()
                
                # 檢查是否準備就緒
                is_ready = validate_deployment_readiness()
                
                if is_ready:
                    st.success("🎉 恭喜！系統已完全準備就緒，可以開始部署！")
                    st.balloons()
                    
                    # 顯示部署連結
                    st.markdown("""
                    **下一步：**
                    1. 訪問 [Streamlit Cloud](https://share.streamlit.io/)
                    2. 連接您的GitHub倉庫
                    3. 選擇main分支和app.py文件
                    4. 設定環境變數（如需要）
                    5. 點擊Deploy開始部署
                    """)
                else:
                    st.error("❌ 系統尚未準備就緒，請修復以下問題：")
                    
                    failed_checks = [c for c in result['checks'] if c.startswith('❌')]
                    for check in failed_checks:
                        st.error(check)
                
            except Exception as e:
                st.error(f"❌ 最終檢查失敗: {str(e)}")

if __name__ == "__main__":
    main() 