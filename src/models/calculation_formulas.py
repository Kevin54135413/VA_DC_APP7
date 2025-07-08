"""
核心計算公式模組 (Core Calculation Formulas Module)

本模組實作投資策略比較系統的所有核心計算邏輯，包括：
- 參數頻率轉換模組
- Value Averaging (VA) 策略公式模組  
- Dollar Cost Averaging (DCA) 策略公式模組
- 股債混合組合計算模組
- 績效指標計算模組

嚴格遵循需求文件第2章第2.1節的數學公式和邊界條件處理要求。
"""

import numpy as np
import pandas as pd
from scipy.optimize import fsolve
from dateutil.relativedelta import relativedelta
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Union
import logging

# 設置日誌
logger = logging.getLogger(__name__)

# ============================================================================
# 2.1.1 參數頻率轉換模組
# ============================================================================

# 頻率轉換映射表
FREQUENCY_MAPPING = {
    "Monthly": {"periods_per_year": 12, "label": "每月"},
    "Quarterly": {"periods_per_year": 4, "label": "每季"},
    "Semi-annually": {"periods_per_year": 2, "label": "每半年"},
    "Annually": {"periods_per_year": 1, "label": "每年"}
}

def validate_conversion_parameters(annual_growth_rate: float, annual_inflation_rate: float) -> bool:
    """
    參數轉換前的驗證邏輯
    
    Args:
        annual_growth_rate: 年化成長率 (%)
        annual_inflation_rate: 年化通膨率 (%)
    
    Returns:
        bool: True表示需要使用極限公式，False表示使用一般公式
        
    Raises:
        ValueError: 當參數超出合理範圍時
    """
    # 確保成長率與通膨率在合理範圍
    if annual_growth_rate < -20 or annual_growth_rate > 50:
        raise ValueError("年化成長率必須在 -20% 到 50% 之間")
    
    if annual_inflation_rate < -5 or annual_inflation_rate > 15:
        raise ValueError("年化通膨率必須在 -5% 到 15% 之間")
    
    # 檢查極限情況：成長率與通膨率相等的處理
    if abs(annual_growth_rate - annual_inflation_rate) < 1e-6:
        return True  # 需要使用極限公式
    
    return False

def convert_annual_to_period_parameters(annual_investment: float, annual_growth_rate: float, 
                                      annual_inflation_rate: float, investment_years: int, 
                                      frequency: str) -> Dict[str, float]:
    """
    年度參數轉換為期間參數
    
    Args:
        annual_investment: 年度投入金額 ($)
        annual_growth_rate: 年化成長率 (%)
        annual_inflation_rate: 年化通膨率 (%)
        investment_years: 投資年數
        frequency: 投資頻率 (Monthly/Quarterly/Semi-annually/Annually)
    
    Returns:
        Dict: 包含轉換後參數的字典
            - C_period: 每期基準投入金額
            - r_period: 每期成長率
            - g_period: 每期通膨率
            - total_periods: 總投資期數
            - periods_per_year: 每年期數
    
    Raises:
        ValueError: 當輸入參數無效時
    """
    # 驗證輸入參數
    if annual_investment <= 0:
        raise ValueError("年度投入金額必須大於0")
    
    if investment_years <= 0:
        raise ValueError("投資年數必須大於0")
    
    if frequency not in FREQUENCY_MAPPING:
        raise ValueError(f"不支援的投資頻率: {frequency}")
    
    # 驗證成長率和通膨率
    validate_conversion_parameters(annual_growth_rate, annual_inflation_rate)
    
    periods_per_year = FREQUENCY_MAPPING[frequency]["periods_per_year"]
    
    # 每期基準投入金額
    C_period = annual_investment / periods_per_year
    
    # 複利轉換：年化率轉每期率
    r_period = (1 + annual_growth_rate / 100) ** (1/periods_per_year) - 1
    g_period = (1 + annual_inflation_rate / 100) ** (1/periods_per_year) - 1
    
    # 總投資期數
    total_periods = investment_years * periods_per_year
    
    return {
        "C_period": C_period,
        "r_period": r_period, 
        "g_period": g_period,
        "total_periods": total_periods,
        "periods_per_year": periods_per_year
    }

# ============================================================================
# 2.1.2 Value Averaging (VA) 策略公式模組
# ============================================================================

def calculate_va_target_value(C0: float, C_period: float, r_period: float, 
                            g_period: float, t: int) -> float:
    """
    計算VA策略第t期目標價值
    
    Args:
        C0: 期初投入金額 (Initial Investment)
        C_period: 基準每期投入金額
        r_period: 每期資產成長率
        g_period: 每期通膨率
        t: 期數 (1-based)
    
    Returns:
        float: 第t期目標價值Vt
    
    Raises:
        ValueError: 當輸入參數無效時
    """
    if C0 < 0 or C_period < 0:
        raise ValueError("投入金額不能為負值")
    
    if t <= 0:
        raise ValueError("期數必須大於0")
    
    # 檢查是否為極限情況
    if abs(r_period - g_period) < 1e-10:
        # 當 r_period = g_period 時的極限公式
        term1 = C0 * ((1 + r_period) ** t)
        term2 = C_period * t * ((1 + r_period) ** (t - 1))
        Vt = term1 + term2
        logger.debug(f"使用極限公式計算VA目標價值，期數={t}, Vt={Vt:.2f}")
    else:
        # 一般情況的VA公式
        term1 = C0 * ((1 + r_period) ** t)
        growth_factor = (1 + r_period) ** t
        inflation_factor = (1 + g_period) ** t
        term2 = C_period * (1 / (r_period - g_period)) * (growth_factor - inflation_factor)
        Vt = term1 + term2
        logger.debug(f"使用一般公式計算VA目標價值，期數={t}, Vt={Vt:.2f}")
    
    return Vt

def execute_va_strategy(target_value: float, current_value: float, stock_ratio: float, 
                       bond_ratio: float, spy_price: float, bond_price: float, 
                       strategy_type: str) -> Dict[str, float]:
    """
    執行VA策略的買賣邏輯 - 每期期末依資產目標與資產現值進行買賣
    
    Args:
        target_value: 目標資產價值Vt (使用C_period計算得出的理論目標)
        current_value: 當期期末累積單位數所對應的資產價值
        stock_ratio: 股票配置比例 (0-1)
        bond_ratio: 債券配置比例 (0-1)
        spy_price: 當期期末股票價格
        bond_price: 當期期末債券價格
        strategy_type: "Rebalance" 或 "No Sell"
    
    Returns:
        Dict: 包含交易結果的字典
            - investment_gap: 投資缺口
            - stock_trade_units: 股票交易單位數 (正為買入，負為賣出)
            - bond_trade_units: 債券交易單位數
            - actual_investment: 實際投入金額 (負值表示賣出)
    
    Raises:
        ValueError: 當輸入參數無效時
    """
    # 驗證輸入參數
    if target_value < 0 or current_value < 0:
        raise ValueError("資產價值不能為負值")
    
    if not (0 <= stock_ratio <= 1) or not (0 <= bond_ratio <= 1):
        raise ValueError("配置比例必須在0到1之間")
    
    if abs(stock_ratio + bond_ratio - 1.0) > 1e-6:
        raise ValueError("股債配置比例總和必須等於1")
    
    if spy_price <= 0 or bond_price <= 0:
        raise ValueError("資產價格必須大於0")
    
    if strategy_type not in ["Rebalance", "No Sell"]:
        raise ValueError("策略類型必須是 'Rebalance' 或 'No Sell'")
    
    investment_gap = target_value - current_value
    
    if investment_gap > 0:
        # 需要買入
        stock_investment = investment_gap * stock_ratio
        bond_investment = investment_gap * bond_ratio
        
        stock_trade_units = stock_investment / spy_price
        bond_trade_units = bond_investment / bond_price
        
        actual_investment = investment_gap
        
        logger.debug(f"VA策略買入: 缺口={investment_gap:.2f}, 股票單位={stock_trade_units:.4f}, 債券單位={bond_trade_units:.4f}")
        
    elif investment_gap < 0 and strategy_type == "Rebalance":
        # Rebalance策略：需要賣出
        stock_divestment = abs(investment_gap) * stock_ratio
        bond_divestment = abs(investment_gap) * bond_ratio
        
        stock_trade_units = -stock_divestment / spy_price  # 負值表示賣出
        bond_trade_units = -bond_divestment / bond_price
        
        actual_investment = investment_gap  # 負值
        
        logger.debug(f"VA策略賣出: 缺口={investment_gap:.2f}, 股票單位={stock_trade_units:.4f}, 債券單位={bond_trade_units:.4f}")
        
    else:
        # No Sell策略且investment_gap <= 0：不執行任何操作
        stock_trade_units = 0
        bond_trade_units = 0
        actual_investment = 0
        
        logger.debug("VA策略無操作")
    
    return {
        "investment_gap": investment_gap,
        "stock_trade_units": stock_trade_units,
        "bond_trade_units": bond_trade_units,
        "actual_investment": actual_investment
    }

# ============================================================================
# 2.1.3 Dollar Cost Averaging (DCA) 策略公式模組
# ============================================================================

def calculate_dca_investment(C_period: float, g_period: float, t: int) -> float:
    """
    計算DCA策略第t期投入金額(含通膨調整) - 僅適用於第1期及以後的C_period投入
    
    Args:
        C_period: 基準每期投入金額
        g_period: 每期通膨率  
        t: 期數 (1-based)
    
    Returns:
        float: 通膨調整後的投入金額
    
    Raises:
        ValueError: 當輸入參數無效時
    """
    if C_period < 0:
        raise ValueError("基準投入金額不能為負值")
    
    if t <= 0:
        raise ValueError("期數必須大於0")
    
    # 通膨調整後的投入金額
    adjusted_investment = C_period * ((1 + g_period) ** (t - 1))
    
    logger.debug(f"DCA第{t}期投入金額: {adjusted_investment:.2f} (基準: {C_period:.2f}, 通膨率: {g_period:.4f})")
    
    return adjusted_investment

def calculate_dca_cumulative_investment(C0: float, C_period: float, g_period: float, t: int) -> float:
    """
    計算DCA策略截至第t期的累積投入金額
    
    Args:
        C0: 期初投入金額（僅第1期投入）
        C_period: 基準每期投入金額（每期初都投入，含第1期）
        g_period: 每期通膨率
        t: 期數 (1-based)
    
    Returns:
        float: 累積投入金額
        
    Notes:
        - C0僅在第1期投入
        - C_period每期初都投入（含第1期），並按通膨調整
        - 累積投入 = C0 + Σ(C_period * (1+g)^(i-1)) for i=1 to t
    
    Raises:
        ValueError: 當輸入參數無效時
    """
    if C0 < 0 or C_period < 0:
        raise ValueError("投入金額不能為負值")
    
    if t <= 0:
        raise ValueError("期數必須大於0")
    
    if abs(g_period) < 1e-10:
        # 當通膨率為0時
        cumulative_regular = C_period * t
    else:
        # 等比數列求和公式
        cumulative_regular = C_period * (((1 + g_period) ** t - 1) / g_period)
    
    total_cumulative = C0 + cumulative_regular
    
    logger.debug(f"DCA截至第{t}期累積投入: {total_cumulative:.2f} (C0: {C0:.2f}, 定期投入: {cumulative_regular:.2f})")
    
    return total_cumulative

def execute_dca_strategy(fixed_investment: float, stock_ratio: float, bond_ratio: float, 
                        spy_price: float, bond_price: float) -> Dict[str, float]:
    """
    執行DCA策略的投資邏輯 - 每期期初固定投入，無賣出操作
    
    Args:
        fixed_investment: 當期固定投入金額
        stock_ratio: 股票配置比例 (0-1)
        bond_ratio: 債券配置比例 (0-1)
        spy_price: 當期期初股票價格
        bond_price: 當期期初債券價格
    
    Returns:
        Dict: 包含交易結果的字典
            - stock_trade_units: 股票購買單位數
            - bond_trade_units: 債券購買單位數
            - stock_investment: 股票投資金額
            - bond_investment: 債券投資金額
    
    Raises:
        ValueError: 當輸入參數無效時
    """
    # 驗證輸入參數
    if fixed_investment < 0:
        raise ValueError("固定投入金額不能為負值")
    
    if not (0 <= stock_ratio <= 1) or not (0 <= bond_ratio <= 1):
        raise ValueError("配置比例必須在0到1之間")
    
    if abs(stock_ratio + bond_ratio - 1.0) > 1e-6:
        raise ValueError("股債配置比例總和必須等於1")
    
    if spy_price <= 0 or bond_price <= 0:
        raise ValueError("資產價格必須大於0")
    
    stock_investment = fixed_investment * stock_ratio
    bond_investment = fixed_investment * bond_ratio
    
    stock_trade_units = stock_investment / spy_price
    bond_trade_units = bond_investment / bond_price
    
    logger.debug(f"DCA策略投入: 總額={fixed_investment:.2f}, 股票={stock_investment:.2f}({stock_trade_units:.4f}單位), 債券={bond_investment:.2f}({bond_trade_units:.4f}單位)")
    
    return {
        "stock_trade_units": stock_trade_units,
        "bond_trade_units": bond_trade_units,
        "stock_investment": stock_investment,
        "bond_investment": bond_investment
    }

# ============================================================================
# 2.1.4 股債混合組合計算模組
# ============================================================================

def calculate_portfolio_allocation(stock_ratio: float, bond_ratio: Optional[float] = None) -> Tuple[float, float]:
    """
    驗證並標準化股債配置比例
    
    Args:
        stock_ratio: 股票比例 (0-100)
        bond_ratio: 債券比例 (自動計算為 100-stock_ratio)
    
    Returns:
        Tuple[float, float]: (標準化股票比例, 標準化債券比例) (0-1範圍)
    
    Raises:
        ValueError: 當配置比例無效時
    """
    # 驗證股票比例
    if stock_ratio < 0 or stock_ratio > 100:
        raise ValueError("股票比例必須在 0% 到 100% 之間")
    
    # 自動計算債券比例
    calculated_bond_ratio = 100 - stock_ratio
    
    # 如果提供了債券比例，驗證一致性
    if bond_ratio is not None:
        if abs(bond_ratio - calculated_bond_ratio) > 1e-6:
            raise ValueError("股票比例和債券比例總和必須等於100%")
    
    # 標準化為 0-1 範圍
    normalized_stock_ratio = stock_ratio / 100
    normalized_bond_ratio = calculated_bond_ratio / 100
    
    logger.debug(f"資產配置 - 股票: {stock_ratio}% ({normalized_stock_ratio:.3f}), 債券: {calculated_bond_ratio}% ({normalized_bond_ratio:.3f})")
    
    return normalized_stock_ratio, normalized_bond_ratio

def calculate_bond_price(yield_rate: float, face_value: float = 100, time_to_maturity: float = 1) -> float:
    """
    根據殖利率計算債券價格
    
    Args:
        yield_rate: 債券殖利率 (%)
        face_value: 債券面值 (預設100)
        time_to_maturity: 到期時間 (年，預設1年)
    
    Returns:
        float: 債券價格
    
    Raises:
        ValueError: 當輸入參數無效時
    """
    if yield_rate < 0:
        raise ValueError("債券殖利率不能為負值")
    
    if face_value <= 0:
        raise ValueError("債券面值必須大於0")
    
    if time_to_maturity <= 0:
        raise ValueError("到期時間必須大於0")
    
    # 簡化債券定價模型（零息債券）
    bond_price = face_value / ((1 + yield_rate / 100) ** time_to_maturity)
    
    logger.debug(f"債券定價: 殖利率={yield_rate:.2f}%, 面值={face_value}, 到期={time_to_maturity}年, 價格={bond_price:.2f}")
    
    return bond_price

# ============================================================================
# 2.1.5 績效指標計算模組
# ============================================================================

def calculate_annualized_return(final_value: float, total_investment: float, investment_years: float) -> float:
    """
    計算年化報酬率
    
    Args:
        final_value: 期末總資產價值
        total_investment: 累計總投入金額
        investment_years: 投資年數
    
    Returns:
        float: 年化報酬率 (%)
    
    Raises:
        ValueError: 當輸入參數無效時
    """
    if final_value < 0 or total_investment <= 0:
        raise ValueError("資產價值必須非負，投入金額必須大於0")
    
    if investment_years <= 0:
        raise ValueError("投資年數必須大於0")
    
    if total_investment == 0:
        return 0
    
    # 年化報酬率公式
    annualized_return = ((final_value / total_investment) ** (1 / investment_years)) - 1
    annualized_return_percent = annualized_return * 100
    
    logger.debug(f"年化報酬率計算: 期末價值={final_value:.2f}, 總投入={total_investment:.2f}, 年數={investment_years:.2f}, 年化報酬={annualized_return_percent:.2f}%")
    
    return annualized_return_percent

def calculate_irr(cash_flows: List[float]) -> Optional[float]:
    """
    計算內部報酬率
    
    Args:
        cash_flows: 現金流序列 [期初投入(負), 各期投入(負), ..., 期末回收(正)]
    
    Returns:
        Optional[float]: 內部報酬率 (%)，無法收斂時返回None
    
    Raises:
        ValueError: 當現金流序列無效時
    """
    if not cash_flows or len(cash_flows) < 2:
        raise ValueError("現金流序列至少需要2個數據點")
    
    def npv(rate: float, cash_flows: List[float]) -> float:
        """計算淨現值"""
        return sum(cf / (1 + rate) ** i for i, cf in enumerate(cash_flows))
    
    try:
        # 使用數值方法求解 NPV = 0 的利率
        irr_rate = fsolve(npv, 0.1, args=(cash_flows,))[0]
        irr_percent = irr_rate * 100
        
        # 驗證解的有效性
        if abs(npv(irr_rate, cash_flows)) > 1e-6:
            logger.warning("IRR計算未能收斂到足夠精度")
            return None
        
        logger.debug(f"IRR計算成功: {irr_percent:.2f}%")
        return irr_percent
    except Exception as e:
        logger.warning(f"IRR計算失敗: {e}")
        return None

def build_va_cash_flows(C0: float, investment_history: List[float], final_value: float, 
                       final_investment: float) -> List[float]:
    """
    建構VA策略的現金流序列用於IRR計算
    
    Args:
        C0: 期初投入金額
        investment_history: 各期實際投入金額列表 (包含負值賣出)
        final_value: 期末總資產價值
        final_investment: 最後一期投入金額
    
    Returns:
        List[float]: 現金流序列
    
    Raises:
        ValueError: 當輸入參數無效時
    """
    if C0 < 0:
        raise ValueError("期初投入金額不能為負值")
    
    if not investment_history:
        raise ValueError("投資歷史不能為空")
    
    if final_value < 0:
        raise ValueError("期末價值不能為負值")
    
    cash_flows = [-C0]  # 期初投入為負值
    
    # 中間各期投入
    for investment in investment_history[:-1]:
        cash_flows.append(-investment)  # 投入為負值，賣出為正值
    
    # 最後一期：期末總價值減去最後投入
    final_cash_flow = final_value - final_investment
    cash_flows.append(final_cash_flow)
    
    logger.debug(f"VA現金流序列構建完成，共{len(cash_flows)}期")
    
    return cash_flows

def build_dca_cash_flows(C0: float, fixed_investment: float, periods: int, final_value: float) -> List[float]:
    """
    建構DCA策略的現金流序列用於IRR計算
    
    Args:
        C0: 期初投入金額
        fixed_investment: 固定投入金額(已含通膨調整)
        periods: 總期數
        final_value: 期末總資產價值
    
    Returns:
        List[float]: 現金流序列
    
    Raises:
        ValueError: 當輸入參數無效時
    """
    if C0 < 0:
        raise ValueError("期初投入金額不能為負值")
    
    if fixed_investment < 0:
        raise ValueError("固定投入金額不能為負值")
    
    if periods <= 0:
        raise ValueError("期數必須大於0")
    
    if final_value < 0:
        raise ValueError("期末價值不能為負值")
    
    cash_flows = [-C0]  # 期初投入
    
    # 中間各期固定投入（不包括最後一期）
    for i in range(1, periods - 1):
        cash_flows.append(-fixed_investment)
    
    # 最後一期：期末總價值減去最後投入
    final_cash_flow = final_value - fixed_investment
    cash_flows.append(final_cash_flow)
    
    logger.debug(f"DCA現金流序列構建完成，共{len(cash_flows)}期")
    
    return cash_flows

def calculate_volatility_and_sharpe(period_returns: List[float], periods_per_year: int, 
                                  risk_free_rate: float = 0.02) -> Tuple[float, float]:
    """
    計算年化波動率與夏普比率
    
    Args:
        period_returns: 各期報酬率列表 (小數形式，如0.05表示5%)
        periods_per_year: 每年期數
        risk_free_rate: 無風險利率 (年化，預設2%)
    
    Returns:
        Tuple[float, float]: (年化波動率(%), 夏普比率)
    
    Raises:
        ValueError: 當輸入參數無效時
    """
    if not period_returns or len(period_returns) < 2:
        return 0.0, 0.0
    
    if periods_per_year <= 0:
        raise ValueError("每年期數必須大於0")
    
    # 計算期間報酬率標準差
    period_std = np.std(period_returns, ddof=1)
    
    # 年化波動率
    annualized_volatility = period_std * np.sqrt(periods_per_year) * 100
    
    # 平均年化報酬率
    avg_period_return = np.mean(period_returns)
    annualized_avg_return = ((1 + avg_period_return) ** periods_per_year) - 1
    
    # 夏普比率
    if annualized_volatility == 0:
        sharpe_ratio = 0
    else:
        sharpe_ratio = (annualized_avg_return - risk_free_rate) / (annualized_volatility / 100)
    
    logger.debug(f"風險指標計算: 波動率={annualized_volatility:.2f}%, 夏普比率={sharpe_ratio:.3f}")
    
    return annualized_volatility, sharpe_ratio

def calculate_max_drawdown(cumulative_values: List[float]) -> Tuple[float, Tuple[int, int]]:
    """
    計算最大回撤
    
    Args:
        cumulative_values: 累積資產價值序列
    
    Returns:
        Tuple[float, Tuple[int, int]]: (最大回撤(%), (回撤開始期, 回撤結束期))
    
    Raises:
        ValueError: 當輸入參數無效時
    """
    if not cumulative_values or len(cumulative_values) < 2:
        return 0.0, (0, 0)
    
    if any(val < 0 for val in cumulative_values):
        raise ValueError("累積資產價值不能為負值")
    
    values = np.array(cumulative_values)
    
    # 計算各期的歷史最高點
    running_max = np.maximum.accumulate(values)
    
    # 計算回撤 (當前值相對歷史最高點的下跌幅度)
    drawdown = (values - running_max) / running_max
    
    # 找出最大回撤
    max_drawdown_idx = np.argmin(drawdown)
    max_drawdown = drawdown[max_drawdown_idx] * 100  # 轉為百分比
    
    # 找出回撤期間的起始點
    peak_idx = int(np.argmax(running_max[:max_drawdown_idx + 1]))
    max_drawdown_idx = int(max_drawdown_idx)
    
    logger.debug(f"最大回撤計算: {abs(max_drawdown):.2f}%, 發生在第{peak_idx}期到第{max_drawdown_idx}期")
    
    return abs(max_drawdown), (peak_idx, max_drawdown_idx)

# ============================================================================
# 輔助函數
# ============================================================================

def validate_strategy_parameters(C0: float, C_period: float, stock_ratio: float, 
                                bond_ratio: float) -> None:
    """
    驗證策略參數的有效性
    
    Args:
        C0: 期初投入金額
        C_period: 每期投入金額
        stock_ratio: 股票比例
        bond_ratio: 債券比例
    
    Raises:
        ValueError: 當參數無效時
    """
    if C0 < 0 or C_period < 0:
        raise ValueError("投入金額不能為負值")
    
    if not (0 <= stock_ratio <= 1) or not (0 <= bond_ratio <= 1):
        raise ValueError("配置比例必須在0到1之間")
    
    if abs(stock_ratio + bond_ratio - 1.0) > 1e-6:
        raise ValueError("股債配置比例總和必須等於1")

def format_calculation_result(result: Union[float, Dict, List], decimal_places: int = 4) -> Union[float, Dict, List]:
    """
    格式化計算結果，統一精度
    
    Args:
        result: 計算結果
        decimal_places: 小數位數
    
    Returns:
        格式化後的結果
    """
    if isinstance(result, float):
        return round(result, decimal_places)
    elif isinstance(result, dict):
        return {k: round(v, decimal_places) if isinstance(v, float) else v for k, v in result.items()}
    elif isinstance(result, list):
        return [round(x, decimal_places) if isinstance(x, float) else x for x in result]
    else:
        return result

# ============================================================================
# 模組測試函數
# ============================================================================

def test_calculation_formulas():
    """
    測試所有計算公式的基本功能
    """
    print("開始測試核心計算公式模組...")
    
    try:
        # 測試參數轉換
        params = convert_annual_to_period_parameters(12000, 8, 3, 10, "Monthly")
        print(f"✓ 參數轉換測試通過: {params}")
        
        # 測試VA目標價值計算
        va_target = calculate_va_target_value(1000, params["C_period"], params["r_period"], params["g_period"], 12)
        print(f"✓ VA目標價值計算測試通過: {va_target:.2f}")
        
        # 測試DCA投入計算
        dca_investment = calculate_dca_investment(params["C_period"], params["g_period"], 12)
        print(f"✓ DCA投入計算測試通過: {dca_investment:.2f}")
        
        # 測試資產配置
        stock_ratio, bond_ratio = calculate_portfolio_allocation(70)
        print(f"✓ 資產配置測試通過: 股票{stock_ratio:.1%}, 債券{bond_ratio:.1%}")
        
        # 測試債券定價
        bond_price = calculate_bond_price(5.0)
        print(f"✓ 債券定價測試通過: {bond_price:.2f}")
        
        # 測試年化報酬率
        annual_return = calculate_annualized_return(15000, 12000, 2)
        print(f"✓ 年化報酬率測試通過: {annual_return:.2f}%")
        
        print("\n✅ 所有核心計算公式測試通過！")
        
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        raise

# ============================================================================
# 2.1.5+ VA策略投報率增強計算模組
# ============================================================================

def calculate_time_weighted_return(period_returns: List[float], periods_per_year: int) -> float:
    """
    計算時間加權報酬率 (Time-Weighted Return, TWR)
    
    解決VA Rebalance策略中累積投入<0時投報率計算問題的專業方案
    時間加權報酬率不受現金流進出影響，反映真實的投資策略績效
    
    Args:
        period_returns: 各期報酬率列表 (百分比形式)
        periods_per_year: 每年期數
    
    Returns:
        float: 年化時間加權報酬率 (%)
    
    財務金融理論基礎:
    TWR = [(1+R1) × (1+R2) × ... × (1+Rn)]^(1/年數) - 1
    此方法是投資組合績效評估的國際標準，消除了現金流時機的影響
    """
    if not period_returns or len(period_returns) == 0:
        return 0.0
    
    if periods_per_year <= 0:
        raise ValueError("每年期數必須大於0")
    
    # 過濾有效的報酬率數據（移除NaN和第一期的0值）
    valid_returns = [r for r in period_returns if pd.notna(r) and r != 0]
    
    if len(valid_returns) == 0:
        return 0.0
    
    # 將百分比轉為小數形式
    returns_decimal = [r / 100 for r in valid_returns]
    
    # 複合計算：將各期報酬率相乘
    compound_return = 1.0
    for r in returns_decimal:
        compound_return *= (1 + r)
    
    # 計算投資年數
    total_periods = len(returns_decimal)
    years = total_periods / periods_per_year
    
    if years > 0 and compound_return > 0:
        # 年化處理
        annualized_twr = (compound_return ** (1 / years)) - 1
        return annualized_twr * 100
    
    return 0.0

def calculate_enhanced_annualized_return(final_value: float, total_investment: float, 
                                       investment_years: float, period_returns: List[float] = None,
                                       periods_per_year: int = 4) -> float:
    """
    增強的年化報酬率計算
    
    根據累積投入情況自動選擇最適當的計算方法：
    - 累積投入>0：使用傳統CAGR
    - 累積投入≤0：使用時間加權報酬率作為主要指標
    
    Args:
        final_value: 期末總資產價值
        total_investment: 累計總投入金額 (可能為負)
        investment_years: 投資年數
        period_returns: 各期報酬率列表 (可選)
        periods_per_year: 每年期數
    
    Returns:
        float: 推薦的年化報酬率 (%)
    """
    if final_value < 0:
        raise ValueError("資產價值必須非負")
    
    if investment_years <= 0:
        raise ValueError("投資年數必須大於0")
    
    try:
        # 情況1：累積投入>0，使用傳統CAGR
        if total_investment > 0:
            return calculate_annualized_return(final_value, total_investment, investment_years)
        
        # 情況2：累積投入≤0，使用時間加權報酬率
        elif period_returns and len(period_returns) > 0:
            twr = calculate_time_weighted_return(period_returns, periods_per_year)
            logger.info(f"累積投入≤0，使用時間加權報酬率: {twr:.2f}%")
            return twr
        
        # 情況3：無有效數據，返回0
        else:
            logger.warning("無足夠數據計算年化報酬率，返回0")
            return 0.0
            
    except Exception as e:
        logger.error(f"增強年化報酬率計算失敗: {e}")
        return 0.0

if __name__ == "__main__":
    test_calculation_formulas()