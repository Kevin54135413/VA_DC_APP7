"""
API客戶端模組 - API安全機制與連通性測試

本模組提供API金鑰管理、格式驗證、連通性測試等安全機制。
容錯管理功能已移至 fault_tolerance.py 中的 EnhancedAPIFaultToleranceManager。

主要功能：
- API金鑰多層級獲取策略
- API金鑰格式驗證
- API連通性測試
- 安全API請求包裝器
"""

import os
import json
import time
import random
import logging
import requests
from typing import Optional, Dict, Any

# 導入API安全機制
from ..utils.api_security import get_api_key

logger = logging.getLogger(__name__)


def validate_api_key_format(key_name: str, key_value: str) -> bool:
    """
    驗證API金鑰格式
    
    根據第1章第1.2節規範：
    - Tiingo API金鑰：至少20字符的字母數字組合
    - FRED API金鑰：32字符的字母數字組合
    
    Args:
        key_name: API金鑰名稱 ('TIINGO_API_KEY' 或 'FRED_API_KEY')
        key_value: 要驗證的API金鑰值
        
    Returns:
        bool: 格式是否有效
    """
    if not key_value:
        return False
    
    try:
        if key_name == 'TIINGO_API_KEY':
            # Tiingo API金鑰：至少20字符，字母數字組合
            if len(key_value) < 20:
                logger.warning(f"Tiingo API金鑰長度不足20字符: {len(key_value)}")
                return False
            
            if not key_value.isalnum():
                logger.warning("Tiingo API金鑰包含非字母數字字符")
                return False
                
        elif key_name == 'FRED_API_KEY':
            # FRED API金鑰：32字符，字母數字組合
            if len(key_value) != 32:
                logger.warning(f"FRED API金鑰應為32字符: {len(key_value)}")
                return False
            
            if not key_value.isalnum():
                logger.warning("FRED API金鑰包含非字母數字字符")
                return False
        else:
            logger.warning(f"未知的API金鑰類型: {key_name}")
            return False
        
        logger.info(f"{key_name} 格式驗證通過")
        return True
        
    except Exception as e:
        logger.error(f"API金鑰格式驗證失敗 {key_name}: {e}")
        return False


def test_api_connectivity(api_service: str, api_key: str) -> Dict[str, Any]:
    """
    測試API連通性
    
    Args:
        api_service: API服務名稱 ('tiingo' 或 'fred')
        api_key: API金鑰
        
    Returns:
        dict: 連通性測試結果
        {
            'is_connected': bool,
            'response_time_ms': float,
            'status_code': int,
            'error_message': str
        }
    """
    if api_service == 'tiingo':
        return _test_tiingo_api(api_key)
    elif api_service == 'fred':
        return _test_fred_api(api_key)
    else:
        return {
            'is_connected': False,
            'response_time_ms': 0.0,
            'status_code': 0,
            'error_message': f'不支援的API服務: {api_service}'
        }


def _test_tiingo_api(api_key: str) -> Dict[str, Any]:
    """測試Tiingo API連通性"""
    test_url = "https://api.tiingo.com/api/test"
    params = {'token': api_key}
    
    start_time = time.time()
    
    try:
        response = requests.get(test_url, params=params, timeout=10)
        response_time = (time.time() - start_time) * 1000
        
        if response.status_code == 200:
            result_data = response.json()
            if result_data.get('message') == 'You successfully sent a request':
                return {
                    'is_connected': True,
                    'response_time_ms': round(response_time, 2),
                    'status_code': 200,
                    'error_message': None
                }
        
        return {
            'is_connected': False,
            'response_time_ms': round(response_time, 2),
            'status_code': response.status_code,
            'error_message': f'API測試失敗: {response.text[:100]}'
        }
        
    except requests.exceptions.Timeout:
        return {
            'is_connected': False,
            'response_time_ms': (time.time() - start_time) * 1000,
            'status_code': 0,
            'error_message': 'API請求逾時'
        }
    except requests.exceptions.ConnectionError:
        return {
            'is_connected': False,
            'response_time_ms': (time.time() - start_time) * 1000,
            'status_code': 0,
            'error_message': 'API連線失敗'
        }
    except Exception as e:
        return {
            'is_connected': False,
            'response_time_ms': (time.time() - start_time) * 1000,
            'status_code': 0,
            'error_message': f'API測試異常: {str(e)}'
        }


def _test_fred_api(api_key: str) -> Dict[str, Any]:
    """測試FRED API連通性"""
    test_url = "https://api.stlouisfed.org/fred/series"
    params = {
        'series_id': 'GDP',
        'api_key': api_key,
        'file_type': 'json'
    }
    
    start_time = time.time()
    
    try:
        response = requests.get(test_url, params=params, timeout=10)
        response_time = (time.time() - start_time) * 1000
        
        if response.status_code == 200:
            result_data = response.json()
            if 'seriess' in result_data:
                return {
                    'is_connected': True,
                    'response_time_ms': round(response_time, 2),
                    'status_code': 200,
                    'error_message': None
                }
        
        return {
            'is_connected': False,
            'response_time_ms': round(response_time, 2),
            'status_code': response.status_code,
            'error_message': f'API測試失敗: {response.text[:100]}'
        }
        
    except requests.exceptions.Timeout:
        return {
            'is_connected': False,
            'response_time_ms': (time.time() - start_time) * 1000,
            'status_code': 0,
            'error_message': 'API請求逾時'
        }
    except requests.exceptions.ConnectionError:
        return {
            'is_connected': False,
            'response_time_ms': (time.time() - start_time) * 1000,
            'status_code': 0,
            'error_message': 'API連線失敗'
        }
    except Exception as e:
        return {
            'is_connected': False,
            'response_time_ms': (time.time() - start_time) * 1000,
            'status_code': 0,
            'error_message': f'API測試異常: {str(e)}'
        } 