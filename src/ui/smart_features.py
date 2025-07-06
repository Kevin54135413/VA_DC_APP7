"""
智能功能與用戶體驗模組 - 實作第3章3.4節規格
嚴格保持第1章技術規範的完整性
"""

import streamlit as st
import pandas as pd
import numpy as np
import time
import logging
from typing import Dict, Any, Optional, Union, List, Tuple
from datetime import datetime
import os
import sys

# 添加src目錄到Python路徑
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# 導入第1章技術規範模組
from ..utils.api_security import get_api_key, validate_api_key_format
from ..data_sources.api_client import test_api_connectivity
from ..data_sources.fault_tolerance import APIFaultToleranceManager, DataQualityValidator
from ..data_sources.simulation import SimulationDataGenerator
from ..data_sources.cache_manager import IntelligentCacheManager, cached_data
from ..data_sources.data_fetcher import TiingoDataFetcher, FREDDataFetcher, BatchDataFetcher

# 導入第2章計算模組
from ..models.calculation_formulas import (
    convert_annual_to_period_parameters,
    calculate_va_target_value, execute_va_strategy,
    calculate_dca_investment, calculate_dca_cumulative_investment, execute_dca_strategy,
    calculate_annualized_return, calculate_volatility_and_sharpe
)
from ..models.strategy_engine import calculate_va_strategy, calculate_dca_strategy
from ..models.table_calculator import calculate_summary_metrics

# 設置日誌
logger = logging.getLogger(__name__)

# ============================================================================
# 3.4.1 智能數據源管理實作
# ============================================================================

class APIConnectionError(Exception):
    """API連接錯誤"""
    pass

@st.cache_data(ttl=3600)
def smart_data_source_manager() -> Dict[str, Any]:
    """
    智能數據源管理器 - 嚴格保持第1章技術規範
    
    Returns:
        Dict: 包含數據源狀態和數據的字典
    """
    logger.info("開始智能數據源管理")
    
    try:
        # 嘗試獲取真實市場數據
        market_data = get_real_market_data_with_security()
        if market_data is not None:
            st.session_state.data_source_status = "real_data"
            return {
                "status": "real_data",
                "data": market_data,
                "message": "🟢 使用真實市場數據"
            }
    except APIConnectionError as e:
        logger.warning(f"API連接失敗，切換到模擬數據: {e}")
        # 自動切換到模擬數據
        simulation_data = get_simulation_data_chapter1_compliant()
        st.session_state.data_source_status = "simulation"
        st.info("💡 正在使用模擬數據進行分析")
        return {
            "status": "simulation", 
            "data": simulation_data,
            "message": "🟡 使用模擬數據"
        }
    except Exception as e:
        logger.error(f"數據獲取失敗，使用離線模式: {e}")
        # 切換為離線模式
        cached_data = get_cached_data_or_default()
        st.session_state.data_source_status = "offline"
        st.warning("🌐 網路連線問題，已切換為離線模式")
        return {
            "status": "offline",
            "data": cached_data,
            "message": "🔴 離線模式"
        }

def get_real_market_data_with_security() -> Optional[pd.DataFrame]:
    """
    使用第1章API安全機制獲取真實市場數據
    
    Returns:
        pd.DataFrame: 市場數據或None
    
    Raises:
        APIConnectionError: 當API連接失敗時
    """
    # 獲取API金鑰 - 使用第1章多層級策略
    tiingo_key = get_api_key('TIINGO_API_KEY')
    fred_key = get_api_key('FRED_API_KEY')
    
    if not tiingo_key or not fred_key:
        raise APIConnectionError("API金鑰未設定")
    
    # 驗證API金鑰格式
    if not validate_api_key_format('TIINGO_API_KEY', tiingo_key):
        raise APIConnectionError("Tiingo API金鑰格式無效")
    
    if not validate_api_key_format('FRED_API_KEY', fred_key):
        raise APIConnectionError("FRED API金鑰格式無效")
    
    # 測試API連通性
    tiingo_connected = test_api_connectivity('tiingo', tiingo_key)
    fred_connected = test_api_connectivity('fred', fred_key)
    
    if not (tiingo_connected and fred_connected):
        raise APIConnectionError("API連通性測試失敗")
    
    # 使用第1章數據獲取器
    try:
        tiingo_fetcher = TiingoDataFetcher(tiingo_key)
        fred_fetcher = FREDDataFetcher(fred_key)
        batch_fetcher = BatchDataFetcher(tiingo_fetcher, fred_fetcher)
        
        # 獲取市場數據
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - pd.DateOffset(years=10)).strftime('%Y-%m-%d')
        
        market_data = batch_fetcher.fetch_combined_data(start_date, end_date)
        
        # 使用第1章數據品質驗證器
        validator = DataQualityValidator()
        validation_result = validator.validate_market_data(market_data)
        
        if not validation_result.is_valid:
            raise APIConnectionError(f"數據品質驗證失敗: {validation_result.error_message}")
        
        logger.info("成功獲取並驗證真實市場數據")
        return market_data
        
    except Exception as e:
        logger.error(f"真實數據獲取失敗: {e}")
        raise APIConnectionError(f"數據獲取失敗: {e}")

def get_simulation_data_chapter1_compliant() -> pd.DataFrame:
    """
    使用第1章模擬數據生成器獲取數據
    
    Returns:
        pd.DataFrame: 模擬市場數據
    """
    # 使用第1章模擬數據生成器
    simulator = SimulationDataGenerator()
    
    # 生成10年模擬數據
    end_date = datetime.now()
    start_date = end_date - pd.DateOffset(years=10)
    
    simulation_config = {
        "start_date": start_date,
        "end_date": end_date,
        "frequency": "daily",
        "market_regime": "normal",
        "volatility_level": "medium"
    }
    
    market_data = simulator.generate_market_scenario(simulation_config)
    
    logger.info("成功生成第1章規範的模擬數據")
    return market_data

@cached_data(ttl=86400)  # 使用第1章快取機制
def get_cached_data_or_default() -> pd.DataFrame:
    """
    使用第1章快取機制獲取數據或預設數據
    
    Returns:
        pd.DataFrame: 快取數據或預設數據
    """
    cache_manager = IntelligentCacheManager()
    
    # 嘗試從快取獲取數據
    cached_market_data = cache_manager.get_cached_data("market_data")
    
    if cached_market_data is not None:
        logger.info("使用快取的市場數據")
        return cached_market_data
    
    # 生成預設數據
    default_data = _generate_default_market_data()
    
    # 存入快取
    cache_manager.cache_data("market_data", default_data)
    
    logger.info("使用預設市場數據")
    return default_data

def _generate_default_market_data() -> pd.DataFrame:
    """生成預設市場數據"""
    dates = pd.date_range(start='2014-01-01', end='2024-01-01', freq='D')
    
    # 生成基本的股票和債券數據
    np.random.seed(42)  # 確保可重現性
    
    spy_prices = 200 * np.exp(np.cumsum(np.random.normal(0.0003, 0.015, len(dates))))
    bond_yields = 2.0 + np.random.normal(0, 0.1, len(dates))
    bond_yields = np.clip(bond_yields, 0.5, 5.0)  # 限制在合理範圍
    
    return pd.DataFrame({
        'Date': dates,
        'SPY_Price': spy_prices,
        'Bond_Yield': bond_yields,
        'Bond_Price': 100 / (1 + bond_yields/100)  # 簡化債券價格計算
    })

# ============================================================================
# 異常處理機制
# ============================================================================

def user_friendly_error_handler(error_type: str, error_message: str, 
                               debug_mode: bool = False) -> None:
    """
    用戶友善錯誤處理器
    
    Args:
        error_type: 錯誤類型
        error_message: 錯誤訊息
        debug_mode: 是否為開發者模式
    """
    error_messages = {
        "api_error": {
            "title": "🔌 API連接問題",
            "message": "無法連接到數據服務，已自動切換到模擬數據模式",
            "suggestion": "請檢查網路連接或稍後再試"
        },
        "calculation_error": {
            "title": "🧮 計算錯誤",
            "message": "投資策略計算過程中發生錯誤",
            "suggestion": "請檢查輸入參數是否正確"
        },
        "data_error": {
            "title": "📊 數據問題",
            "message": "市場數據處理過程中發生錯誤",
            "suggestion": "正在嘗試使用備用數據源"
        },
        "validation_error": {
            "title": "✅ 參數驗證錯誤",
            "message": "輸入的參數不符合要求",
            "suggestion": "請調整參數設定後重試"
        }
    }
    
    if error_type in error_messages:
        error_info = error_messages[error_type]
        
        st.error(f"""
        **{error_info['title']}**
        
        {error_info['message']}
        
        💡 **建議**: {error_info['suggestion']}
        """)
        
        if debug_mode:
            with st.expander("🔧 開發者詳情"):
                st.code(f"錯誤類型: {error_type}\n錯誤訊息: {error_message}")
    else:
        st.error(f"未知錯誤: {error_message}")

# ============================================================================
# 3.4.2 漸進式載入與反饋實作
# ============================================================================

def progressive_calculation_with_feedback(parameters: Dict[str, Any]) -> Dict[str, Any]:
    """
    漸進式計算與反饋系統
    
    Args:
        parameters: 投資參數字典
    
    Returns:
        Dict: 計算結果
    """
    # 創建進度條和狀態文字
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        # 階段1：準備市場數據
        status_text.text("📊 準備市場數據...")
        progress_bar.progress(25)
        time.sleep(0.5)  # 模擬處理時間
        
        market_data = prepare_market_data()
        
        # 階段2：計算定期定值策略
        status_text.text("🎯 計算定期定值策略...")
        progress_bar.progress(50)
        time.sleep(0.5)
        
        va_results = calculate_va_strategy_with_chapter2(parameters, market_data)
        
        # 階段3：計算定期定額策略
        status_text.text("💰 計算定期定額策略...")
        progress_bar.progress(75)
        time.sleep(0.5)
        
        dca_results = calculate_dca_strategy_with_chapter2(parameters, market_data)
        
        # 階段4：生成績效比較
        status_text.text("📈 生成績效比較...")
        progress_bar.progress(100)
        time.sleep(0.5)
        
        comparison_analysis = generate_comparison_analysis(va_results, dca_results, parameters)
        
        # 完成
        status_text.text("✅ 計算完成！")
        time.sleep(1)
        
        # 清除進度顯示
        progress_bar.empty()
        status_text.empty()
        
        return {
            "va_results": va_results,
            "dca_results": dca_results,
            "comparison_analysis": comparison_analysis,
            "market_data": market_data
        }
        
    except Exception as e:
        progress_bar.empty()
        status_text.empty()
        logger.error(f"漸進式計算失敗: {e}")
        user_friendly_error_handler("calculation_error", str(e))
        return {}

def prepare_market_data() -> pd.DataFrame:
    """
    準備市場數據 - 調用第1章數據獲取機制
    
    Returns:
        pd.DataFrame: 市場數據
    """
    data_source_result = smart_data_source_manager()
    return data_source_result["data"]

def calculate_va_strategy_with_chapter2(parameters: Dict[str, Any], 
                                       market_data: pd.DataFrame) -> pd.DataFrame:
    """
    使用第2章VA計算公式計算策略
    
    Args:
        parameters: 投資參數
        market_data: 市場數據
    
    Returns:
        pd.DataFrame: VA策略結果
    """
    return calculate_va_strategy(
        C0=parameters.get("initial_investment", 10000),
        annual_investment=parameters.get("annual_investment", 120000),
        annual_growth_rate=parameters.get("annual_growth_rate", 8.0),
        annual_inflation_rate=parameters.get("annual_inflation_rate", 3.0),
        investment_years=parameters.get("investment_years", 10),
        frequency=parameters.get("frequency", "Quarterly"),
        stock_ratio=parameters.get("stock_ratio", 80),
        strategy_type=parameters.get("strategy_type", "Rebalance"),
        market_data=market_data
    )

def calculate_dca_strategy_with_chapter2(parameters: Dict[str, Any], 
                                        market_data: pd.DataFrame) -> pd.DataFrame:
    """
    使用第2章DCA計算公式計算策略
    
    Args:
        parameters: 投資參數
        market_data: 市場數據
    
    Returns:
        pd.DataFrame: DCA策略結果
    """
    return calculate_dca_strategy(
        C0=parameters.get("initial_investment", 10000),
        annual_investment=parameters.get("annual_investment", 120000),
        annual_growth_rate=parameters.get("annual_growth_rate", 8.0),
        annual_inflation_rate=parameters.get("annual_inflation_rate", 3.0),
        investment_years=parameters.get("investment_years", 10),
        frequency=parameters.get("frequency", "Quarterly"),
        stock_ratio=parameters.get("stock_ratio", 80),
        market_data=market_data
    )

def generate_comparison_analysis(va_results: pd.DataFrame, dca_results: pd.DataFrame,
                               parameters: Dict[str, Any]) -> Dict[str, Any]:
    """
    使用第2章績效指標生成比較分析
    
    Args:
        va_results: VA策略結果
        dca_results: DCA策略結果
        parameters: 投資參數
    
    Returns:
        Dict: 比較分析結果
    """
    # 使用第2章計算摘要指標
    frequency_map = {"Monthly": 12, "Quarterly": 4, "Semi-annually": 2, "Annually": 1}
    periods_per_year = frequency_map.get(parameters.get("frequency", "Quarterly"), 4)
    
    summary_df = calculate_summary_metrics(
        va_rebalance_df=va_results,
        dca_df=dca_results,
        initial_investment=parameters.get("initial_investment", 10000),
        periods_per_year=periods_per_year,
        risk_free_rate=2.0
    )
    
    return {
        "summary_df": summary_df,
        "va_final_value": va_results["Cum_Value"].iloc[-1] if len(va_results) > 0 else 0,
        "dca_final_value": dca_results["Cum_Value"].iloc[-1] if len(dca_results) > 0 else 0,
        "va_annualized_return": va_results["Annualized_Return"].iloc[-1] if len(va_results) > 0 else 0,
        "dca_annualized_return": dca_results["Annualized_Return"].iloc[-1] if len(dca_results) > 0 else 0
    }

# ============================================================================
# 3.4.3 智能建議系統整合實作
# ============================================================================

SMART_RECOMMENDATIONS = {
    "personalized_advice": {
        "recommendation_engine": {
            "factors": [
                "investment_amount",
                "time_horizon", 
                "risk_tolerance",
                "strategy_performance"
            ],
            "calculation_basis": "comparison_metrics"
        },
        "templates": {
            "va_preferred": {
                "title": "🎯 建議採用VA策略",
                "reason": "基於您的參數，VA策略預期表現較佳",
                "key_points": [
                    "較高預期報酬",
                    "適合您的風險承受度",
                    "投資金額充足"
                ],
                "calculation_basis": "第2章comparison_metrics"
            },
            "dca_preferred": {
                "title": "💰 建議採用DCA策略", 
                "reason": "DCA策略更適合您的投資目標",
                "key_points": [
                    "操作簡單",
                    "風險相對較低",
                    "適合長期投資"
                ],
                "calculation_basis": "第2章comparison_metrics"
            },
            "neutral_analysis": {
                "title": "📊 兩種策略各有優勢",
                "reason": "根據分析，兩種策略表現相近",
                "key_points": [
                    "績效差異較小",
                    "可依個人偏好選擇",
                    "建議考慮操作便利性"
                ],
                "calculation_basis": "第2章comparison_metrics"
            }
        }
    },
    "investment_knowledge": {
        "strategy_explanation_cards": {
            "what_is_va": {
                "title": "💡 什麼是定期定值(VA)？",
                "content": "定期定值策略會根據市場表現調整投入金額，當市場下跌時增加投入，市場上漲時減少投入，追求平穩的資產成長軌跡。",
                "expandable": True,
                "beginner_friendly": True
            },
            "what_is_dca": {
                "title": "💡 什麼是定期定額(DCA)？",
                "content": "定期定額策略每期投入固定金額，不論市場漲跌都持續投入，透過時間分散投資成本，適合長期投資。",
                "expandable": True,
                "beginner_friendly": True
            }
        },
        "risk_warnings": {
            "importance": "high",
            "content": "投資有風險，過去績效不代表未來結果。請根據自身風險承受能力謹慎投資。",
            "always_visible": True
        },
        "help_section": {
            "quick_start_guide": {
                "title": "🚀 快速開始",
                "steps": [
                    "設定投資參數",
                    "選擇策略類型", 
                    "查看分析結果",
                    "參考智能建議"
                ]
            },
            "faq": {
                "title": "❓ 常見問題",
                "questions": [
                    {
                        "q": "哪種策略比較好？",
                        "a": "沒有絕對的好壞，需要根據個人情況選擇。"
                    },
                    {
                        "q": "如何選擇投資期間？",
                        "a": "建議至少3-5年以上，長期投資能降低波動影響。"
                    }
                ]
            },
            "contact": {
                "title": "📞 聯絡支援",
                "options": [
                    "線上客服",
                    "電子郵件",
                    "電話諮詢"
                ]
            }
        }
    }
}

class SmartRecommendationEngine:
    """智能建議引擎 - 整合第2章計算結果"""
    
    def __init__(self):
        self.recommendations_config = SMART_RECOMMENDATIONS
        
    def generate_personalized_advice(self, parameters: Dict[str, Any], 
                                   calculation_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        生成個人化建議
        
        Args:
            parameters: 投資參數
            calculation_results: 第2章計算結果
        
        Returns:
            Dict: 個人化建議
        """
        # 分析用戶檔案
        user_profile = self._analyze_user_profile(parameters)
        
        # 分析策略表現
        strategy_performance = self._analyze_strategy_performance(calculation_results)
        
        # 生成建議
        recommendation = self._generate_recommendation(user_profile, strategy_performance)
        
        return recommendation
    
    def _analyze_user_profile(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """分析用戶檔案"""
        investment_amount = parameters.get("initial_investment", 10000)
        time_horizon = parameters.get("investment_years", 10)
        stock_ratio = parameters.get("stock_ratio", 80)
        
        # 風險承受度評估
        if stock_ratio >= 80 and time_horizon >= 10 and investment_amount >= 500000:
            risk_tolerance = "high"
        elif stock_ratio >= 60 and time_horizon >= 5:
            risk_tolerance = "moderate"
        else:
            risk_tolerance = "conservative"
        
        return {
            "investment_amount": investment_amount,
            "time_horizon": time_horizon,
            "risk_tolerance": risk_tolerance,
            "stock_ratio": stock_ratio
        }
    
    def _analyze_strategy_performance(self, calculation_results: Dict[str, Any]) -> Dict[str, Any]:
        """分析策略表現"""
        if "summary_df" not in calculation_results:
            return {"performance_difference": 0, "better_strategy": "neutral"}
        
        summary_df = calculation_results["summary_df"]
        
        if len(summary_df) >= 2:
            va_row = summary_df[summary_df["Strategy"] == "VA_Rebalance"]
            dca_row = summary_df[summary_df["Strategy"] == "DCA"]
            
            if len(va_row) > 0 and len(dca_row) > 0:
                va_return = va_row["Annualized_Return"].iloc[0]
                dca_return = dca_row["Annualized_Return"].iloc[0]
                
                performance_diff = abs(va_return - dca_return)
                better_strategy = "VA" if va_return > dca_return else "DCA"
                
                return {
                    "performance_difference": performance_diff,
                    "better_strategy": better_strategy,
                    "va_return": va_return,
                    "dca_return": dca_return
                }
        
        return {"performance_difference": 0, "better_strategy": "neutral"}
    
    def _generate_recommendation(self, user_profile: Dict[str, Any], 
                               strategy_performance: Dict[str, Any]) -> Dict[str, Any]:
        """生成建議"""
        performance_diff = strategy_performance.get("performance_difference", 0)
        better_strategy = strategy_performance.get("better_strategy", "neutral")
        
        templates = self.recommendations_config["personalized_advice"]["templates"]
        
        if performance_diff < 2.0:  # 績效差異小於2%
            return templates["neutral_analysis"]
        elif better_strategy == "VA":
            return templates["va_preferred"]
        else:
            return templates["dca_preferred"]
    
    def render_investment_knowledge(self):
        """渲染投資知識卡片"""
        knowledge = self.recommendations_config["investment_knowledge"]
        
        # 策略解釋卡片
        cards = knowledge["strategy_explanation_cards"]
        
        with st.expander(cards["what_is_va"]["title"]):
            st.write(cards["what_is_va"]["content"])
        
        with st.expander(cards["what_is_dca"]["title"]):
            st.write(cards["what_is_dca"]["content"])
        
        # 風險警告
        risk_warning = knowledge["risk_warnings"]
        st.warning(f"""
        **⚠️ 投資風險說明**
        
        {risk_warning['content']}
        """)
        
        # 幫助區域
        help_section = knowledge["help_section"]
        
        st.subheader("🙋‍♀️ 需要幫助？")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🚀 快速開始"):
                self._show_quick_start_guide(help_section["quick_start_guide"])
        
        with col2:
            if st.button("❓ 常見問題"):
                self._show_faq(help_section["faq"])
        
        with col3:
            if st.button("📞 聯絡支援"):
                self._show_contact_info(help_section["contact"])
    
    def _show_quick_start_guide(self, guide_config: Dict[str, Any]):
        """顯示快速開始指南"""
        with st.expander("🚀 快速開始指南", expanded=True):
            st.markdown("### 📋 操作步驟")
            for i, step in enumerate(guide_config["steps"], 1):
                st.markdown(f"**步驟{i}**: {step}")
    
    def _show_faq(self, faq_config: Dict[str, Any]):
        """顯示常見問題"""
        with st.expander("❓ 常見問題", expanded=True):
            for item in faq_config["questions"]:
                st.markdown(f"**Q: {item['q']}**")
                st.markdown(f"A: {item['a']}")
                st.markdown("---")
    
    def _show_contact_info(self, contact_config: Dict[str, Any]):
        """顯示聯絡資訊"""
        with st.expander("📞 聯絡支援", expanded=True):
            st.markdown("### 📞 聯絡方式")
            for option in contact_config["options"]:
                st.markdown(f"- {option}")

# ============================================================================
# 整合函數
# ============================================================================

def render_smart_features(parameters: Dict[str, Any]) -> Dict[str, Any]:
    """
    渲染完整智能功能
    
    Args:
        parameters: 投資參數
    
    Returns:
        Dict: 計算結果和建議
    """
    # 漸進式計算
    calculation_results = progressive_calculation_with_feedback(parameters)
    
    if calculation_results:
        # 生成智能建議
        recommendation_engine = SmartRecommendationEngine()
        personalized_advice = recommendation_engine.generate_personalized_advice(
            parameters, calculation_results
        )
        
        # 顯示建議
        st.success(f"""
        **{personalized_advice['title']}**
        
        {personalized_advice['reason']}
        
        **主要優勢：**
        """)
        
        for point in personalized_advice['key_points']:
            st.markdown(f"- {point}")
        
        # 渲染投資知識
        recommendation_engine.render_investment_knowledge()
        
        return {
            "calculation_results": calculation_results,
            "personalized_advice": personalized_advice
        }
    
    return {}