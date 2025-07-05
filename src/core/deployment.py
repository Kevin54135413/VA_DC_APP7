"""
第4.5節 - 部署配置（簡化版）

實作簡化的部署配置檢查和必要文件生成功能。
確保第1-3章所有功能可正常部署，支援Streamlit Cloud快速部署。
"""

import os
import sys
import importlib
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
import subprocess
import json

# 設置日誌
logger = logging.getLogger(__name__)

# ============================================================================
# 部署配置常數
# ============================================================================

# 必要文件列表
REQUIRED_FILES = ['app.py', 'requirements.txt']

# 基本套件列表
REQUIRED_PACKAGES = ['streamlit', 'pandas', 'numpy', 'requests']

# 完整requirements.txt內容
REQUIREMENTS_CONTENT = """streamlit>=1.28.0
pandas>=1.5.0
numpy>=1.21.0
requests>=2.25.0
plotly>=5.0.0
yfinance>=0.2.0
fredapi>=0.5.0
python-dateutil>=2.8.0
pytz>=2023.3
"""

# Streamlit配置文件內容
STREAMLIT_CONFIG_CONTENT = """[server]
headless = true
enableCORS = false
enableXsrfProtection = false

[browser]
gatherUsageStats = false

[theme]
primaryColor = "#FF6B6B"
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#F0F2F6"
textColor = "#262730"
font = "sans serif"
"""

# API金鑰環境變數
API_KEY_VARS = ['TIINGO_API_KEY', 'FRED_API_KEY']

# ============================================================================
# 第4.5節核心函數
# ============================================================================

def quick_deployment_check() -> List[str]:
    """
    快速部署檢查函數
    
    按照需求文件第4.5節規格實作：
    - 檢查必要文件：['app.py', 'requirements.txt']
    - 檢查基本套件導入：streamlit, pandas, numpy, requests
    - 檢查API金鑰設定（警告但不阻止）
    
    Returns:
        List[str]: 檢查結果列表，包含✅、❌、⚠️狀態
    """
    logger.info("開始執行快速部署檢查")
    
    results = []
    
    # 1. 檢查必要文件
    results.extend(_check_required_files())
    
    # 2. 檢查基本套件導入
    results.extend(_check_package_imports())
    
    # 3. 檢查API金鑰設定
    results.extend(_check_api_keys())
    
    # 4. 檢查Streamlit配置
    results.extend(_check_streamlit_config())
    
    # 5. 檢查項目結構
    results.extend(_check_project_structure())
    
    # 6. 檢查部署相容性
    results.extend(_check_deployment_compatibility())
    
    logger.info(f"部署檢查完成，共 {len(results)} 項檢查")
    return results

def _check_required_files() -> List[str]:
    """檢查必要文件"""
    results = []
    
    for file_name in REQUIRED_FILES:
        file_path = Path(file_name)
        if file_path.exists():
            results.append(f"✅ 必要文件 {file_name} 存在")
            logger.info(f"必要文件檢查通過: {file_name}")
        else:
            results.append(f"❌ 必要文件 {file_name} 不存在")
            logger.error(f"必要文件缺失: {file_name}")
    
    return results

def _check_package_imports() -> List[str]:
    """檢查基本套件導入"""
    results = []
    
    for package in REQUIRED_PACKAGES:
        try:
            importlib.import_module(package)
            results.append(f"✅ 套件 {package} 可正常導入")
            logger.info(f"套件導入檢查通過: {package}")
        except ImportError as e:
            results.append(f"❌ 套件 {package} 導入失敗: {str(e)}")
            logger.error(f"套件導入失敗: {package} - {str(e)}")
        except Exception as e:
            results.append(f"⚠️ 套件 {package} 檢查時發生錯誤: {str(e)}")
            logger.warning(f"套件檢查異常: {package} - {str(e)}")
    
    return results

def _check_api_keys() -> List[str]:
    """檢查API金鑰設定（警告但不阻止）"""
    results = []
    
    for api_key_var in API_KEY_VARS:
        api_key = os.getenv(api_key_var)
        if api_key:
            # 不顯示實際金鑰內容，只顯示前4個字符
            masked_key = api_key[:4] + "..." if len(api_key) > 4 else "***"
            results.append(f"✅ API金鑰 {api_key_var} 已設定 ({masked_key})")
            logger.info(f"API金鑰檢查通過: {api_key_var}")
        else:
            results.append(f"⚠️ API金鑰 {api_key_var} 未設定（將使用模擬數據）")
            logger.warning(f"API金鑰未設定: {api_key_var}")
    
    return results

def _check_streamlit_config() -> List[str]:
    """檢查Streamlit配置"""
    results = []
    
    config_path = Path('.streamlit/config.toml')
    if config_path.exists():
        results.append("✅ Streamlit配置文件 .streamlit/config.toml 存在")
        logger.info("Streamlit配置文件檢查通過")
    else:
        results.append("⚠️ Streamlit配置文件 .streamlit/config.toml 不存在（將使用預設配置）")
        logger.warning("Streamlit配置文件不存在")
    
    return results

def _check_project_structure() -> List[str]:
    """檢查項目結構"""
    results = []
    
    # 檢查src目錄結構
    src_dirs = ['src/core', 'src/data_sources', 'src/models', 'src/ui']
    for src_dir in src_dirs:
        if Path(src_dir).exists():
            results.append(f"✅ 項目目錄 {src_dir} 存在")
            logger.info(f"項目結構檢查通過: {src_dir}")
        else:
            results.append(f"⚠️ 項目目錄 {src_dir} 不存在")
            logger.warning(f"項目目錄不存在: {src_dir}")
    
    return results

def _check_deployment_compatibility() -> List[str]:
    """檢查部署相容性"""
    results = []
    
    # 檢查Python版本
    python_version = sys.version_info
    if python_version >= (3, 8):
        results.append(f"✅ Python版本 {python_version.major}.{python_version.minor} 符合要求")
        logger.info(f"Python版本檢查通過: {python_version.major}.{python_version.minor}")
    else:
        results.append(f"❌ Python版本 {python_version.major}.{python_version.minor} 過低，建議3.8+")
        logger.error(f"Python版本過低: {python_version.major}.{python_version.minor}")
    
    # 檢查是否有敏感信息
    if Path('.env').exists():
        results.append("⚠️ 發現 .env 文件，請確保不會上傳到版本控制")
        logger.warning("發現.env文件")
    
    return results

# ============================================================================
# 配置文件生成函數
# ============================================================================

def generate_requirements_txt() -> bool:
    """
    生成requirements.txt文件
    
    Returns:
        bool: 生成成功返回True
    """
    try:
        with open('requirements.txt', 'w', encoding='utf-8') as f:
            f.write(REQUIREMENTS_CONTENT)
        
        logger.info("requirements.txt 生成成功")
        return True
    except Exception as e:
        logger.error(f"requirements.txt 生成失敗: {str(e)}")
        return False

def generate_streamlit_config() -> bool:
    """
    生成Streamlit配置文件
    
    Returns:
        bool: 生成成功返回True
    """
    try:
        # 創建.streamlit目錄
        config_dir = Path('.streamlit')
        config_dir.mkdir(exist_ok=True)
        
        # 生成config.toml
        config_path = config_dir / 'config.toml'
        with open(config_path, 'w', encoding='utf-8') as f:
            f.write(STREAMLIT_CONFIG_CONTENT)
        
        logger.info("Streamlit配置文件生成成功")
        return True
    except Exception as e:
        logger.error(f"Streamlit配置文件生成失敗: {str(e)}")
        return False

def generate_deployment_files() -> Dict[str, bool]:
    """
    生成所有部署相關文件
    
    Returns:
        Dict[str, bool]: 各文件生成結果
    """
    results = {}
    
    # 生成requirements.txt
    results['requirements.txt'] = generate_requirements_txt()
    
    # 生成Streamlit配置
    results['streamlit_config'] = generate_streamlit_config()
    
    return results

# ============================================================================
# 部署準備函數
# ============================================================================

def prepare_for_deployment() -> Dict[str, Any]:
    """
    準備部署環境
    
    Returns:
        Dict[str, Any]: 準備結果
    """
    logger.info("開始準備部署環境")
    
    result = {
        'timestamp': str(Path.cwd()),
        'checks': [],
        'files_generated': {},
        'recommendations': []
    }
    
    # 執行部署檢查
    result['checks'] = quick_deployment_check()
    
    # 生成配置文件
    result['files_generated'] = generate_deployment_files()
    
    # 生成建議
    result['recommendations'] = _generate_deployment_recommendations(result['checks'])
    
    logger.info("部署環境準備完成")
    return result

def _generate_deployment_recommendations(checks: List[str]) -> List[str]:
    """根據檢查結果生成部署建議"""
    recommendations = []
    
    # 檢查錯誤項目
    error_count = sum(1 for check in checks if check.startswith('❌'))
    warning_count = sum(1 for check in checks if check.startswith('⚠️'))
    
    if error_count > 0:
        recommendations.append(f"發現 {error_count} 個錯誤，建議修復後再部署")
    
    if warning_count > 0:
        recommendations.append(f"發現 {warning_count} 個警告，建議檢查相關設定")
    
    # 特定建議
    if any('requirements.txt' in check and '❌' in check for check in checks):
        recommendations.append("請執行 generate_requirements_txt() 生成requirements.txt")
    
    if any('config.toml' in check and '⚠️' in check for check in checks):
        recommendations.append("建議執行 generate_streamlit_config() 生成Streamlit配置")
    
    if any('API金鑰' in check and '⚠️' in check for check in checks):
        recommendations.append("建議在Streamlit Cloud中設定API金鑰環境變數")
    
    if not recommendations:
        recommendations.append("所有檢查項目正常，可以開始部署")
    
    return recommendations

# ============================================================================
# 便利函數
# ============================================================================

def get_deployment_status() -> Dict[str, Any]:
    """
    獲取部署狀態摘要
    
    Returns:
        Dict[str, Any]: 部署狀態摘要
    """
    checks = quick_deployment_check()
    
    status = {
        'total_checks': len(checks),
        'passed': sum(1 for check in checks if check.startswith('✅')),
        'failed': sum(1 for check in checks if check.startswith('❌')),
        'warnings': sum(1 for check in checks if check.startswith('⚠️')),
        'ready_for_deployment': sum(1 for check in checks if check.startswith('❌')) == 0
    }
    
    return status

def validate_deployment_readiness() -> bool:
    """
    驗證部署準備狀態
    
    Returns:
        bool: 準備就緒返回True
    """
    status = get_deployment_status()
    return status['ready_for_deployment'] 