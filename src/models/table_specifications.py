"""
表格規格定義模組 (Table Specifications Module)

本模組定義了投資策略比較系統中所有表格的完整數據結構，包括：
- VA策略表格規格
- DCA策略表格規格  
- 綜合比較摘要表格規格
- 表格格式化規則
- 數據驗證標準

嚴格遵循需求文件第2章第2.2節的規格要求。
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, date
import logging

# 設置日誌
logger = logging.getLogger(__name__)

# ============================================================================
# 2.2.1 VA策略完整數據結構定義
# ============================================================================

VA_COLUMN_SPECS = {
    # 期間與日期欄位
    "Period": {
        "type": "int", 
        "description": "期數（1,2,3,4,...）",
        "format": "整數",
        "validation": ">=1"
    },
    "Date_Origin": {
        "type": "date",
        "description": "當期起始日期", 
        "format": "YYYY-MM-DD",
        "validation": "valid_date"
    },
    "Date_End": {
        "type": "date",
        "description": "當期期末日期",
        "format": "YYYY-MM-DD", 
        "validation": "valid_date"
    },
    
    # 市場價格欄位
    "SPY_Price_Origin": {
        "type": "float",
        "description": "當期期初SPY調整後收盤價",
        "format": "2位小數",
        "validation": ">0"
    },
    "SPY_Price_End": {
        "type": "float", 
        "description": "當期期末SPY調整後收盤價",
        "format": "2位小數",
        "validation": ">0"
    },
    "Bond_Yield_Origin": {
        "type": "float",
        "description": "當期期初債券殖利率(%)",
        "format": "2位小數",
        "validation": "合理範圍"
    },
    "Bond_Yield_End": {
        "type": "float",
        "description": "當期期末債券殖利率(%)", 
        "format": "2位小數",
        "validation": "合理範圍"
    },
    "Bond_Price_Origin": {
        "type": "float",
        "description": "當期期初債券價格",
        "format": "2位小數", 
        "validation": ">0"
    },
    "Bond_Price_End": {
        "type": "float",
        "description": "當期期末債券價格",
        "format": "2位小數",
        "validation": ">0"
    },
    
    # VA策略特有欄位
    "Prev_Stock_Units": {
        "type": "float",
        "description": "前期累積股票單位數",
        "format": "4位小數",
        "validation": ">=0"
    },
    "Prev_Bond_Units": {
        "type": "float",
        "description": "前期累積債券單位數",
        "format": "4位小數",
        "validation": ">=0"
    },
    "Initial_Investment": {
        "type": "float", 
        "description": "期初投入金額",
        "format": "千分位符號",
        "validation": ">0"
    },
    "VA_Target": {
        "type": "float",
        "description": "VA公式計算的當期目標資產價值", 
        "format": "千分位符號",
        "validation": ">0"
    },
    "Current_Asset_Value": {
        "type": "float",
        "description": "當期調整前資產價值 = 當期期末股票價格×前期股票累積單位數 + 當期期末債券價格×前期債券累積單位數",
        "format": "千分位符號", 
        "validation": ">=0"
    },
    "Invested": {
        "type": "float",
        "description": "當期實際投入/賣出金額（須視再平衡機制調整）",
        "format": "千分位符號，負值顯示括號",
        "validation": "可為負值"
    },
    
    # 交易單位欄位
    "stock_trade_units": {
        "type": "float",
        "description": "當期股票買賣單位數",
        "format": "4位小數，負值顯示括號",
        "validation": "可為負值"
    },
    "bond_trade_units": {
        "type": "float", 
        "description": "當期債券買賣單位數",
        "format": "4位小數，負值顯示括號",
        "validation": "可為負值"
    },
    
    # 累積欄位
    "Cum_stock_units": {
        "type": "float",
        "description": "累積股票單位數",
        "format": "4位小數",
        "validation": ">=0"
    },
    "Cum_bond_units": {
        "type": "float",
        "description": "累積債券單位數", 
        "format": "4位小數",
        "validation": ">=0"
    },
    "Cum_Inv": {
        "type": "float",
        "description": "累計投入金額",
        "format": "千分位符號", 
        "validation": ">0"
    },
    "Cum_Value": {
        "type": "float",
        "description": "當期期末資產價值 = 當期期末股票價格×當期股票累積單位數 + 當期期末債券價格×當期債券累積單位數",
        "format": "千分位符號",
        "validation": ">0"
    },
    
    # 績效指標欄位
    "Period_Return": {
        "type": "float",
        "description": "當期報酬率(%)",
        "format": "2位小數%",
        "validation": "合理範圍"
    },
    "Cumulative_Return": {
        "type": "float", 
        "description": "累計報酬率(%)",
        "format": "2位小數%",
        "validation": "合理範圍"
    },
    "Annualized_Return": {
        "type": "float",
        "description": "截至當期的年化報酬率(%)",
        "format": "2位小數%",
        "validation": "合理範圍"
    }
}

# 完整VA欄位順序定義 - 期末相關欄位調整到VA_Target附近，反映VA策略期末執行特性
VA_COLUMNS_ORDER = [
    "Period", "Date_Origin", "SPY_Price_Origin", "Bond_Yield_Origin",
    "Bond_Price_Origin", "Prev_Stock_Units", "Prev_Bond_Units", "Initial_Investment",
    "Date_End", "VA_Target", "SPY_Price_End", "Bond_Yield_End", "Bond_Price_End",
    "Current_Asset_Value", "Invested", "Cum_Inv", "stock_trade_units", "bond_trade_units",
    "Cum_stock_units", "Cum_bond_units", "Cum_Value", "Period_Return", 
    "Cumulative_Return", "Annualized_Return"
]

# ============================================================================
# 2.2.2 DCA策略完整數據結構定義
# ============================================================================

# DCA策略繼承VA策略的基本欄位，但排除VA特有欄位
DCA_COLUMN_SPECS = {
    # 繼承VA策略的基本欄位（保留Prev_Stock_Units和Prev_Bond_Units用於股債比例計算）
    **{k: v for k, v in VA_COLUMN_SPECS.items() 
       if k not in ["VA_Target", "Current_Asset_Value", "Invested"]},
    
    # DCA策略特有欄位
    "Fixed_Investment": {
        "type": "float",
        "description": "固定投入金額(含通膨調整)",
        "format": "千分位符號",
        "validation": ">0"
    }
}

# 完整DCA欄位順序
DCA_COLUMNS_ORDER = [
    "Period", "Date_Origin", "SPY_Price_Origin", "Bond_Yield_Origin",
    "Bond_Price_Origin", "Initial_Investment", "Prev_Stock_Units", "Prev_Bond_Units", 
    "Fixed_Investment", "stock_trade_units", "bond_trade_units", "Cum_stock_units", "Cum_bond_units",
    "Cum_Inv", "Date_End", "SPY_Price_End", "Bond_Yield_End", "Bond_Price_End",
    "Cum_Value", "Period_Return", "Cumulative_Return", "Annualized_Return"
]

# ============================================================================
# 2.2.3 綜合比較摘要表格規格
# ============================================================================

SUMMARY_COLUMN_SPECS = {
    # 與原始requirements.md保持一致的欄位規格
    "Strategy": {
        "type": "str",
        "description": "策略名稱(VA/DCA)", 
        "format": "字串",
        "validation": "預設選項"
    },
    "Final_Value": {
        "type": "float",
        "description": "期末總資產價值",
        "format": "千分位符號",
        "validation": ">0"
    },
    "Total_Investment": {
        "type": "float", 
        "description": "累計總投入金額",
        "format": "千分位符號",
        "validation": ">0"
    },
    "Total_Return": {
        "type": "float",
        "description": "總報酬率(%)",
        "format": "2位小數%",
        "validation": "合理範圍"
    },
    "Annualized_Return": {
        "type": "float",
        "description": "年化報酬率(%)",
        "format": "2位小數%", 
        "validation": "合理範圍"
    },
    "Volatility": {
        "type": "float",
        "description": "年化波動率(%)",
        "format": "2位小數%",
        "validation": ">0"
    },
    "Sharpe_Ratio": {
        "type": "float", 
        "description": "夏普比率",
        "format": "2位小數",
        "validation": "合理範圍"
    },
    "Max_Drawdown": {
        "type": "float",
        "description": "最大回撤(%)",
        "format": "2位小數%",
        "validation": ">=0"
    }
}

# 完整Summary欄位順序 - 與原始requirements.md一致
SUMMARY_COLUMNS_ORDER = [
    "Strategy", "Final_Value", "Total_Investment", "Total_Return", 
    "Annualized_Return", "Volatility", "Sharpe_Ratio", "Max_Drawdown"
]

# ============================================================================
# 2.2.4 表格格式化與驗證模組配置
# ============================================================================

# 統一百分比格式精度標準
PERCENTAGE_PRECISION_RULES = {
    "Period_Return": 2,        # 期間報酬率: 2位小數
    "Cumulative_Return": 2,    # 累計報酬率: 2位小數  
    "Annualized_Return": 2,    # 年化報酬率: 2位小數
    "Volatility": 2,           # 波動率: 2位小數
    "Sharpe_Ratio": 2,         # 夏普比率: 2位小數
    "Total_Return": 2,         # 總報酬率: 2位小數
    "Max_Drawdown": 2,         # 最大回撤: 2位小數
    "Bond_Yield_Origin": 2,    # 債券殖利率: 2位小數
    "Bond_Yield_End": 2        # 債券殖利率: 2位小數
}

# 數值比較容差標準
NUMERIC_TOLERANCE = 1e-6

# 支援的策略類型
SUPPORTED_STRATEGY_TYPES = ["VA", "DCA", "SUMMARY"]

# 必要欄位檢查映射
REQUIRED_COLUMNS_MAP = {
    "VA": set(VA_COLUMN_SPECS.keys()),
    "DCA": set(DCA_COLUMN_SPECS.keys()),
    "SUMMARY": set(SUMMARY_COLUMN_SPECS.keys())
}

# 欄位順序映射
COLUMNS_ORDER_MAP = {
    "VA": VA_COLUMNS_ORDER,
    "DCA": DCA_COLUMNS_ORDER,
    "SUMMARY": SUMMARY_COLUMNS_ORDER
}

# 欄位規格映射
COLUMN_SPECS_MAP = {
    "VA": VA_COLUMN_SPECS,
    "DCA": DCA_COLUMN_SPECS,
    "SUMMARY": SUMMARY_COLUMN_SPECS
}

# ============================================================================
# 輔助函數
# ============================================================================

def get_column_specs(strategy_type: str) -> Dict[str, Dict[str, Any]]:
    """
    獲取指定策略類型的欄位規格
    
    Args:
        strategy_type: 策略類型 ("VA", "DCA", "SUMMARY")
    
    Returns:
        Dict: 欄位規格字典
    
    Raises:
        ValueError: 當策略類型不支援時
    """
    if strategy_type not in COLUMN_SPECS_MAP:
        raise ValueError(f"不支援的策略類型: {strategy_type}")
    
    return COLUMN_SPECS_MAP[strategy_type]

def get_columns_order(strategy_type: str) -> List[str]:
    """
    獲取指定策略類型的欄位順序
    
    Args:
        strategy_type: 策略類型 ("VA", "DCA", "SUMMARY")
    
    Returns:
        List[str]: 欄位順序列表
    
    Raises:
        ValueError: 當策略類型不支援時
    """
    if strategy_type not in COLUMNS_ORDER_MAP:
        raise ValueError(f"不支援的策略類型: {strategy_type}")
    
    return COLUMNS_ORDER_MAP[strategy_type]

def get_required_columns(strategy_type: str) -> set:
    """
    獲取指定策略類型的必要欄位
    
    Args:
        strategy_type: 策略類型 ("VA", "DCA", "SUMMARY")
    
    Returns:
        set: 必要欄位集合
    
    Raises:
        ValueError: 當策略類型不支援時
    """
    if strategy_type not in REQUIRED_COLUMNS_MAP:
        raise ValueError(f"不支援的策略類型: {strategy_type}")
    
    return REQUIRED_COLUMNS_MAP[strategy_type]

def is_percentage_column(column_name: str) -> bool:
    """
    判斷欄位是否為百分比類型
    
    Args:
        column_name: 欄位名稱
    
    Returns:
        bool: True表示是百分比欄位
    """
    return column_name in PERCENTAGE_PRECISION_RULES

def get_percentage_precision(column_name: str) -> int:
    """
    獲取百分比欄位的精確度
    
    Args:
        column_name: 欄位名稱
    
    Returns:
        int: 小數位數，預設為2
    """
    return PERCENTAGE_PRECISION_RULES.get(column_name, 2)

def is_currency_column(column_name: str, column_specs: Dict[str, Dict[str, Any]]) -> bool:
    """
    判斷欄位是否為金額類型
    
    Args:
        column_name: 欄位名稱
        column_specs: 欄位規格字典
    
    Returns:
        bool: True表示是金額欄位
    """
    if column_name not in column_specs:
        return False
    
    format_str = column_specs[column_name].get("format", "")
    return "千分位符號" in format_str

def is_units_column(column_name: str, column_specs: Dict[str, Dict[str, Any]]) -> bool:
    """
    判斷欄位是否為單位數類型
    
    Args:
        column_name: 欄位名稱
        column_specs: 欄位規格字典
    
    Returns:
        bool: True表示是單位數欄位
    """
    if column_name not in column_specs:
        return False
    
    format_str = column_specs[column_name].get("format", "")
    return "位小數" in format_str and "%" not in format_str

def get_decimal_places(column_name: str, column_specs: Dict[str, Dict[str, Any]]) -> int:
    """
    獲取欄位的小數位數
    
    Args:
        column_name: 欄位名稱
        column_specs: 欄位規格字典
    
    Returns:
        int: 小數位數，預設為2
    """
    if column_name not in column_specs:
        return 2
    
    format_str = column_specs[column_name].get("format", "")
    if "位小數" in format_str:
        try:
            return int(format_str.split("位")[0])
        except (ValueError, IndexError):
            return 2
    
    return 2

def validate_strategy_type(strategy_type: str) -> bool:
    """
    驗證策略類型是否有效
    
    Args:
        strategy_type: 策略類型
    
    Returns:
        bool: True表示有效
    """
    return strategy_type in SUPPORTED_STRATEGY_TYPES

# ============================================================================
# 測試函數
# ============================================================================

def test_table_specifications():
    """
    測試表格規格定義的完整性
    """
    print("開始測試表格規格定義...")
    
    try:
        # 測試所有策略類型的規格獲取
        for strategy_type in SUPPORTED_STRATEGY_TYPES:
            specs = get_column_specs(strategy_type)
            order = get_columns_order(strategy_type)
            required = get_required_columns(strategy_type)
            
            print(f"✓ {strategy_type}策略規格獲取成功:")
            print(f"  - 欄位數量: {len(specs)}")
            print(f"  - 排序欄位數量: {len(order)}")
            print(f"  - 必要欄位數量: {len(required)}")
        
        # 測試百分比欄位識別
        percentage_columns = [col for col in PERCENTAGE_PRECISION_RULES.keys()]
        print(f"✓ 識別出{len(percentage_columns)}個百分比欄位")
        
        # 測試欄位類型判斷
        test_column = "Cum_Value"
        va_specs = get_column_specs("VA")
        is_currency = is_currency_column(test_column, va_specs)
        print(f"✓ {test_column}是否為金額欄位: {is_currency}")
        
        print("\n✅ 所有表格規格定義測試通過！")
        
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        raise

if __name__ == "__main__":
    test_table_specifications() 