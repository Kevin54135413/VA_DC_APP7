"""
第4.1節使用範例
展示如何正確使用應用程式啟動流程的所有核心函數
"""

import streamlit as st
import sys
import os

# 添加源代碼路徑
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from core.app_initialization import (
    simple_app_initialization,
    get_api_key,
    error_handling_flow,
    handle_api_error,
    get_logger,
    ErrorSeverity,
    SystemError,
    APIConnectionError
)
from core.app_integration import Chapter4Integration


def main():
    """主函數：展示第4.1節的完整使用流程"""
    
    st.title("🚀 第4.1節：應用程式啟動流程展示")
    st.markdown("---")
    
    # 創建選項卡
    tab1, tab2, tab3, tab4 = st.tabs([
        "📋 基本初始化", 
        "🔐 API金鑰管理", 
        "⚠️ 錯誤處理", 
        "🔗 整合展示"
    ])
    
    with tab1:
        demonstrate_basic_initialization()
    
    with tab2:
        demonstrate_api_key_management()
    
    with tab3:
        demonstrate_error_handling()
    
    with tab4:
        demonstrate_integration()


def demonstrate_basic_initialization():
    """展示基本初始化功能"""
    st.header("📋 基本初始化展示")
    
    if st.button("執行 simple_app_initialization()", key="init_button"):
        with st.spinner("正在執行應用程式初始化..."):
            try:
                # 調用核心函數
                result = simple_app_initialization()
                
                # 顯示結果
                st.success("✅ 應用程式初始化成功！")
                
                # 顯示返回的API金鑰狀態
                st.subheader("API金鑰狀態")
                col1, col2 = st.columns(2)
                
                with col1:
                    tiingo_status = "🟢 已設定" if result['tiingo'] else "🔴 未設定"
                    st.metric("Tiingo API", tiingo_status)
                
                with col2:
                    fred_status = "🟢 已設定" if result['fred'] else "🔴 未設定"
                    st.metric("FRED API", fred_status)
                
                # 顯示詳細信息
                with st.expander("詳細初始化結果"):
                    st.json({
                        "tiingo_key_length": len(result['tiingo']) if result['tiingo'] else 0,
                        "fred_key_length": len(result['fred']) if result['fred'] else 0,
                        "initialization_complete": True
                    })
                
            except Exception as e:
                st.error(f"❌ 初始化失敗: {str(e)}")
                st.exception(e)


def demonstrate_api_key_management():
    """展示API金鑰管理功能"""
    st.header("🔐 API金鑰管理展示")
    
    # 測試不同的API金鑰獲取方式
    st.subheader("測試 get_api_key() 函數")
    
    key_name = st.selectbox(
        "選擇要測試的API金鑰",
        ["TIINGO_API_KEY", "FRED_API_KEY", "CUSTOM_KEY"]
    )
    
    if st.button("獲取API金鑰", key="get_key_button"):
        try:
            # 調用核心函數
            api_key = get_api_key(key_name)
            
            if api_key:
                st.success(f"✅ 成功獲取 {key_name}")
                st.info(f"金鑰長度: {len(api_key)} 字符")
                
                # 顯示金鑰的前幾個字符（安全考慮）
                if len(api_key) > 8:
                    masked_key = api_key[:4] + "*" * (len(api_key) - 8) + api_key[-4:]
                    st.code(f"金鑰預覽: {masked_key}")
                else:
                    st.code(f"金鑰預覽: {'*' * len(api_key)}")
            else:
                st.warning(f"⚠️ 未找到 {key_name}")
                st.info("請檢查以下位置：")
                st.markdown("""
                1. Streamlit Secrets (.streamlit/secrets.toml)
                2. 環境變數
                3. 系統配置
                """)
                
        except Exception as e:
            st.error(f"❌ 獲取API金鑰失敗: {str(e)}")
    
    # 顯示API金鑰優先順序說明
    st.subheader("API金鑰優先順序")
    st.markdown("""
    ```
    1. Streamlit Secrets (最高優先級)
       └── .streamlit/secrets.toml
    2. 環境變數 (備用)
       └── os.environ
    3. 返回空字串 (未找到)
    ```
    """)


def demonstrate_error_handling():
    """展示錯誤處理功能"""
    st.header("⚠️ 錯誤處理展示")
    
    # 錯誤嚴重程度展示
    st.subheader("錯誤嚴重程度分級")
    
    severity_options = {
        "LOW": ErrorSeverity.LOW,
        "MEDIUM": ErrorSeverity.MEDIUM,
        "HIGH": ErrorSeverity.HIGH,
        "CRITICAL": ErrorSeverity.CRITICAL
    }
    
    selected_severity = st.selectbox(
        "選擇錯誤嚴重程度",
        list(severity_options.keys())
    )
    
    error_message = st.text_input(
        "錯誤訊息",
        value="這是一個測試錯誤訊息"
    )
    
    if st.button("測試 handle_api_error()", key="error_button"):
        try:
            # 調用核心函數
            handle_api_error(
                "test_api",
                {"error": error_message, "timestamp": "2024-01-01T10:00:00Z"},
                severity_options[selected_severity]
            )
            
            st.success("✅ 錯誤處理函數執行完成")
            
        except Exception as e:
            st.error(f"❌ 錯誤處理失敗: {str(e)}")
    
    # 完整錯誤處理流程
    st.subheader("完整錯誤處理流程")
    
    if st.button("執行 error_handling_flow()", key="error_flow_button"):
        with st.spinner("正在執行錯誤處理流程..."):
            try:
                # 調用核心函數
                error_handling_flow()
                st.success("✅ 錯誤處理流程執行完成")
                
            except Exception as e:
                st.error(f"❌ 錯誤處理流程失敗: {str(e)}")
    
    # 錯誤類型展示
    st.subheader("錯誤類型測試")
    
    error_types = {
        "SystemError": SystemError,
        "APIConnectionError": APIConnectionError,
        "ValueError": ValueError,
        "TypeError": TypeError,
        "Exception": Exception
    }
    
    selected_error_type = st.selectbox(
        "選擇錯誤類型",
        list(error_types.keys())
    )
    
    if st.button("測試錯誤嚴重程度評估", key="assess_error_button"):
        try:
            from core.app_initialization import assess_error_severity
            
            # 創建測試錯誤
            test_error = error_types[selected_error_type]("測試錯誤")
            
            # 評估錯誤嚴重程度
            severity = assess_error_severity(test_error)
            
            st.success(f"✅ 錯誤類型: {selected_error_type}")
            st.info(f"評估嚴重程度: {severity.value}")
            
            # 顯示對應的處理方式
            severity_actions = {
                ErrorSeverity.CRITICAL: "🚨 停止應用程式",
                ErrorSeverity.HIGH: "❌ 顯示錯誤訊息",
                ErrorSeverity.MEDIUM: "⚠️ 顯示警告訊息",
                ErrorSeverity.LOW: "ℹ️ 僅記錄日誌"
            }
            
            st.markdown(f"**處理方式**: {severity_actions[severity]}")
            
        except Exception as e:
            st.error(f"❌ 錯誤評估失敗: {str(e)}")


def demonstrate_integration():
    """展示整合功能"""
    st.header("🔗 整合展示")
    
    st.subheader("與其他章節的整合關係")
    
    # 整合流程圖
    st.markdown("""
    ```mermaid
    graph TD
        A[第4.1節 應用程式啟動] --> B[第1章 API安全機制]
        A --> C[第2章 數據處理]
        A --> D[第3章 UI組件]
        
        B --> E[API金鑰驗證]
        B --> F[安全策略應用]
        
        C --> G[數據源初始化]
        C --> H[備用數據配置]
        
        D --> I[錯誤顯示組件]
        D --> J[進度條組件]
        
        E --> K[完整初始化結果]
        F --> K
        G --> K
        H --> K
        I --> K
        J --> K
    ```
    """)
    
    # 完整整合展示
    if st.button("執行完整整合展示", key="integration_button"):
        with st.spinner("正在執行完整整合..."):
            try:
                # 創建整合協調器
                integrator = Chapter4Integration()
                
                # 展示整合流程
                integrator.demonstrate_integration_flow()
                
                # 執行完整初始化
                result = integrator.initialize_application_with_full_integration()
                
                if result['initialization_status'] == 'success':
                    st.success("✅ 完整整合成功！")
                    
                    # 顯示整合結果
                    st.subheader("整合結果")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.metric("整合章節數", len(result['integrated_chapters']))
                        st.metric("API金鑰數", len(result['api_keys']))
                    
                    with col2:
                        st.metric("數據源數", len(result['data_sources']))
                        security_passed = sum(result['security_validation'].values())
                        st.metric("安全驗證通過", f"{security_passed}/{len(result['security_validation'])}")
                    
                    # 詳細結果
                    with st.expander("詳細整合結果"):
                        st.json(result)
                
                else:
                    st.error(f"❌ 整合失敗: {result.get('error', '未知錯誤')}")
                    
            except Exception as e:
                st.error(f"❌ 整合展示失敗: {str(e)}")
                st.exception(e)
    
    # 整合特性說明
    st.subheader("整合特性")
    
    features = {
        "🔐 API安全整合": "與第1章的多層級API金鑰驗證機制整合",
        "📊 數據處理整合": "與第2章的數據源初始化和備用機制整合",
        "🎨 UI組件整合": "與第3章的錯誤顯示和進度條組件整合",
        "📝 日誌記錄整合": "統一的日誌記錄格式和處理機制",
        "⚡ 效能監控整合": "與系統監控和效能分析功能整合"
    }
    
    for feature, description in features.items():
        st.markdown(f"**{feature}**: {description}")


def demonstrate_logger_functionality():
    """展示日誌記錄功能"""
    st.subheader("📝 日誌記錄展示")
    
    logger_name = st.text_input("日誌記錄器名稱", value="demo_logger")
    
    if st.button("測試 get_logger()", key="logger_button"):
        try:
            # 調用核心函數
            logger = get_logger(logger_name)
            
            st.success(f"✅ 成功創建日誌記錄器: {logger_name}")
            
            # 顯示日誌記錄器信息
            st.info(f"日誌級別: {logger.level}")
            st.info(f"處理器數量: {len(logger.handlers)}")
            
            # 測試不同級別的日誌
            log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
            selected_level = st.selectbox("選擇日誌級別", log_levels)
            log_message = st.text_input("日誌訊息", value="這是測試日誌訊息")
            
            if st.button("記錄日誌", key="log_message_button"):
                log_method = getattr(logger, selected_level.lower())
                log_method(log_message)
                st.success(f"✅ 已記錄 {selected_level} 級別日誌")
                
        except Exception as e:
            st.error(f"❌ 日誌記錄器創建失敗: {str(e)}")


if __name__ == "__main__":
    # 設置頁面配置
    st.set_page_config(
        page_title="第4.1節使用範例",
        page_icon="🚀",
        layout="wide"
    )
    
    # 執行主函數
    main()
    
    # 添加側邊欄信息
    with st.sidebar:
        st.header("📚 使用說明")
        st.markdown("""
        ### 功能概覽
        
        1. **基本初始化**: 展示 `simple_app_initialization()` 函數
        2. **API金鑰管理**: 展示 `get_api_key()` 函數
        3. **錯誤處理**: 展示錯誤處理機制
        4. **整合展示**: 展示與其他章節的整合
        
        ### 核心函數
        
        - `simple_app_initialization()` → Dict[str, str]
        - `get_api_key(key_name: str)` → str
        - `error_handling_flow()` → None
        - `handle_api_error()` → None
        - `get_logger(name: str)` → Logger
        
        ### 錯誤嚴重程度
        
        - **LOW**: 輕微問題
        - **MEDIUM**: 中級問題
        - **HIGH**: 嚴重問題
        - **CRITICAL**: 致命問題
        """)
        
        st.markdown("---")
        st.markdown("**版本**: 第4.1節實作版本")
        st.markdown("**狀態**: ✅ 完全實作") 