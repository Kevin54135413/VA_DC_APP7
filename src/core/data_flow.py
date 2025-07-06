"""
第4.4節 - 簡化資料流整合

實作簡化的資料流程和基本錯誤恢復機制，整合第1-3章功能。
資料流程圖：[用戶輸入] → [基本驗證] → [數據獲取] → [策略計算] → [結果顯示]
"""

import streamlit as st
import pandas as pd
import numpy as np
from typing import Optional, Dict, Any, List, Tuple, Callable
from datetime import datetime, timedelta
import logging
from dataclasses import dataclass

# 導入第1章數據源
from src.data_sources.simulation import SimulationDataGenerator, MarketRegime
from src.data_sources.data_fetcher import TiingoDataFetcher, FREDDataFetcher
from src.data_sources.fault_tolerance import APIFaultToleranceManager

# 導入第2章計算引擎
from src.models.strategy_engine import calculate_va_strategy, calculate_dca_strategy
from src.models.table_calculator import calculate_summary_metrics

# 導入第3章UI組件
from src.ui.results_display import ResultsDisplayManager

# 設置日誌
logger = logging.getLogger(__name__)

# ============================================================================
# 資料流程配置
# ============================================================================

@dataclass
class DataFlowConfig:
    """資料流程配置"""
    enable_api_fallback: bool = True
    enable_simulation_fallback: bool = True
    max_retry_attempts: int = 2
    data_validation_enabled: bool = True
    streamlit_progress_enabled: bool = True

# ============================================================================
# 第4.4節核心函數
# ============================================================================

def basic_error_recovery() -> Optional[Any]:
    """
    基本錯誤恢復機制
    
    按照需求文件第4.4節規格實作：
    - 實作fallback_methods列表
    - 循序嘗試各種備援方法
    - 使用Streamlit訊息提示當前使用的數據源
    - 所有方法都失敗時顯示錯誤訊息
    
    Returns:
        Optional[Any]: 成功獲取的數據，失敗則返回None
    """
    logger.info("啟動基本錯誤恢復機制")
    
    # 定義備援方法列表（按照需求文件規格）
    fallback_methods = [
        ("歷史數據API", fetch_historical_data_simple),
        ("模擬數據", generate_simulation_data_simple)
    ]
    
    for method_name, method_func in fallback_methods:
        try:
            logger.info(f"嘗試使用數據源: {method_name}")
            
            # 顯示當前使用的數據源
            st.info(f"🔄 正在使用 {method_name} 獲取數據...")
            
            result = method_func()
            
            if result is not None:
                st.success(f"✅ 成功使用 {method_name} 獲取數據")
                logger.info(f"數據源 {method_name} 成功返回數據")
                return result
                
        except Exception as e:
            logger.warning(f"數據源 {method_name} 失敗: {str(e)}")
            st.warning(f"⚠️ {method_name} 暫時無法使用，嘗試下一個數據源...")
            continue
    
    # 所有方法都失敗
    error_message = "❌ 所有數據源都無法使用，請檢查網路連接或稍後再試"
    st.error(error_message)
    logger.error("所有備援方法都失敗")
    return None

def fetch_historical_data_simple() -> Optional[Dict[str, Any]]:
    """
    簡化的歷史數據獲取函數
    
    整合第1章API數據源，簡化複雜的容錯機制
    
    Returns:
        Optional[Dict[str, Any]]: 歷史市場數據
    """
    try:
        logger.info("嘗試獲取歷史數據")
        
        # 使用第1章的數據獲取器
        fault_manager = APIFaultToleranceManager()
        
        # 設定預設時間範圍（最近1年）
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365)
        
        start_date_str = start_date.strftime('%Y-%m-%d')
        end_date_str = end_date.strftime('%Y-%m-%d')
        
        # 嘗試獲取股票數據
        tiingo_fetcher = TiingoDataFetcher()
        stock_data = tiingo_fetcher.fetch_stock_data(
            symbol='SPY',
            start_date=start_date_str,
            end_date=end_date_str
        )
        
        # 嘗試獲取債券數據
        fred_fetcher = FREDDataFetcher()
        bond_data = fred_fetcher.fetch_yield_data(
            start_date=start_date_str,
            end_date=end_date_str
        )
        
        if stock_data and bond_data:
            historical_data = {
                'stock_data': stock_data,
                'bond_data': bond_data,
                'metadata': {
                    'start_date': start_date_str,
                    'end_date': end_date_str,
                    'data_source': 'historical_api',
                    'total_records': len(stock_data) + len(bond_data)
                }
            }
            
            logger.info(f"成功獲取歷史數據: {len(stock_data)} 股票記錄, {len(bond_data)} 債券記錄")
            return historical_data
        else:
            logger.warning("歷史數據獲取不完整")
            return None
            
    except Exception as e:
        logger.error(f"歷史數據獲取失敗: {str(e)}")
        return None

def generate_simulation_data_simple() -> Optional[Dict[str, Any]]:
    """
    簡化的模擬數據生成函數
    
    使用第1章模擬數據生成器，提供可靠的備援數據
    
    Returns:
        Optional[Dict[str, Any]]: 模擬市場數據
    """
    try:
        logger.info("生成模擬數據")
        
        # 使用第1章的模擬數據生成器
        simulator = SimulationDataGenerator()
        
        # 設定模擬參數
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365)
        
        start_date_str = start_date.strftime('%Y-%m-%d')
        end_date_str = end_date.strftime('%Y-%m-%d')
        
        # 生成股票模擬數據
        stock_data = simulator.generate_stock_data(
            start_date=start_date_str,
            end_date=end_date_str,
            scenario=MarketRegime.SIDEWAYS
        )
        
        # 生成債券模擬數據
        bond_data = simulator.generate_yield_data(
            start_date=start_date_str,
            end_date=end_date_str
        )
        
        if stock_data and bond_data:
            simulation_data = {
                'stock_data': stock_data,
                'bond_data': bond_data,
                'metadata': {
                    'start_date': start_date_str,
                    'end_date': end_date_str,
                    'data_source': 'simulation',
                    'scenario': 'sideways',
                    'total_records': len(stock_data) + len(bond_data)
                }
            }
            
            logger.info(f"成功生成模擬數據: {len(stock_data)} 股票記錄, {len(bond_data)} 債券記錄")
            return simulation_data
        else:
            logger.warning("模擬數據生成不完整")
            return None
            
    except Exception as e:
        logger.error(f"模擬數據生成失敗: {str(e)}")
        return None

# ============================================================================
# 簡化資料流程管道
# ============================================================================

class SimpleDataFlowPipeline:
    """
    簡化資料流程管道
    
    實作資料流程圖：[用戶輸入] → [基本驗證] → [數據獲取] → [策略計算] → [結果顯示]
    """
    
    def __init__(self, config: Optional[DataFlowConfig] = None):
        """
        初始化簡化資料流程管道
        
        Args:
            config: 資料流程配置
        """
        self.config = config or DataFlowConfig()
        self.results_manager = ResultsDisplayManager()
        logger.info("簡化資料流程管道初始化完成")
    
    def execute_pipeline(self, user_parameters: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        執行完整的資料流程管道
        
        Args:
            user_parameters: 用戶輸入參數
        
        Returns:
            Optional[Dict[str, Any]]: 處理結果
        """
        try:
            logger.info("開始執行簡化資料流程管道")
            
            # 步驟1: 基本驗證
            if not self._validate_user_input(user_parameters):
                st.error("❌ 參數驗證失敗，請檢查輸入值")
                return None
            
            # 步驟2: 數據獲取
            market_data = self._fetch_market_data()
            if not market_data:
                st.error("❌ 數據獲取失敗")
                return None
            
            # 步驟3: 策略計算
            calculation_results = self._calculate_strategies(user_parameters, market_data)
            if not calculation_results:
                st.error("❌ 策略計算失敗")
                return None
            
            # 步驟4: 結果顯示
            display_results = self._display_results(calculation_results)
            
            logger.info("簡化資料流程管道執行完成")
            return display_results
            
        except Exception as e:
            logger.error(f"資料流程管道執行失敗: {str(e)}")
            st.error(f"❌ 系統錯誤: {str(e)}")
            return None
    
    def _validate_user_input(self, parameters: Dict[str, Any]) -> bool:
        """
        基本用戶輸入驗證
        
        Args:
            parameters: 用戶參數
        
        Returns:
            bool: 驗證結果
        """
        try:
            logger.info("執行用戶輸入驗證")
            
            required_fields = [
                'initial_investment', 'annual_investment', 'investment_years',
                'stock_ratio', 'annual_growth_rate', 'annual_inflation_rate'
            ]
            
            # 檢查必要欄位
            for field in required_fields:
                if field not in parameters:
                    st.error(f"❌ 缺少必要參數: {field}")
                    return False
            
            # 檢查數值範圍
            if parameters['initial_investment'] <= 0:
                st.error("❌ 初始投資金額必須大於0")
                return False
            
            if parameters['annual_investment'] <= 0:
                st.error("❌ 年度投資金額必須大於0")
                return False
            
            if not (1 <= parameters['investment_years'] <= 50):
                st.error("❌ 投資年數必須在1-50年之間")
                return False
            
            if not (0 <= parameters['stock_ratio'] <= 100):
                st.error("❌ 股票比例必須在0-100%之間")
                return False
            
            logger.info("用戶輸入驗證通過")
            return True
            
        except Exception as e:
            logger.error(f"用戶輸入驗證失敗: {str(e)}")
            return False
    
    def _fetch_market_data(self) -> Optional[Dict[str, Any]]:
        """
        獲取市場數據（使用錯誤恢復機制）
        
        Returns:
            Optional[Dict[str, Any]]: 市場數據
        """
        try:
            logger.info("開始獲取市場數據")
            
            if self.config.streamlit_progress_enabled:
                with st.spinner("🔄 正在獲取市場數據..."):
                    market_data = basic_error_recovery()
            else:
                market_data = basic_error_recovery()
            
            if market_data:
                logger.info("市場數據獲取成功")
                return market_data
            else:
                logger.warning("市場數據獲取失敗")
                return None
                
        except Exception as e:
            logger.error(f"市場數據獲取異常: {str(e)}")
            return None
    
    def _calculate_strategies(self, parameters: Dict[str, Any], market_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        計算投資策略（整合第2章計算引擎）
        
        Args:
            parameters: 用戶參數
            market_data: 市場數據
        
        Returns:
            Optional[Dict[str, Any]]: 計算結果
        """
        try:
            logger.info("開始策略計算")
            
            # 轉換市場數據格式（支援起始日期參數）
            market_df = self._convert_market_data_to_dataframe(market_data, parameters)
            
            if self.config.streamlit_progress_enabled:
                with st.spinner("📊 正在計算投資策略..."):
                    # 計算VA策略
                    va_results = calculate_va_strategy(
                        C0=parameters['initial_investment'],
                        annual_investment=parameters['annual_investment'],
                        annual_growth_rate=parameters['annual_growth_rate'],
                        annual_inflation_rate=parameters['annual_inflation_rate'],
                        investment_years=parameters['investment_years'],
                        frequency=parameters.get('frequency', 'Monthly'),
                        stock_ratio=parameters['stock_ratio'],
                        strategy_type="Rebalance",
                        market_data=market_df
                    )
                    
                    # 計算DCA策略
                    dca_results = calculate_dca_strategy(
                        C0=parameters['initial_investment'],
                        annual_investment=parameters['annual_investment'],
                        annual_growth_rate=parameters['annual_growth_rate'],
                        annual_inflation_rate=parameters['annual_inflation_rate'],
                        investment_years=parameters['investment_years'],
                        frequency=parameters.get('frequency', 'Monthly'),
                        stock_ratio=parameters['stock_ratio'],
                        market_data=market_df
                    )
                    
                    # 計算綜合指標
                    summary_metrics = calculate_summary_metrics(
                        va_rebalance_df=va_results,
                        va_nosell_df=None,
                        dca_df=dca_results,
                        initial_investment=parameters['initial_investment'],
                        periods_per_year=12
                    )
            else:
                # 無進度提示的計算
                va_results = calculate_va_strategy(
                    C0=parameters['initial_investment'],
                    annual_investment=parameters['annual_investment'],
                    annual_growth_rate=parameters['annual_growth_rate'],
                    annual_inflation_rate=parameters['annual_inflation_rate'],
                    investment_years=parameters['investment_years'],
                    frequency=parameters.get('frequency', 'Monthly'),
                    stock_ratio=parameters['stock_ratio'],
                    strategy_type="Rebalance",
                    market_data=market_df
                )
                
                dca_results = calculate_dca_strategy(
                    C0=parameters['initial_investment'],
                    annual_investment=parameters['annual_investment'],
                    annual_growth_rate=parameters['annual_growth_rate'],
                    annual_inflation_rate=parameters['annual_inflation_rate'],
                    investment_years=parameters['investment_years'],
                    frequency=parameters.get('frequency', 'Monthly'),
                    stock_ratio=parameters['stock_ratio'],
                    market_data=market_df
                )
                
                summary_metrics = calculate_summary_metrics(
                    va_rebalance_df=va_results,
                    va_nosell_df=None,
                    dca_df=dca_results,
                    initial_investment=parameters['initial_investment'],
                    periods_per_year=12
                )
            
            calculation_results = {
                'va_results': va_results,
                'dca_results': dca_results,
                'summary_metrics': summary_metrics,
                'market_data': market_data,
                'parameters': parameters
            }
            
            logger.info("策略計算完成")
            return calculation_results
            
        except Exception as e:
            logger.error(f"策略計算失敗: {str(e)}")
            return None
    
    def _convert_market_data_to_dataframe(self, market_data: Dict[str, Any], parameters: Dict[str, Any] = None) -> pd.DataFrame:
        """
        轉換市場數據為DataFrame格式（支援起始日期參數）
        
        Args:
            market_data: 原始市場數據
            parameters: 用戶參數（包含起始日期）
        
        Returns:
            pd.DataFrame: 轉換後的市場數據
        """
        try:
            stock_data = market_data['stock_data']
            bond_data = market_data['bond_data']
            
            # 生成時間軸（如果提供了參數）
            if parameters:
                from src.utils.trading_days import generate_simulation_timeline
                from datetime import datetime as dt
                
                # 獲取起始日期參數
                user_start_date = parameters.get("investment_start_date")
                if user_start_date:
                    # 將date對象轉換為datetime對象
                    if hasattr(user_start_date, 'date'):
                        start_datetime = dt.combine(user_start_date, dt.min.time())
                    else:
                        start_datetime = dt.combine(user_start_date, dt.min.time())
                else:
                    start_datetime = None
                
                # 生成時間軸
                timeline = generate_simulation_timeline(
                    investment_years=parameters["investment_years"],
                    frequency=parameters["investment_frequency"],
                    user_start_date=start_datetime
                )
                
                # 使用時間軸中的日期
                dates = [period_info['adjusted_start_date'] for period_info in timeline]
            else:
                # 創建基本的市場數據DataFrame
                dates = pd.to_datetime(stock_data[0]['date'] if isinstance(stock_data, list) else stock_data['dates'])
            
            if isinstance(stock_data, list):
                # 列表格式
                stock_prices = [item['adjClose'] for item in stock_data]
                bond_yields = [float(item['value']) for item in bond_data]
            else:
                # 字典格式
                stock_prices = stock_data['prices']
                bond_yields = bond_data['prices']
            
            # 創建DataFrame
            market_df = pd.DataFrame({
                'Date': dates,
                'SPY_Price_Origin': stock_prices,
                'SPY_Price_End': stock_prices,
                'Bond_Price_Origin': [100 - y for y in bond_yields],  # 簡化債券價格計算
                'Bond_Price_End': [100 - y for y in bond_yields]
            })
            
            return market_df
            
        except Exception as e:
            logger.error(f"市場數據轉換失敗: {str(e)}")
            # 返回預設數據
            return self._create_default_market_data()
    
    def _create_default_market_data(self) -> pd.DataFrame:
        """
        創建預設市場數據
        
        Returns:
            pd.DataFrame: 預設市場數據
        """
        dates = pd.date_range(start='2023-01-01', end='2023-12-31', freq='ME')
        
        # 生成簡單的模擬價格
        stock_prices = 400 + np.random.normal(0, 20, len(dates))
        bond_prices = 98 + np.random.normal(0, 2, len(dates))
        
        return pd.DataFrame({
            'Date': dates,
            'SPY_Price_Origin': stock_prices,
            'SPY_Price_End': stock_prices,
            'Bond_Price_Origin': bond_prices,
            'Bond_Price_End': bond_prices
        })
    
    def _display_results(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """
        顯示計算結果（整合第3章UI組件）
        
        Args:
            results: 計算結果
        
        Returns:
            Dict[str, Any]: 顯示結果
        """
        try:
            logger.info("開始顯示結果")
            
            if self.config.streamlit_progress_enabled:
                with st.spinner("📈 正在準備結果顯示..."):
                    display_data = self._prepare_display_data(results)
            else:
                display_data = self._prepare_display_data(results)
            
            # 顯示基本指標
            self._display_basic_metrics(results)
            
            # 顯示圖表
            self._display_charts(results)
            
            # 顯示詳細表格
            self._display_detailed_tables(results)
            
            logger.info("結果顯示完成")
            return display_data
            
        except Exception as e:
            logger.error(f"結果顯示失敗: {str(e)}")
            st.error(f"❌ 結果顯示錯誤: {str(e)}")
            return {}
    
    def _prepare_display_data(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """準備顯示數據"""
        va_final = results['va_results']['Cum_Value'].iloc[-1]
        dca_final = results['dca_results']['Cum_Value'].iloc[-1]
        
        return {
            'va_final_value': va_final,
            'dca_final_value': dca_final,
            'difference': va_final - dca_final,
            'difference_percentage': (va_final - dca_final) / dca_final * 100,
            'summary_metrics': results['summary_metrics']
        }
    
    def _display_basic_metrics(self, results: Dict[str, Any]):
        """顯示基本指標"""
        st.subheader("📊 投資策略比較結果")
        
        va_final = results['va_results']['Cum_Value'].iloc[-1]
        dca_final = results['dca_results']['Cum_Value'].iloc[-1]
        difference = va_final - dca_final
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("VA策略最終價值", f"${va_final:,.0f}")
        
        with col2:
            st.metric("DCA策略最終價值", f"${dca_final:,.0f}")
        
        with col3:
            st.metric("VA vs DCA差異", f"${difference:,.0f}", 
                     delta=f"{difference/dca_final*100:.1f}%")
    
    def _display_charts(self, results: Dict[str, Any]):
        """顯示圖表"""
        st.subheader("📈 投資成長趨勢")
        
        # 準備圖表數據
        chart_data = pd.DataFrame({
            'VA策略': results['va_results']['Cum_Value'],
            'DCA策略': results['dca_results']['Cum_Value']
        })
        
        st.line_chart(chart_data)
    
    def _display_detailed_tables(self, results: Dict[str, Any]):
        """顯示詳細表格"""
        st.subheader("📋 詳細計算結果")
        
        tab1, tab2, tab3 = st.tabs(["VA策略", "DCA策略", "綜合指標"])
        
        with tab1:
            st.dataframe(results['va_results'].head(10))
        
        with tab2:
            st.dataframe(results['dca_results'].head(10))
        
        with tab3:
            if results['summary_metrics'] is not None:
                st.dataframe(results['summary_metrics'])

# ============================================================================
# 便利函數
# ============================================================================

def create_simple_data_flow_pipeline(config: Optional[DataFlowConfig] = None) -> SimpleDataFlowPipeline:
    """
    創建簡化資料流程管道
    
    Args:
        config: 資料流程配置
    
    Returns:
        SimpleDataFlowPipeline: 資料流程管道實例
    """
    return SimpleDataFlowPipeline(config)

def validate_basic_parameters(parameters: Dict[str, Any]) -> bool:
    """
    基本參數驗證
    
    Args:
        parameters: 用戶參數
    
    Returns:
        bool: 驗證結果
    """
    pipeline = SimpleDataFlowPipeline()
    return pipeline._validate_user_input(parameters)

def get_market_data_simple(parameters: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    簡化的市場數據獲取
    
    Args:
        parameters: 用戶參數
    
    Returns:
        Optional[Dict[str, Any]]: 市場數據
    """
    pipeline = SimpleDataFlowPipeline()
    return pipeline._fetch_market_data() 