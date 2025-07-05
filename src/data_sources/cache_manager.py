"""
智能快取管理器

實作第1章第1.2節要求的智能快取管理系統：
1. 多層級快取策略
2. LRU與TTL過期機制
3. 快取統計與監控
4. 自動清理與優化
"""

import os
import json
import hashlib
import pickle
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass, field
from pathlib import Path
import logging

# 嘗試導入streamlit，如果失敗則使用本地快取
try:
    import streamlit as st
    HAS_STREAMLIT = True
except ImportError:
    HAS_STREAMLIT = False
    st = None

logger = logging.getLogger(__name__)


@dataclass
class CacheConfig:
    """快取配置"""
    # TTL設定（秒）
    historical_data_ttl: int = 86400      # 24小時
    simulation_data_ttl: int = 3600       # 1小時
    api_test_results_ttl: int = 300       # 5分鐘
    performance_metrics_ttl: int = 300    # 5分鐘
    
    # 大小限制
    max_cache_size_mb: int = 100          # 最大快取大小(MB)
    max_entries: int = 1000               # 最大條目數
    
    # 清理策略
    cleanup_threshold: float = 0.8        # 觸發清理的閾值
    cleanup_ratio: float = 0.3            # 清理比例
    
    # 本地快取路徑
    local_cache_dir: str = ".cache"
    
    # 策略配置
    enable_local_cache: bool = True
    enable_memory_cache: bool = True
    enable_compression: bool = True


@dataclass
class CacheEntry:
    """快取條目"""
    key: str
    data: Any
    created_at: datetime
    expires_at: Optional[datetime]
    access_count: int = 0
    last_accessed: datetime = field(default_factory=datetime.now)
    size_bytes: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def is_expired(self) -> bool:
        """檢查是否過期"""
        if self.expires_at is None:
            return False
        return datetime.now() > self.expires_at
    
    def touch(self):
        """更新訪問時間"""
        self.last_accessed = datetime.now()
        self.access_count += 1


class IntelligentCacheManager:
    """
    智能快取管理器
    
    提供多層級快取策略、自動清理、統計監控等功能
    """
    
    def __init__(self, config: Optional[CacheConfig] = None):
        """
        初始化快取管理器
        
        Args:
            config: 快取配置，如果為None則使用預設配置
        """
        self.config = config or CacheConfig()
        
        # 記憶體快取
        self._memory_cache: Dict[str, CacheEntry] = {}
        
        # 快取統計
        self.stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0,
            'cleanup_count': 0,
            'total_requests': 0,
            'memory_usage_mb': 0.0,
            'disk_usage_mb': 0.0
        }
        
        # 確保本地快取目錄存在
        if self.config.enable_local_cache:
            self._cache_dir = Path(self.config.local_cache_dir)
            self._cache_dir.mkdir(exist_ok=True)
        
        logger.info("IntelligentCacheManager 初始化完成")
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        獲取快取數據
        
        Args:
            key: 快取鍵
            default: 預設值
        
        Returns:
            快取的數據或預設值
        """
        self.stats['total_requests'] += 1
        
        try:
            # 1. 檢查記憶體快取
            if self.config.enable_memory_cache and key in self._memory_cache:
                entry = self._memory_cache[key]
                
                if not entry.is_expired():
                    entry.touch()
                    self.stats['hits'] += 1
                    logger.debug(f"記憶體快取命中: {key[:16]}...")
                    return entry.data
                else:
                    # 過期，移除
                    del self._memory_cache[key]
                    logger.debug(f"記憶體快取過期: {key[:16]}...")
            
            # 2. 檢查Streamlit快取
            if HAS_STREAMLIT:
                try:
                    streamlit_data = self._get_from_streamlit_cache(key)
                    if streamlit_data is not None:
                        self.stats['hits'] += 1
                        logger.debug(f"Streamlit快取命中: {key[:16]}...")
                        return streamlit_data
                except Exception as e:
                    logger.debug(f"Streamlit快取獲取失敗: {e}")
            
            # 3. 檢查本地檔案快取
            if self.config.enable_local_cache:
                local_data = self._get_from_local_cache(key)
                if local_data is not None:
                    self.stats['hits'] += 1
                    logger.debug(f"本地快取命中: {key[:16]}...")
                    
                    # 回填到記憶體快取
                    if self.config.enable_memory_cache:
                        self._store_in_memory(key, local_data)
                    
                    return local_data
            
            # 快取未命中
            self.stats['misses'] += 1
            logger.debug(f"快取未命中: {key[:16]}...")
            return default
            
        except Exception as e:
            logger.error(f"快取獲取錯誤: {e}")
            return default
    
    def set(
        self, 
        key: str, 
        data: Any, 
        ttl: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        設定快取數據
        
        Args:
            key: 快取鍵
            data: 要快取的數據
            ttl: 生存時間（秒），如果為None則使用預設TTL
            metadata: 額外的元數據
        """
        try:
            # 決定TTL
            if ttl is None:
                ttl = self._get_default_ttl(key)
            
            expires_at = datetime.now() + timedelta(seconds=ttl) if ttl > 0 else None
            
            # 1. 記憶體快取
            if self.config.enable_memory_cache:
                self._store_in_memory(key, data, expires_at, metadata)
            
            # 2. Streamlit快取
            if HAS_STREAMLIT:
                try:
                    self._store_in_streamlit_cache(key, data, ttl)
                except Exception as e:
                    logger.debug(f"Streamlit快取存儲失敗: {e}")
            
            # 3. 本地檔案快取
            if self.config.enable_local_cache:
                self._store_in_local_cache(key, data, expires_at, metadata)
            
            # 檢查是否需要清理
            self._check_and_cleanup()
            
            logger.debug(f"快取已設定: {key[:16]}... (TTL: {ttl}s)")
            
        except Exception as e:
            logger.error(f"快取設定錯誤: {e}")
    
    def delete(self, key: str) -> bool:
        """
        刪除快取條目
        
        Args:
            key: 快取鍵
        
        Returns:
            bool: 是否成功刪除
        """
        deleted = False
        
        try:
            # 從記憶體快取刪除
            if key in self._memory_cache:
                del self._memory_cache[key]
                deleted = True
            
            # 從本地快取刪除
            if self.config.enable_local_cache:
                cache_file = self._get_cache_file_path(key)
                if cache_file.exists():
                    cache_file.unlink()
                    deleted = True
            
            # Streamlit快取會自動處理過期
            
            if deleted:
                logger.debug(f"快取已刪除: {key[:16]}...")
            
            return deleted
            
        except Exception as e:
            logger.error(f"快取刪除錯誤: {e}")
            return False
    
    def clear(self, pattern: Optional[str] = None):
        """
        清除快取
        
        Args:
            pattern: 要清除的鍵模式，如果為None則清除所有
        """
        try:
            if pattern is None:
                # 清除所有快取
                self._memory_cache.clear()
                
                if self.config.enable_local_cache and self._cache_dir.exists():
                    for cache_file in self._cache_dir.glob("*.cache"):
                        cache_file.unlink()
                
                if HAS_STREAMLIT:
                    st.cache_data.clear()
                
                logger.info("已清除所有快取")
            else:
                # 根據模式清除
                keys_to_delete = [
                    key for key in self._memory_cache.keys() 
                    if pattern in key
                ]
                
                for key in keys_to_delete:
                    self.delete(key)
                
                logger.info(f"已清除匹配模式 '{pattern}' 的快取: {len(keys_to_delete)} 個條目")
            
        except Exception as e:
            logger.error(f"快取清除錯誤: {e}")
    
    def _store_in_memory(
        self, 
        key: str, 
        data: Any, 
        expires_at: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """存儲到記憶體快取"""
        try:
            # 計算數據大小
            size_bytes = len(pickle.dumps(data))
            
            entry = CacheEntry(
                key=key,
                data=data,
                created_at=datetime.now(),
                expires_at=expires_at,
                size_bytes=size_bytes,
                metadata=metadata or {}
            )
            
            self._memory_cache[key] = entry
            self._update_memory_usage()
            
        except Exception as e:
            logger.error(f"記憶體快取存儲失敗: {e}")
    
    def _get_from_streamlit_cache(self, key: str) -> Optional[Any]:
        """從Streamlit快取獲取數據"""
        if not HAS_STREAMLIT:
            return None
        
        # Streamlit快取通過裝飾器處理，這裡簡化處理
        return None
    
    def _store_in_streamlit_cache(self, key: str, data: Any, ttl: int):
        """存儲到Streamlit快取"""
        if not HAS_STREAMLIT:
            return
        
        # Streamlit快取通過裝飾器處理
        pass
    
    def _get_from_local_cache(self, key: str) -> Optional[Any]:
        """從本地檔案快取獲取數據"""
        try:
            cache_file = self._get_cache_file_path(key)
            
            if not cache_file.exists():
                return None
            
            with open(cache_file, 'rb') as f:
                cache_data = pickle.load(f)
            
            # 檢查過期時間
            if 'expires_at' in cache_data:
                expires_at = cache_data['expires_at']
                if expires_at and datetime.now() > expires_at:
                    cache_file.unlink()  # 刪除過期檔案
                    return None
            
            return cache_data.get('data')
            
        except Exception as e:
            logger.debug(f"本地快取讀取失敗: {e}")
            return None
    
    def _store_in_local_cache(
        self, 
        key: str, 
        data: Any, 
        expires_at: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """存儲到本地檔案快取"""
        try:
            cache_file = self._get_cache_file_path(key)
            
            cache_data = {
                'key': key,
                'data': data,
                'created_at': datetime.now(),
                'expires_at': expires_at,
                'metadata': metadata or {}
            }
            
            # 可選壓縮
            if self.config.enable_compression:
                import gzip
                with gzip.open(cache_file.with_suffix('.cache.gz'), 'wb') as f:
                    pickle.dump(cache_data, f)
            else:
                with open(cache_file, 'wb') as f:
                    pickle.dump(cache_data, f)
            
        except Exception as e:
            logger.error(f"本地快取存儲失敗: {e}")
    
    def _get_cache_file_path(self, key: str) -> Path:
        """獲取快取檔案路徑"""
        # 使用MD5雜湊避免檔案名過長或包含特殊字符
        safe_key = hashlib.md5(key.encode()).hexdigest()
        
        if self.config.enable_compression:
            return self._cache_dir / f"{safe_key}.cache.gz"
        else:
            return self._cache_dir / f"{safe_key}.cache"
    
    def _get_default_ttl(self, key: str) -> int:
        """根據鍵類型獲取預設TTL"""
        if 'historical_data' in key:
            return self.config.historical_data_ttl
        elif 'simulation' in key:
            return self.config.simulation_data_ttl
        elif 'api_test' in key:
            return self.config.api_test_results_ttl
        elif 'performance' in key:
            return self.config.performance_metrics_ttl
        else:
            return self.config.historical_data_ttl  # 預設值
    
    def _check_and_cleanup(self):
        """檢查並執行清理"""
        try:
            # 檢查記憶體使用量
            current_usage = self._calculate_memory_usage_mb()
            
            if current_usage > self.config.max_cache_size_mb * self.config.cleanup_threshold:
                self._cleanup_memory_cache()
            
            # 檢查條目數量
            if len(self._memory_cache) > self.config.max_entries * self.config.cleanup_threshold:
                self._cleanup_memory_cache()
            
            # 定期清理過期條目
            self._cleanup_expired_entries()
            
        except Exception as e:
            logger.error(f"快取清理檢查失敗: {e}")
    
    def _cleanup_memory_cache(self):
        """清理記憶體快取"""
        try:
            if not self._memory_cache:
                return
            
            # LRU策略：按最後訪問時間排序
            entries = list(self._memory_cache.items())
            entries.sort(key=lambda x: x[1].last_accessed)
            
            # 計算要清理的條目數
            cleanup_count = int(len(entries) * self.config.cleanup_ratio)
            
            # 移除最舊的條目
            for i in range(cleanup_count):
                key, _ = entries[i]
                del self._memory_cache[key]
                self.stats['evictions'] += 1
            
            self.stats['cleanup_count'] += 1
            self._update_memory_usage()
            
            logger.info(f"記憶體快取清理完成: 移除 {cleanup_count} 個條目")
            
        except Exception as e:
            logger.error(f"記憶體快取清理失敗: {e}")
    
    def _cleanup_expired_entries(self):
        """清理過期條目"""
        try:
            expired_keys = []
            
            for key, entry in self._memory_cache.items():
                if entry.is_expired():
                    expired_keys.append(key)
            
            for key in expired_keys:
                del self._memory_cache[key]
            
            if expired_keys:
                self._update_memory_usage()
                logger.debug(f"清理過期條目: {len(expired_keys)} 個")
            
        except Exception as e:
            logger.error(f"過期條目清理失敗: {e}")
    
    def _calculate_memory_usage_mb(self) -> float:
        """計算記憶體使用量(MB)"""
        try:
            total_bytes = sum(entry.size_bytes for entry in self._memory_cache.values())
            return total_bytes / (1024 * 1024)
        except Exception:
            return 0.0
    
    def _update_memory_usage(self):
        """更新記憶體使用統計"""
        self.stats['memory_usage_mb'] = self._calculate_memory_usage_mb()
    
    def generate_cache_key(
        self, 
        prefix: str, 
        params: Dict[str, Any],
        include_timestamp: bool = False
    ) -> str:
        """
        生成快取鍵
        
        Args:
            prefix: 鍵前綴
            params: 參數字典
            include_timestamp: 是否包含時間戳
        
        Returns:
            str: 生成的快取鍵
        """
        try:
            # 標準化參數
            normalized_params = {}
            for key, value in params.items():
                if value is not None:
                    if isinstance(value, (datetime, timedelta)):
                        normalized_params[key] = value.isoformat()
                    else:
                        normalized_params[key] = str(value)
            
            # 排序確保一致性
            sorted_params = sorted(normalized_params.items())
            
            # 生成參數字符串
            params_str = "&".join(f"{k}={v}" for k, v in sorted_params)
            
            # 組合鍵
            key_parts = [prefix]
            if params_str:
                key_parts.append(params_str)
            
            if include_timestamp:
                key_parts.append(datetime.now().strftime("%Y%m%d%H"))
            
            cache_key = "|".join(key_parts)
            
            # 如果鍵太長，使用雜湊
            if len(cache_key) > 200:
                cache_key = f"{prefix}|{hashlib.md5(cache_key.encode()).hexdigest()}"
            
            return cache_key
            
        except Exception as e:
            logger.error(f"快取鍵生成失敗: {e}")
            return f"{prefix}|{hashlib.md5(str(params).encode()).hexdigest()}"
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """獲取快取統計信息"""
        stats = self.stats.copy()
        
        # 計算命中率
        if stats['total_requests'] > 0:
            stats['hit_rate'] = stats['hits'] / stats['total_requests']
            stats['miss_rate'] = stats['misses'] / stats['total_requests']
        else:
            stats['hit_rate'] = 0.0
            stats['miss_rate'] = 0.0
        
        # 添加快取狀態
        stats['memory_entries'] = len(self._memory_cache)
        stats['memory_usage_mb'] = self._calculate_memory_usage_mb()
        
        # 計算本地快取大小
        if self.config.enable_local_cache and self._cache_dir.exists():
            try:
                disk_usage = sum(
                    f.stat().st_size for f in self._cache_dir.iterdir() 
                    if f.is_file()
                )
                stats['disk_usage_mb'] = disk_usage / (1024 * 1024)
            except Exception:
                stats['disk_usage_mb'] = 0.0
        
        return stats
    
    def reset_stats(self):
        """重設快取統計"""
        self.stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0,
            'cleanup_count': 0,
            'total_requests': 0,
            'memory_usage_mb': 0.0,
            'disk_usage_mb': 0.0
        }
        logger.info("快取統計已重設")


# Streamlit快取裝飾器（如果可用）
def cached_data(ttl: int = 3600, max_entries: int = 100):
    """
    Streamlit快取裝飾器包裝器
    
    Args:
        ttl: 生存時間（秒）
        max_entries: 最大條目數
    """
    if HAS_STREAMLIT:
        return st.cache_data(ttl=ttl, max_entries=max_entries)
    else:
        # 如果沒有Streamlit，返回空裝飾器
        def decorator(func):
            return func
        return decorator


def cached_resource(ttl: int = 3600):
    """
    Streamlit資源快取裝飾器包裝器
    
    Args:
        ttl: 生存時間（秒）
    """
    if HAS_STREAMLIT:
        return st.cache_resource(ttl=ttl)
    else:
        def decorator(func):
            return func
        return decorator


# 全域快取管理器實例
_global_cache_manager: Optional[IntelligentCacheManager] = None


def get_cache_manager() -> IntelligentCacheManager:
    """獲取全域快取管理器實例"""
    global _global_cache_manager
    
    if _global_cache_manager is None:
        _global_cache_manager = IntelligentCacheManager()
    
    return _global_cache_manager


def set_cache_manager(manager: IntelligentCacheManager):
    """設定全域快取管理器"""
    global _global_cache_manager
    _global_cache_manager = manager 