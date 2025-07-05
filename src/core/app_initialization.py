"""
第4.1節：應用程式啟動流程（簡化版）
實作基本初始化序列和錯誤處理機制
"""

import logging
import os
import streamlit as st
from enum import Enum
from typing import Dict, Any, Optional
from datetime import datetime


class ErrorSeverity(Enum):
    """錯誤嚴重程度枚舉"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class SystemError(Exception):
    """系統級錯誤"""
    pass


class APIConnectionError(Exception):
    """API連接錯誤"""
    pass


def simple_app_initialization() -> Dict[str, str]:
    """
    簡化版應用程式啟動初始化
    
    Returns:
        Dict[str, str]: API金鑰字典 {'tiingo': key, 'fred': key}
    """
    # 1. 基本日誌配置
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('app.log', mode='a', encoding='utf-8')
        ]
    )
    logger = logging.getLogger(__name__)
    logger.info("應用程式啟動")
    
    # 2. 環境變數檢查
    api_keys = {
        'tiingo': get_api_key('TIINGO_API_KEY'),
        'fred': get_api_key('FRED_API_KEY')
    }
    
    # 3. 基本健康檢查
    if not any(api_keys.values()):
        logger.warning("未檢測到API金鑰，將使用模擬數據")
    else:
        logger.info(f"API金鑰狀態 - Tiingo: {'✓' if api_keys['tiingo'] else '✗'}, FRED: {'✓' if api_keys['fred'] else '✗'}")
    
    # 4. Streamlit配置
    try:
        st.set_page_config(
            page_title="投資策略比較系統",
            page_icon="📈",
            layout="wide",
            initial_sidebar_state="expanded"
        )
        logger.info("Streamlit頁面配置完成")
    except Exception as e:
        logger.warning(f"Streamlit配置警告: {str(e)}")
    
    logger.info("應用程式初始化完成")
    return api_keys


def get_api_key(key_name: str) -> str:
    """
    簡化版API金鑰獲取
    優先順序：Streamlit Secrets > 環境變數
    
    Args:
        key_name: API金鑰名稱
        
    Returns:
        str: API金鑰值，未找到時返回空字串
    """
    logger = get_logger(__name__)
    
    # 優先順序：Streamlit Secrets > 環境變數
    try:
        # 嘗試從Streamlit Secrets獲取
        if hasattr(st, 'secrets') and key_name in st.secrets:
            api_key = st.secrets[key_name]
            logger.info(f"從Streamlit Secrets獲取 {key_name}")
            return api_key
    except Exception as e:
        logger.debug(f"Streamlit Secrets獲取失敗: {str(e)}")
    
    # 從環境變數獲取
    api_key = os.getenv(key_name, '')
    if api_key:
        logger.info(f"從環境變數獲取 {key_name}")
    else:
        logger.warning(f"未找到API金鑰: {key_name}")
    
    return api_key


def error_handling_flow() -> None:
    """統一錯誤處理流程"""
    logger = get_logger(__name__)
    
    try:
        # API連接測試
        api_status = test_api_connectivity_comprehensive()
        
        if not api_status['tiingo']['healthy']:
            handle_api_error('tiingo', api_status['tiingo'], ErrorSeverity.HIGH)
        
        if not api_status['fred']['healthy']:
            handle_api_error('fred', api_status['fred'], ErrorSeverity.MEDIUM)
            
    except APIConnectionError as e:
        logger.error(f"API連接錯誤: {str(e)}")
        # 啟用離線模式或備用數據源
        fallback_success = activate_fallback_mode()
        if fallback_success:
            display_warning_message("已切換至離線模式，部分功能可能受限")
        else:
            display_error_message("無法建立數據連接，請檢查網路設定")
            
    except SystemError as e:
        logger.critical(f"系統錯誤: {str(e)}")
        display_critical_error_message(str(e))
        
    except Exception as e:
        # 記錄詳細錯誤資訊
        error_context = {
            'error_type': type(e).__name__,
            'error_message': str(e),
            'user_action': get_current_user_action(),
            'system_state': get_system_state_snapshot(),
            'timestamp': datetime.now().isoformat()
        }
        
        logger.error(f"未預期錯誤: {error_context}")
        
        # 根據錯誤嚴重程度決定處理方式
        severity = assess_error_severity(e)
        handle_error_by_severity(e, severity, error_context)


def handle_api_error(api_name: str, error_info: Dict, severity: ErrorSeverity) -> None:
    """
    處理API錯誤
    
    Args:
        api_name: API名稱
        error_info: 錯誤資訊字典
        severity: 錯誤嚴重程度
    """
    logger = get_logger(__name__)
    
    if severity == ErrorSeverity.CRITICAL:
        logger.critical(f"{api_name} API完全不可用: {error_info}")
        st.error(f"❌ {api_name} 服務不可用，系統將使用備用數據")
        
    elif severity == ErrorSeverity.HIGH:
        logger.error(f"{api_name} API錯誤: {error_info}")
        st.warning(f"⚠️ {api_name} 服務異常，正在嘗試備用方案")
        
    elif severity == ErrorSeverity.MEDIUM:
        logger.warning(f"{api_name} API警告: {error_info}")
        st.info(f"ℹ️ {api_name} 服務回應較慢，請稍候")
        
    elif severity == ErrorSeverity.LOW:
        logger.info(f"{api_name} API輕微問題: {error_info}")
        # 低級別錯誤不顯示用戶界面訊息
    
    # 記錄API錯誤統計
    record_api_error_stats(api_name, severity, error_info)


def get_logger(name: str) -> logging.Logger:
    """
    獲取配置好的日誌記錄器
    
    Args:
        name: 日誌記錄器名稱
        
    Returns:
        logging.Logger: 配置好的日誌記錄器
    """
    logger = logging.getLogger(name)
    
    # 避免重複添加handler
    if not logger.handlers:
        # 創建控制台handler
        console_handler = logging.StreamHandler()
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
        
        # 創建文件handler
        try:
            file_handler = logging.FileHandler('app.log', mode='a', encoding='utf-8')
            file_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
            )
            file_handler.setFormatter(file_formatter)
            logger.addHandler(file_handler)
        except Exception as e:
            # 如果無法創建文件handler，只使用控制台handler
            console_handler.setLevel(logging.WARNING)
            logger.warning(f"無法創建文件日誌handler: {str(e)}")
        
        logger.setLevel(logging.INFO)
    
    return logger


# 輔助函數實作

def test_api_connectivity_comprehensive() -> Dict[str, Dict[str, Any]]:
    """
    綜合API連接測試
    
    Returns:
        Dict: API狀態字典
    """
    logger = get_logger(__name__)
    
    api_status = {
        'tiingo': {'healthy': False, 'error': None, 'response_time': None},
        'fred': {'healthy': False, 'error': None, 'response_time': None}
    }
    
    # 測試Tiingo API
    try:
        import requests
        import time
        
        tiingo_key = get_api_key('TIINGO_API_KEY')
        if tiingo_key:
            start_time = time.time()
            response = requests.get(
                f"https://api.tiingo.com/api/test?token={tiingo_key}",
                timeout=10
            )
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                api_status['tiingo']['healthy'] = True
                api_status['tiingo']['response_time'] = response_time
                logger.info(f"Tiingo API連接正常，響應時間: {response_time:.2f}秒")
            else:
                api_status['tiingo']['error'] = f"HTTP {response.status_code}"
                
    except Exception as e:
        api_status['tiingo']['error'] = str(e)
        logger.warning(f"Tiingo API測試失敗: {str(e)}")
    
    # 測試FRED API
    try:
        fred_key = get_api_key('FRED_API_KEY')
        if fred_key:
            start_time = time.time()
            response = requests.get(
                f"https://api.stlouisfed.org/fred/series?series_id=GDP&api_key={fred_key}&file_type=json&limit=1",
                timeout=10
            )
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                api_status['fred']['healthy'] = True
                api_status['fred']['response_time'] = response_time
                logger.info(f"FRED API連接正常，響應時間: {response_time:.2f}秒")
            else:
                api_status['fred']['error'] = f"HTTP {response.status_code}"
                
    except Exception as e:
        api_status['fred']['error'] = str(e)
        logger.warning(f"FRED API測試失敗: {str(e)}")
    
    return api_status


def activate_fallback_mode() -> bool:
    """
    啟用備用模式
    
    Returns:
        bool: 是否成功啟用備用模式
    """
    logger = get_logger(__name__)
    
    try:
        # 設定備用模式標誌
        if 'fallback_mode' not in st.session_state:
            st.session_state.fallback_mode = True
            logger.info("已啟用備用模式")
            return True
        return True
        
    except Exception as e:
        logger.error(f"啟用備用模式失敗: {str(e)}")
        return False


def display_warning_message(message: str) -> None:
    """顯示警告訊息"""
    st.warning(f"⚠️ {message}")


def display_error_message(message: str) -> None:
    """顯示錯誤訊息"""
    st.error(f"❌ {message}")


def display_critical_error_message(message: str) -> None:
    """顯示嚴重錯誤訊息"""
    st.error(f"🚨 系統嚴重錯誤: {message}")
    st.stop()


def get_current_user_action() -> str:
    """獲取當前用戶操作"""
    try:
        # 從Streamlit session state獲取當前操作
        return st.session_state.get('current_action', 'unknown')
    except:
        return 'unknown'


def get_system_state_snapshot() -> Dict[str, Any]:
    """獲取系統狀態快照"""
    try:
        return {
            'session_state_keys': list(st.session_state.keys()) if hasattr(st, 'session_state') else [],
            'timestamp': datetime.now().isoformat(),
            'memory_usage': get_memory_usage(),
            'active_connections': get_active_connections_count()
        }
    except Exception as e:
        return {'error': str(e), 'timestamp': datetime.now().isoformat()}


def assess_error_severity(error: Exception) -> ErrorSeverity:
    """評估錯誤嚴重程度"""
    if isinstance(error, SystemError):
        return ErrorSeverity.CRITICAL
    elif isinstance(error, APIConnectionError):
        return ErrorSeverity.HIGH
    elif isinstance(error, (ValueError, TypeError)):
        return ErrorSeverity.MEDIUM
    else:
        return ErrorSeverity.LOW


def handle_error_by_severity(error: Exception, severity: ErrorSeverity, context: Dict[str, Any]) -> None:
    """根據嚴重程度處理錯誤"""
    logger = get_logger(__name__)
    
    if severity == ErrorSeverity.CRITICAL:
        logger.critical(f"嚴重錯誤: {context}")
        st.error("🚨 系統遇到嚴重錯誤，請聯繫技術支援")
        st.stop()
        
    elif severity == ErrorSeverity.HIGH:
        logger.error(f"高級錯誤: {context}")
        st.error("❌ 系統功能受限，正在嘗試恢復")
        
    elif severity == ErrorSeverity.MEDIUM:
        logger.warning(f"中級錯誤: {context}")
        st.warning("⚠️ 部分功能可能受影響")
        
    elif severity == ErrorSeverity.LOW:
        logger.info(f"輕微錯誤: {context}")
        # 低級別錯誤不顯示用戶界面訊息


def record_api_error_stats(api_name: str, severity: ErrorSeverity, error_info: Dict) -> None:
    """記錄API錯誤統計"""
    logger = get_logger(__name__)
    
    try:
        # 初始化錯誤統計
        if 'api_error_stats' not in st.session_state:
            st.session_state.api_error_stats = {}
        
        if api_name not in st.session_state.api_error_stats:
            st.session_state.api_error_stats[api_name] = {
                'total_errors': 0,
                'by_severity': {s.value: 0 for s in ErrorSeverity},
                'last_error': None
            }
        
        # 更新統計
        st.session_state.api_error_stats[api_name]['total_errors'] += 1
        st.session_state.api_error_stats[api_name]['by_severity'][severity.value] += 1
        st.session_state.api_error_stats[api_name]['last_error'] = {
            'timestamp': datetime.now().isoformat(),
            'severity': severity.value,
            'error_info': error_info
        }
        
        logger.info(f"API錯誤統計已更新: {api_name} - {severity.value}")
        
    except Exception as e:
        logger.error(f"記錄API錯誤統計失敗: {str(e)}")


def get_memory_usage() -> float:
    """獲取記憶體使用量（MB）"""
    try:
        import psutil
        process = psutil.Process()
        return process.memory_info().rss / 1024 / 1024
    except:
        return 0.0


def get_active_connections_count() -> int:
    """獲取活躍連接數"""
    try:
        import psutil
        process = psutil.Process()
        return len(process.connections())
    except:
        return 0 