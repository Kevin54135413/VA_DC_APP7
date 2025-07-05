"""
表格格式化與驗證模組 (Table Formatter Module)

本模組提供投資策略比較系統的表格格式化與數據驗證功能，包括：
- 數據格式化函數 (format_currency, format_percentage等)
- 表格生成與驗證函數 (generate_formatted_table, validate_table_data)
- CSV匯出功能
- 數據一致性檢查

嚴格遵循需求文件第2章第2.2節的規格要求。
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Union, Tuple
from datetime import datetime, date
import logging
import io
import csv

# 導入表格規格定義
from .table_specifications import (
    PERCENTAGE_PRECISION_RULES, NUMERIC_TOLERANCE,
    get_column_specs, get_columns_order, get_required_columns,
    is_percentage_column, get_percentage_precision,
    is_currency_column, is_units_column, get_decimal_places,
    validate_strategy_type
)

# 設置日誌
logger = logging.getLogger(__name__)

# ============================================================================
# 2.2.4 表格格式化與驗證模組
# ============================================================================

def format_currency(value: Union[float, int, None], decimal_places: int = 2) -> str:
    """
    格式化金額顯示（千分位符號）
    
    Args:
        value: 要格式化的數值
        decimal_places: 小數位數，預設為2
    
    Returns:
        str: 格式化後的金額字串，如 "$1,234.56"
    """
    if pd.isna(value) or value is None:
        return "N/A"
    
    try:
        return f"${value:,.{decimal_places}f}"
    except (ValueError, TypeError):
        return "N/A"

def format_percentage(value: Union[float, int, None], 
                     column_name: Optional[str] = None, 
                     decimal_places: int = 2) -> str:
    """
    格式化百分比顯示（支援欄位特定精度）
    
    Args:
        value: 要格式化的數值
        column_name: 欄位名稱，用於決定精度
        decimal_places: 預設小數位數
    
    Returns:
        str: 格式化後的百分比字串，如 "12.34%"
    """
    if pd.isna(value) or value is None:
        return "N/A"
    
    # 使用欄位特定精度，若未定義則使用預設值
    if column_name and column_name in PERCENTAGE_PRECISION_RULES:
        decimal_places = PERCENTAGE_PRECISION_RULES[column_name]
    
    try:
        return f"{value:.{decimal_places}f}%"
    except (ValueError, TypeError):
        return "N/A"

def format_units(value: Union[float, int, None], decimal_places: int = 4) -> str:
    """
    格式化單位數顯示
    
    Args:
        value: 要格式化的數值
        decimal_places: 小數位數，預設為4
    
    Returns:
        str: 格式化後的單位數字串，如 "1234.5678"
    """
    if pd.isna(value) or value is None:
        return "N/A"
    
    try:
        return f"{value:.{decimal_places}f}"
    except (ValueError, TypeError):
        return "N/A"

def format_negative_with_minus(value: Union[float, int, None], 
                              format_func: callable = format_currency) -> str:
    """
    負值統一使用負號顯示（避免Excel解析問題）
    
    Args:
        value: 要格式化的數值
        format_func: 格式化函數
    
    Returns:
        str: 格式化後的字串，負值使用負號
    """
    if pd.isna(value) or value is None:
        return "N/A"
    
    try:
        if value < 0:
            formatted = format_func(abs(value))
            if formatted.startswith('$'):
                return f"-${formatted[1:]}"
            else:
                return f"-{formatted}"
        return format_func(value)
    except (ValueError, TypeError):
        return "N/A"

def format_negative_parentheses(value: Union[float, int, None], 
                               format_func: callable = format_currency) -> str:
    """
    負值使用括號顯示（僅限表格顯示用）
    
    Args:
        value: 要格式化的數值
        format_func: 格式化函數
    
    Returns:
        str: 格式化後的字串，負值使用括號
    """
    if pd.isna(value) or value is None:
        return "N/A"
    
    try:
        if value < 0:
            return f"({format_func(abs(value))})"
        return format_func(value)
    except (ValueError, TypeError):
        return "N/A"

def format_date(value: Union[datetime, date, str, None]) -> str:
    """
    格式化日期顯示
    
    Args:
        value: 要格式化的日期值
    
    Returns:
        str: 格式化後的日期字串，如 "2024-01-01"
    """
    if pd.isna(value) or value is None:
        return "N/A"
    
    try:
        if isinstance(value, str):
            # 如果已經是字串，檢查格式
            if len(value) == 10 and value.count('-') == 2:
                return value
            # 嘗試解析
            parsed_date = pd.to_datetime(value)
            return parsed_date.strftime('%Y-%m-%d')
        elif isinstance(value, (datetime, date)):
            return value.strftime('%Y-%m-%d')
        else:
            # 嘗試轉換
            parsed_date = pd.to_datetime(value)
            return parsed_date.strftime('%Y-%m-%d')
    except (ValueError, TypeError):
        return "N/A"

def validate_numeric_consistency(streamlit_val: Union[float, int, None], 
                               csv_val: Union[float, int, None], 
                               tolerance: float = NUMERIC_TOLERANCE) -> bool:
    """
    增強數值比較精度檢查
    
    Args:
        streamlit_val: Streamlit顯示的數值
        csv_val: CSV中的數值
        tolerance: 容差
    
    Returns:
        bool: True表示數值一致
    """
    if pd.isna(streamlit_val) and pd.isna(csv_val):
        return True
    if pd.isna(streamlit_val) or pd.isna(csv_val):
        return False
    
    try:
        # 對於很小的數值，使用相對誤差
        if abs(csv_val) > 1e-10:
            relative_error = abs(streamlit_val - csv_val) / abs(csv_val)
            return relative_error <= tolerance
        else:
            # 對於接近零的數值，使用絕對誤差
            return abs(streamlit_val - csv_val) <= tolerance
    except (ValueError, TypeError, ZeroDivisionError):
        return False

def generate_formatted_table(data_df: pd.DataFrame, strategy_type: str) -> pd.DataFrame:
    """
    生成格式化的策略表格（增強版）
    
    Args:
        data_df: 原始計算數據DataFrame
        strategy_type: "VA", "DCA", 或 "SUMMARY"
    
    Returns:
        pd.DataFrame: 格式化後的DataFrame
    
    Raises:
        ValueError: 當策略類型不支援時
    """
    if not validate_strategy_type(strategy_type):
        raise ValueError(f"未支援的策略類型: {strategy_type}")
    
    logger.info(f"開始格式化{strategy_type}策略表格，原始數據行數: {len(data_df)}")
    
    # 複製數據避免修改原始DataFrame
    formatted_df = data_df.copy()
    
    # 獲取策略對應的規格
    column_specs = get_column_specs(strategy_type)
    columns_order = get_columns_order(strategy_type)
    
    # 確保欄位順序一致，只保留存在的欄位
    ordered_columns = [col for col in columns_order if col in formatted_df.columns]
    formatted_df = formatted_df[ordered_columns]
    
    logger.info(f"調整欄位順序，保留{len(ordered_columns)}個欄位")
    
    # 應用統一格式化規則
    for column in formatted_df.columns:
        if column in column_specs:
            spec = column_specs[column]
            format_str = spec.get("format", "")
            
            logger.debug(f"格式化欄位 {column}: {format_str}")
            
            try:
                if "千分位符號" in format_str:
                    if "負值顯示括號" in format_str:
                        formatted_df[column] = formatted_df[column].apply(
                            lambda x: format_negative_parentheses(x, format_currency)
                        )
                    else:
                        formatted_df[column] = formatted_df[column].apply(
                            lambda x: format_currency(x, decimal_places=2)
                        )
                elif "%" in format_str or column in PERCENTAGE_PRECISION_RULES:
                    # 應用統一百分比格式標準
                    formatted_df[column] = formatted_df[column].apply(
                        lambda x: format_percentage(x, column_name=column)
                    )
                elif "位小數" in format_str:
                    decimal_places = get_decimal_places(column, column_specs)
                    if "負值顯示括號" in format_str:
                        formatted_df[column] = formatted_df[column].apply(
                            lambda x: format_negative_parentheses(
                                x, lambda v: format_units(v, decimal_places)
                            )
                        )
                    else:
                        formatted_df[column] = formatted_df[column].apply(
                            lambda x: format_units(x, decimal_places)
                        )
                elif spec["type"] == "date":
                    # 確保日期格式統一
                    formatted_df[column] = formatted_df[column].apply(format_date)
                elif spec["type"] == "int":
                    # 整數格式化
                    formatted_df[column] = formatted_df[column].apply(
                        lambda x: str(int(x)) if pd.notna(x) else "N/A"
                    )
                    
            except Exception as e:
                logger.warning(f"格式化欄位 {column} 時出現錯誤: {e}")
                continue
    
    logger.info(f"表格格式化完成，最終行數: {len(formatted_df)}")
    return formatted_df

def validate_table_data(data_df: pd.DataFrame, strategy_type: str) -> Dict[str, Any]:
    """
    驗證表格數據的完整性和正確性（增強版）
    
    Args:
        data_df: 計算數據DataFrame
        strategy_type: "VA", "DCA", 或 "SUMMARY"
    
    Returns:
        Dict: 驗證結果字典，包含 is_valid, errors, warnings, data_quality_score
    """
    logger.info(f"開始驗證{strategy_type}策略表格數據")
    
    if not validate_strategy_type(strategy_type):
        return {
            "is_valid": False, 
            "errors": [f"未知策略類型: {strategy_type}"], 
            "warnings": [],
            "data_quality_score": 0
        }
    
    errors = []
    warnings = []
    
    # 選擇對應的欄位規格
    required_columns = get_required_columns(strategy_type)
    column_specs = get_column_specs(strategy_type)
    
    # 檢查必要欄位
    missing_columns = required_columns - set(data_df.columns)
    if missing_columns:
        errors.append(f"缺少必要欄位: {list(missing_columns)}")
    
    # 檢查數據行數
    if len(data_df) == 0:
        errors.append("數據表格為空")
        return {
            "is_valid": False,
            "errors": errors,
            "warnings": warnings,
            "data_quality_score": 0
        }
    
    # 檢查數據合理性
    for column in data_df.columns:
        if column in column_specs:
            spec = column_specs[column]
            
            # 檢查非空值
            null_count = data_df[column].isnull().sum()
            if null_count > 0:
                if null_count == len(data_df):
                    errors.append(f"{column} 欄位完全為空")
                else:
                    warnings.append(f"{column} 有 {null_count} 個空值")
            
            # 檢查數值範圍（增強版）
            if spec["type"] in ["float", "int"] and len(data_df[column].dropna()) > 0:
                try:
                    numeric_values = pd.to_numeric(data_df[column].dropna(), errors='coerce')
                    numeric_values = numeric_values.dropna()  # 移除無法轉換的值
                    
                    if len(numeric_values) == 0:
                        errors.append(f"{column} 沒有有效的數值")
                        continue
                    
                    validation_rule = spec.get("validation", "")
                    
                    if validation_rule == ">0":
                        non_positive_count = (numeric_values <= 0).sum()
                        if non_positive_count > 0:
                            errors.append(f"{column} 有 {non_positive_count} 個非正值")
                    elif validation_rule == ">=0":
                        negative_count = (numeric_values < 0).sum()
                        if negative_count > 0:
                            errors.append(f"{column} 有 {negative_count} 個負值")
                    elif validation_rule == ">=1":
                        invalid_count = (numeric_values < 1).sum()
                        if invalid_count > 0:
                            errors.append(f"{column} 有 {invalid_count} 個小於1的值")
                    elif validation_rule == "合理範圍":
                        # 檢查異常值（使用IQR方法）
                        if len(numeric_values) >= 4:  # 至少需要4個值來計算IQR
                            Q1 = numeric_values.quantile(0.25)
                            Q3 = numeric_values.quantile(0.75)
                            IQR = Q3 - Q1
                            if IQR > 0:
                                outlier_mask = ((numeric_values < (Q1 - 1.5 * IQR)) | 
                                              (numeric_values > (Q3 + 1.5 * IQR)))
                                outlier_count = outlier_mask.sum()
                                if outlier_count > len(numeric_values) * 0.1:  # 超過10%為異常值
                                    warnings.append(f"{column} 有 {outlier_count} 個潛在異常值")
                                    
                except Exception as e:
                    warnings.append(f"檢查 {column} 欄位時出現錯誤: {str(e)}")
            
            # 檢查日期格式
            elif spec["type"] == "date" and len(data_df[column].dropna()) > 0:
                try:
                    date_values = data_df[column].dropna()
                    for idx, date_val in enumerate(date_values):
                        if pd.notna(date_val):
                            try:
                                pd.to_datetime(date_val)
                            except:
                                errors.append(f"{column} 第{idx+1}行日期格式無效: {date_val}")
                                break
                except Exception as e:
                    warnings.append(f"檢查 {column} 日期格式時出現錯誤: {str(e)}")
    
    # 檢查邏輯一致性（針對特定策略）
    try:
        if strategy_type in ["VA", "DCA"] and len(data_df) > 1:
            # 檢查累積投入是否遞增
            if "Cum_Inv" in data_df.columns:
                cum_inv_diff = data_df["Cum_Inv"].diff()
                decreasing_count = (cum_inv_diff < 0).sum()
                if decreasing_count > 0:
                    warnings.append(f"累積投入金額有 {decreasing_count} 次下降")
            
            # 檢查期數是否連續
            if "Period" in data_df.columns:
                periods = data_df["Period"].dropna()
                if len(periods) > 1:
                    expected_periods = range(int(periods.min()), int(periods.max()) + 1)
                    missing_periods = set(expected_periods) - set(periods)
                    if missing_periods:
                        warnings.append(f"期數不連續，缺少: {sorted(missing_periods)}")
                        
    except Exception as e:
        warnings.append(f"邏輯一致性檢查時出現錯誤: {str(e)}")
    
    # 計算數據品質分數
    data_quality_score = max(0, 100 - len(errors) * 20 - len(warnings) * 5)
    
    result = {
        "is_valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "data_quality_score": data_quality_score
    }
    
    logger.info(f"數據驗證完成: 有效={result['is_valid']}, " + 
                f"錯誤={len(errors)}個, 警告={len(warnings)}個, " +
                f"品質分數={data_quality_score}")
    
    return result

def export_to_csv(data_df: pd.DataFrame, 
                 strategy_type: str, 
                 filename: Optional[str] = None,
                 preserve_numeric_values: bool = True) -> str:
    """
    匯出表格為CSV格式
    
    Args:
        data_df: 要匯出的DataFrame
        strategy_type: 策略類型
        filename: 檔案名稱，若為None則自動生成
        preserve_numeric_values: 是否保留原始數值（True）或使用格式化字串（False）
    
    Returns:
        str: CSV檔案內容
    """
    logger.info(f"開始匯出{strategy_type}策略表格為CSV格式")
    
    if not validate_strategy_type(strategy_type):
        raise ValueError(f"未支援的策略類型: {strategy_type}")
    
    # 決定是否使用格式化版本
    if preserve_numeric_values:
        # 保留原始數值，方便Excel計算
        export_df = data_df.copy()
        
        # 確保欄位順序
        columns_order = get_columns_order(strategy_type)
        ordered_columns = [col for col in columns_order if col in export_df.columns]
        export_df = export_df[ordered_columns]
        
        # 僅格式化日期欄位
        column_specs = get_column_specs(strategy_type)
        for column in export_df.columns:
            if column in column_specs and column_specs[column]["type"] == "date":
                export_df[column] = export_df[column].apply(format_date)
    else:
        # 使用完全格式化版本
        export_df = generate_formatted_table(data_df, strategy_type)
    
    # 生成CSV內容
    output = io.StringIO()
    export_df.to_csv(output, index=False, encoding='utf-8')
    csv_content = output.getvalue()
    output.close()
    
    logger.info(f"CSV匯出完成，內容長度: {len(csv_content)} 字符")
    return csv_content

def compare_table_formats(original_df: pd.DataFrame, 
                         formatted_df: pd.DataFrame, 
                         strategy_type: str) -> Dict[str, Any]:
    """
    比較原始表格與格式化表格的一致性
    
    Args:
        original_df: 原始數據DataFrame
        formatted_df: 格式化後的DataFrame
        strategy_type: 策略類型
    
    Returns:
        Dict: 比較結果
    """
    logger.info(f"開始比較{strategy_type}策略表格格式一致性")
    
    inconsistencies = []
    warnings = []
    
    # 檢查欄位一致性
    orig_columns = set(original_df.columns)
    formatted_columns = set(formatted_df.columns)
    
    missing_in_formatted = orig_columns - formatted_columns
    extra_in_formatted = formatted_columns - orig_columns
    
    if missing_in_formatted:
        warnings.append(f"格式化表格缺少欄位: {list(missing_in_formatted)}")
    if extra_in_formatted:
        warnings.append(f"格式化表格多出欄位: {list(extra_in_formatted)}")
    
    # 檢查行數一致性
    if len(original_df) != len(formatted_df):
        inconsistencies.append(
            f"行數不一致: 原始({len(original_df)}) vs 格式化({len(formatted_df)})"
        )
    
    # 檢查共同欄位的數值一致性
    common_columns = orig_columns & formatted_columns
    column_specs = get_column_specs(strategy_type)
    
    for column in common_columns:
        if column in column_specs and column_specs[column]["type"] in ["float", "int"]:
            try:
                # 對於數值欄位，檢查是否只是格式差異
                orig_values = pd.to_numeric(original_df[column], errors='coerce')
                
                # 從格式化字串中提取數值
                formatted_values = formatted_df[column].apply(
                    lambda x: _extract_numeric_from_formatted(x) if x != "N/A" else None
                )
                
                # 比較非空值
                for i, (orig_val, fmt_val) in enumerate(zip(orig_values, formatted_values)):
                    if pd.notna(orig_val) and pd.notna(fmt_val):
                        if not validate_numeric_consistency(orig_val, fmt_val):
                            inconsistencies.append(
                                f"{column} 第{i+1}行數值不一致: {orig_val} vs {fmt_val}"
                            )
                            
            except Exception as e:
                warnings.append(f"比較 {column} 欄位時出現錯誤: {str(e)}")
    
    consistency_score = max(0, 100 - len(inconsistencies) * 10 - len(warnings) * 2)
    
    result = {
        "is_consistent": len(inconsistencies) == 0,
        "inconsistencies": inconsistencies,
        "warnings": warnings,
        "consistency_score": consistency_score
    }
    
    logger.info(f"格式一致性檢查完成: 一致={result['is_consistent']}, " +
                f"不一致={len(inconsistencies)}個, 警告={len(warnings)}個")
    
    return result

def _extract_numeric_from_formatted(formatted_str: str) -> Optional[float]:
    """
    從格式化字串中提取數值
    
    Args:
        formatted_str: 格式化後的字串
    
    Returns:
        Optional[float]: 提取的數值，失敗時返回None
    """
    if not isinstance(formatted_str, str) or formatted_str == "N/A":
        return None
    
    try:
        # 移除貨幣符號、千分位符號、百分號等
        cleaned = formatted_str.replace('$', '').replace(',', '').replace('%', '')
        
        # 處理括號（負數）
        if cleaned.startswith('(') and cleaned.endswith(')'):
            cleaned = '-' + cleaned[1:-1]
        
        return float(cleaned)
    except (ValueError, TypeError):
        return None

def test_table_formatter():
    """
    測試表格格式化功能
    """
    print("開始測試表格格式化功能...")
    
    try:
        # 測試格式化函數
        print("✓ 測試基本格式化函數:")
        
        # 測試金額格式化
        assert format_currency(1234.567) == "$1,234.57"
        assert format_currency(-1234.567) == "$-1,234.57"
        assert format_currency(None) == "N/A"
        print("  - 金額格式化測試通過")
        
        # 測試百分比格式化
        assert format_percentage(12.345) == "12.35%"
        assert format_percentage(12.345, "Sharpe_Ratio") == "12.345%"
        assert format_percentage(None) == "N/A"
        print("  - 百分比格式化測試通過")
        
        # 測試單位數格式化
        assert format_units(1234.56789) == "1234.5679"
        assert format_units(None) == "N/A"
        print("  - 單位數格式化測試通過")
        
        # 測試負值括號格式化
        assert format_negative_parentheses(-1234.56) == "($1,234.56)"
        assert format_negative_parentheses(1234.56) == "$1,234.56"
        print("  - 負值格式化測試通過")
        
        # 測試日期格式化
        assert format_date("2024-01-01") == "2024-01-01"
        assert format_date(datetime(2024, 1, 1)) == "2024-01-01"
        print("  - 日期格式化測試通過")
        
        # 測試數值一致性檢查
        assert validate_numeric_consistency(1.0, 1.0000001) == True
        assert validate_numeric_consistency(1.0, 2.0) == False
        assert validate_numeric_consistency(None, None) == True
        print("  - 數值一致性檢查測試通過")
        
        print("\n✅ 所有表格格式化功能測試通過！")
        
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        raise

if __name__ == "__main__":
    test_table_formatter() 