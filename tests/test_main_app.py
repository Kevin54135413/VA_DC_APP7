"""
第4.6節 - 主應用程式架構測試套件

測試所有核心函數和功能，確保符合需求文件規格。
"""

import pytest
import streamlit as st
import pandas as pd
import numpy as np
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any, Optional
import logging
import io
from datetime import datetime

# 導入待測試的模組
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

class TestMainAppCore:
    """測試主應用程式核心函數"""
    
    def test_main_function_signature(self):
        """測試main函數簽名"""
        import inspect
        sig = inspect.signature(main)
        
        # 檢查函數簽名
        assert len(sig.parameters) == 0, "main函數不應有參數"
        assert sig.return_annotation == None or sig.return_annotation == type(None), "main函數應返回None"
    
    @patch('src.core.main_app.st')
    @patch('src.core.main_app.simple_app_initialization')
    @patch('src.core.main_app.simple_state_management')
    @patch('src.core.main_app.render_sidebar_controls')
    @patch('src.core.main_app.render_main_content')
    def test_main_function_calls(self, mock_render_main, mock_render_sidebar, 
                                mock_state, mock_init, mock_st):
        """測試main函數調用順序"""
        # 模擬streamlit session_state
        mock_session_state = MagicMock()
        mock_st.session_state = mock_session_state
        
        # 執行main函數
        main()
        
        # 驗證所有函數被調用
        mock_init.assert_called_once()
        mock_state.assert_called_once()
        mock_render_sidebar.assert_called_once()
        mock_render_main.assert_called_once()
        mock_st.set_page_config.assert_called_once()
    
    def test_render_sidebar_controls_signature(self):
        """測試render_sidebar_controls函數簽名"""
        import inspect
        sig = inspect.signature(render_sidebar_controls)
        
        assert len(sig.parameters) == 0, "render_sidebar_controls函數不應有參數"
        assert sig.return_annotation == None or sig.return_annotation == type(None), "應返回None"
    
    def test_render_sidebar_controls_widgets(self):
        """測試側邊欄控件實作"""
        # 簡化測試，只檢查函數可以被調用而不出錯
        with patch('src.core.main_app.st') as mock_st:
            # 設置基本的mock
            mock_session_state = MagicMock()
            mock_st.session_state = mock_session_state
            
            # 模擬sidebar context manager
            mock_sidebar = MagicMock()
            mock_sidebar.__enter__ = Mock(return_value=mock_sidebar)
            mock_sidebar.__exit__ = Mock(return_value=None)
            mock_st.sidebar = mock_sidebar
            
            # 模擬所有streamlit組件
            for attr in ['title', 'subheader', 'number_input', 'slider', 'selectbox', 
                        'button', 'markdown', 'write', 'rerun', 'expander']:
                if attr == 'expander':
                    mock_expander = MagicMock()
                    mock_expander.__enter__ = Mock(return_value=mock_expander)
                    mock_expander.__exit__ = Mock(return_value=None)
                    setattr(mock_st, attr, Mock(return_value=mock_expander))
                else:
                    setattr(mock_st, attr, Mock())
            
            # 設置返回值
            mock_st.number_input.side_effect = [10000, 1000]
            mock_st.slider.side_effect = [10, 0.8]
            mock_st.selectbox.return_value = 'historical'
            mock_st.button.return_value = False
            
            # 執行函數（不應該拋出異常）
            try:
                render_sidebar_controls()
                assert True  # 如果沒有異常，測試通過
            except Exception as e:
                assert False, f"函數執行失敗: {str(e)}"
    
    def test_render_main_content_signature(self):
        """測試render_main_content函數簽名"""
        import inspect
        sig = inspect.signature(render_main_content)
        
        assert len(sig.parameters) == 0, "render_main_content函數不應有參數"
        assert sig.return_annotation == None or sig.return_annotation == type(None), "應返回None"
    
    def test_display_results_simple_signature(self):
        """測試display_results_simple函數簽名"""
        import inspect
        sig = inspect.signature(display_results_simple)
        
        assert len(sig.parameters) == 1, "display_results_simple函數應有1個參數"
        assert 'results' in sig.parameters, "應有results參數"
        assert sig.return_annotation == None or sig.return_annotation == type(None), "應返回None"
    
    def test_simplified_calculation_flow_signature(self):
        """測試simplified_calculation_flow函數簽名"""
        import inspect
        sig = inspect.signature(simplified_calculation_flow)
        
        assert len(sig.parameters) == 1, "simplified_calculation_flow函數應有1個參數"
        assert 'user_params' in sig.parameters, "應有user_params參數"
        assert sig.return_annotation == Optional[Dict] or str(sig.return_annotation) == 'typing.Union[dict, NoneType]', "應返回Optional[Dict]"
    
    def test_simple_state_management_signature(self):
        """測試simple_state_management函數簽名"""
        import inspect
        sig = inspect.signature(simple_state_management)
        
        assert len(sig.parameters) == 0, "simple_state_management函數不應有參數"
        assert sig.return_annotation == None or sig.return_annotation == type(None), "應返回None"

class TestParameterValidation:
    """測試參數驗證功能"""
    
    def test_validate_parameters_valid_input(self):
        """測試有效參數驗證"""
        valid_params = {
            'initial_investment': 10000,
            'monthly_investment': 1000,
            'investment_years': 10,
            'stock_ratio': 0.8,
            'scenario': 'historical'
        }
        
        result = _validate_parameters(valid_params)
        assert result == True, "有效參數應通過驗證"
    
    def test_validate_parameters_missing_required(self):
        """測試缺少必要參數"""
        invalid_params = {
            'initial_investment': 10000,
            'monthly_investment': 1000
            # 缺少其他必要參數
        }
        
        result = _validate_parameters(invalid_params)
        assert result == False, "缺少必要參數應驗證失敗"
    
    def test_validate_parameters_out_of_range(self):
        """測試參數超出範圍"""
        # 初始投資金額超出範圍
        invalid_params = {
            'initial_investment': 2000000,  # 超過最大值
            'monthly_investment': 1000,
            'investment_years': 10,
            'stock_ratio': 0.8,
            'scenario': 'historical'
        }
        
        result = _validate_parameters(invalid_params)
        assert result == False, "超出範圍的參數應驗證失敗"
    
    def test_validate_parameters_invalid_scenario(self):
        """測試無效市場情境"""
        invalid_params = {
            'initial_investment': 10000,
            'monthly_investment': 1000,
            'investment_years': 10,
            'stock_ratio': 0.8,
            'scenario': 'invalid_scenario'
        }
        
        result = _validate_parameters(invalid_params)
        assert result == False, "無效情境應驗證失敗"

class TestCalculationFlow:
    """測試計算流程功能"""
    
    @patch('src.core.main_app.st')
    @patch('src.core.main_app._validate_parameters')
    @patch('src.core.main_app._fetch_market_data')
    @patch('src.core.main_app._calculate_strategies')
    @patch('src.core.main_app._analyze_performance')
    def test_simplified_calculation_flow_success(self, mock_analyze, mock_calculate, 
                                               mock_fetch, mock_validate, mock_st):
        """測試成功的計算流程"""
        # 設置模擬
        mock_validate.return_value = True
        mock_fetch.return_value = {'data': 'test', 'metadata': {'data_source': 'test'}}
        mock_calculate.return_value = {'va_strategy': {}, 'dca_strategy': {}}
        mock_analyze.return_value = {'summary_metrics': {}}
        
        # 模擬streamlit spinner context manager
        mock_spinner = MagicMock()
        mock_spinner.__enter__ = Mock(return_value=mock_spinner)
        mock_spinner.__exit__ = Mock(return_value=None)
        mock_st.spinner = Mock(return_value=mock_spinner)
        mock_st.success = Mock()
        
        user_params = {
            'initial_investment': 10000,
            'monthly_investment': 1000,
            'investment_years': 10,
            'stock_ratio': 0.8,
            'scenario': 'historical'
        }
        
        # 執行計算流程
        result = simplified_calculation_flow(user_params)
        
        # 驗證結果
        assert result is not None, "成功的計算流程應返回結果"
        assert 'user_params' in result, "結果應包含用戶參數"
        assert 'market_data_info' in result, "結果應包含市場數據信息"
        
        # 驗證所有步驟都被調用
        mock_validate.assert_called_once_with(user_params)
        mock_fetch.assert_called_once_with(user_params)
        mock_calculate.assert_called_once()
        mock_analyze.assert_called_once()
    
    @patch('src.core.main_app.st')
    @patch('src.core.main_app._validate_parameters')
    def test_simplified_calculation_flow_validation_failure(self, mock_validate, mock_st):
        """測試參數驗證失敗的情況"""
        # 設置模擬
        mock_validate.return_value = False
        mock_st.spinner = Mock()
        mock_st.spinner.__enter__ = Mock(return_value=Mock())
        mock_st.spinner.__exit__ = Mock(return_value=None)
        mock_st.error = Mock()
        
        user_params = {'invalid': 'params'}
        
        # 執行計算流程
        result = simplified_calculation_flow(user_params)
        
        # 驗證結果
        assert result is None, "驗證失敗應返回None"
        mock_st.error.assert_called_once()
    
    @patch('src.core.main_app.st')
    @patch('src.core.main_app._validate_parameters')
    @patch('src.core.main_app._fetch_market_data')
    def test_simplified_calculation_flow_data_fetch_failure(self, mock_fetch, mock_validate, mock_st):
        """測試數據獲取失敗的情況"""
        # 設置模擬
        mock_validate.return_value = True
        mock_fetch.return_value = None
        mock_st.spinner = Mock()
        mock_st.spinner.__enter__ = Mock(return_value=Mock())
        mock_st.spinner.__exit__ = Mock(return_value=None)
        mock_st.success = Mock()
        mock_st.error = Mock()
        
        user_params = {
            'initial_investment': 10000,
            'monthly_investment': 1000,
            'investment_years': 10,
            'stock_ratio': 0.8,
            'scenario': 'historical'
        }
        
        # 執行計算流程
        result = simplified_calculation_flow(user_params)
        
        # 驗證結果
        assert result is None, "數據獲取失敗應返回None"
        mock_st.error.assert_called()

class TestErrorHandling:
    """測試錯誤處理功能"""
    
    def test_simple_error_handler_decorator(self):
        """測試錯誤處理裝飾器"""
        @simple_error_handler
        def test_function():
            raise ValueError("測試錯誤")
        
        with patch('src.core.main_app.st') as mock_st:
            mock_st.error = Mock()
            
            result = test_function()
            
            assert result is None, "錯誤處理應返回None"
            mock_st.error.assert_called_once()
    
    def test_simple_error_handler_success(self):
        """測試錯誤處理裝飾器成功情況"""
        @simple_error_handler
        def test_function():
            return "success"
        
        result = test_function()
        assert result == "success", "成功執行應返回正確結果"

class TestStateManagement:
    """測試狀態管理功能"""
    
    @patch('src.core.main_app.st')
    def test_simple_state_management_initialization(self, mock_st):
        """測試狀態管理初始化"""
        # 模擬空的session_state
        mock_session_state = MagicMock()
        mock_st.session_state = mock_session_state
        
        # 執行狀態管理
        simple_state_management()
        
        # 驗證session_state被初始化
        assert mock_session_state.app_initialized == True
    
    @patch('src.core.main_app.st')
    @patch('src.core.main_app._check_system_health')
    def test_simple_state_management_health_check(self, mock_health, mock_st):
        """測試系統健康檢查"""
        # 模擬session_state
        mock_session_state = MagicMock()
        mock_session_state.app_initialized = True
        mock_st.session_state = mock_session_state
        mock_health.return_value = {'status': 'healthy'}
        
        # 執行狀態管理
        simple_state_management()
        
        # 驗證健康檢查被調用
        mock_health.assert_called_once()

class TestDisplayFunctions:
    """測試顯示功能"""
    
    @patch('src.core.main_app.st')
    def test_display_results_simple_empty_results(self, mock_st):
        """測試空結果顯示"""
        mock_st.error = Mock()
        mock_st.subheader = Mock()
        mock_st.columns = Mock(return_value=[Mock(), Mock(), Mock()])
        
        # 測試空結果
        display_results_simple(None)
        
        # 驗證錯誤信息被顯示
        mock_st.error.assert_called_once()
    
    def test_display_results_simple_with_data(self):
        """測試有數據的結果顯示"""
        # 簡化測試，只檢查函數可以被調用而不出錯
        with patch('src.core.main_app.st') as mock_st:
            # 設置基本的mock
            mock_st.subheader = Mock()
            mock_st.markdown = Mock()
            mock_st.metric = Mock()
            mock_st.line_chart = Mock()
            mock_st.bar_chart = Mock()
            mock_st.download_button = Mock()
            mock_st.error = Mock()
            
            # 模擬columns返回context manager
            mock_col = MagicMock()
            mock_col.__enter__ = Mock(return_value=mock_col)
            mock_col.__exit__ = Mock(return_value=None)
            
            # 設置多次調用返回不同數量的columns
            mock_st.columns = Mock(side_effect=[
                [mock_col, mock_col, mock_col],  # 第一次調用返回3個
                [mock_col, mock_col, mock_col, mock_col],  # 第二次調用返回4個
                [mock_col, mock_col],  # 第三次調用返回2個
                [mock_col, mock_col, mock_col],  # 後續調用返回3個
                [mock_col, mock_col, mock_col, mock_col],  # 後續調用返回4個
                [mock_col, mock_col]  # 後續調用返回2個
            ])
            
            # 測試數據
            results = {
                'va_strategy': {'final_portfolio_value': 100000},
                'dca_strategy': {'final_portfolio_value': 95000},
                'summary_metrics': {
                    'va_annualized_return': 0.08,
                    'dca_annualized_return': 0.075
                }
            }
            
            # 執行顯示（不應該拋出異常）
            try:
                display_results_simple(results)
                assert True  # 如果沒有異常，測試通過
            except Exception as e:
                assert False, f"函數執行失敗: {str(e)}"

class TestUtilityFunctions:
    """測試輔助函數"""
    
    def test_check_system_health(self):
        """測試系統健康檢查"""
        health = _check_system_health()
        
        assert isinstance(health, dict), "健康檢查應返回字典"
        assert 'overall_status' in health, "應包含整體狀態"
        assert 'data_sources_available' in health, "應包含數據源狀態"
        assert 'modules_loaded' in health, "應包含模組載入狀態"
        assert 'errors' in health, "應包含錯誤列表"
    
    def test_generate_csv_data(self):
        """測試CSV數據生成"""
        results = {
            'va_strategy': {'final_portfolio_value': 100000},
            'dca_strategy': {'final_portfolio_value': 95000},
            'summary_metrics': {
                'va_annualized_return': 0.08,
                'dca_annualized_return': 0.075
            },
            'user_params': {
                'initial_investment': 10000,
                'monthly_investment': 1000,
                'investment_years': 10,
                'stock_ratio': 0.8,
                'scenario': 'historical'
            }
        }
        
        csv_data = _generate_csv_data(results)
        
        assert isinstance(csv_data, str), "CSV數據應為字符串"
        assert len(csv_data) > 0, "CSV數據不應為空"
        assert '參數設定' in csv_data, "應包含參數設定"
        assert '計算結果' in csv_data, "應包含計算結果"
    
    def test_generate_summary_report(self):
        """測試摘要報告生成"""
        results = {
            'va_strategy': {'final_portfolio_value': 100000},
            'dca_strategy': {'final_portfolio_value': 95000},
            'summary_metrics': {
                'va_annualized_return': 0.08,
                'dca_annualized_return': 0.075
            },
            'user_params': {
                'initial_investment': 10000,
                'monthly_investment': 1000,
                'investment_years': 10,
                'stock_ratio': 0.8,
                'scenario': 'historical'
            }
        }
        
        report = _generate_summary_report(results)
        
        assert isinstance(report, str), "摘要報告應為字符串"
        assert len(report) > 0, "摘要報告不應為空"
        assert '投資策略比較分析報告' in report, "應包含標題"
        assert '參數設定' in report, "應包含參數設定"
        assert '計算結果' in report, "應包含計算結果"
        assert '績效指標' in report, "應包含績效指標"

class TestDataProcessing:
    """測試數據處理功能"""
    
    @patch('src.core.main_app.basic_error_recovery')
    def test_fetch_market_data_success(self, mock_recovery):
        """測試市場數據獲取成功"""
        mock_recovery.return_value = {'data': 'test'}
        
        user_params = {'scenario': 'historical'}
        result = _fetch_market_data(user_params)
        
        assert result is not None, "數據獲取應成功"
        mock_recovery.assert_called_once()
    
    @patch('src.core.main_app.basic_error_recovery')
    def test_fetch_market_data_failure(self, mock_recovery):
        """測試市場數據獲取失敗"""
        mock_recovery.side_effect = Exception("數據獲取失敗")
        
        user_params = {'scenario': 'historical'}
        result = _fetch_market_data(user_params)
        
        assert result is None, "數據獲取失敗應返回None"
    
    @patch('src.core.main_app.calculate_va_strategy')
    @patch('src.core.main_app.calculate_dca_strategy')
    @patch('src.core.main_app.convert_annual_to_period_parameters')
    def test_calculate_strategies_success(self, mock_convert, mock_dca, mock_va):
        """測試策略計算成功"""
        # 設置模擬
        mock_convert.return_value = {'period_return': 0.006, 'period_volatility': 0.04}
        mock_va.return_value = {'final_portfolio_value': 100000}
        mock_dca.return_value = {'final_portfolio_value': 95000}
        
        user_params = {
            'initial_investment': 10000,
            'monthly_investment': 1000,
            'investment_years': 10,
            'stock_ratio': 0.8
        }
        
        market_data = {'data': 'test'}
        
        result = _calculate_strategies(user_params, market_data)
        
        assert result is not None, "策略計算應成功"
        assert 'va_strategy' in result, "應包含VA策略結果"
        assert 'dca_strategy' in result, "應包含DCA策略結果"
        
        # 驗證函數被調用
        mock_convert.assert_called_once()
        mock_va.assert_called_once()
        mock_dca.assert_called_once()
    
    @patch('src.core.main_app.calculate_summary_metrics')
    def test_analyze_performance_success(self, mock_summary):
        """測試績效分析成功"""
        mock_summary.return_value = {
            'va_annualized_return': 0.08,
            'dca_annualized_return': 0.075
        }
        
        calculation_results = {
            'va_strategy': {'final_portfolio_value': 100000},
            'dca_strategy': {'final_portfolio_value': 95000}
        }
        
        result = _analyze_performance(calculation_results)
        
        assert result is not None, "績效分析應成功"
        assert 'summary_metrics' in result, "應包含摘要指標"
        
        mock_summary.assert_called_once()

class TestIntegration:
    """測試整合功能"""
    
    def test_required_imports(self):
        """測試必要的導入"""
        # 測試第1章數據獲取機制導入
        from src.data_sources.simulation import SimulationDataGenerator
        from src.data_sources.data_fetcher import TiingoDataFetcher
        
        # 測試第2章核心計算函數導入
        from src.models.strategy_engine import calculate_va_strategy
        from src.models.calculation_formulas import calculate_va_target_value
        
        # 測試第3章UI組件導入
        from src.ui.parameter_manager import ParameterManager
        from src.ui.results_display import ResultsDisplayManager
        
        # 測試第4章功能模組導入
        from src.core.app_initialization import simple_app_initialization
        from src.core.data_flow import basic_error_recovery
        
        # 如果所有導入都成功，測試通過
        assert True, "所有必要模組都能正常導入"
    
    def test_function_signatures_compatibility(self):
        """測試函數簽名兼容性"""
        # 檢查所有必要函數都存在且簽名正確
        functions_to_check = [
            (main, 0, type(None)),
            (render_sidebar_controls, 0, type(None)),
            (render_main_content, 0, type(None)),
            (simple_state_management, 0, type(None))
        ]
        
        for func, expected_params, expected_return in functions_to_check:
            import inspect
            sig = inspect.signature(func)
            
            assert len(sig.parameters) == expected_params, f"{func.__name__}參數數量不正確"
            assert sig.return_annotation == expected_return or sig.return_annotation == None, f"{func.__name__}返回類型不正確"

class TestConstants:
    """測試常數和配置"""
    
    def test_parameter_ranges(self):
        """測試參數範圍常數"""
        # 測試各種邊界值
        test_cases = [
            # (initial_investment, expected_valid)
            (999, False),      # 低於最小值
            (1000, True),      # 最小值
            (10000, True),     # 預設值
            (1000000, True),   # 最大值
            (1000001, False),  # 超過最大值
        ]
        
        for investment, expected in test_cases:
            params = {
                'initial_investment': investment,
                'monthly_investment': 1000,
                'investment_years': 10,
                'stock_ratio': 0.8,
                'scenario': 'historical'
            }
            
            result = _validate_parameters(params)
            assert result == expected, f"投資金額{investment}的驗證結果不正確"
    
    def test_scenario_options(self):
        """測試市場情境選項"""
        valid_scenarios = ['historical', 'bull_market', 'bear_market']
        
        for scenario in valid_scenarios:
            params = {
                'initial_investment': 10000,
                'monthly_investment': 1000,
                'investment_years': 10,
                'stock_ratio': 0.8,
                'scenario': scenario
            }
            
            result = _validate_parameters(params)
            assert result == True, f"市場情境{scenario}應該有效"
        
        # 測試無效情境
        invalid_params = {
            'initial_investment': 10000,
            'monthly_investment': 1000,
            'investment_years': 10,
            'stock_ratio': 0.8,
            'scenario': 'invalid_scenario'
        }
        
        result = _validate_parameters(invalid_params)
        assert result == False, "無效市場情境應該驗證失敗"

# 執行測試的主函數
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"]) 