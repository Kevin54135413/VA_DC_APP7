"""
績效指標計算模組 - 第2章規格實現

提供完整的投資績效指標計算功能：
- IRR（內部報酬率）計算
- 夏普比率計算（3位小數精度）
- 年化報酬率計算
- 最大回撤計算
- 波動率計算
"""

import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# 第2章規格：績效指標精度規則
PERFORMANCE_PRECISION = {
    'irr': 4,           # IRR精度：小數點後4位
    'sharpe_ratio': 3,  # 夏普比率：3位小數精度
    'return': 4,        # 報酬率精度：小數點後4位
    'volatility': 4,    # 波動率精度：小數點後4位
    'drawdown': 4       # 回撤精度：小數點後4位
}

def calculate_irr(cash_flows: List[float], dates: Optional[List[datetime]] = None, 
                  max_iterations: int = 100, tolerance: float = 1e-6) -> float:
    """
    計算內部報酬率（IRR）
    
    Args:
        cash_flows: 現金流列表（負值為投入，正值為收入）
        dates: 日期列表（可選）
        max_iterations: 最大迭代次數
        tolerance: 收斂容忍度
        
    Returns:
        float: IRR值（年化）
    """
    if not cash_flows or len(cash_flows) < 2:
        return 0.0
    
    # 檢查現金流是否有效
    if sum(cash_flows) == 0:
        return 0.0
    
    # 使用牛頓法求解IRR
    try:
        # 初始猜測值
        rate = 0.1
        
        for i in range(max_iterations):
            # 計算NPV和NPV的導數
            npv = 0.0
            npv_derivative = 0.0
            
            for j, cf in enumerate(cash_flows):
                if dates:
                    # 使用實際日期計算時間差
                    time_factor = (dates[j] - dates[0]).days / 365.25
                else:
                    # 假設等間隔現金流
                    time_factor = j
                
                if time_factor == 0:
                    npv += cf
                else:
                    discount_factor = (1 + rate) ** time_factor
                    npv += cf / discount_factor
                    npv_derivative -= cf * time_factor / (discount_factor * (1 + rate))
            
            # 檢查收斂
            if abs(npv) < tolerance:
                break
            
            # 檢查導數是否為零
            if abs(npv_derivative) < tolerance:
                break
            
            # 牛頓法更新
            rate = rate - npv / npv_derivative
        
        # 確保結果在合理範圍內
        if rate < -0.99 or rate > 10.0:
            return 0.0
        
        return round(rate, PERFORMANCE_PRECISION['irr'])
        
    except Exception as e:
        logger.warning(f"IRR計算失敗: {str(e)}")
        return 0.0

def calculate_sharpe_ratio(returns: List[float], risk_free_rate: float = 0.02) -> float:
    """
    計算夏普比率（3位小數精度）
    
    Args:
        returns: 報酬率列表
        risk_free_rate: 無風險利率（年化）
        
    Returns:
        float: 夏普比率
    """
    if not returns or len(returns) < 2:
        return 0.0
    
    try:
        returns_array = np.array(returns)
        
        # 計算超額報酬
        excess_returns = returns_array - risk_free_rate / len(returns)
        
        # 計算平均超額報酬
        mean_excess_return = np.mean(excess_returns)
        
        # 計算標準差
        std_excess_return = np.std(excess_returns, ddof=1)
        
        # 避免除零
        if std_excess_return == 0:
            return 0.0
        
        # 計算夏普比率
        sharpe_ratio = mean_excess_return / std_excess_return
        
        # 年化調整
        sharpe_ratio = sharpe_ratio * np.sqrt(len(returns))
        
        return round(sharpe_ratio, PERFORMANCE_PRECISION['sharpe_ratio'])
        
    except Exception as e:
        logger.warning(f"夏普比率計算失敗: {str(e)}")
        return 0.0

def calculate_annualized_return(total_return: float, years: float) -> float:
    """
    計算年化報酬率
    
    Args:
        total_return: 總報酬率
        years: 投資年數
        
    Returns:
        float: 年化報酬率
    """
    if years <= 0:
        return 0.0
    
    try:
        # 年化報酬率公式：(1 + 總報酬率)^(1/年數) - 1
        annualized_return = (1 + total_return) ** (1 / years) - 1
        
        return round(annualized_return, PERFORMANCE_PRECISION['return'])
        
    except Exception as e:
        logger.warning(f"年化報酬率計算失敗: {str(e)}")
        return 0.0

def calculate_max_drawdown(values: List[float]) -> float:
    """
    計算最大回撤
    
    Args:
        values: 投資組合價值列表
        
    Returns:
        float: 最大回撤（負值）
    """
    if not values or len(values) < 2:
        return 0.0
    
    try:
        values_array = np.array(values)
        
        # 計算累計最高點
        running_max = np.maximum.accumulate(values_array)
        
        # 計算回撤
        drawdown = (values_array - running_max) / running_max
        
        # 找出最大回撤
        max_drawdown = np.min(drawdown)
        
        return round(max_drawdown, PERFORMANCE_PRECISION['drawdown'])
        
    except Exception as e:
        logger.warning(f"最大回撤計算失敗: {str(e)}")
        return 0.0

def calculate_volatility(returns: List[float], annualized: bool = True) -> float:
    """
    計算波動率
    
    Args:
        returns: 報酬率列表
        annualized: 是否年化
        
    Returns:
        float: 波動率
    """
    if not returns or len(returns) < 2:
        return 0.0
    
    try:
        returns_array = np.array(returns)
        
        # 計算標準差
        volatility = np.std(returns_array, ddof=1)
        
        # 年化調整
        if annualized:
            volatility = volatility * np.sqrt(len(returns))
        
        return round(volatility, PERFORMANCE_PRECISION['volatility'])
        
    except Exception as e:
        logger.warning(f"波動率計算失敗: {str(e)}")
        return 0.0

def calculate_sortino_ratio(returns: List[float], risk_free_rate: float = 0.02) -> float:
    """
    計算Sortino比率
    
    Args:
        returns: 報酬率列表
        risk_free_rate: 無風險利率
        
    Returns:
        float: Sortino比率
    """
    if not returns or len(returns) < 2:
        return 0.0
    
    try:
        returns_array = np.array(returns)
        
        # 計算超額報酬
        excess_returns = returns_array - risk_free_rate / len(returns)
        
        # 計算平均超額報酬
        mean_excess_return = np.mean(excess_returns)
        
        # 計算下行標準差（只考慮負報酬）
        negative_returns = excess_returns[excess_returns < 0]
        
        if len(negative_returns) == 0:
            return float('inf')
        
        downside_std = np.std(negative_returns, ddof=1)
        
        # 避免除零
        if downside_std == 0:
            return 0.0
        
        # 計算Sortino比率
        sortino_ratio = mean_excess_return / downside_std
        
        # 年化調整
        sortino_ratio = sortino_ratio * np.sqrt(len(returns))
        
        return round(sortino_ratio, PERFORMANCE_PRECISION['sharpe_ratio'])
        
    except Exception as e:
        logger.warning(f"Sortino比率計算失敗: {str(e)}")
        return 0.0

def calculate_calmar_ratio(total_return: float, max_drawdown: float, years: float) -> float:
    """
    計算Calmar比率
    
    Args:
        total_return: 總報酬率
        max_drawdown: 最大回撤
        years: 投資年數
        
    Returns:
        float: Calmar比率
    """
    if years <= 0 or max_drawdown >= 0:
        return 0.0
    
    try:
        # 年化報酬率
        annualized_return = calculate_annualized_return(total_return, years)
        
        # Calmar比率 = 年化報酬率 / |最大回撤|
        calmar_ratio = annualized_return / abs(max_drawdown)
        
        return round(calmar_ratio, PERFORMANCE_PRECISION['return'])
        
    except Exception as e:
        logger.warning(f"Calmar比率計算失敗: {str(e)}")
        return 0.0

def calculate_information_ratio(portfolio_returns: List[float], benchmark_returns: List[float]) -> float:
    """
    計算信息比率
    
    Args:
        portfolio_returns: 投資組合報酬率列表
        benchmark_returns: 基準報酬率列表
        
    Returns:
        float: 信息比率
    """
    if not portfolio_returns or not benchmark_returns or len(portfolio_returns) != len(benchmark_returns):
        return 0.0
    
    try:
        portfolio_array = np.array(portfolio_returns)
        benchmark_array = np.array(benchmark_returns)
        
        # 計算超額報酬
        excess_returns = portfolio_array - benchmark_array
        
        # 計算平均超額報酬
        mean_excess_return = np.mean(excess_returns)
        
        # 計算追蹤誤差
        tracking_error = np.std(excess_returns, ddof=1)
        
        # 避免除零
        if tracking_error == 0:
            return 0.0
        
        # 計算信息比率
        information_ratio = mean_excess_return / tracking_error
        
        return round(information_ratio, PERFORMANCE_PRECISION['return'])
        
    except Exception as e:
        logger.warning(f"信息比率計算失敗: {str(e)}")
        return 0.0

def calculate_comprehensive_metrics(values: List[float], dates: Optional[List[datetime]] = None,
                                   risk_free_rate: float = 0.02) -> Dict[str, float]:
    """
    計算綜合績效指標
    
    Args:
        values: 投資組合價值列表
        dates: 日期列表（可選）
        risk_free_rate: 無風險利率
        
    Returns:
        Dict[str, float]: 綜合績效指標
    """
    if not values or len(values) < 2:
        return {}
    
    try:
        # 計算報酬率
        returns = []
        for i in range(1, len(values)):
            return_rate = (values[i] - values[i-1]) / values[i-1]
            returns.append(return_rate)
        
        # 計算總報酬率
        total_return = (values[-1] - values[0]) / values[0]
        
        # 計算投資年數
        if dates:
            years = (dates[-1] - dates[0]).days / 365.25
        else:
            years = len(values) / 12  # 假設月頻率
        
        # 計算現金流（用於IRR計算）
        cash_flows = [-values[0]]  # 初始投入
        cash_flows.extend([0] * (len(values) - 2))  # 中間無現金流
        cash_flows.append(values[-1])  # 最終價值
        
        # 計算各項指標
        metrics = {
            'total_return': round(total_return, PERFORMANCE_PRECISION['return']),
            'annualized_return': calculate_annualized_return(total_return, years),
            'volatility': calculate_volatility(returns),
            'sharpe_ratio': calculate_sharpe_ratio(returns, risk_free_rate),
            'sortino_ratio': calculate_sortino_ratio(returns, risk_free_rate),
            'max_drawdown': calculate_max_drawdown(values),
            'irr': calculate_irr(cash_flows, dates),
            'calmar_ratio': calculate_calmar_ratio(total_return, calculate_max_drawdown(values), years)
        }
        
        return metrics
        
    except Exception as e:
        logger.error(f"綜合績效指標計算失敗: {str(e)}")
        return {} 