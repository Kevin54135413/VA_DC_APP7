"""
第4.5節 - 部署配置（簡化版）測試套件

測試所有部署檢查和配置文件生成功能
"""

import unittest
from unittest.mock import Mock, patch, MagicMock, mock_open
import os
import sys
from pathlib import Path
import tempfile
import shutil

# 添加src目錄到Python路徑
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from core.deployment import (
    quick_deployment_check,
    generate_requirements_txt,
    generate_streamlit_config,
    generate_deployment_files,
    prepare_for_deployment,
    get_deployment_status,
    validate_deployment_readiness,
    _check_required_files,
    _check_package_imports,
    _check_api_keys,
    _check_streamlit_config,
    _check_project_structure,
    _check_deployment_compatibility,
    _generate_deployment_recommendations,
    REQUIRED_FILES,
    REQUIRED_PACKAGES,
    REQUIREMENTS_CONTENT,
    STREAMLIT_CONFIG_CONTENT,
    API_KEY_VARS
)

class TestQuickDeploymentCheck(unittest.TestCase):
    """測試快速部署檢查函數"""
    
    def setUp(self):
        """設置測試環境"""
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)
    
    def tearDown(self):
        """清理測試環境"""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.temp_dir)
    
    def test_quick_deployment_check_function_exists(self):
        """測試quick_deployment_check函數是否存在"""
        self.assertTrue(callable(quick_deployment_check))
    
    def test_quick_deployment_check_returns_list(self):
        """測試quick_deployment_check返回列表"""
        with patch('core.deployment._check_required_files', return_value=[]), \
             patch('core.deployment._check_package_imports', return_value=[]), \
             patch('core.deployment._check_api_keys', return_value=[]), \
             patch('core.deployment._check_streamlit_config', return_value=[]), \
             patch('core.deployment._check_project_structure', return_value=[]), \
             patch('core.deployment._check_deployment_compatibility', return_value=[]):
            
            result = quick_deployment_check()
            self.assertIsInstance(result, list)
    
    def test_quick_deployment_check_comprehensive(self):
        """測試完整的部署檢查"""
        # 創建必要文件
        Path('app.py').touch()
        Path('requirements.txt').touch()
        
        # 創建項目結構
        for dir_name in ['src/core', 'src/data_sources', 'src/models', 'src/ui']:
            Path(dir_name).mkdir(parents=True, exist_ok=True)
        
        # 創建Streamlit配置
        Path('.streamlit').mkdir(exist_ok=True)
        Path('.streamlit/config.toml').touch()
        
        result = quick_deployment_check()
        
        # 檢查結果格式
        self.assertIsInstance(result, list)
        self.assertGreater(len(result), 0)
        
        # 檢查狀態符號
        for check in result:
            self.assertTrue(any(symbol in check for symbol in ['✅', '❌', '⚠️']))
    
    def test_quick_deployment_check_with_missing_files(self):
        """測試缺少必要文件的情況"""
        result = quick_deployment_check()
        
        # 應該包含錯誤信息
        error_checks = [check for check in result if check.startswith('❌')]
        self.assertGreater(len(error_checks), 0)

class TestFileChecking(unittest.TestCase):
    """測試文件檢查功能"""
    
    def setUp(self):
        """設置測試環境"""
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)
    
    def tearDown(self):
        """清理測試環境"""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.temp_dir)
    
    def test_check_required_files_all_exist(self):
        """測試所有必要文件都存在"""
        # 創建必要文件
        for file_name in REQUIRED_FILES:
            Path(file_name).touch()
        
        result = _check_required_files()
        
        # 所有檢查應該通過
        for check in result:
            self.assertTrue(check.startswith('✅'))
    
    def test_check_required_files_missing(self):
        """測試缺少必要文件"""
        result = _check_required_files()
        
        # 應該有錯誤
        error_checks = [check for check in result if check.startswith('❌')]
        self.assertEqual(len(error_checks), len(REQUIRED_FILES))
    
    def test_check_package_imports_success(self):
        """測試套件導入成功"""
        with patch('core.deployment.importlib.import_module') as mock_import:
            mock_import.return_value = Mock()
            
            result = _check_package_imports()
            
            # 所有檢查應該通過
            for check in result:
                self.assertTrue(check.startswith('✅'))
    
    def test_check_package_imports_failure(self):
        """測試套件導入失敗"""
        with patch('core.deployment.importlib.import_module') as mock_import:
            mock_import.side_effect = ImportError("Package not found")
            
            result = _check_package_imports()
            
            # 應該有錯誤
            error_checks = [check for check in result if check.startswith('❌')]
            self.assertEqual(len(error_checks), len(REQUIRED_PACKAGES))

class TestAPIKeyChecking(unittest.TestCase):
    """測試API金鑰檢查功能"""
    
    def test_check_api_keys_all_set(self):
        """測試所有API金鑰都設定"""
        with patch.dict(os.environ, {
            'TIINGO_API_KEY': 'test_tiingo_key',
            'FRED_API_KEY': 'test_fred_key'
        }):
            result = _check_api_keys()
            
            # 所有檢查應該通過
            for check in result:
                self.assertTrue(check.startswith('✅'))
    
    def test_check_api_keys_not_set(self):
        """測試API金鑰未設定"""
        with patch.dict(os.environ, {}, clear=True):
            result = _check_api_keys()
            
            # 應該有警告
            warning_checks = [check for check in result if check.startswith('⚠️')]
            self.assertEqual(len(warning_checks), len(API_KEY_VARS))
    
    def test_check_api_keys_partial_set(self):
        """測試部分API金鑰設定"""
        with patch.dict(os.environ, {'TIINGO_API_KEY': 'test_key'}, clear=True):
            result = _check_api_keys()
            
            # 應該有一個通過，一個警告
            success_checks = [check for check in result if check.startswith('✅')]
            warning_checks = [check for check in result if check.startswith('⚠️')]
            self.assertEqual(len(success_checks), 1)
            self.assertEqual(len(warning_checks), 1)
    
    def test_api_key_masking(self):
        """測試API金鑰遮罩功能"""
        with patch.dict(os.environ, {'TIINGO_API_KEY': 'test_long_key_123'}):
            result = _check_api_keys()
            
            # 檢查是否有遮罩
            tiingo_check = [check for check in result if 'TIINGO_API_KEY' in check][0]
            self.assertIn('test...', tiingo_check)
            self.assertNotIn('test_long_key_123', tiingo_check)

class TestStreamlitConfig(unittest.TestCase):
    """測試Streamlit配置檢查"""
    
    def setUp(self):
        """設置測試環境"""
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)
    
    def tearDown(self):
        """清理測試環境"""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.temp_dir)
    
    def test_check_streamlit_config_exists(self):
        """測試Streamlit配置文件存在"""
        Path('.streamlit').mkdir(exist_ok=True)
        Path('.streamlit/config.toml').touch()
        
        result = _check_streamlit_config()
        
        self.assertEqual(len(result), 1)
        self.assertTrue(result[0].startswith('✅'))
    
    def test_check_streamlit_config_missing(self):
        """測試Streamlit配置文件不存在"""
        result = _check_streamlit_config()
        
        self.assertEqual(len(result), 1)
        self.assertTrue(result[0].startswith('⚠️'))

class TestProjectStructure(unittest.TestCase):
    """測試項目結構檢查"""
    
    def setUp(self):
        """設置測試環境"""
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)
    
    def tearDown(self):
        """清理測試環境"""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.temp_dir)
    
    def test_check_project_structure_all_exist(self):
        """測試所有項目目錄都存在"""
        src_dirs = ['src/core', 'src/data_sources', 'src/models', 'src/ui']
        for src_dir in src_dirs:
            Path(src_dir).mkdir(parents=True, exist_ok=True)
        
        result = _check_project_structure()
        
        # 所有檢查應該通過
        for check in result:
            self.assertTrue(check.startswith('✅'))
    
    def test_check_project_structure_missing(self):
        """測試缺少項目目錄"""
        result = _check_project_structure()
        
        # 應該有警告
        warning_checks = [check for check in result if check.startswith('⚠️')]
        self.assertGreater(len(warning_checks), 0)

class TestDeploymentCompatibility(unittest.TestCase):
    """測試部署相容性檢查"""
    
    def setUp(self):
        """設置測試環境"""
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)
    
    def tearDown(self):
        """清理測試環境"""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.temp_dir)
    
    def test_check_deployment_compatibility_python_version(self):
        """測試Python版本檢查"""
        result = _check_deployment_compatibility()
        
        # 應該有Python版本檢查
        python_checks = [check for check in result if 'Python版本' in check]
        self.assertEqual(len(python_checks), 1)
    
    def test_check_deployment_compatibility_with_env_file(self):
        """測試有.env文件的情況"""
        Path('.env').touch()
        
        result = _check_deployment_compatibility()
        
        # 應該有.env文件警告
        env_checks = [check for check in result if '.env' in check]
        self.assertEqual(len(env_checks), 1)
        self.assertTrue(env_checks[0].startswith('⚠️'))

class TestConfigFileGeneration(unittest.TestCase):
    """測試配置文件生成功能"""
    
    def setUp(self):
        """設置測試環境"""
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)
    
    def tearDown(self):
        """清理測試環境"""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.temp_dir)
    
    def test_generate_requirements_txt_success(self):
        """測試成功生成requirements.txt"""
        result = generate_requirements_txt()
        
        self.assertTrue(result)
        self.assertTrue(Path('requirements.txt').exists())
        
        # 檢查內容
        with open('requirements.txt', 'r', encoding='utf-8') as f:
            content = f.read()
            self.assertIn('streamlit>=1.28.0', content)
            self.assertIn('pandas>=1.5.0', content)
            self.assertIn('numpy>=1.21.0', content)
    
    def test_generate_requirements_txt_failure(self):
        """測試生成requirements.txt失敗"""
        with patch('builtins.open', mock_open()) as mock_file:
            mock_file.side_effect = IOError("Permission denied")
            
            result = generate_requirements_txt()
            self.assertFalse(result)
    
    def test_generate_streamlit_config_success(self):
        """測試成功生成Streamlit配置"""
        result = generate_streamlit_config()
        
        self.assertTrue(result)
        self.assertTrue(Path('.streamlit/config.toml').exists())
        
        # 檢查內容
        with open('.streamlit/config.toml', 'r', encoding='utf-8') as f:
            content = f.read()
            self.assertIn('[server]', content)
            self.assertIn('[browser]', content)
            self.assertIn('[theme]', content)
    
    def test_generate_streamlit_config_failure(self):
        """測試生成Streamlit配置失敗"""
        with patch('core.deployment.Path.mkdir') as mock_mkdir:
            mock_mkdir.side_effect = OSError("Permission denied")
            
            result = generate_streamlit_config()
            self.assertFalse(result)
    
    def test_generate_deployment_files(self):
        """測試生成所有部署文件"""
        result = generate_deployment_files()
        
        self.assertIsInstance(result, dict)
        self.assertIn('requirements.txt', result)
        self.assertIn('streamlit_config', result)
        
        # 檢查文件是否生成
        self.assertTrue(Path('requirements.txt').exists())
        self.assertTrue(Path('.streamlit/config.toml').exists())

class TestDeploymentPreparation(unittest.TestCase):
    """測試部署準備功能"""
    
    def setUp(self):
        """設置測試環境"""
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)
    
    def tearDown(self):
        """清理測試環境"""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.temp_dir)
    
    def test_prepare_for_deployment(self):
        """測試部署準備"""
        with patch('core.deployment.quick_deployment_check') as mock_check, \
             patch('core.deployment.generate_deployment_files') as mock_generate:
            
            mock_check.return_value = ['✅ 測試通過']
            mock_generate.return_value = {'requirements.txt': True}
            
            result = prepare_for_deployment()
            
            self.assertIsInstance(result, dict)
            self.assertIn('checks', result)
            self.assertIn('files_generated', result)
            self.assertIn('recommendations', result)
    
    def test_generate_deployment_recommendations_no_issues(self):
        """測試無問題時的建議生成"""
        checks = ['✅ 所有檢查通過']
        
        recommendations = _generate_deployment_recommendations(checks)
        
        self.assertEqual(len(recommendations), 1)
        self.assertIn('可以開始部署', recommendations[0])
    
    def test_generate_deployment_recommendations_with_errors(self):
        """測試有錯誤時的建議生成"""
        checks = ['❌ 錯誤1', '⚠️ 警告1', '✅ 正常1']
        
        recommendations = _generate_deployment_recommendations(checks)
        
        self.assertGreater(len(recommendations), 0)
        self.assertTrue(any('錯誤' in rec for rec in recommendations))
        self.assertTrue(any('警告' in rec for rec in recommendations))

class TestDeploymentStatus(unittest.TestCase):
    """測試部署狀態功能"""
    
    def test_get_deployment_status(self):
        """測試獲取部署狀態"""
        with patch('core.deployment.quick_deployment_check') as mock_check:
            mock_check.return_value = ['✅ 通過1', '❌ 錯誤1', '⚠️ 警告1']
            
            status = get_deployment_status()
            
            self.assertIsInstance(status, dict)
            self.assertEqual(status['total_checks'], 3)
            self.assertEqual(status['passed'], 1)
            self.assertEqual(status['failed'], 1)
            self.assertEqual(status['warnings'], 1)
            self.assertFalse(status['ready_for_deployment'])
    
    def test_validate_deployment_readiness_ready(self):
        """測試部署準備狀態 - 準備就緒"""
        with patch('core.deployment.get_deployment_status') as mock_status:
            mock_status.return_value = {'ready_for_deployment': True}
            
            result = validate_deployment_readiness()
            self.assertTrue(result)
    
    def test_validate_deployment_readiness_not_ready(self):
        """測試部署準備狀態 - 未準備就緒"""
        with patch('core.deployment.get_deployment_status') as mock_status:
            mock_status.return_value = {'ready_for_deployment': False}
            
            result = validate_deployment_readiness()
            self.assertFalse(result)

class TestConstants(unittest.TestCase):
    """測試常數定義"""
    
    def test_required_files_constant(self):
        """測試必要文件常數"""
        self.assertIsInstance(REQUIRED_FILES, list)
        self.assertIn('app.py', REQUIRED_FILES)
        self.assertIn('requirements.txt', REQUIRED_FILES)
    
    def test_required_packages_constant(self):
        """測試必要套件常數"""
        self.assertIsInstance(REQUIRED_PACKAGES, list)
        self.assertIn('streamlit', REQUIRED_PACKAGES)
        self.assertIn('pandas', REQUIRED_PACKAGES)
        self.assertIn('numpy', REQUIRED_PACKAGES)
        self.assertIn('requests', REQUIRED_PACKAGES)
    
    def test_requirements_content_constant(self):
        """測試requirements.txt內容常數"""
        self.assertIsInstance(REQUIREMENTS_CONTENT, str)
        self.assertIn('streamlit>=1.28.0', REQUIREMENTS_CONTENT)
        self.assertIn('pandas>=1.5.0', REQUIREMENTS_CONTENT)
        self.assertIn('numpy>=1.21.0', REQUIREMENTS_CONTENT)
        self.assertIn('requests>=2.25.0', REQUIREMENTS_CONTENT)
        self.assertIn('plotly>=5.0.0', REQUIREMENTS_CONTENT)
    
    def test_streamlit_config_content_constant(self):
        """測試Streamlit配置內容常數"""
        self.assertIsInstance(STREAMLIT_CONFIG_CONTENT, str)
        self.assertIn('[server]', STREAMLIT_CONFIG_CONTENT)
        self.assertIn('[browser]', STREAMLIT_CONFIG_CONTENT)
        self.assertIn('[theme]', STREAMLIT_CONFIG_CONTENT)
    
    def test_api_key_vars_constant(self):
        """測試API金鑰變數常數"""
        self.assertIsInstance(API_KEY_VARS, list)
        self.assertIn('TIINGO_API_KEY', API_KEY_VARS)
        self.assertIn('FRED_API_KEY', API_KEY_VARS)

class TestFunctionSignatures(unittest.TestCase):
    """測試函數簽名"""
    
    def test_quick_deployment_check_signature(self):
        """測試quick_deployment_check函數簽名"""
        import inspect
        
        sig = inspect.signature(quick_deployment_check)
        
        # 檢查返回類型註解
        self.assertEqual(str(sig.return_annotation), "typing.List[str]")
        
        # 檢查無參數
        self.assertEqual(len(sig.parameters), 0)

class TestIntegrationWithOtherChapters(unittest.TestCase):
    """測試與其他章節的整合"""
    
    def test_deployment_check_covers_all_chapters(self):
        """測試部署檢查涵蓋所有章節"""
        # 創建完整的項目結構
        temp_dir = tempfile.mkdtemp()
        original_cwd = os.getcwd()
        
        try:
            os.chdir(temp_dir)
            
            # 創建第1-3章相關文件和目錄
            Path('app.py').touch()
            Path('requirements.txt').touch()
            
            for dir_name in ['src/core', 'src/data_sources', 'src/models', 'src/ui']:
                Path(dir_name).mkdir(parents=True, exist_ok=True)
            
            Path('.streamlit').mkdir(exist_ok=True)
            Path('.streamlit/config.toml').touch()
            
            # 執行檢查
            result = quick_deployment_check()
            
            # 檢查是否涵蓋所有重要項目
            check_text = ' '.join(result)
            self.assertIn('app.py', check_text)
            self.assertIn('requirements.txt', check_text)
            self.assertIn('streamlit', check_text)
            self.assertIn('pandas', check_text)
            self.assertIn('numpy', check_text)
            self.assertIn('src/core', check_text)
            self.assertIn('src/data_sources', check_text)
            self.assertIn('src/models', check_text)
            self.assertIn('src/ui', check_text)
        
        finally:
            os.chdir(original_cwd)
            shutil.rmtree(temp_dir)

if __name__ == '__main__':
    unittest.main() 