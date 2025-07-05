"""
API安全機制與金鑰管理模組
實現第一章規格中定義的多層級安全機制
"""

import os
import logging
import requests
import time
from datetime import datetime, timedelta
from typing import Optional, Dict
from dotenv import load_dotenv
import time

# 設定日誌記錄
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_api_key(key_name: str, required: bool = True) -> Optional[str]:
    """
    安全獲取API金鑰的多層級策略
    
    Args:
        key_name: 金鑰名稱 ('TIINGO_API_KEY', 'FRED_API_KEY')
        required: 是否為必要金鑰
    
    Returns:
        str: API金鑰，如果找不到且required=True則拋出異常
    """
    
    # 第1層：Streamlit Secrets (雲端部署優先)
    try:
        import streamlit as st
        if hasattr(st, 'secrets') and key_name in st.secrets:
            key = st.secrets[key_name]
            if validate_api_key_format(key_name, key):
                logger.info(f"成功從Streamlit Secrets獲取{key_name}")
                return key
            else:
                logger.warning(f"Streamlit Secrets中的{key_name}格式無效")
    except Exception as e:
        logger.warning(f"無法從Streamlit Secrets獲取{key_name}: {e}")
    
    # 第2層：環境變數
    key = os.environ.get(key_name)
    if key and validate_api_key_format(key_name, key):
        logger.info(f"成功從環境變數獲取{key_name}")
        return key
    
    # 第3層：.env檔案 (本地開發)
    load_dotenv()
    key = os.getenv(key_name)
    if key and validate_api_key_format(key_name, key):
        logger.info(f"成功從.env檔案獲取{key_name}")
        return key
    
    # 第4層：錯誤處理
    if required:
        raise ValueError(f"必要API金鑰 {key_name} 未設定或格式無效")
    else:
        logger.warning(f"選用API金鑰 {key_name} 未設定，將使用備用方案")
        return None


def validate_api_key_format(key_name: str, key_value: str) -> bool:
    """
    驗證API金鑰格式
    
    Args:
        key_name: 金鑰名稱
        key_value: 金鑰值
    
    Returns:
        bool: 是否為有效格式
    """
    if not key_value or not isinstance(key_value, str):
        return False
    
    # Tiingo API金鑰驗證
    if key_name == 'TIINGO_API_KEY':
        # 至少20字符的字母數字組合
        return len(key_value) >= 20 and key_value.replace('_', '').replace('-', '').isalnum()
    
    # FRED API金鑰驗證  
    elif key_name == 'FRED_API_KEY':
        # 32字符的字母數字組合
        return len(key_value) == 32 and key_value.isalnum()
    
    return False


def test_api_connectivity(api_service: str, api_key: str) -> Dict:
    """
    測試API連通性
    
    Args:
        api_service: 'tiingo' 或 'fred'
        api_key: API金鑰
    
    Returns:
        dict: 連通性測試結果
    """
    test_result = {
        'service': api_service,
        'is_connected': False,
        'response_time': None,
        'error_message': None,
        'status_code': None
    }
    
    try:
        start_time = datetime.now()
        
        if api_service == 'tiingo':
            # 測試Tiingo API
            test_url = "https://api.tiingo.com/tiingo/daily/SPY/prices"
            test_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
            
            params = {
                'startDate': test_date,
                'endDate': test_date,
                'columns': 'date,adjClose',
                'token': api_key
            }
            
            response = requests.get(test_url, params=params, timeout=10)
            
        elif api_service == 'fred':
            # 測試FRED API
            test_url = "https://api.stlouisfed.org/fred/series/observations"
            test_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
            
            params = {
                'series_id': 'DGS1',
                'observation_start': test_date,
                'observation_end': test_date,
                'api_key': api_key,
                'file_type': 'json',
                'limit': 1
            }
            
            response = requests.get(test_url, params=params, timeout=10)
        
        else:
            raise ValueError(f"不支援的API服務: {api_service}")
        
        end_time = datetime.now()
        response_time = (end_time - start_time).total_seconds()
        
        test_result['response_time'] = response_time
        test_result['status_code'] = response.status_code
        
        if response.status_code == 200:
            test_result['is_connected'] = True
            logger.info(f"{api_service} API連通性測試成功，響應時間: {response_time:.2f}秒")
        else:
            test_result['error_message'] = f"HTTP {response.status_code}: {response.text}"
            logger.error(f"{api_service} API連通性測試失敗: {test_result['error_message']}")
            
    except requests.exceptions.Timeout:
        test_result['error_message'] = "請求超時"
        logger.error(f"{api_service} API連通性測試超時")
        
    except requests.exceptions.ConnectionError:
        test_result['error_message'] = "連接錯誤"
        logger.error(f"{api_service} API連接失敗")
        
    except Exception as e:
        test_result['error_message'] = str(e)
        logger.error(f"{api_service} API連通性測試異常: {e}")
    
    return test_result


def safe_api_request(url: str, params: Dict, service: str, max_retries: int = 3) -> Optional[Dict]:
    """
    安全的API請求，包含重試機制
    
    Args:
        url: API端點URL
        params: 請求參數
        service: 服務名稱
        max_retries: 最大重試次數
    
    Returns:
        Dict: API回應數據，失敗時返回None
    """
    for attempt in range(max_retries):
        try:
            response = requests.get(url, params=params, timeout=30)
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 429:
                # 速率限制，等待後重試
                wait_time = 2 ** attempt  # 指數退避
                logger.warning(f"{service} API速率限制，等待{wait_time}秒後重試")
                time.sleep(wait_time)
                continue
            else:
                logger.error(f"{service} API請求失敗: HTTP {response.status_code}")
                return None
                
        except requests.exceptions.Timeout:
            logger.warning(f"{service} API請求超時，第{attempt + 1}次重試")
            if attempt == max_retries - 1:
                logger.error(f"{service} API請求最終超時失敗")
                return None
                
        except Exception as e:
            logger.error(f"{service} API請求異常: {e}")
            return None
    
    return None


class APIKeyManager:
    """API金鑰管理器"""
    
    def __init__(self):
        self.keys = {}
        self.connectivity_status = {}
    
    def initialize_keys(self) -> Dict[str, bool]:
        """初始化所有API金鑰"""
        key_names = ['TIINGO_API_KEY', 'FRED_API_KEY']
        status = {}
        
        for key_name in key_names:
            try:
                key = get_api_key(key_name, required=False)
                if key:
                    self.keys[key_name] = key
                    status[key_name] = True
                    logger.info(f"成功獲取{key_name}")
                else:
                    status[key_name] = False
                    logger.warning(f"未能獲取{key_name}")
            except Exception as e:
                status[key_name] = False
                logger.error(f"獲取{key_name}時發生錯誤: {e}")
        
        return status
    
    def test_all_connections(self) -> Dict[str, Dict]:
        """測試所有API的連通性"""
        results = {}
        
        if 'TIINGO_API_KEY' in self.keys:
            results['tiingo'] = test_api_connectivity('tiingo', self.keys['TIINGO_API_KEY'])
        
        if 'FRED_API_KEY' in self.keys:
            results['fred'] = test_api_connectivity('fred', self.keys['FRED_API_KEY'])
        
        self.connectivity_status = results
        return results
    
    def get_key(self, service: str) -> Optional[str]:
        """獲取指定服務的API金鑰"""
        key_mapping = {
            'tiingo': 'TIINGO_API_KEY',
            'fred': 'FRED_API_KEY'
        }
        
        key_name = key_mapping.get(service)
        if key_name and key_name in self.keys:
            return self.keys[key_name]
        
        return None
    
    def is_service_available(self, service: str) -> bool:
        """檢查服務是否可用"""
        return (
            service in self.connectivity_status and 
            self.connectivity_status[service].get('is_connected', False)
        ) 