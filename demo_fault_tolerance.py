"""
容錯機制與品質控制演示腳本

演示第1章第1.2節實作的完整容錯機制：
1. API容錯管理器演示
2. 數據品質驗證器演示
3. 模擬數據生成器演示
4. 智能快取管理器演示
5. 完整工作流程演示
"""

import os
import sys
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any

# 添加src到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# 統一導入增強版組件
from src.data_sources.fault_tolerance import (
    APIFaultToleranceManager,
    DataQualityValidator,
    RetryConfig,
    ValidationRules
)
from src.data_sources.simulation import (
    SimulationDataGenerator,
    MarketRegime,
    MarketScenarioConfig,
    YieldCurveConfig
)
from src.data_sources.cache_manager import (
    IntelligentCacheManager,
    CacheConfig,
    get_cache_manager
)
from src.utils.logger import setup_logger

# 設定日誌
logger = setup_logger('FaultToleranceDemo', level=logging.INFO)

def print_section_header(title: str):
    """列印章節標題"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")


def print_subsection_header(title: str):
    """列印小節標題"""
    print(f"\n{'-'*40}")
    print(f"  {title}")
    print(f"{'-'*40}")


def demo_api_fault_tolerance():
    """演示API容錯管理器"""
    print_section_header("1. API容錯管理器演示")
    
    # 創建自定義重試配置
    retry_config = RetryConfig(
        max_retries=3,
        base_delay=0.5,
        backoff_factor=2.0,
        timeout=10
    )
    
    fault_manager = APIFaultToleranceManager(retry_config)
    
    print_subsection_header("1.1 重試機制演示")
    
    # 模擬失敗後成功的API調用
    call_count = 0
    def mock_unstable_api():
        nonlocal call_count
        call_count += 1
        print(f"  📞 API調用嘗試 #{call_count}")
        
        if call_count < 3:
            raise Exception(f"網路錯誤 #{call_count}")
        
        return {"status": "success", "data": [{"date": "2024-01-01", "price": 400.0}]}
    
    try:
        result = fault_manager.fetch_with_retry(mock_unstable_api)
        print(f"  ✅ 重試成功: {result['status']}")
    except Exception as e:
        print(f"  ❌ 重試失敗: {e}")
    
    print_subsection_header("1.2 備援策略演示")
    
    # 演示備援策略
    print("  🔄 測試Yahoo Finance備援...")
    with unittest.mock.patch.object(
        fault_manager, '_fetch_yahoo_finance',
        return_value=[{"date": "2024-01-01", "adjClose": 405.0, "data_source": "yahoo_finance"}]
    ):
        data, method = fault_manager.execute_fallback_strategy(
            'tiingo', '2024-01-01', '2024-01-31'
        )
        
        if data:
            print(f"  ✅ {method} 備援成功: 獲取 {len(data)} 筆數據")
        else:
            print("  ❌ 備援失敗")
    
    print_subsection_header("1.3 統計信息")
    
    stats = fault_manager.get_stats()
    print(f"  📊 API調用統計:")
    print(f"     總請求數: {stats['total_requests']}")
    print(f"     失敗請求數: {stats['failed_requests']}")
    print(f"     重試次數: {stats['retry_attempts']}")
    print(f"     成功率: {stats['success_rate']:.2%}")
    print(f"     備援使用次數: {stats['fallback_used']}")


def demo_data_quality_validator():
    """演示數據品質驗證器"""
    print_section_header("2. 數據品質驗證器演示")
    
    validator = DataQualityValidator()
    
    print_subsection_header("2.1 高品質數據驗證")
    
    # 高品質股票數據
    high_quality_data = [
        {"date": "2024-01-01", "adjClose": 400.0},
        {"date": "2024-01-02", "adjClose": 402.5},
        {"date": "2024-01-03", "adjClose": 401.8},
        {"date": "2024-01-04", "adjClose": 405.2},
        {"date": "2024-01-05", "adjClose": 403.9}
    ]
    
    result = validator.validate_market_data(high_quality_data, 'price_data')
    
    print(f"  📈 股票數據驗證結果:")
    print(f"     驗證狀態: {'✅ 通過' if result['is_valid'] else '❌ 失敗'}")
    print(f"     品質分數: {result['data_quality_score']:.1f}/100")
    print(f"     錯誤數量: {len(result['errors'])}")
    print(f"     警告數量: {len(result['warnings'])}")
    
    if 'statistics' in result:
        stats = result['statistics']
        if 'count' in stats:
            print(f"     數據點數: {stats['count']}")
            print(f"     價格範圍: ${stats['min_value']:.2f} - ${stats['max_value']:.2f}")
            print(f"     平均價格: ${stats['mean_value']:.2f}")
    
    print_subsection_header("2.2 低品質數據檢測")
    
    # 低品質數據（包含錯誤）
    low_quality_data = [
        {"date": "2024-01-01", "adjClose": 400.0},
        {"date": "invalid-date", "adjClose": 402.5},      # 無效日期
        {"date": "2024-01-03", "adjClose": -50.0},        # 負價格
        {"date": "2024-01-04", "adjClose": "invalid"},    # 無效數值
        {"date": "2024-01-05", "adjClose": 1000.0}        # 極端價格變化
    ]
    
    result = validator.validate_market_data(low_quality_data, 'price_data')
    
    print(f"  ⚠️  問題數據驗證結果:")
    print(f"     驗證狀態: {'✅ 通過' if result['is_valid'] else '❌ 失敗'}")
    print(f"     品質分數: {result['data_quality_score']:.1f}/100")
    
    if result['errors']:
        print(f"     錯誤詳情:")
        for error in result['errors'][:3]:  # 顯示前3個錯誤
            print(f"       • {error}")
    
    if result['warnings']:
        print(f"     警告詳情:")
        for warning in result['warnings'][:3]:  # 顯示前3個警告
            print(f"       • {warning}")
    
    print_subsection_header("2.3 殖利率數據驗證")
    
    # FRED殖利率數據（包含缺失值）
    yield_data = [
        {"date": "2024-01-01", "value": "4.25"},
        {"date": "2024-01-02", "value": "4.30"},
        {"date": "2024-01-03", "value": "."},      # FRED缺失值
        {"date": "2024-01-04", "value": "4.35"},
        {"date": "2024-01-05", "value": "4.28"}
    ]
    
    result = validator.validate_market_data(yield_data, 'yield_data')
    
    print(f"  📊 殖利率數據驗證:")
    print(f"     驗證狀態: {'✅ 通過' if result['is_valid'] else '❌ 失敗'}")
    print(f"     品質分數: {result['data_quality_score']:.1f}/100")
    
    if 'missing_values' in result.get('statistics', {}):
        missing = result['statistics']['missing_values']
        print(f"     缺失值: {missing['count']}/{missing['total']} ({missing['ratio']:.1%})")
    
    print_subsection_header("2.4 驗證器統計")
    
    quality_stats = validator.get_quality_stats()
    print(f"  📈 品質驗證統計:")
    print(f"     總驗證次數: {quality_stats['total_validations']}")
    print(f"     通過次數: {quality_stats['passed_validations']}")
    print(f"     失敗次數: {quality_stats['failed_validations']}")
    if quality_stats['total_validations'] > 0:
        print(f"     通過率: {quality_stats.get('pass_rate', 0):.1%}")
        print(f"     平均品質分數: {quality_stats['average_quality_score']:.1f}")


def demo_simulation_data_generator():
    """演示模擬數據生成器"""
    print_section_header("3. 模擬數據生成器演示")
    
    generator = SimulationDataGenerator(random_seed=42)
    
    print_subsection_header("3.1 不同市場情境模擬")
    
    start_date = "2024-01-01"
    end_date = "2024-01-31"
    initial_price = 400.0
    
    scenarios = [MarketRegime.BULL, MarketRegime.BEAR, MarketRegime.SIDEWAYS]
    
    for scenario in scenarios:
        print(f"\n  📈 {scenario.value} 市場模擬:")
        
        data = generator.generate_stock_data(
            start_date, end_date, 
            initial_price=initial_price,
            scenario=scenario
        )
        
        if data:
            summary = generator.get_market_summary(data)
            
            print(f"     數據點數: {len(data)}")
            print(f"     期間報酬: {summary.get('total_return', 0):.2%}")
            print(f"     年化報酬: {summary.get('annual_return', 0):.2%}")
            print(f"     波動率: {summary.get('volatility', 0):.2%}")
            print(f"     最大回撤: {summary.get('max_drawdown', 0):.2%}")
            print(f"     最終價格: ${summary.get('final_price', 0):.2f}")
    
    print_subsection_header("3.2 債券殖利率模擬")
    
    yield_data = generator.generate_yield_data(start_date, end_date, maturity='1Y')
    
    if yield_data:
        yields = [float(item['value']) for item in yield_data if item['value'] != '.']
        
        print(f"  📊 1年期殖利率模擬:")
        print(f"     數據點數: {len(yield_data)}")
        print(f"     殖利率範圍: {min(yields):.3f}% - {max(yields):.3f}%")
        print(f"     平均殖利率: {sum(yields)/len(yields):.3f}%")
        print(f"     初始殖利率: {yields[0]:.3f}%")
        print(f"     最終殖利率: {yields[-1]:.3f}%")
    
    print_subsection_header("3.3 混合情境模擬")
    
    # 混合情境：牛市 → 熊市 → 復甦
    scenario_sequence = [
        (MarketRegime.BULL, 10),
        (MarketRegime.BEAR, 10),
        (MarketRegime.RECOVERY, 11)
    ]
    
    mixed_data = generator.generate_mixed_scenario_data(
        start_date, end_date,
        initial_price=initial_price,
        scenario_sequence=scenario_sequence
    )
    
    if mixed_data:
        summary = generator.get_market_summary(mixed_data)
        
        print(f"  🔄 混合情境模擬結果:")
        print(f"     總數據點: {len(mixed_data)}")
        print(f"     整體報酬: {summary.get('total_return', 0):.2%}")
        print(f"     整體波動: {summary.get('volatility', 0):.2%}")
        print(f"     夏普比率: {summary.get('sharpe_ratio', 0):.3f}")
    
    print_subsection_header("3.4 壓力測試數據")
    
    stress_types = ['black_swan', 'prolonged_bear', 'high_volatility']
    
    for stress_type in stress_types:
        stress_data = generator.generate_stress_test_data(
            start_date, end_date,
            initial_price=initial_price,
            stress_type=stress_type
        )
        
        if stress_data:
            summary = generator.get_market_summary(stress_data)
            
            print(f"\n  ⚡ {stress_type} 壓力測試:")
            print(f"     期間報酬: {summary.get('total_return', 0):.2%}")
            print(f"     最大回撤: {summary.get('max_drawdown', 0):.2%}")
            print(f"     波動率: {summary.get('volatility', 0):.2%}")


def demo_intelligent_cache_manager():
    """演示智能快取管理器"""
    print_section_header("4. 智能快取管理器演示")
    
    # 使用自定義配置
    cache_config = CacheConfig(
        max_cache_size_mb=5,
        max_entries=20,
        historical_data_ttl=3600,
        simulation_data_ttl=1800
    )
    
    cache_manager = IntelligentCacheManager(cache_config)
    
    print_subsection_header("4.1 基本快取操作")
    
    # 設置快取
    market_data = [
        {"date": "2024-01-01", "price": 400.0},
        {"date": "2024-01-02", "price": 402.5}
    ]
    
    cache_key = cache_manager.generate_cache_key(
        "historical_data",
        {"start_date": "2024-01-01", "end_date": "2024-01-02", "symbol": "SPY"}
    )
    
    print(f"  🔑 生成快取鍵: {cache_key[:50]}...")
    
    cache_manager.set(cache_key, market_data, ttl=3600)
    print(f"  💾 數據已快取 (TTL: 1小時)")
    
    # 獲取快取
    cached_data = cache_manager.get(cache_key)
    if cached_data:
        print(f"  ✅ 快取命中: 獲取 {len(cached_data)} 筆數據")
    else:
        print(f"  ❌ 快取未命中")
    
    print_subsection_header("4.2 快取統計")
    
    # 執行更多快取操作以生成統計
    for i in range(5):
        key = f"test_data_{i}"
        cache_manager.set(key, {"test": i})
        cache_manager.get(key)
    
    # 測試未命中
    cache_manager.get("nonexistent_key", "default")
    
    stats = cache_manager.get_cache_stats()
    
    print(f"  📊 快取性能統計:")
    print(f"     總請求數: {stats['total_requests']}")
    print(f"     命中數: {stats['hits']}")
    print(f"     未命中數: {stats['misses']}")
    print(f"     命中率: {stats['hit_rate']:.1%}")
    print(f"     記憶體使用: {stats['memory_usage_mb']:.2f} MB")
    print(f"     記憶體條目數: {stats['memory_entries']}")
    
    print_subsection_header("4.3 TTL過期演示")
    
    # 設置短TTL進行演示
    cache_manager.set("short_ttl_key", "will_expire", ttl=2)
    print(f"  ⏰ 設置2秒TTL快取")
    
    # 立即獲取
    result = cache_manager.get("short_ttl_key")
    print(f"  ✅ 立即獲取: {result}")
    
    print(f"  ⏳ 等待3秒...")
    time.sleep(3)
    
    # 過期後獲取
    result = cache_manager.get("short_ttl_key", "expired")
    print(f"  ❌ 過期後獲取: {result}")
    
    print_subsection_header("4.4 快取清理演示")
    
    # 填充大量數據觸發清理
    print(f"  📦 填充快取數據...")
    for i in range(25):  # 超過max_entries
        large_data = {"data": list(range(i * 100, (i + 1) * 100))}
        cache_manager.set(f"large_data_{i}", large_data)
    
    final_stats = cache_manager.get_cache_stats()
    print(f"  🧹 清理後統計:")
    print(f"     記憶體條目數: {final_stats['memory_entries']}")
    print(f"     驅逐次數: {final_stats['evictions']}")
    print(f"     清理次數: {final_stats['cleanup_count']}")


def demo_integrated_workflow():
    """演示完整的整合工作流程"""
    print_section_header("5. 完整工作流程演示")
    
    print_subsection_header("5.1 工作流程說明")
    
    workflow_steps = [
        "1. 嘗試從快取獲取數據",
        "2. 快取未命中，嘗試API獲取",
        "3. API失敗，執行重試機制",
        "4. 重試失敗，啟動備援策略",
        "5. 使用模擬數據作為最終備援",
        "6. 驗證數據品質",
        "7. 將結果存入快取",
        "8. 返回驗證後的數據"
    ]
    
    for step in workflow_steps:
        print(f"  {step}")
    
    print_subsection_header("5.2 執行整合工作流程")
    
    # 初始化組件
    cache_manager = get_cache_manager()
    fault_manager = APIFaultToleranceManager()
    validator = DataQualityValidator()
    simulator = SimulationDataGenerator()
    
    # 模擬參數
    params = {
        "start_date": "2024-01-01",
        "end_date": "2024-01-31",
        "symbol": "SPY"
    }
    
    cache_key = cache_manager.generate_cache_key("market_data", params)
    
    print(f"  🔍 步驟1: 檢查快取...")
    cached_data = cache_manager.get(cache_key)
    
    if cached_data:
        print(f"  ✅ 快取命中，獲取數據")
        final_data = cached_data
    else:
        print(f"  ❌ 快取未命中，嘗試API獲取")
        
        print(f"  🔄 步驟2-3: 模擬API失敗與重試...")
        
        def failing_api():
            raise Exception("API暫時不可用")
        
        try:
            api_data = fault_manager.fetch_with_retry(failing_api)
        except Exception:
            print(f"  ❌ API重試失敗，啟動備援策略")
            
            print(f"  🆘 步驟4-5: 使用模擬數據備援...")
            
            # 使用模擬數據作為備援
            fallback_data = simulator.generate_stock_data(
                params["start_date"],
                params["end_date"],
                scenario=MarketRegime.SIDEWAYS
            )
            
            print(f"  📊 步驟6: 驗證數據品質...")
            
            # 驗證數據品質
            validation_result = validator.validate_market_data(
                fallback_data, 'price_data'
            )
            
            print(f"     品質分數: {validation_result['data_quality_score']:.1f}/100")
            print(f"     驗證狀態: {'✅ 通過' if validation_result['is_valid'] else '❌ 失敗'}")
            
            if validation_result['is_valid']:
                print(f"  💾 步驟7: 存入快取...")
                cache_manager.set(cache_key, fallback_data, ttl=1800)
                final_data = fallback_data
            else:
                print(f"  ❌ 數據品質不符要求，工作流程失敗")
                final_data = None
    
    print_subsection_header("5.3 工作流程結果")
    
    if final_data:
        print(f"  ✅ 工作流程成功完成")
        print(f"     獲取數據點: {len(final_data)}")
        print(f"     數據來源: {final_data[0].get('data_source', 'unknown')}")
        print(f"     日期範圍: {final_data[0]['date']} - {final_data[-1]['date']}")
        
        # 顯示統計摘要
        if 'adjClose' in final_data[0]:
            prices = [item['adjClose'] for item in final_data]
            print(f"     價格範圍: ${min(prices):.2f} - ${max(prices):.2f}")
            print(f"     期間報酬: {((prices[-1] / prices[0]) - 1):.2%}")
    else:
        print(f"  ❌ 工作流程失敗")
    
    print_subsection_header("5.4 系統整體統計")
    
    # 獲取各組件統計
    cache_stats = cache_manager.get_cache_stats()
    fault_stats = fault_manager.get_stats()
    quality_stats = validator.get_quality_stats()
    
    print(f"  📈 系統性能總覽:")
    print(f"     快取命中率: {cache_stats['hit_rate']:.1%}")
    print(f"     API成功率: {fault_stats['success_rate']:.1%}")
    print(f"     數據品質通過率: {quality_stats.get('pass_rate', 0):.1%}")
    print(f"     備援使用次數: {fault_stats['fallback_used']}")


def main():
    """主函數"""
    print("🚀 投資策略比較系統 - 容錯機制與品質控制演示")
    print("=" * 80)
    
    print("本演示將展示第1章第1.2節實作的完整容錯機制：")
    print("• API容錯管理器 - 智能重試與備援策略")
    print("• 數據品質驗證器 - 完整的品質檢查與評分")
    print("• 模擬數據生成器 - 多情境市場數據模擬")
    print("• 智能快取管理器 - 多層級快取與自動清理")
    print("• 完整工作流程 - 組件整合演示")
    
    try:
        # 1. API容錯管理器演示
        demo_api_fault_tolerance()
        
        # 2. 數據品質驗證器演示
        demo_data_quality_validator()
        
        # 3. 模擬數據生成器演示
        demo_simulation_data_generator()
        
        # 4. 智能快取管理器演示
        demo_intelligent_cache_manager()
        
        # 5. 完整工作流程演示
        demo_integrated_workflow()
        
        print_section_header("演示完成")
        
        print("🎉 容錯機制與品質控制演示成功完成！")
        print("\n主要特色：")
        print("✅ 多層級容錯策略 - API重試 → 備援數據 → 模擬數據")
        print("✅ 智能數據品質控制 - 範圍檢查、連續性驗證、異常檢測")
        print("✅ 靈活模擬數據生成 - 多市場情境、壓力測試、自定義配置")
        print("✅ 高效快取管理 - 多層級快取、TTL過期、LRU清理")
        print("✅ 完整系統整合 - 無縫組件協作、統計監控")
        
        print("\n系統已準備好處理各種異常情況，確保投資策略計算的穩定性！")
        
    except Exception as e:
        logger.error(f"演示過程中發生錯誤: {e}")
        print(f"\n❌ 演示失敗: {e}")
        sys.exit(1)


if __name__ == "__main__":
    # 由於某些導入可能需要mock，我們在這裡添加必要的mock
    import unittest.mock
    
    # 如果某些模組不可用，提供基本的mock
    try:
        main()
    except ImportError as e:
        print(f"⚠️  某些模組不可用，運行簡化版演示: {e}")
        print("\n請確保所有必要的依賴已安裝：")
        print("pip install numpy pandas")
        print("\n或運行測試來驗證功能：")
        print("python -m pytest tests/test_fault_tolerance.py -v") 