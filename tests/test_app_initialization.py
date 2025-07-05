"""
測試第4.1節：應用程式啟動流程（簡化版）
驗證所有核心函數的功能與整合關係
"""

import pytest
import logging
import os
from typing import Dict
from unittest.mock import patch, MagicMock
from src.core.app_initialization import (
    ErrorSeverity,
    SystemError,
    APIConnectionError,
    simple_app_initialization,
    get_api_key,
    error_handling_flow,
    handle_api_error,
    get_logger,
    activate_fallback_mode,
    assess_error_severity,
    handle_error_by_severity,
    record_api_error_stats
)


class TestErrorSeverity:
    """測試ErrorSeverity枚舉類別"""
    
    def test_error_severity_enum_values(self):
        """測試枚舉值是否正確"""
        assert ErrorSeverity.LOW.value == "low"
        assert ErrorSeverity.MEDIUM.value == "medium"
        assert ErrorSeverity.HIGH.value == "high"
        assert ErrorSeverity.CRITICAL.value == "critical"
    
    def test_error_severity_enum_completeness(self):
        """測試枚舉完整性"""
        expected_values = {"low", "medium", "high", "critical"}
        actual_values = {severity.value for severity in ErrorSeverity}
        assert actual_values == expected_values


class TestSimpleAppInitialization:
    """測試simple_app_initialization函數"""
    
    @patch('src.core.app_initialization.get_api_key')
    @patch('streamlit.set_page_config')
    def test_simple_app_initialization_success(self, mock_set_page_config, mock_get_api_key):
        """測試成功初始化"""
        # 模擬API金鑰
        mock_get_api_key.side_effect = lambda key: 'test_key' if key in ['TIINGO_API_KEY', 'FRED_API_KEY'] else ''
        
        # 執行初始化
        result = simple_app_initialization()
        
        # 驗證返回值
        assert isinstance(result, dict)
        assert 'tiingo' in result
        assert 'fred' in result
        assert result['tiingo'] == 'test_key'
        assert result['fred'] == 'test_key'
        
        # 驗證Streamlit配置被調用
        mock_set_page_config.assert_called_once()
        call_args = mock_set_page_config.call_args[1]
        assert call_args['page_title'] == "投資策略比較系統"
        assert call_args['page_icon'] == "📈"
        assert call_args['layout'] == "wide"
    
    @patch('src.core.app_initialization.get_api_key')
    @patch('streamlit.set_page_config')
    def test_simple_app_initialization_no_api_keys(self, mock_set_page_config, mock_get_api_key):
        """測試無API金鑰的情況"""
        # 模擬無API金鑰
        mock_get_api_key.return_value = ''
        
        # 執行初始化
        result = simple_app_initialization()
        
        # 驗證返回值
        assert result['tiingo'] == ''
        assert result['fred'] == ''
    
    @patch('src.core.app_initialization.get_api_key')
    @patch('streamlit.set_page_config', side_effect=Exception("Streamlit error"))
    def test_simple_app_initialization_streamlit_error(self, mock_set_page_config, mock_get_api_key):
        """測試Streamlit配置錯誤的情況"""
        mock_get_api_key.return_value = 'test_key'
        
        # 應該不會拋出異常
        result = simple_app_initialization()
        
        # 驗證仍然返回API金鑰
        assert result['tiingo'] == 'test_key'
        assert result['fred'] == 'test_key'


class TestGetApiKey:
    """測試get_api_key函數"""
    
    @patch('streamlit.secrets', {'TEST_KEY': 'streamlit_secret_value'})
    @patch.dict(os.environ, {'TEST_KEY': 'env_value'})
    def test_get_api_key_streamlit_priority(self):
        """測試Streamlit Secrets優先順序"""
        result = get_api_key('TEST_KEY')
        assert result == 'streamlit_secret_value'
    
    @patch('streamlit.secrets', {})
    @patch.dict(os.environ, {'TEST_KEY': 'env_value'})
    def test_get_api_key_environment_fallback(self):
        """測試環境變數備用"""
        result = get_api_key('TEST_KEY')
        assert result == 'env_value'
    
    @patch('streamlit.secrets', {})
    @patch.dict(os.environ, {}, clear=True)
    def test_get_api_key_not_found(self):
        """測試金鑰未找到"""
        result = get_api_key('NONEXISTENT_KEY')
        assert result == ''
    
    @patch('streamlit.secrets', side_effect=Exception("Secrets error"))
    @patch.dict(os.environ, {'TEST_KEY': 'env_value'})
    def test_get_api_key_streamlit_error(self, mock_secrets):
        """測試Streamlit Secrets錯誤時的備用機制"""
        result = get_api_key('TEST_KEY')
        assert result == 'env_value'


class TestErrorHandlingFlow:
    """測試error_handling_flow函數"""
    
    @patch('src.core.app_initialization.test_api_connectivity_comprehensive')
    @patch('src.core.app_initialization.handle_api_error')
    def test_error_handling_flow_api_unhealthy(self, mock_handle_api_error, mock_test_api):
        """測試API不健康的情況"""
        # 模擬API狀態
        mock_test_api.return_value = {
            'tiingo': {'healthy': False, 'error': 'Connection timeout'},
            'fred': {'healthy': False, 'error': 'Invalid key'}
        }
        
        # 執行錯誤處理流程
        error_handling_flow()
        
        # 驗證handle_api_error被調用
        assert mock_handle_api_error.call_count == 2
        
        # 驗證調用參數
        calls = mock_handle_api_error.call_args_list
        assert calls[0][0][0] == 'tiingo'
        assert calls[0][0][2] == ErrorSeverity.HIGH
        assert calls[1][0][0] == 'fred'
        assert calls[1][0][2] == ErrorSeverity.MEDIUM
    
    @patch('src.core.app_initialization.test_api_connectivity_comprehensive')
    @patch('src.core.app_initialization.handle_api_error')
    def test_error_handling_flow_api_healthy(self, mock_handle_api_error, mock_test_api):
        """測試API健康的情況"""
        # 模擬API狀態
        mock_test_api.return_value = {
            'tiingo': {'healthy': True, 'response_time': 0.5},
            'fred': {'healthy': True, 'response_time': 0.3}
        }
        
        # 執行錯誤處理流程
        error_handling_flow()
        
        # 驗證handle_api_error未被調用
        mock_handle_api_error.assert_not_called()
    
    @patch('src.core.app_initialization.test_api_connectivity_comprehensive', side_effect=APIConnectionError("Network error"))
    @patch('src.core.app_initialization.activate_fallback_mode')
    @patch('src.core.app_initialization.display_warning_message')
    def test_error_handling_flow_api_connection_error(self, mock_display_warning, mock_activate_fallback, mock_test_api):
        """測試API連接錯誤的情況"""
        mock_activate_fallback.return_value = True
        
        # 執行錯誤處理流程
        error_handling_flow()
        
        # 驗證備用模式被啟用
        mock_activate_fallback.assert_called_once()
        mock_display_warning.assert_called_once()


class TestHandleApiError:
    """測試handle_api_error函數"""
    
    @patch('streamlit.error')
    @patch('src.core.app_initialization.record_api_error_stats')
    def test_handle_api_error_critical(self, mock_record_stats, mock_st_error):
        """測試處理嚴重錯誤"""
        error_info = {'error': 'Service down', 'code': 500}
        
        handle_api_error('tiingo', error_info, ErrorSeverity.CRITICAL)
        
        # 驗證Streamlit錯誤訊息
        mock_st_error.assert_called_once()
        assert "❌ tiingo 服務不可用" in mock_st_error.call_args[0][0]
        
        # 驗證統計記錄
        mock_record_stats.assert_called_once_with('tiingo', ErrorSeverity.CRITICAL, error_info)
    
    @patch('streamlit.warning')
    @patch('src.core.app_initialization.record_api_error_stats')
    def test_handle_api_error_high(self, mock_record_stats, mock_st_warning):
        """測試處理高級錯誤"""
        error_info = {'error': 'Rate limit exceeded'}
        
        handle_api_error('fred', error_info, ErrorSeverity.HIGH)
        
        # 驗證Streamlit警告訊息
        mock_st_warning.assert_called_once()
        assert "⚠️ fred 服務異常" in mock_st_warning.call_args[0][0]
        
        # 驗證統計記錄
        mock_record_stats.assert_called_once_with('fred', ErrorSeverity.HIGH, error_info)
    
    @patch('streamlit.info')
    @patch('src.core.app_initialization.record_api_error_stats')
    def test_handle_api_error_medium(self, mock_record_stats, mock_st_info):
        """測試處理中級錯誤"""
        error_info = {'error': 'Slow response'}
        
        handle_api_error('tiingo', error_info, ErrorSeverity.MEDIUM)
        
        # 驗證Streamlit資訊訊息
        mock_st_info.assert_called_once()
        assert "ℹ️ tiingo 服務回應較慢" in mock_st_info.call_args[0][0]
        
        # 驗證統計記錄
        mock_record_stats.assert_called_once_with('tiingo', ErrorSeverity.MEDIUM, error_info)
    
    @patch('src.core.app_initialization.record_api_error_stats')
    def test_handle_api_error_low(self, mock_record_stats):
        """測試處理低級錯誤"""
        error_info = {'error': 'Minor issue'}
        
        handle_api_error('fred', error_info, ErrorSeverity.LOW)
        
        # 驗證統計記錄
        mock_record_stats.assert_called_once_with('fred', ErrorSeverity.LOW, error_info)


class TestGetLogger:
    """測試get_logger函數"""
    
    def test_get_logger_returns_logger(self):
        """測試返回Logger對象"""
        logger = get_logger('test_logger')
        assert isinstance(logger, logging.Logger)
        assert logger.name == 'test_logger'
    
    def test_get_logger_sets_correct_level(self):
        """測試設定正確的日誌級別"""
        logger = get_logger('test_logger_level')
        assert logger.level == logging.INFO
    
    def test_get_logger_adds_handlers(self):
        """測試添加處理器"""
        logger = get_logger('test_logger_handlers')
        
        # 應該至少有一個控制台處理器
        assert len(logger.handlers) >= 1
        
        # 檢查是否有StreamHandler
        has_stream_handler = any(isinstance(h, logging.StreamHandler) for h in logger.handlers)
        assert has_stream_handler
    
    def test_get_logger_formatter(self):
        """測試日誌格式器"""
        logger = get_logger('test_logger_formatter')
        
        # 檢查處理器的格式器
        for handler in logger.handlers:
            if isinstance(handler, logging.StreamHandler):
                formatter = handler.formatter
                assert formatter is not None
                assert '%(asctime)s' in formatter._fmt
                assert '%(name)s' in formatter._fmt
                assert '%(levelname)s' in formatter._fmt
                assert '%(message)s' in formatter._fmt


class TestAssessErrorSeverity:
    """測試assess_error_severity函數"""
    
    def test_assess_system_error(self):
        """測試SystemError評估"""
        error = SystemError("System failure")
        severity = assess_error_severity(error)
        assert severity == ErrorSeverity.CRITICAL
    
    def test_assess_api_connection_error(self):
        """測試APIConnectionError評估"""
        error = APIConnectionError("Connection failed")
        severity = assess_error_severity(error)
        assert severity == ErrorSeverity.HIGH
    
    def test_assess_value_error(self):
        """測試ValueError評估"""
        error = ValueError("Invalid value")
        severity = assess_error_severity(error)
        assert severity == ErrorSeverity.MEDIUM
    
    def test_assess_type_error(self):
        """測試TypeError評估"""
        error = TypeError("Type mismatch")
        severity = assess_error_severity(error)
        assert severity == ErrorSeverity.MEDIUM
    
    def test_assess_generic_error(self):
        """測試一般錯誤評估"""
        error = Exception("Generic error")
        severity = assess_error_severity(error)
        assert severity == ErrorSeverity.LOW


class TestHandleErrorBySeverity:
    """測試handle_error_by_severity函數"""
    
    @patch('streamlit.error')
    @patch('streamlit.stop')
    def test_handle_critical_error(self, mock_st_stop, mock_st_error):
        """測試處理嚴重錯誤"""
        error = SystemError("Critical failure")
        context = {'error_type': 'SystemError', 'error_message': 'Critical failure'}
        
        handle_error_by_severity(error, ErrorSeverity.CRITICAL, context)
        
        # 驗證顯示錯誤訊息並停止應用
        mock_st_error.assert_called_once()
        mock_st_stop.assert_called_once()
    
    @patch('streamlit.error')
    def test_handle_high_error(self, mock_st_error):
        """測試處理高級錯誤"""
        error = APIConnectionError("Connection failed")
        context = {'error_type': 'APIConnectionError', 'error_message': 'Connection failed'}
        
        handle_error_by_severity(error, ErrorSeverity.HIGH, context)
        
        # 驗證顯示錯誤訊息
        mock_st_error.assert_called_once()
        assert "❌ 系統功能受限" in mock_st_error.call_args[0][0]
    
    @patch('streamlit.warning')
    def test_handle_medium_error(self, mock_st_warning):
        """測試處理中級錯誤"""
        error = ValueError("Invalid input")
        context = {'error_type': 'ValueError', 'error_message': 'Invalid input'}
        
        handle_error_by_severity(error, ErrorSeverity.MEDIUM, context)
        
        # 驗證顯示警告訊息
        mock_st_warning.assert_called_once()
        assert "⚠️ 部分功能可能受影響" in mock_st_warning.call_args[0][0]
    
    def test_handle_low_error(self):
        """測試處理低級錯誤"""
        error = Exception("Minor issue")
        context = {'error_type': 'Exception', 'error_message': 'Minor issue'}
        
        # 低級錯誤不應該顯示用戶界面訊息，只記錄日誌
        handle_error_by_severity(error, ErrorSeverity.LOW, context)
        
        # 沒有具體的斷言，因為低級錯誤只記錄日誌


class TestIntegrationRequirements:
    """測試整合要求"""
    
    def test_function_signatures_match_requirements(self):
        """測試函數簽名符合需求"""
        # 測試simple_app_initialization函數簽名
        import inspect
        sig = inspect.signature(simple_app_initialization)
        assert len(sig.parameters) == 0
        assert sig.return_annotation == Dict[str, str]
        
        # 測試get_api_key函數簽名
        sig = inspect.signature(get_api_key)
        assert len(sig.parameters) == 1
        assert 'key_name' in sig.parameters
        assert sig.parameters['key_name'].annotation == str
        assert sig.return_annotation == str
        
        # 測試error_handling_flow函數簽名
        sig = inspect.signature(error_handling_flow)
        assert len(sig.parameters) == 0
        # None 注解在Python中可能顯示為None而不是type(None)
        assert sig.return_annotation in (None, type(None))
        
        # 測試handle_api_error函數簽名
        sig = inspect.signature(handle_api_error)
        assert len(sig.parameters) == 3
        assert 'api_name' in sig.parameters
        assert 'error_info' in sig.parameters
        assert 'severity' in sig.parameters
        assert sig.return_annotation in (None, type(None))
        
        # 測試get_logger函數簽名
        sig = inspect.signature(get_logger)
        assert len(sig.parameters) == 1
        assert 'name' in sig.parameters
        assert sig.parameters['name'].annotation == str
        assert sig.return_annotation == logging.Logger
    
    def test_error_severity_enum_complete(self):
        """測試ErrorSeverity枚舉完整性"""
        required_values = {'low', 'medium', 'high', 'critical'}
        actual_values = {severity.value for severity in ErrorSeverity}
        assert actual_values == required_values
        
        # 測試枚舉成員
        assert hasattr(ErrorSeverity, 'LOW')
        assert hasattr(ErrorSeverity, 'MEDIUM')
        assert hasattr(ErrorSeverity, 'HIGH')
        assert hasattr(ErrorSeverity, 'CRITICAL')


if __name__ == '__main__':
    pytest.main([__file__, '-v']) 