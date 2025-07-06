"""
策略計算引擎 (Strategy Calculation Engine)

本模組提供投資策略比較系統的完整計算流程，包括：
- VA策略完整計算流程 (calculate_va_strategy)
- DCA策略完整計算流程 (calculate_dca_strategy)
- 策略數據整合與驗證 (integrate_strategy_data)
- 完整數據流處理 (process_complete_data_flow)

嚴格遵循需求文件第2章的所有規格要求，確保數據流的完整性和一致性。
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Union, Tuple
from datetime import datetime, date
import logging

# 導入核心計算公式
from .calculation_formulas import (
    convert_annual_to_period_parameters,
    calculate_va_target_value, execute_va_strategy,
    calculate_dca_investment, calculate_dca_cumulative_investment, execute_dca_strategy,
    calculate_portfolio_allocation, calculate_bond_price,
    validate_conversion_parameters
)

# 導入表格系統
from .table_specifications import (
    VA_COLUMN_SPECS, VA_COLUMNS_ORDER,
    DCA_COLUMN_SPECS, DCA_COLUMNS_ORDER,
    SUMMARY_COLUMN_SPECS, SUMMARY_COLUMNS_ORDER
)

from .table_formatter import (
    generate_formatted_table, validate_table_data
)

from .table_calculator import (
    calculate_derived_metrics, calculate_summary_metrics
)

# 設置日誌
logger = logging.getLogger(__name__)

# ============================================================================
# 完整策略計算引擎
# ============================================================================

def calculate_va_strategy(C0: float,
                         annual_investment: float,
                         annual_growth_rate: float,
                         annual_inflation_rate: float,
                         investment_years: int,
                         frequency: str,
                         stock_ratio: float,
                         strategy_type: str,
                         market_data: pd.DataFrame) -> pd.DataFrame:
    """
    計算VA策略的完整數據流程
    
    Args:
        C0: 期初投入金額
        annual_investment: 年度投入金額
        annual_growth_rate: 年化成長率 (%)
        annual_inflation_rate: 年化通膨率 (%)
        investment_years: 投資年數
        frequency: 投資頻率
        stock_ratio: 股票比例 (0-100)
        strategy_type: "Rebalance" 或 "No Sell"
        market_data: 市場數據DataFrame
    
    Returns:
        pd.DataFrame: 完整的VA策略數據表格
    """
    logger.info(f"開始計算VA {strategy_type}策略")
    
    try:
        # 1. 參數驗證和轉換
        params = convert_annual_to_period_parameters(
            annual_investment, annual_growth_rate, annual_inflation_rate,
            investment_years, frequency
        )
        
        C_period = params["C_period"]
        r_period = params["r_period"]
        g_period = params["g_period"]
        total_periods = params["total_periods"]
        periods_per_year = params["periods_per_year"]
        
        # 2. 股債配置處理
        stock_ratio_decimal, bond_ratio_decimal = calculate_portfolio_allocation(stock_ratio)
        
        # 3. 初始化結果列表
        va_results = []
        
        # 累積變數
        cum_stock_units = 0.0
        cum_bond_units = 0.0
        cum_inv = 0.0
        
        # 4. 逐期計算VA策略
        for period in range(int(total_periods)):
            period_data = {}
            
            # 基本期間信息 - 修正：Period應該從1開始，符合需求文件規格
            period_data["Period"] = period + 1
            if period < len(market_data):
                market_row = market_data.iloc[period]
                # 直接使用市場數據，不提供模擬數據作為預設值
                period_data["Date_Origin"] = market_row["Date_Origin"]
                period_data["Date_End"] = market_row["Date_End"] 
                period_data["SPY_Price_Origin"] = market_row["SPY_Price_Origin"]
                period_data["SPY_Price_End"] = market_row["SPY_Price_End"]
                period_data["Bond_Yield_Origin"] = market_row["Bond_Yield_Origin"]
                period_data["Bond_Yield_End"] = market_row["Bond_Yield_End"]
            else:
                # 如果market_data不足，拋出錯誤而不是使用模擬數據
                raise ValueError(f"市場數據不足：需要{int(total_periods)}期數據，但只有{len(market_data)}期")
            
            # 計算債券價格
            period_data["Bond_Price_Origin"] = calculate_bond_price(period_data["Bond_Yield_Origin"])
            period_data["Bond_Price_End"] = calculate_bond_price(period_data["Bond_Yield_End"])
            
            # 前期累積單位數
            period_data["Prev_Stock_Units"] = cum_stock_units
            period_data["Prev_Bond_Units"] = cum_bond_units
            
            # 期初投入（僅第一期）
            period_data["Initial_Investment"] = C0 if period == 0 else 0
            
            # 計算VA目標價值 - 使用1-based期數
            va_target = calculate_va_target_value(C0, C_period, r_period, g_period, period + 1)
            period_data["VA_Target"] = va_target
            
            # 執行VA策略
            if period == 0:
                # 第一期：期初投入C0，期末計算investment_gap
                # 1. 期初投入C0
                trade_result = execute_dca_strategy(
                    C0, stock_ratio_decimal, bond_ratio_decimal,
                    period_data["SPY_Price_Origin"], period_data["Bond_Price_Origin"]
                )
                # 更新累積單位數（期初投入的結果）
                cum_stock_units += trade_result["stock_trade_units"]
                cum_bond_units += trade_result["bond_trade_units"]
                cum_inv += C0
                
                # 2. 計算當期調整前資產價值（期初投入C0後，期末調整前的資產價值）
                current_asset_value = (cum_stock_units * period_data["SPY_Price_End"] + 
                                     cum_bond_units * period_data["Bond_Price_End"])
                period_data["Current_Asset_Value"] = current_asset_value
                
                # 3. 期末計算investment_gap並執行VA策略調整
                va_result = execute_va_strategy(
                    va_target, current_asset_value, stock_ratio_decimal, bond_ratio_decimal,
                    period_data["SPY_Price_End"], period_data["Bond_Price_End"], strategy_type
                )
                
                # 4. Invested欄位顯示期末的investment_gap，符合需求文件
                period_data["Invested"] = va_result["actual_investment"]
                period_data["stock_trade_units"] = trade_result["stock_trade_units"] + va_result["stock_trade_units"]
                period_data["bond_trade_units"] = trade_result["bond_trade_units"] + va_result["bond_trade_units"]
                cum_inv += va_result["actual_investment"]
                
                # 更新累積單位數（包含期末調整）
                cum_stock_units += va_result["stock_trade_units"]
                cum_bond_units += va_result["bond_trade_units"]
            else:
                # 計算當期調整前資產價值
                current_asset_value = (cum_stock_units * period_data["SPY_Price_End"] + 
                                     cum_bond_units * period_data["Bond_Price_End"])
                period_data["Current_Asset_Value"] = current_asset_value
                
                # 後續期數：根據VA目標調整
                va_result = execute_va_strategy(
                    va_target, current_asset_value, stock_ratio_decimal, bond_ratio_decimal,
                    period_data["SPY_Price_End"], period_data["Bond_Price_End"], strategy_type
                )
                period_data["Invested"] = va_result["actual_investment"]
                period_data["stock_trade_units"] = va_result["stock_trade_units"]
                period_data["bond_trade_units"] = va_result["bond_trade_units"]
                cum_inv += va_result["actual_investment"]
                
                # 更新累積單位數
                cum_stock_units += period_data["stock_trade_units"]
                cum_bond_units += period_data["bond_trade_units"]
            
            period_data["Cum_stock_units"] = cum_stock_units
            period_data["Cum_bond_units"] = cum_bond_units
            period_data["Cum_Inv"] = cum_inv
            
            # 計算當期期末資產價值
            cum_value = (cum_stock_units * period_data["SPY_Price_End"] + 
                        cum_bond_units * period_data["Bond_Price_End"])
            period_data["Cum_Value"] = cum_value
            
            va_results.append(period_data)
        
        # 5. 創建DataFrame並計算衍生指標
        va_df = pd.DataFrame(va_results)
        
        # 確保欄位順序符合規格
        ordered_columns = [col for col in VA_COLUMNS_ORDER if col in va_df.columns]
        va_df = va_df[ordered_columns]
        
        # 計算衍生欄位
        va_df = calculate_derived_metrics(va_df, C0, periods_per_year)
        
        logger.info(f"VA {strategy_type}策略計算完成，共{len(va_df)}期")
        return va_df
        
    except Exception as e:
        logger.error(f"計算VA {strategy_type}策略時出現錯誤: {e}")
        raise

def calculate_dca_strategy(C0: float,
                          annual_investment: float,
                          annual_growth_rate: float,
                          annual_inflation_rate: float,
                          investment_years: int,
                          frequency: str,
                          stock_ratio: float,
                          market_data: pd.DataFrame) -> pd.DataFrame:
    """
    計算DCA策略的完整數據流程
    
    Args:
        C0: 期初投入金額
        annual_investment: 年度投入金額
        annual_growth_rate: 年化成長率 (%)
        annual_inflation_rate: 年化通膨率 (%)
        investment_years: 投資年數
        frequency: 投資頻率
        stock_ratio: 股票比例 (0-100)
        market_data: 市場數據DataFrame
    
    Returns:
        pd.DataFrame: 完整的DCA策略數據表格
    """
    logger.info("開始計算DCA策略")
    
    try:
        # 1. 參數驗證和轉換
        params = convert_annual_to_period_parameters(
            annual_investment, annual_growth_rate, annual_inflation_rate,
            investment_years, frequency
        )
        
        C_period = params["C_period"]
        g_period = params["g_period"]
        total_periods = params["total_periods"]
        periods_per_year = params["periods_per_year"]
        
        # 2. 股債配置處理
        stock_ratio_decimal, bond_ratio_decimal = calculate_portfolio_allocation(stock_ratio)
        
        # 3. 初始化結果列表
        dca_results = []
        
        # 累積變數
        cum_stock_units = 0.0
        cum_bond_units = 0.0
        cum_inv = 0.0
        
        # 4. 逐期計算DCA策略
        for period in range(int(total_periods)):
            period_data = {}
            
            # 基本期間信息 - 修正：Period應該從1開始，符合需求文件規格
            period_data["Period"] = period + 1
            if period < len(market_data):
                market_row = market_data.iloc[period]
                # 直接使用市場數據，不提供模擬數據作為預設值
                period_data["Date_Origin"] = market_row["Date_Origin"]
                period_data["Date_End"] = market_row["Date_End"] 
                period_data["SPY_Price_Origin"] = market_row["SPY_Price_Origin"]
                period_data["SPY_Price_End"] = market_row["SPY_Price_End"]
                period_data["Bond_Yield_Origin"] = market_row["Bond_Yield_Origin"]
                period_data["Bond_Yield_End"] = market_row["Bond_Yield_End"]
            else:
                # 如果market_data不足，拋出錯誤而不是使用模擬數據
                raise ValueError(f"市場數據不足：需要{int(total_periods)}期數據，但只有{len(market_data)}期")
            
            # 計算債券價格
            period_data["Bond_Price_Origin"] = calculate_bond_price(period_data["Bond_Yield_Origin"])
            period_data["Bond_Price_End"] = calculate_bond_price(period_data["Bond_Yield_End"])
            
            # 前期累積單位數
            period_data["Prev_Stock_Units"] = cum_stock_units
            period_data["Prev_Bond_Units"] = cum_bond_units
            
            # 計算固定投入金額 - 修正：Fixed_Investment欄位只顯示通膨調整後的定期投入，不包含C0
            if period == 0:
                # 第一期：C0單獨顯示在Initial_Investment，Fixed_Investment只顯示調整後的C_period
                period_investment = calculate_dca_investment(C_period, g_period, 1)
                fixed_investment = period_investment  # 修正：不包含C0
                actual_total_investment = C0 + period_investment  # 實際總投入用於策略執行
                period_data["Initial_Investment"] = C0
            else:
                # 後續期數：調整後的C_period - 使用1-based期數
                fixed_investment = calculate_dca_investment(C_period, g_period, period + 1)
                actual_total_investment = fixed_investment  # 後續期數沒有C0
                period_data["Initial_Investment"] = 0
            
            period_data["Fixed_Investment"] = fixed_investment
            
            # 執行DCA策略 - 使用實際總投入金額
            dca_result = execute_dca_strategy(
                actual_total_investment, stock_ratio_decimal, bond_ratio_decimal,
                period_data["SPY_Price_Origin"], period_data["Bond_Price_Origin"]
            )
            
            period_data["stock_trade_units"] = dca_result["stock_trade_units"]
            period_data["bond_trade_units"] = dca_result["bond_trade_units"]
            
            # 更新累積單位數和投入 - 使用實際總投入金額
            cum_stock_units += period_data["stock_trade_units"]
            cum_bond_units += period_data["bond_trade_units"]
            cum_inv += actual_total_investment
            
            period_data["Cum_stock_units"] = cum_stock_units
            period_data["Cum_bond_units"] = cum_bond_units
            period_data["Cum_Inv"] = cum_inv
            
            # 計算當期期末資產價值
            cum_value = (cum_stock_units * period_data["SPY_Price_End"] + 
                        cum_bond_units * period_data["Bond_Price_End"])
            period_data["Cum_Value"] = cum_value
            
            dca_results.append(period_data)
        
        # 5. 創建DataFrame並計算衍生指標
        dca_df = pd.DataFrame(dca_results)
        
        # 確保欄位順序符合規格
        ordered_columns = [col for col in DCA_COLUMNS_ORDER if col in dca_df.columns]
        dca_df = dca_df[ordered_columns]
        
        # 計算衍生欄位
        dca_df = calculate_derived_metrics(dca_df, C0, periods_per_year)
        
        logger.info(f"DCA策略計算完成，共{len(dca_df)}期")
        return dca_df
        
    except Exception as e:
        logger.error(f"計算DCA策略時出現錯誤: {e}")
        raise

def process_complete_data_flow(C0: float,
                              annual_investment: float,
                              annual_growth_rate: float,
                              annual_inflation_rate: float,
                              investment_years: int,
                              frequency: str,
                              stock_ratio: float,
                              market_data: Optional[pd.DataFrame] = None) -> Dict[str, pd.DataFrame]:
    """
    處理完整的數據流程：從參數到最終表格和圖表
    
    Args:
        C0: 期初投入金額
        annual_investment: 年度投入金額
        annual_growth_rate: 年化成長率 (%)
        annual_inflation_rate: 年化通膨率 (%)
        investment_years: 投資年數
        frequency: 投資頻率
        stock_ratio: 股票比例 (0-100)
        market_data: 市場數據DataFrame（可選）
    
    Returns:
        Dict: 包含所有策略結果的字典
    """
    logger.info("開始處理完整數據流程")
    
    try:
        # 1. 參數驗證
        validate_conversion_parameters(annual_growth_rate, annual_inflation_rate)
        
        # 2. 生成或使用市場數據
        if market_data is None:
            params = convert_annual_to_period_parameters(
                annual_investment, annual_growth_rate, annual_inflation_rate,
                investment_years, frequency
            )
            total_periods = int(params["total_periods"])
            
            # 生成模擬市場數據
            market_data = generate_market_data(total_periods, annual_growth_rate)
        
        # 3. 計算所有策略
        va_rebalance_df = calculate_va_strategy(
            C0, annual_investment, annual_growth_rate, annual_inflation_rate,
            investment_years, frequency, stock_ratio, "Rebalance", market_data
        )
        
        va_nosell_df = calculate_va_strategy(
            C0, annual_investment, annual_growth_rate, annual_inflation_rate,
            investment_years, frequency, stock_ratio, "No Sell", market_data
        )
        
        dca_df = calculate_dca_strategy(
            C0, annual_investment, annual_growth_rate, annual_inflation_rate,
            investment_years, frequency, stock_ratio, market_data
        )
        
        # 4. 計算綜合比較摘要
        summary_df = calculate_summary_metrics(
            va_rebalance_df, va_nosell_df, dca_df,
            initial_investment=C0,
            periods_per_year=convert_annual_to_period_parameters(
                annual_investment, annual_growth_rate, annual_inflation_rate,
                investment_years, frequency
            )["periods_per_year"]
        )
        
        # 5. 數據驗證
        results = {
            "va_rebalance": va_rebalance_df,
            "va_nosell": va_nosell_df,
            "dca": dca_df,
            "summary": summary_df
        }
        
        # 驗證每個結果
        for strategy_name, df in results.items():
            if strategy_name == "summary":
                validation_result = validate_table_data(df, "SUMMARY")
            elif strategy_name.startswith("va"):
                validation_result = validate_table_data(df, "VA")
            else:
                validation_result = validate_table_data(df, "DCA")
            
            if not validation_result["is_valid"]:
                logger.warning(f"{strategy_name}數據驗證警告: {validation_result['errors']}")
        
        logger.info("完整數據流程處理完成")
        return results
        
    except Exception as e:
        logger.error(f"處理完整數據流程時出現錯誤: {e}")
        raise

def generate_market_data(total_periods: int, annual_growth_rate: float) -> pd.DataFrame:
    """
    生成模擬市場數據
    
    Args:
        total_periods: 總期數
        annual_growth_rate: 年化成長率
    
    Returns:
        pd.DataFrame: 模擬市場數據
    """
    logger.info(f"生成{total_periods}期模擬市場數據")
    
    market_data = []
    base_spy_price = 400.0
    base_bond_yield = 3.0
    
    # 計算期成長率
    period_growth_rate = (1 + annual_growth_rate / 100) ** (1/4) - 1  # 假設季度頻率
    
    for period in range(total_periods):
        # SPY價格隨機波動但總體上升
        noise = np.random.normal(0, 0.02)  # 2%隨機波動
        spy_price_origin = base_spy_price * ((1 + period_growth_rate + noise) ** period)
        spy_price_end = spy_price_origin * (1 + period_growth_rate + np.random.normal(0, 0.02))
        
        # 債券殖利率小幅波動
        bond_yield_origin = base_bond_yield + np.random.normal(0, 0.1)
        bond_yield_end = bond_yield_origin + np.random.normal(0, 0.05)
        
        market_data.append({
            "Period": period,
            "Date_Origin": f"2024-{period//4+1:02d}-{(period%4)*3+1:02d}",
            "Date_End": f"2024-{period//4+1:02d}-{(period%4+1)*3:02d}",
            "SPY_Price_Origin": round(spy_price_origin, 2),
            "SPY_Price_End": round(spy_price_end, 2),
            "Bond_Yield_Origin": round(bond_yield_origin, 2),
            "Bond_Yield_End": round(bond_yield_end, 2)
        })
    
    return pd.DataFrame(market_data)

def test_strategy_engine():
    """測試策略計算引擎"""
    print("🔍 測試策略計算引擎")
    
    try:
        # 測試參數
        test_params = {
            "C0": 100000,
            "annual_investment": 120000,
            "annual_growth_rate": 8.0,
            "annual_inflation_rate": 3.0,
            "investment_years": 3,
            "frequency": "Quarterly",
            "stock_ratio": 60.0
        }
        
        # 測試完整數據流程
        results = process_complete_data_flow(**test_params)
        
        # 驗證結果
        assert "va_rebalance" in results
        assert "va_nosell" in results
        assert "dca" in results
        assert "summary" in results
        
        print("✓ 完整數據流程測試通過")
        
        # 驗證數據結構
        va_df = results["va_rebalance"]
        assert len(va_df) == 12  # 3年*4季度
        assert "VA_Target" in va_df.columns
        assert "Invested" in va_df.columns
        
        dca_df = results["dca"]
        assert len(dca_df) == 12
        assert "Fixed_Investment" in dca_df.columns
        
        summary_df = results["summary"]
        assert len(summary_df) == 3  # 三種策略
        assert "Strategy" in summary_df.columns
        
        print("✓ 數據結構驗證通過")
        
        print("✅ 策略計算引擎測試完成！")
        
    except Exception as e:
        print(f"❌ 策略計算引擎測試失敗: {e}")
        raise

if __name__ == "__main__":
    test_strategy_engine() 