"""
衍生欄位計算模組 (Table Calculator Module)

本模組提供投資策略比較系統的衍生欄位計算功能，包括：
- 績效指標衍生計算 (calculate_derived_metrics)
- 綜合比較摘要計算 (calculate_summary_metrics)
- 現金流序列建構 (build_cash_flows_for_strategy)
- 表格數據完整性檢查

嚴格遵循需求文件第2章第2.2節第5子節的規格要求。
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Union, Tuple
import logging

# 導入計算公式模組
from .calculation_formulas import (
    calculate_annualized_return, calculate_irr,
    build_va_cash_flows, build_dca_cash_flows,
    calculate_volatility_and_sharpe, calculate_max_drawdown,
    calculate_enhanced_annualized_return, calculate_time_weighted_return
)

# 導入表格規格定義
from .table_specifications import (
    get_column_specs, get_columns_order, validate_strategy_type,
    SUMMARY_COLUMN_SPECS, SUMMARY_COLUMNS_ORDER
)

# 設置日誌
logger = logging.getLogger(__name__)

# ============================================================================
# 2.2.5 衍生欄位計算模組
# ============================================================================

def calculate_derived_metrics(df: pd.DataFrame, 
                            initial_investment: float, 
                            periods_per_year: int) -> pd.DataFrame:
    """
    計算表格中的衍生欄位
    
    Args:
        df: 基礎數據DataFrame
        initial_investment: 期初投入金額
        periods_per_year: 每年期數
    
    Returns:
        pd.DataFrame: 添加衍生欄位的DataFrame
    """
    logger.info(f"開始計算衍生欄位，數據行數: {len(df)}")
    
    enhanced_df = df.copy()
    
    try:
        # 確保必要欄位存在
        required_columns = ["Cum_Value", "Cum_Inv", "Period"]
        missing_columns = [col for col in required_columns if col not in enhanced_df.columns]
        if missing_columns:
            logger.warning(f"缺少必要欄位: {missing_columns}")
            return enhanced_df
        
        # 計算期間報酬率
        if "Period_Return" not in enhanced_df.columns:
            enhanced_df["Period_Return"] = 0.0
            
            # 對於第一期，報酬率設為0
            enhanced_df.loc[0, "Period_Return"] = 0.0
            
            # 對於後續期數，計算期間報酬率
            for i in range(1, len(enhanced_df)):
                prev_value = enhanced_df.loc[i-1, "Cum_Value"]
                curr_value = enhanced_df.loc[i, "Cum_Value"]
                
                if pd.notna(prev_value) and prev_value > 0:
                    period_return = ((curr_value / prev_value) - 1) * 100
                    enhanced_df.loc[i, "Period_Return"] = period_return
                else:
                    enhanced_df.loc[i, "Period_Return"] = 0.0
        
        # 計算累計報酬率 - 增強版本，處理累積投入≤0的情況
        if "Cumulative_Return" not in enhanced_df.columns:
            enhanced_df["Cumulative_Return"] = 0.0
            
            for i in range(len(enhanced_df)):
                cum_value = enhanced_df.loc[i, "Cum_Value"]
                cum_inv = enhanced_df.loc[i, "Cum_Inv"]
                
                if pd.notna(cum_value) and pd.notna(cum_inv):
                    if cum_inv > 0:
                        # 傳統計算方式：累積投入>0
                        cumulative_return = ((cum_value / cum_inv) - 1) * 100
                        enhanced_df.loc[i, "Cumulative_Return"] = cumulative_return
                    else:
                        # 累積投入≤0：使用時間加權方法計算
                        if i > 0:
                            period_returns = enhanced_df.loc[:i, "Period_Return"].dropna().tolist()
                            if period_returns:
                                # 計算累積複合報酬率
                                returns_decimal = [r/100 for r in period_returns if r != 0]
                                if returns_decimal:
                                    compound_return = 1.0
                                    for r in returns_decimal:
                                        compound_return *= (1 + r)
                                    cumulative_return = (compound_return - 1) * 100
                                    enhanced_df.loc[i, "Cumulative_Return"] = cumulative_return
        
        # 計算年化報酬率 - 增強版本，處理累積投入≤0的情況
        if "Annualized_Return" not in enhanced_df.columns:
            enhanced_df["Annualized_Return"] = 0.0
            
            for i in range(len(enhanced_df)):
                period = enhanced_df.loc[i, "Period"]
                cum_value = enhanced_df.loc[i, "Cum_Value"]
                cum_inv = enhanced_df.loc[i, "Cum_Inv"]
                
                if period > 0 and pd.notna(cum_value) and pd.notna(cum_inv):
                    investment_years = (period + 1) / periods_per_year
                    if investment_years > 0:
                        # 獲取到目前為止的期間報酬率用於TWR計算
                        period_returns = enhanced_df.loc[:i, "Period_Return"].dropna().tolist()
                        
                        # 使用增強年化報酬率計算（自動處理累積投入≤0的情況）
                        ann_return = calculate_enhanced_annualized_return(
                            cum_value, cum_inv, investment_years, 
                            period_returns, periods_per_year
                        )
                        enhanced_df.loc[i, "Annualized_Return"] = ann_return
        
        logger.info("衍生欄位計算完成")
        
    except Exception as e:
        logger.error(f"計算衍生欄位時出現錯誤: {e}")
        # 返回原始DataFrame，避免數據丟失
        return df
    
    return enhanced_df

def calculate_summary_metrics(va_rebalance_df: Optional[pd.DataFrame] = None,
                            va_nosell_df: Optional[pd.DataFrame] = None, 
                            dca_df: Optional[pd.DataFrame] = None, 
                            initial_investment: float = 100000,
                            periods_per_year: int = 4,
                            risk_free_rate: float = 2.0) -> pd.DataFrame:
    """
    計算三種策略的綜合比較指標
    
    Args:
        va_rebalance_df: VA Rebalance策略完整數據
        va_nosell_df: VA NoSell策略完整數據
        dca_df: DCA策略完整數據
        initial_investment: 期初投入金額
        periods_per_year: 每年期數
        risk_free_rate: 無風險利率（%）
    
    Returns:
        pd.DataFrame: 綜合比較摘要DataFrame
    """
    logger.info("開始計算綜合比較指標")
    
    strategies = {
        "VA_Rebalance": va_rebalance_df,
        "VA_NoSell": va_nosell_df, 
        "DCA": dca_df
    }
    
    summary_data = []
    
    for strategy_name, strategy_df in strategies.items():
        if strategy_df is not None and len(strategy_df) > 0:
            logger.info(f"計算 {strategy_name} 策略指標")
            
            try:
                final_row = strategy_df.iloc[-1]
                
                # 基本指標
                final_value = final_row.get("Cum_Value", 0)
                total_investment = final_row.get("Cum_Inv", 0)
                
                # 總報酬率計算 - 處理累積投入≤0的情況
                if total_investment > 0:
                    total_return = ((final_value / total_investment) - 1) * 100
                else:
                    # 累積投入≤0：使用最終期的累積報酬率
                    total_return = final_row.get("Cumulative_Return", 0)
                
                # 年化報酬率 - 使用增強版本處理累積投入≤0的情況
                investment_years = len(strategy_df) / periods_per_year
                if investment_years > 0:
                    # 獲取期間報酬率用於TWR計算
                    period_returns = strategy_df["Period_Return"].dropna().tolist() if "Period_Return" in strategy_df.columns else []
                    
                    # 使用增強年化報酬率計算
                    annualized_return = calculate_enhanced_annualized_return(
                        final_value, total_investment, investment_years,
                        period_returns, periods_per_year
                    )
                else:
                    annualized_return = 0
                
# IRR計算已移除，不符合需求文件第2.2.3節SUMMARY表格規格
                
                # 風險指標
                volatility = 0
                sharpe_ratio = 0
                try:
                    if "Period_Return" in strategy_df.columns:
                        period_returns = strategy_df["Period_Return"].dropna()
                        if len(period_returns) > 1:
                            # 轉換為小數形式，過濾掉第一期的0報酬率
                            returns_decimal = [r/100 for r in period_returns if pd.notna(r) and r != 0]
                            if len(returns_decimal) > 1:
                                volatility, sharpe_ratio = calculate_volatility_and_sharpe(
                                    returns_decimal, periods_per_year, risk_free_rate/100
                                )
                                # calculate_volatility_and_sharpe已經返回百分比形式，無需再轉換
                except Exception as e:
                    logger.warning(f"計算 {strategy_name} 風險指標時出現錯誤: {e}")
                
                # 最大回撤
                max_drawdown = 0
                try:
                    if "Cum_Value" in strategy_df.columns:
                        cumulative_values = strategy_df["Cum_Value"].dropna().tolist()
                        if len(cumulative_values) > 1:
                            max_drawdown, _ = calculate_max_drawdown(cumulative_values)
                            max_drawdown *= 100  # 轉換為百分比
                except Exception as e:
                    logger.warning(f"計算 {strategy_name} 最大回撤時出現錯誤: {e}")
                
                summary_data.append({
                    "Strategy": strategy_name,
                    "Final_Value": final_value,
                    "Total_Investment": total_investment,
                    "Total_Return": total_return,
                    "Annualized_Return": annualized_return,
                    "Volatility": volatility,
                    "Sharpe_Ratio": sharpe_ratio,
                    "Max_Drawdown": max_drawdown
                })
                
                logger.info(f"{strategy_name} 指標計算完成")
                
            except Exception as e:
                logger.error(f"計算 {strategy_name} 策略指標時出現錯誤: {e}")
                # 添加空數據行，避免遺漏策略
                summary_data.append({
                    "Strategy": strategy_name,
                    "Final_Value": 0,
                    "Total_Investment": 0,
                    "Total_Return": 0,
                    "Annualized_Return": 0,
                    "Volatility": 0,
                    "Sharpe_Ratio": 0,
                    "Max_Drawdown": 0
                })
    
    result_df = pd.DataFrame(summary_data)
    
    # 確保欄位順序符合規格
    if not result_df.empty:
        ordered_columns = [col for col in SUMMARY_COLUMNS_ORDER if col in result_df.columns]
        result_df = result_df[ordered_columns]
    
    logger.info(f"綜合比較指標計算完成，策略數量: {len(result_df)}")
    return result_df

def build_cash_flows_for_strategy(strategy_df: pd.DataFrame, strategy_name: str) -> List[float]:
    """
    根據策略類型建構現金流序列
    
    Args:
        strategy_df: 策略數據DataFrame
        strategy_name: 策略名稱
    
    Returns:
        List[float]: 現金流序列
    """
    logger.debug(f"建構 {strategy_name} 策略現金流序列")
    
    try:
        if len(strategy_df) == 0:
            return [0, 0]
        
        initial_investment = strategy_df.iloc[0].get("Initial_Investment", 0)
        final_value = strategy_df.iloc[-1].get("Cum_Value", 0)
        
        if strategy_name.startswith("VA"):
            # VA策略現金流
            if "Invested" in strategy_df.columns:
                investments = strategy_df["Invested"].fillna(0).tolist()
                
                # 處理第一期投入
                if len(investments) > 0:
                    investments[0] = initial_investment
                else:
                    investments = [initial_investment]
                
                return build_va_cash_flows(
                    initial_investment, investments, final_value, 
                    investments[-1] if investments else 0
                )
            else:
                # 簡化現金流
                return [-initial_investment, final_value]
                
        else:
            # DCA策略現金流
            if "Fixed_Investment" in strategy_df.columns and len(strategy_df) > 1:
                fixed_investment = strategy_df.iloc[1].get("Fixed_Investment", 0)
                periods = len(strategy_df) - 1  # 扣除期初
                
                return build_dca_cash_flows(
                    initial_investment, fixed_investment, periods, final_value
                )
            else:
                # 簡化現金流
                periods = len(strategy_df)
                avg_investment = initial_investment / periods if periods > 0 else 0
                cash_flows = [-avg_investment] * periods
                cash_flows.append(final_value)
                return cash_flows
                
    except Exception as e:
        logger.warning(f"建構 {strategy_name} 現金流時出現錯誤: {e}")
        # 返回最基本的現金流
        initial_investment = strategy_df.iloc[0].get("Initial_Investment", 0) if len(strategy_df) > 0 else 0
        final_value = strategy_df.iloc[-1].get("Cum_Value", 0) if len(strategy_df) > 0 else 0
        return [-initial_investment, final_value]

def test_table_calculator():
    """
    測試衍生欄位計算功能
    """
    print("開始測試衍生欄位計算功能...")
    
    try:
        # 創建測試數據
        test_data = {
            "Period": [0, 1, 2, 3],
            "Cum_Value": [100000, 105000, 110000, 115000],
            "Cum_Inv": [100000, 100000, 100000, 100000],
            "Initial_Investment": [100000, 0, 0, 0]
        }
        test_df = pd.DataFrame(test_data)
        
        # 測試衍生欄位計算
        enhanced_df = calculate_derived_metrics(test_df, 100000, 4)
        
        # 驗證結果
        assert "Period_Return" in enhanced_df.columns
        assert "Cumulative_Return" in enhanced_df.columns
        assert "Annualized_Return" in enhanced_df.columns
        
        print("✓ 衍生欄位計算測試通過")
        
        # 測試綜合比較指標計算
        summary_df = calculate_summary_metrics(
            va_rebalance_df=enhanced_df,
            va_nosell_df=enhanced_df,
            dca_df=enhanced_df
        )
        
        assert len(summary_df) == 3  # 三種策略
        assert "Strategy" in summary_df.columns
        assert "Final_Value" in summary_df.columns
        
        print("✓ 綜合比較指標計算測試通過")
        
        # 測試現金流建構
        cash_flows = build_cash_flows_for_strategy(enhanced_df, "VA_Rebalance")
        assert len(cash_flows) >= 2
        
        print("✓ 現金流建構測試通過")
        
        print("\n✅ 所有衍生欄位計算功能測試通過！")
        
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        raise

if __name__ == "__main__":
    test_table_calculator()
