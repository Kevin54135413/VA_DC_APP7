"""
智能建議區域 - 實作第3章3.4節規格
嚴格保持所有智能功能和教育內容
"""

import streamlit as st
import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, Union, List, Tuple
import os
import sys
from datetime import datetime

# 添加src目錄到Python路徑
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# 導入第2章計算模組
from models.calculation_formulas import calculate_annualized_return
from models.table_calculator import calculate_summary_metrics

# ============================================================================
# 智能建議與教育內容配置
# ============================================================================

SMART_RECOMMENDATIONS = {
    "recommendation_templates": {
        "va_recommended": {
            "title": "🎯 建議您使用定期定值策略",
            "style": "success_card",
            "content_template": "根據您的投資配置，定期定值策略預計可以為您帶來額外 ${amount_difference:,.0f} 的收益。在 {investment_period} 年的投資期間，這種策略能夠自動調節市場波動。",
            "reasoning": [
                "在您的投資期間內表現較佳",
                "能夠自動平衡市場波動",
                "適合您的風險承受度"
            ]
        },
        "dca_recommended": {
            "title": "💰 建議您使用定期定額策略",
            "style": "success_card",
            "content_template": "定期定額策略簡單易執行，預計最終價值為 ${final_value:,.0f}，年化報酬率為 {annualized_return:.2f}%。這種策略特別適合忙碌的投資者。",
            "reasoning": [
                "操作簡單，適合忙碌生活",
                "減少情緒影響的投資決策",
                "長期持續的投資紀律"
            ]
        },
        "neutral_analysis": {
            "title": "📊 兩種策略表現相近",
            "style": "info_card",
            "content_template": "經過分析，兩種策略的表現差異不大。定期定值的優勢：{va_advantage}；定期定額的優勢：{dca_advantage}。建議根據個人偏好選擇。",
            "reasoning": [
                "表現差異小於5%",
                "各有不同優勢",
                "依個人情況選擇"
            ]
        }
    },
    "risk_assessment": {
        "high_risk": {
            "threshold": 0.7,
            "recommendations": ["考慮降低股票比例", "增加投資分散度"],
            "warning_message": "您的投資組合風險較高，請謹慎評估"
        },
        "moderate_risk": {
            "threshold": 0.5,
            "recommendations": ["維持目前配置", "定期檢視調整"],
            "warning_message": "您的投資組合風險適中"
        },
        "low_risk": {
            "threshold": 0.3,
            "recommendations": ["可考慮增加股票比例", "提高報酬潛力"],
            "warning_message": "您的投資組合較為保守"
        }
    }
}

EDUCATIONAL_CONTENT = {
    "knowledge_cards": {
        "what_is_va": {
            "title": "💡 什麼是定期定值？",
            "content": "就像設定目標存款，不夠就多存，超過就少存。當市場下跌時自動加碼，上漲時減少投入，追求平穩的成長軌跡。",
            "expandable": True,
            "beginner_friendly": True,
            "icon": "🎯",
            "category": "strategy_explanation"
        },
        "what_is_dca": {
            "title": "💡 什麼是定期定額？",
            "content": "每月固定投入相同金額，就像定期定額存款。不管市場漲跌都持續投入，用時間來分散成本。",
            "expandable": True,
            "beginner_friendly": True,
            "icon": "💰",
            "category": "strategy_explanation"
        },
        "risk_explanation": {
            "title": "⚠️ 投資風險說明",
            "content": "所有投資都有風險，過去績效不代表未來表現。請根據自身風險承受能力謹慎投資。",
            "importance": "high",
            "always_visible": True,
            "icon": "⚠️",
            "category": "risk_education"
        },
        "portfolio_balance": {
            "title": "⚖️ 投資組合平衡",
            "content": "適當的股債配置能平衡風險與報酬。年輕投資者可承擔較高風險，年長者宜採保守策略。",
            "expandable": True,
            "beginner_friendly": True,
            "icon": "⚖️",
            "category": "portfolio_education"
        },
        "time_horizon": {
            "title": "⏰ 投資時間重要性",
            "content": "長期投資能有效降低短期波動影響。建議投資期間至少3-5年以上，讓時間成為您的朋友。",
            "expandable": True,
            "beginner_friendly": True,
            "icon": "⏰",
            "category": "time_education"
        },
        "market_volatility": {
            "title": "📈 市場波動管理",
            "content": "市場波動是常態，不要因短期波動而改變長期投資計畫。定期檢視但避免頻繁調整。",
            "expandable": True,
            "beginner_friendly": True,
            "icon": "📈",
            "category": "volatility_education"
        },
        "diversification": {
            "title": "🎯 分散投資重要性",
            "content": "不要把雞蛋放在同一個籃子裡。透過股債配置、地區分散等方式降低整體投資風險。",
            "expandable": True,
            "beginner_friendly": True,
            "icon": "🎯",
            "category": "diversification_education"
        },
        "investment_discipline": {
            "title": "💪 投資紀律",
            "content": "成功投資需要紀律。設定投資計畫後要堅持執行，避免因情緒影響而偏離策略。",
            "expandable": True,
            "beginner_friendly": True,
            "icon": "💪",
            "category": "discipline_education"
        },
        "cost_awareness": {
            "title": "💸 成本意識",
            "content": "投資成本會侵蝕報酬。選擇低費用的投資工具，關注管理費、交易成本等。",
            "expandable": True,
            "beginner_friendly": True,
            "icon": "💸",
            "category": "cost_education"
        },
        "investment_timeline": {
            "title": "⏰ 投資時間的重要性",
            "content": "長期投資能有效降低短期波動的影響。建議投資期間至少3-5年以上。",
            "expandable": True,
            "beginner_friendly": True,
            "icon": "⏰",
            "category": "time_education"
        }
    },
    "help_section": {
        "title": "🙋‍♀️ 需要幫助？",
        "quick_links": [
            {
                "text": "📖 新手指南",
                "action": "show_beginner_guide",
                "icon": "📖",
                "description": "投資基礎知識"
            },
            {
                "text": "❓ 常見問題",
                "action": "show_faq",
                "icon": "❓", 
                "description": "解答疑問"
            }
        ],
        "tutorial_button": {
            "text": "🚀 5分鐘快速上手",
            "style": "primary",
            "action": "start_tutorial",
            "description": "快速了解系統使用方法"
        },
        "additional_resources": {
            "investment_calculator": "投資計算器",
            "strategy_simulator": "策略模擬器",
            "risk_assessment": "風險評估工具"
        }
    }
}

# ============================================================================
# 智能建議區域管理器
# ============================================================================

class SmartRecommendationsManager:
    """智能建議區域管理器 - 實作第3章3.4節所有規格"""
    
    def __init__(self):
        self.recommendations_config = SMART_RECOMMENDATIONS
        self.educational_config = EDUCATIONAL_CONTENT
        self.current_recommendation = None
        self.user_profile = {}
        
    def render_complete_smart_recommendations(self, parameters: Dict[str, Any], calculation_results: Dict[str, Any]):
        """渲染完整智能建議區域"""
        st.header("💡 智能建議")
        
        # 分析用戶參數和計算結果
        self._analyze_user_profile(parameters, calculation_results)
        
        # 渲染個人化建議系統
        self.render_personalized_recommendations()
        
        # 渲染投資知識卡片
        self.render_educational_content()
        
        # 渲染幫助區域
        self.render_help_section()
    
    def _analyze_user_profile(self, parameters: Dict[str, Any], calculation_results: Dict[str, Any]):
        """分析用戶檔案以生成個人化建議"""
        self.user_profile = {
            "investment_amount": parameters.get("initial_investment", 10000),
            "time_horizon": parameters.get("investment_years", 10),
            "risk_tolerance_derived": self._derive_risk_tolerance(parameters),
            "strategy_performance_comparison": self._compare_strategy_performance(calculation_results)
        }
        
        # 生成建議
        self.current_recommendation = self._generate_recommendation()
    
    def _derive_risk_tolerance(self, parameters: Dict[str, Any]) -> str:
        """從參數推導風險承受度"""
        investment_amount = parameters.get("initial_investment", 10000)
        time_horizon = parameters.get("investment_years", 10)
        stock_ratio = parameters.get("stock_ratio", 80)
        
        # 基於投資金額、時間和股票比例推導風險承受度
        if stock_ratio >= 80 and time_horizon >= 10 and investment_amount >= 500000:
            return "high"
        elif stock_ratio >= 60 and time_horizon >= 5:
            return "moderate"
        else:
            return "conservative"
    
    def _compare_strategy_performance(self, calculation_results: Dict[str, Any]) -> Dict[str, Any]:
        """比較策略績效"""
        if not calculation_results or "summary_df" not in calculation_results:
            return {"performance_difference": 0, "better_strategy": "neutral"}
        
        summary_df = calculation_results["summary_df"]
        
        if len(summary_df) >= 2:
            va_row = summary_df[summary_df["Strategy"] == "VA_Rebalance"]
            dca_row = summary_df[summary_df["Strategy"] == "DCA"]
            
            if len(va_row) > 0 and len(dca_row) > 0:
                va_return = va_row["Annualized_Return"].iloc[0]
                dca_return = dca_row["Annualized_Return"].iloc[0]
                va_final = va_row["Final_Value"].iloc[0]
                dca_final = dca_row["Final_Value"].iloc[0]
                
                performance_diff = abs(va_return - dca_return)
                
                return {
                    "performance_difference": performance_diff,
                    "better_strategy": "VA" if va_return > dca_return else "DCA",
                    "va_final_value": va_final,
                    "dca_final_value": dca_final,
                    "va_return": va_return,
                    "dca_return": dca_return,
                    "amount_difference": abs(va_final - dca_final)
                }
        
        return {"performance_difference": 0, "better_strategy": "neutral"}
    
    def _generate_recommendation(self) -> Dict[str, Any]:
        """生成個人化建議"""
        performance = self.user_profile["strategy_performance_comparison"]
        
        # 檢查績效差異是否小於5%（百分點）
        performance_diff = performance.get("performance_difference", 0)
        
        if performance_diff < 5:
            # 績效差異小於5%，使用中性分析
            return self._prepare_neutral_recommendation()
        elif performance.get("better_strategy") == "VA":
            # VA策略表現更好
            return self._prepare_va_recommendation()
        else:
            # DCA策略表現更好
            return self._prepare_dca_recommendation()
    
    def _prepare_va_recommendation(self) -> Dict[str, Any]:
        """準備VA策略推薦"""
        template = self.recommendations_config["recommendation_templates"]["va_recommended"]
        performance = self.user_profile["strategy_performance_comparison"]
        
        return {
            "title": template["title"],
            "style": template["style"],
            "content": template["content_template"].format(
                amount_difference=performance.get("amount_difference", 0),
                investment_period=self.user_profile["time_horizon"]
            ),
            "recommendation_type": "va_recommended"
        }
    
    def _prepare_dca_recommendation(self) -> Dict[str, Any]:
        """準備DCA策略推薦"""
        template = self.recommendations_config["recommendation_templates"]["dca_recommended"]
        performance = self.user_profile["strategy_performance_comparison"]
        
        return {
            "title": template["title"],
            "style": template["style"],
            "content": template["content_template"].format(
                final_value=performance.get("dca_final_value", 0),
                annualized_return=performance.get("dca_return", 0)
            ),
            "recommendation_type": "dca_recommended"
        }
    
    def _prepare_neutral_recommendation(self) -> Dict[str, Any]:
        """準備中性分析"""
        template = self.recommendations_config["recommendation_templates"]["neutral_analysis"]
        
        va_advantage = "可能在市場波動中獲得更好表現"
        dca_advantage = "操作簡單，情緒影響較小"
        
        return {
            "title": template["title"],
            "style": template["style"],
            "content": template["content_template"].format(
                va_advantage=va_advantage,
                dca_advantage=dca_advantage
            ),
            "recommendation_type": "neutral_analysis"
        }
    
    def render_personalized_recommendations(self):
        """渲染個人化建議系統 - 3.4.1節實作"""
        if not self.current_recommendation:
            st.info("請設定投資參數後獲取個人化建議")
            return
        
        recommendation = self.current_recommendation
        
        # 根據建議類型選擇樣式
        if recommendation["style"] == "success_card":
            st.success(f"""
            **{recommendation["title"]}**
            
            {recommendation["content"]}
            """)
        elif recommendation["style"] == "info_card":
            st.info(f"""
            **{recommendation["title"]}**
            
            {recommendation["content"]}
            """)
        else:  # neutral_card
            st.write(f"""
            **{recommendation["title"]}**
            
            {recommendation["content"]}
            """)
    
    def render_educational_content(self):
        """渲染投資知識卡片 - 3.4.2節實作"""
        knowledge_cards = self.educational_config["knowledge_cards"]
        
        # 首先顯示風險說明（always_visible）
        risk_card = knowledge_cards["risk_explanation"]
        st.warning(f"""
        **{risk_card["title"]}**
        
        {risk_card["content"]}
        """)
        
        # 顯示策略解釋卡片
        with st.expander(knowledge_cards["what_is_va"]["title"]):
            st.write(knowledge_cards["what_is_va"]["content"])
        
        with st.expander(knowledge_cards["what_is_dca"]["title"]):
            st.write(knowledge_cards["what_is_dca"]["content"])
        
        # 顯示進階教育內容
        with st.expander(knowledge_cards["market_volatility"]["title"]):
            st.write(knowledge_cards["market_volatility"]["content"])
        
        with st.expander(knowledge_cards["investment_timeline"]["title"]):
            st.write(knowledge_cards["investment_timeline"]["content"])
    
    def render_help_section(self):
        """渲染幫助區域"""
        help_config = self.educational_config["help_section"]
        
        st.subheader(help_config["title"])
        
        # 快速連結按鈕
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button(help_config["quick_links"][0]["text"], use_container_width=True):
                self._handle_help_action(help_config["quick_links"][0]["action"])
        
        with col2:
            if st.button(help_config["quick_links"][1]["text"], use_container_width=True):
                self._handle_help_action(help_config["quick_links"][1]["action"])
        
        # 教學按鈕
        tutorial_btn = help_config["tutorial_button"]
        if st.button(tutorial_btn["text"], type="primary", use_container_width=True):
            self._handle_help_action(tutorial_btn["action"])
    
    def _handle_help_action(self, action: str):
        """處理幫助動作"""
        if action == "show_beginner_guide":
            self._show_beginner_guide()
        elif action == "show_faq":
            self._show_faq()
        elif action == "start_tutorial":
            self._start_tutorial()
    
    def _show_beginner_guide(self):
        """顯示新手指南"""
        with st.expander("📖 新手指南", expanded=True):
            st.markdown("""
            ### 🚀 投資入門指南
            
            **第1步：了解兩種策略**
            - 定期定值(VA)：根據目標調整投入金額
            - 定期定額(DCA)：固定金額定期投入
            
            **第2步：設定投資參數**
            - 期初投入金額
            - 投資年數
            - 投資頻率
            - 股債配置比例
            
            **第3步：比較分析結果**
            - 查看預期報酬率
            - 了解風險指標
            - 參考智能建議
            
            **第4步：做出投資決策**
            - 考慮個人風險承受度
            - 評估時間和精力投入
            - 選擇適合的策略
            """)
    
    def _show_faq(self):
        """顯示常見問題"""
        with st.expander("❓ 常見問題", expanded=True):
            st.markdown("""
            ### 🤔 常見問題解答
            
            **Q: 哪種策略比較好？**
            A: 沒有絕對的好壞，要根據個人情況選擇。VA策略可能獲得更高報酬但需要主動管理；DCA策略操作簡單但報酬可能較低。
            
            **Q: 投資多長時間比較合適？**
            A: 建議至少3-5年以上，長期投資能有效降低短期波動的影響。
            
            **Q: 股債配置如何選擇？**
            A: 年輕人可以選擇較高股票比例（70-80%），年紀較大或風險承受度較低的投資者可以選擇較高債券比例。
            
            **Q: 系統的計算結果準確嗎？**
            A: 系統使用歷史數據和數學模型進行計算，但過去績效不代表未來表現，請謹慎參考。
            """)
    
    def _start_tutorial(self):
        """開始教學"""
        with st.expander("🚀 5分鐘快速上手", expanded=True):
            st.markdown("""
            ### 🚀 快速上手指南
            
            **步驟1 (1分鐘)：設定基本參數**
            - 在左側面板設定期初投入金額
            - 選擇投資年數和頻率
            
            **步驟2 (2分鐘)：調整投資配置**
            - 設定股票和債券比例
            - 調整預期成長率
            
            **步驟3 (1分鐘)：查看結果**
            - 觀察中央區域的摘要卡片
            - 比較兩種策略的表現
            
            **步驟4 (1分鐘)：分析圖表**
            - 查看資產成長趨勢
            - 了解風險指標差異
            
            **完成！**
            - 根據智能建議做決策
            - 下載詳細數據進行分析
            """)
    
    def get_recommendation_summary(self) -> Dict[str, Any]:
        """獲取建議摘要"""
        if not self.current_recommendation:
            return {"status": "no_recommendation"}
        
        return {
            "status": "active",
            "recommendation_type": self.current_recommendation["recommendation_type"],
            "title": self.current_recommendation["title"],
            "user_profile": self.user_profile
        }
    
    def update_recommendation(self, parameters: Dict[str, Any], calculation_results: Dict[str, Any]):
        """更新建議（當參數改變時）"""
        self._analyze_user_profile(parameters, calculation_results)
    
    def render_compact_recommendations(self, parameters: Dict[str, Any], calculation_results: Dict[str, Any]):
        """
        渲染緊湊建議 - 移動端版本，3.5.1節規格
        """
        if not calculation_results:
            st.info("請先完成投資策略計算")
            return
        
        # 分析用戶檔案並生成建議
        self._analyze_user_profile(parameters, calculation_results)
        
        if not self.current_recommendation:
            st.error("無法生成建議，請檢查計算結果")
            return
        
        # 簡化的建議展示
        recommendation = self.current_recommendation
        
        # 主要推薦
        if recommendation["recommendation_type"] == "va_recommended":
            st.success(f"""
            **🎯 推薦策略: 定期定值 (VA)**
            
            {recommendation["content"]}
            """)
        elif recommendation["recommendation_type"] == "dca_recommended":
            st.success(f"""
            **💰 推薦策略: 定期定額 (DCA)**
            
            {recommendation["content"]}
            """)
        else:
            st.info(f"""
            **📊 策略分析**
            
            {recommendation["content"]}
            """)
        
        # 投資知識卡片 - 緊湊版
        self._render_compact_knowledge_cards()
        
        # 風險提醒
        st.warning("⚠️ **風險提醒**: 過去績效不代表未來表現，請謹慎評估投資風險")
        
        # 快速操作按鈕
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📊 重新計算", use_container_width=True):
                st.rerun()
        with col2:
            if st.button("📋 查看詳情", use_container_width=True):
                st.info("請切換到「📊 結果」標籤查看詳細分析")
    
    def _render_compact_knowledge_cards(self):
        """渲染緊湊版知識卡片"""
        st.markdown("#### 💡 投資小貼士")
        
        # 簡化的知識卡片
        with st.expander("🎯 什麼是定期定值？"):
            st.write("就像設定目標存款，不夠就多存，超過就少存。當市場下跌時自動加碼，上漲時減少投入。")
        
        with st.expander("💰 什麼是定期定額？"):
            st.write("每月固定投入相同金額，就像定期定額存款。不管市場漲跌都持續投入，用時間來分散成本。")
        
        # 快速幫助
        st.markdown("#### 🙋‍♀️ 需要幫助？")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📖 新手指南", use_container_width=True):
                st.info("定期定值適合想要平穩成長的投資者")
        with col2:
            if st.button("❓ 常見問題", use_container_width=True):
                st.info("定期定額適合想要簡單投資的投資者")