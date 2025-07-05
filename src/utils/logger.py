"""
投資策略比較系統 - 日誌系統模組
提供統一的日誌配置和管理功能

作者：VA_DC_APP7 系統
版本：1.0
日期：2024年
"""

import logging
import sys
from pathlib import Path
from typing import Optional
from datetime import datetime
import os

class LoggerConfig:
    """日誌配置類別"""
    
    # 日誌級別映射
    LEVEL_MAPPING = {
        'DEBUG': logging.DEBUG,
        'INFO': logging.INFO,
        'WARNING': logging.WARNING,
        'ERROR': logging.ERROR,
        'CRITICAL': logging.CRITICAL
    }
    
    # 預設配置
    DEFAULT_LEVEL = 'INFO'
    DEFAULT_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    DEFAULT_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'
    
    @classmethod
    def setup_logging(
        cls,
        level: str = DEFAULT_LEVEL,
        log_file: Optional[str] = None,
        console_output: bool = True,
        format_string: Optional[str] = None,
        date_format: Optional[str] = None
    ) -> logging.Logger:
        """
        設定日誌系統
        
        Args:
            level: 日誌級別
            log_file: 日誌檔案路徑
            console_output: 是否輸出到控制台
            format_string: 自定義格式字串
            date_format: 日期格式
            
        Returns:
            配置好的Logger實例
        """
        # 創建root logger
        logger = logging.getLogger()
        logger.setLevel(cls.LEVEL_MAPPING.get(level.upper(), logging.INFO))
        
        # 清除現有handlers
        logger.handlers.clear()
        
        # 設定格式器
        formatter = logging.Formatter(
            format_string or cls.DEFAULT_FORMAT,
            datefmt=date_format or cls.DEFAULT_DATE_FORMAT
        )
        
        # 控制台輸出
        if console_output:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)
        
        # 檔案輸出
        if log_file:
            cls._setup_file_handler(logger, log_file, formatter)
        
        return logger
    
    @classmethod
    def _setup_file_handler(cls, logger: logging.Logger, log_file: str, formatter: logging.Formatter):
        """設定檔案處理器"""
        try:
            # 確保日誌目錄存在
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 創建檔案處理器
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
            
        except Exception as e:
            # 如果無法創建檔案處理器，記錄警告但不中斷程序
            logger.warning(f"無法創建日誌檔案 {log_file}: {e}")
    
    @classmethod
    def get_logger(cls, name: str, level: Optional[str] = None) -> logging.Logger:
        """
        獲取指定名稱的Logger
        
        Args:
            name: Logger名稱
            level: 可選的日誌級別覆蓋
            
        Returns:
            Logger實例
        """
        logger = logging.getLogger(name)
        
        if level and level.upper() in cls.LEVEL_MAPPING:
            logger.setLevel(cls.LEVEL_MAPPING[level.upper()])
        
        return logger

class SystemLogger:
    """系統日誌管理器"""
    
    def __init__(self, component_name: str):
        """
        初始化系統日誌管理器
        
        Args:
            component_name: 組件名稱
        """
        self.component_name = component_name
        self.logger = LoggerConfig.get_logger(component_name)
    
    def info(self, message: str, **kwargs):
        """記錄資訊級別日誌"""
        self.logger.info(f"[{self.component_name}] {message}", **kwargs)
    
    def debug(self, message: str, **kwargs):
        """記錄除錯級別日誌"""
        self.logger.debug(f"[{self.component_name}] {message}", **kwargs)
    
    def warning(self, message: str, **kwargs):
        """記錄警告級別日誌"""
        self.logger.warning(f"[{self.component_name}] {message}", **kwargs)
    
    def error(self, message: str, exception: Optional[Exception] = None, **kwargs):
        """記錄錯誤級別日誌"""
        error_msg = f"[{self.component_name}] {message}"
        if exception:
            error_msg += f" - 異常: {str(exception)}"
        self.logger.error(error_msg, **kwargs)
    
    def critical(self, message: str, exception: Optional[Exception] = None, **kwargs):
        """記錄嚴重級別日誌"""
        critical_msg = f"[{self.component_name}] {message}"
        if exception:
            critical_msg += f" - 異常: {str(exception)}"
        self.logger.critical(critical_msg, **kwargs)
    
    def log_performance(self, operation: str, duration: float, **kwargs):
        """記錄性能相關日誌"""
        self.info(f"性能監控 - {operation}: 耗時 {duration:.3f} 秒", **kwargs)
    
    def log_data_quality(self, data_type: str, quality_score: float, details: str = "", **kwargs):
        """記錄數據品質相關日誌"""
        self.info(f"數據品質 - {data_type}: 分數 {quality_score:.1f} {details}", **kwargs)

def setup_application_logging(
    app_name: str = "VA_DC_APP7",
    log_level: str = "INFO",
    enable_file_logging: bool = True,
    log_directory: str = "logs"
) -> logging.Logger:
    """
    設定應用程式級別的日誌系統
    
    Args:
        app_name: 應用程式名稱
        log_level: 日誌級別
        enable_file_logging: 是否啟用檔案日誌
        log_directory: 日誌目錄
        
    Returns:
        配置好的Logger實例
    """
    # 創建日誌檔案名稱（包含時間戳）
    log_file = None
    if enable_file_logging:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_filename = f"{app_name}_{timestamp}.log"
        log_file = os.path.join(log_directory, log_filename)
    
    # 設定日誌系統
    logger = LoggerConfig.setup_logging(
        level=log_level,
        log_file=log_file,
        console_output=True
    )
    
    logger.info(f"=== {app_name} 日誌系統啟動 ===")
    logger.info(f"日誌級別: {log_level}")
    if log_file:
        logger.info(f"日誌檔案: {log_file}")
    
    return logger

# 便利函數
def get_component_logger(component_name: str) -> SystemLogger:
    """
    獲取組件專用的日誌管理器
    
    Args:
        component_name: 組件名稱
        
    Returns:
        SystemLogger實例
    """
    return SystemLogger(component_name)

# 預設日誌配置（如果直接導入此模組）
if not logging.getLogger().handlers:
    setup_application_logging() 