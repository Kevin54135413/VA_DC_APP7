"""
模擬數據生成器

實作第1章第1.2節要求的模擬數據生成功能：
1. 市場情境模擬（牛市、熊市、震盪市）
2. 隨機遊走模型
3. 債券殖利率模擬
4. 自定義參數配置
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class MarketRegime(Enum):
    """市場狀態枚舉"""
    BULL = "bull_market"      # 牛市
    BEAR = "bear_market"      # 熊市
    SIDEWAYS = "sideways"     # 震盪市
    RECOVERY = "recovery"     # 復甦期
    CRASH = "crash"           # 崩盤


@dataclass
class MarketScenarioConfig:
    """市場情境配置"""
    annual_return: float        # 年化報酬率
    annual_volatility: float    # 年化波動率
    duration_years: float       # 持續年數
    regime: MarketRegime        # 市場狀態
    drift_component: float = 0.0  # 趨勢分量
    mean_reversion: float = 0.0   # 均值回歸系數
    
    # 特殊事件參數
    crash_probability: float = 0.001  # 崩盤機率（每日）
    crash_magnitude: float = -0.2     # 崩盤幅度
    recovery_speed: float = 0.02      # 復甦速度


@dataclass
class YieldCurveConfig:
    """殖利率曲線配置"""
    base_yield: float = 4.0           # 基準殖利率 (%)
    volatility: float = 0.5           # 殖利率波動率 (%)
    mean_reversion_speed: float = 0.1 # 均值回歸速度
    long_term_mean: float = 4.0       # 長期均值 (%)
    
    # 期限結構參數
    term_structure: Dict[str, float] = field(default_factory=lambda: {
        '1M': -0.2,   # 1個月相對基準殖利率的差異
        '3M': -0.1,
        '6M': 0.0,
        '1Y': 0.1,
        '2Y': 0.3,
        '5Y': 0.6,
        '10Y': 1.0
    })


class SimulationDataGenerator:
    """
    模擬數據生成器
    
    提供各種市場情境的股票和債券數據模擬功能
    """
    
    def __init__(self, random_seed: Optional[int] = None):
        """
        初始化模擬器
        
        Args:
            random_seed: 隨機種子，用於結果重現
        """
        self.random_seed = random_seed
        # 不在初始化時設定全域隨機種子，確保每次調用都能產生不同的隨機序列
        
        # 預設市場情境配置
        self.market_scenarios = {
            MarketRegime.BULL: MarketScenarioConfig(
                annual_return=0.12,
                annual_volatility=0.18,
                duration_years=4.0,
                regime=MarketRegime.BULL,
                drift_component=0.0002,
                mean_reversion=0.05
            ),
            MarketRegime.BEAR: MarketScenarioConfig(
                annual_return=-0.08,
                annual_volatility=0.30,
                duration_years=1.5,
                regime=MarketRegime.BEAR,
                drift_component=-0.0003,
                mean_reversion=0.10,
                crash_probability=0.005,
                crash_magnitude=-0.15
            ),
            MarketRegime.SIDEWAYS: MarketScenarioConfig(
                annual_return=0.02,
                annual_volatility=0.15,
                duration_years=2.0,
                regime=MarketRegime.SIDEWAYS,
                mean_reversion=0.15
            ),
            MarketRegime.RECOVERY: MarketScenarioConfig(
                annual_return=0.25,
                annual_volatility=0.25,
                duration_years=1.0,
                regime=MarketRegime.RECOVERY,
                drift_component=0.0005,
                recovery_speed=0.05
            )
        }
        
        # 預設殖利率配置
        self.yield_config = YieldCurveConfig()
        
        logger.info("SimulationDataGenerator 初始化完成")
    
    def generate_stock_data(
        self,
        start_date: str,
        end_date: str,
        initial_price: float = 400.0,
        scenario: Optional[MarketRegime] = None,
        custom_config: Optional[MarketScenarioConfig] = None
    ) -> List[Dict[str, Any]]:
        """
        生成股票價格模擬數據
        
        Args:
            start_date: 開始日期 (YYYY-MM-DD)
            end_date: 結束日期 (YYYY-MM-DD)
            initial_price: 初始價格
            scenario: 市場情境
            custom_config: 自定義配置
        
        Returns:
            List[Dict]: 股票價格數據列表
        """
        try:
            # 生成日期序列
            dates = pd.date_range(start=start_date, end=end_date, freq='D')
            
            if len(dates) == 0:
                return []
            
            # 決定使用的配置
            if custom_config:
                config = custom_config
            elif scenario:
                config = self.market_scenarios.get(scenario, self.market_scenarios[MarketRegime.SIDEWAYS])
            else:
                # 隨機選擇一個情境
                scenario = np.random.choice(list(MarketRegime))
                config = self.market_scenarios[scenario]
            
            # 生成價格序列
            prices = self._generate_price_series(
                dates=dates,
                initial_price=initial_price,
                config=config
            )
            
            # 格式化輸出
            result = []
            for date, price in zip(dates, prices):
                result.append({
                    'date': date.strftime('%Y-%m-%d'),
                    'adjClose': round(float(price), 2),
                    'data_source': 'simulation',
                    'scenario': config.regime.value,
                    'annual_return': config.annual_return,
                    'annual_volatility': config.annual_volatility
                })
            
            logger.info(f"生成股票模擬數據: {len(result)} 筆, 情境: {config.regime.value}")
            return result
            
        except Exception as e:
            logger.error(f"股票數據生成失敗: {e}")
            return []
    
    def generate_yield_data(
        self,
        start_date: str,
        end_date: str,
        maturity: str = '1Y',
        custom_config: Optional[YieldCurveConfig] = None
    ) -> List[Dict[str, Any]]:
        """
        生成債券殖利率模擬數據
        
        Args:
            start_date: 開始日期 (YYYY-MM-DD)
            end_date: 結束日期 (YYYY-MM-DD)
            maturity: 債券期限 ('1M', '3M', '6M', '1Y', '2Y', '5Y', '10Y')
            custom_config: 自定義殖利率配置
        
        Returns:
            List[Dict]: 殖利率數據列表
        """
        try:
            # 生成日期序列
            dates = pd.date_range(start=start_date, end=end_date, freq='D')
            
            if len(dates) == 0:
                return []
            
            # 使用配置
            config = custom_config or self.yield_config
            
            # 計算該期限的基準殖利率
            base_adjustment = config.term_structure.get(maturity, 0.0)
            target_yield = config.base_yield + base_adjustment
            
            # 生成殖利率序列
            yields = self._generate_yield_series(
                dates=dates,
                target_yield=target_yield,
                config=config
            )
            
            # 格式化輸出
            result = []
            for date, yield_val in zip(dates, yields):
                result.append({
                    'date': date.strftime('%Y-%m-%d'),
                    'value': str(round(float(yield_val), 4)),
                    'data_source': 'simulation',
                    'maturity': maturity,
                    'base_yield': config.base_yield,
                    'volatility': config.volatility
                })
            
            logger.info(f"生成殖利率模擬數據: {len(result)} 筆, 期限: {maturity}")
            return result
            
        except Exception as e:
            logger.error(f"殖利率數據生成失敗: {e}")
            return []
    
    def generate_mixed_scenario_data(
        self,
        start_date: str,
        end_date: str,
        initial_price: float = 400.0,
        scenario_sequence: Optional[List[Tuple[MarketRegime, int]]] = None
    ) -> List[Dict[str, Any]]:
        """
        生成多情境混合的模擬數據
        
        Args:
            start_date: 開始日期
            end_date: 結束日期  
            initial_price: 初始價格
            scenario_sequence: 情境序列 [(情境, 持續天數), ...]
        
        Returns:
            List[Dict]: 混合情境股票數據
        """
        try:
            dates = pd.date_range(start=start_date, end=end_date, freq='D')
            total_days = len(dates)
            
            if total_days == 0:
                return []
            
            # 預設情境序列
            if scenario_sequence is None:
                scenario_sequence = [
                    (MarketRegime.BULL, total_days // 3),
                    (MarketRegime.SIDEWAYS, total_days // 3),
                    (MarketRegime.BEAR, total_days - 2 * (total_days // 3))
                ]
            
            # 生成混合數據
            all_prices = []
            current_price = initial_price
            start_idx = 0
            
            for scenario, duration in scenario_sequence:
                end_idx = min(start_idx + duration, total_days)
                
                if start_idx >= total_days:
                    break
                
                # 生成該情境的數據
                scenario_dates = dates[start_idx:end_idx]
                config = self.market_scenarios[scenario]
                
                scenario_prices = self._generate_price_series(
                    dates=scenario_dates,
                    initial_price=current_price,
                    config=config
                )
                
                all_prices.extend(scenario_prices)
                current_price = scenario_prices[-1] if scenario_prices else current_price
                start_idx = end_idx
            
            # 格式化輸出
            result = []
            for i, (date, price) in enumerate(zip(dates[:len(all_prices)], all_prices)):
                # 判斷當前屬於哪個情境
                current_scenario = self._get_scenario_at_index(i, scenario_sequence)
                
                result.append({
                    'date': date.strftime('%Y-%m-%d'),
                    'adjClose': round(float(price), 2),
                    'data_source': 'simulation_mixed',
                    'scenario': current_scenario.value if current_scenario else 'unknown'
                })
            
            logger.info(f"生成混合情境模擬數據: {len(result)} 筆")
            return result
            
        except Exception as e:
            logger.error(f"混合情境數據生成失敗: {e}")
            return []
    
    def _generate_price_series(
        self,
        dates: pd.DatetimeIndex,
        initial_price: float,
        config: MarketScenarioConfig
    ) -> np.ndarray:
        """生成價格序列"""
        n_days = len(dates)
        
        if n_days == 0:
            return np.array([])
        
        # 使用動態隨機種子確保每次調用都產生不同的隨機序列
        if self.random_seed is None:
            # 基於當前時間戳和日期範圍生成動態種子
            import time
            dynamic_seed = int(time.time() * 1000000) % 2147483647
            dynamic_seed ^= hash(dates[0].strftime('%Y-%m-%d')) % 2147483647
            np.random.seed(dynamic_seed)
        else:
            # 如果指定了隨機種子，結合日期信息確保不同期間有不同的隨機序列
            combined_seed = (self.random_seed + hash(dates[0].strftime('%Y-%m-%d'))) % 2147483647
            np.random.seed(combined_seed)
        
        # 計算日報酬率參數
        daily_return = config.annual_return / 252  # 252個交易日
        daily_volatility = config.annual_volatility / np.sqrt(252)
        
        # 生成隨機沖擊
        random_shocks = np.random.normal(0, daily_volatility, n_days)
        
        # 添加趨勢分量
        if config.drift_component != 0:
            trend = np.linspace(0, config.drift_component * n_days, n_days)
            random_shocks += trend
        
        # 添加均值回歸
        if config.mean_reversion > 0:
            for i in range(1, n_days):
                reversion = -config.mean_reversion * random_shocks[i-1]
                random_shocks[i] += reversion
        
        # 添加特殊事件（崩盤）
        if config.regime == MarketRegime.BEAR and config.crash_probability > 0:
            crash_events = np.random.random(n_days) < config.crash_probability
            random_shocks[crash_events] += config.crash_magnitude
        
        # 添加復甦加速
        if config.regime == MarketRegime.RECOVERY and config.recovery_speed > 0:
            recovery_boost = np.random.exponential(config.recovery_speed, n_days)
            positive_days = random_shocks > 0
            random_shocks[positive_days] += recovery_boost[positive_days]
        
        # 計算累積報酬率
        log_returns = daily_return + random_shocks
        cumulative_returns = np.cumsum(log_returns)
        
        # 轉換為價格
        prices = initial_price * np.exp(cumulative_returns)
        
        # 確保價格為正數
        prices = np.maximum(prices, 0.01)
        
        return prices
    
    def _generate_yield_series(
        self,
        dates: pd.DatetimeIndex,
        target_yield: float,
        config: YieldCurveConfig
    ) -> np.ndarray:
        """生成殖利率序列"""
        n_days = len(dates)
        
        if n_days == 0:
            return np.array([])
        
        # 使用動態隨機種子確保每次調用都產生不同的隨機序列
        if self.random_seed is None:
            # 基於當前時間戳和日期範圍生成動態種子
            import time
            dynamic_seed = int(time.time() * 1000000) % 2147483647
            dynamic_seed ^= hash(dates[0].strftime('%Y-%m-%d-yield')) % 2147483647
            np.random.seed(dynamic_seed)
        else:
            # 如果指定了隨機種子，結合日期信息確保不同期間有不同的隨機序列
            combined_seed = (self.random_seed + hash(dates[0].strftime('%Y-%m-%d-yield'))) % 2147483647
            np.random.seed(combined_seed)
        
        # 初始化
        yields = np.zeros(n_days)
        yields[0] = target_yield
        
        # 日波動率
        daily_volatility = config.volatility / np.sqrt(252)
        
        # 生成序列
        for i in range(1, n_days):
            # 均值回歸項
            mean_reversion = config.mean_reversion_speed * (
                config.long_term_mean - yields[i-1]
            )
            
            # 隨機沖擊
            random_shock = np.random.normal(0, daily_volatility)
            
            # 更新殖利率
            yields[i] = yields[i-1] + mean_reversion + random_shock
            
            # 限制在合理範圍內
            yields[i] = np.clip(yields[i], -2.0, 15.0)
        
        return yields
    
    def _get_scenario_at_index(
        self,
        index: int,
        scenario_sequence: List[Tuple[MarketRegime, int]]
    ) -> Optional[MarketRegime]:
        """獲取指定索引處的市場情境"""
        current_idx = 0
        
        for scenario, duration in scenario_sequence:
            if current_idx <= index < current_idx + duration:
                return scenario
            current_idx += duration
        
        return None
    
    def generate_stress_test_data(
        self,
        start_date: str,
        end_date: str,
        initial_price: float = 400.0,
        stress_type: str = 'black_swan'
    ) -> List[Dict[str, Any]]:
        """
        生成壓力測試數據
        
        Args:
            start_date: 開始日期
            end_date: 結束日期
            initial_price: 初始價格
            stress_type: 壓力測試類型 ('black_swan', 'prolonged_bear', 'high_volatility')
        
        Returns:
            List[Dict]: 壓力測試數據
        """
        stress_configs = {
            'black_swan': MarketScenarioConfig(
                annual_return=-0.30,
                annual_volatility=0.50,
                duration_years=0.5,
                regime=MarketRegime.CRASH,
                crash_probability=0.02,
                crash_magnitude=-0.25
            ),
            'prolonged_bear': MarketScenarioConfig(
                annual_return=-0.15,
                annual_volatility=0.35,
                duration_years=3.0,
                regime=MarketRegime.BEAR,
                mean_reversion=0.02
            ),
            'high_volatility': MarketScenarioConfig(
                annual_return=0.05,
                annual_volatility=0.60,
                duration_years=2.0,
                regime=MarketRegime.SIDEWAYS,
                mean_reversion=0.20
            )
        }
        
        config = stress_configs.get(stress_type, stress_configs['black_swan'])
        
        return self.generate_stock_data(
            start_date=start_date,
            end_date=end_date,
            initial_price=initial_price,
            custom_config=config
        )
    
    def get_market_summary(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        計算模擬數據的市場統計摘要
        
        Args:
            data: 模擬數據
        
        Returns:
            Dict: 統計摘要
        """
        if not data:
            return {}
        
        try:
            prices = [item['adjClose'] for item in data if 'adjClose' in item]
            
            if len(prices) < 2:
                return {}
            
            # 計算日報酬率
            returns = [(prices[i] / prices[i-1]) - 1 for i in range(1, len(prices))]
            
            # 計算統計指標
            total_return = (prices[-1] / prices[0]) - 1
            annual_return = (1 + total_return) ** (252 / len(prices)) - 1
            volatility = np.std(returns) * np.sqrt(252)
            
            # 最大回撤
            peak = prices[0]
            max_drawdown = 0
            for price in prices:
                peak = max(peak, price)
                drawdown = (peak - price) / peak
                max_drawdown = max(max_drawdown, drawdown)
            
            # 夏普比率（假設無風險利率為2%）
            excess_return = annual_return - 0.02
            sharpe_ratio = excess_return / volatility if volatility > 0 else 0
            
            return {
                'total_return': total_return,
                'annual_return': annual_return,
                'volatility': volatility,
                'max_drawdown': max_drawdown,
                'sharpe_ratio': sharpe_ratio,
                'min_price': min(prices),
                'max_price': max(prices),
                'final_price': prices[-1],
                'data_points': len(prices)
            }
            
        except Exception as e:
            logger.error(f"市場摘要計算失敗: {e}")
            return {}

    def generate_period_price_timeline(
        self,
        period_info: Dict[str, Any],
        initial_price: float,
        market_params: Dict[str, float]
    ) -> Dict[str, Any]:
        """
        為特定期間生成完整的價格時間序列
        
        依據需求文件1.1.3節規格實作，使用幾何布朗運動生成每日價格
        
        Args:
            period_info: 從 generate_simulation_timeline 取得的期間資訊
            initial_price: 期初價格
            market_params: 市場參數字典，包含:
                - annual_return: 年化報酬率
                - volatility: 年化波動率 (σ)
                - drift_component: 趨勢分量 (可選)
                - mean_reversion: 均值回歸系數 (可選)
        
        Returns:
            dict: 包含每日價格和關鍵日期價格的詳細字典
        """
        try:
            # 提取期間內的交易日
            trading_days = period_info.get('trading_days', [])
            
            if not trading_days:
                logger.warning(f"期間 {period_info.get('period', 'unknown')} 無交易日數據")
                return self._create_empty_timeline_result(period_info, initial_price)
            
            # 轉換交易日為datetime對象（如果需要）
            if isinstance(trading_days[0], str):
                trading_days = [datetime.strptime(day, '%Y-%m-%d') for day in trading_days]
            
            daily_prices = []
            current_price = initial_price
            
            # 提取市場參數
            annual_return = market_params.get('annual_return', 0.08)
            volatility = market_params.get('volatility', 0.15)
            drift_component = market_params.get('drift_component', 0.0)
            mean_reversion = market_params.get('mean_reversion', 0.0)
            
            # 設定基於期間的動態隨機種子確保每期都有不同的隨機序列
            period_num = period_info.get('period', 1)
            start_date_str = trading_days[0].strftime('%Y-%m-%d')
            if self.random_seed is None:
                # 基於當前時間戳、期間編號和起始日期生成動態種子
                import time
                dynamic_seed = int(time.time() * 1000000) % 2147483647
                dynamic_seed ^= (period_num * 31 + hash(start_date_str)) % 2147483647
                np.random.seed(dynamic_seed)
            else:
                # 如果指定了隨機種子，結合期間信息確保不同期間有不同的隨機序列
                combined_seed = (self.random_seed + period_num * 31 + hash(start_date_str)) % 2147483647
                np.random.seed(combined_seed)
            
            # 使用幾何布朗運動生成每日價格
            for i, date in enumerate(trading_days):
                if i == 0:
                    # 期初價格
                    daily_prices.append({
                        'date': date,
                        'price': current_price,
                        'price_type': 'period_start'
                    })
                else:
                    # 使用隨機過程生成下一日價格
                    dt = 1/252  # 每日時間增量（252個交易日）
                    
                    # 幾何布朗運動公式: S(t+1) = S(t) * exp((μ - σ²/2) * dt + σ * √dt * Z)
                    drift = annual_return - 0.5 * volatility**2
                    diffusion = volatility * np.random.normal(0, np.sqrt(dt))
                    
                    # 添加趨勢分量
                    if drift_component != 0:
                        drift += drift_component
                    
                    # 計算價格變化
                    price_change = np.exp(drift * dt + diffusion)
                    current_price = current_price * price_change
                    
                    # 添加均值回歸效應
                    if mean_reversion > 0 and i > 1:
                        # 計算與初始價格的偏離
                        deviation = (current_price - initial_price) / initial_price
                        reversion_factor = 1 - mean_reversion * deviation * dt
                        current_price *= reversion_factor
                    
                    # 確保價格為正數
                    current_price = max(current_price, 0.01)
                    
                    # 判斷價格類型
                    price_type = 'period_end' if i == len(trading_days) - 1 else 'intermediate'
                    
                    daily_prices.append({
                        'date': date,
                        'price': round(current_price, 2),
                        'price_type': price_type
                    })
            
            # 計算期間統計
            prices_only = [p['price'] for p in daily_prices]
            period_return = (daily_prices[-1]['price'] / daily_prices[0]['price']) - 1
            
            # 計算價格統計
            price_statistics = {
                'min_price': min(prices_only),
                'max_price': max(prices_only),
                'avg_price': sum(prices_only) / len(prices_only),
                'price_range': max(prices_only) - min(prices_only),
                'price_volatility': np.std(prices_only) if len(prices_only) > 1 else 0.0
            }
            
            # 計算日報酬率統計
            if len(daily_prices) > 1:
                daily_returns = []
                for i in range(1, len(daily_prices)):
                    daily_return = (daily_prices[i]['price'] / daily_prices[i-1]['price']) - 1
                    daily_returns.append(daily_return)
                
                return_statistics = {
                    'daily_returns': daily_returns,
                    'avg_daily_return': np.mean(daily_returns),
                    'daily_volatility': np.std(daily_returns),
                    'max_daily_gain': max(daily_returns) if daily_returns else 0.0,
                    'max_daily_loss': min(daily_returns) if daily_returns else 0.0
                }
            else:
                return_statistics = {
                    'daily_returns': [],
                    'avg_daily_return': 0.0,
                    'daily_volatility': 0.0,
                    'max_daily_gain': 0.0,
                    'max_daily_loss': 0.0
                }
            
            # 構建完整結果
            result = {
                'period': period_info.get('period', 1),
                'period_start_price': daily_prices[0]['price'],
                'period_end_price': daily_prices[-1]['price'],
                'period_return': period_return,
                'daily_prices': daily_prices,
                'price_statistics': price_statistics,
                'return_statistics': return_statistics,
                'market_params_used': {
                    'annual_return': annual_return,
                    'volatility': volatility,
                    'drift_component': drift_component,
                    'mean_reversion': mean_reversion
                },
                'period_info': {
                    'trading_days_count': len(trading_days),
                    'start_date': trading_days[0].strftime('%Y-%m-%d'),
                    'end_date': trading_days[-1].strftime('%Y-%m-%d'),
                    'raw_start_date': period_info.get('raw_start_date'),
                    'raw_end_date': period_info.get('raw_end_date'),
                    'date_adjustments': period_info.get('date_adjustments', {})
                }
            }
            
            logger.info(f"成功生成第{result['period']}期價格時間軸: "
                       f"{len(daily_prices)}個交易日, "
                       f"期間報酬率: {period_return:.2%}")
            
            return result
            
        except Exception as e:
            logger.error(f"generate_period_price_timeline 失敗: {e}")
            return self._create_empty_timeline_result(period_info, initial_price)
    
    def _create_empty_timeline_result(
        self,
        period_info: Dict[str, Any],
        initial_price: float
    ) -> Dict[str, Any]:
        """創建空的時間軸結果（錯誤處理用）"""
        return {
            'period': period_info.get('period', 1),
            'period_start_price': initial_price,
            'period_end_price': initial_price,
            'period_return': 0.0,
            'daily_prices': [{
                'date': datetime.now(),
                'price': initial_price,
                'price_type': 'period_start'
            }],
            'price_statistics': {
                'min_price': initial_price,
                'max_price': initial_price,
                'avg_price': initial_price,
                'price_range': 0.0,
                'price_volatility': 0.0
            },
            'return_statistics': {
                'daily_returns': [],
                'avg_daily_return': 0.0,
                'daily_volatility': 0.0,
                'max_daily_gain': 0.0,
                'max_daily_loss': 0.0
            },
            'market_params_used': {},
            'period_info': {
                'trading_days_count': 0,
                'start_date': '',
                'end_date': '',
                'raw_start_date': None,
                'raw_end_date': None,
                'date_adjustments': {}
            },
            'error': '無有效交易日數據'
        } 