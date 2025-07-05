"""
容錯機制與品質控制模組

本模組實作第1章第1.2節要求的容錯機制：
1. APIFaultToleranceManager - API容錯與備援管理
2. DataQualityValidator - 數據品質驗證器
3. SimulationDataGenerator - 模擬數據生成器
4. IntelligentCacheManager - 智能快取管理器
"""

import os
import time
import random
import logging
import hashlib
import json
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, field

# 配置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class RetryConfig:
    """重試配置"""
    max_retries: int = 3
    base_delay: float = 1.0
    backoff_factor: float = 2.0
    max_delay: float = 60.0
    timeout: int = 30
    jitter_range: Tuple[float, float] = (0.1, 0.5)


@dataclass
class ValidationRules:
    """數據驗證規則"""
    price_data: Dict[str, Union[float, int]] = field(default_factory=lambda: {
        'min_price': 0.01,
        'max_price': 10000.0,
        'max_daily_change': 0.2,  # 20%
        'min_data_points': 1
    })
    
    yield_data: Dict[str, Union[float, int]] = field(default_factory=lambda: {
        'min_yield': -5.0,  # -5%
        'max_yield': 25.0,  # 25%
        'max_daily_change': 5.0,  # 5個百分點
        'min_data_points': 1
    })
    
    date_continuity: Dict[str, Union[float, int]] = field(default_factory=lambda: {
        'max_gap_days': 10,
        'required_coverage': 0.8
    })


class APIFaultToleranceManager:
    """
    API容錯與備援管理器
    
    實作智能重試機制、多級備援策略與錯誤恢復功能
    """
    
    def __init__(self, retry_config: Optional[RetryConfig] = None):
        """
        初始化容錯管理器
        
        Args:
            retry_config: 重試配置，如果為None則使用預設配置
        """
        self.retry_config = retry_config or RetryConfig()
        
        # 備援策略配置
        self.fallback_strategies = {
            'tiingo': ['yahoo_finance', 'local_csv', 'simulation'],
            'fred': ['local_yield_data', 'fixed_yield_assumption', 'simulation']
        }
        
        # 錯誤統計
        self.error_stats = {
            'total_requests': 0,
            'failed_requests': 0,
            'retry_attempts': 0,
            'fallback_used': 0,
            'success_rate': 1.0
        }
        
        logger.info("APIFaultToleranceManager 初始化完成")
    
    def fetch_with_retry(self, api_function, *args, **kwargs) -> Optional[Any]:
        """
        具備重試機制的API請求
        
        Args:
            api_function: API請求函數
            *args, **kwargs: API函數的參數
        
        Returns:
            API回應數據或None（如果所有重試都失敗）
        
        Raises:
            Exception: 如果所有重試都失敗
        """
        self.error_stats['total_requests'] += 1
        last_exception = None
        
        for attempt in range(self.retry_config.max_retries):
            try:
                logger.info(f"API請求嘗試 {attempt + 1}/{self.retry_config.max_retries}")
                
                # 執行API請求
                result = api_function(*args, **kwargs)
                
                if result is not None:
                    if attempt > 0:
                        logger.info(f"API請求在第{attempt + 1}次嘗試後成功")
                        self.error_stats['retry_attempts'] += attempt
                    
                    self._update_success_rate()
                    return result
                    
            except Exception as e:
                last_exception = e
                self.error_stats['failed_requests'] += 1
                logger.warning(f"API請求第{attempt + 1}次失敗: {str(e)[:100]}")
                
                # 計算延遲時間（指數退避 + 隨機抖動）
                if attempt < self.retry_config.max_retries - 1:
                    delay = self._calculate_backoff_delay(attempt)
                    logger.info(f"等待 {delay:.2f} 秒後重試...")
                    time.sleep(delay)
        
        # 所有重試都失敗
        logger.error(f"API請求在{self.retry_config.max_retries}次嘗試後全部失敗")
        self._update_success_rate()
        
        if last_exception:
            raise last_exception
        else:
            raise Exception("API請求失敗，原因未知")
    
    def execute_fallback_strategy(
        self, 
        primary_service: str, 
        start_date: str, 
        end_date: str,
        **kwargs
    ) -> Tuple[Optional[List[Dict]], Optional[str]]:
        """
        執行備援策略
        
        Args:
            primary_service: 主要服務名稱 ('tiingo' 或 'fred')
            start_date: 開始日期 (YYYY-MM-DD)
            end_date: 結束日期 (YYYY-MM-DD)
            **kwargs: 額外參數
        
        Returns:
            tuple: (data, fallback_method_used) 或 (None, None) 如果所有備援都失敗
        """
        fallback_methods = self.fallback_strategies.get(primary_service, [])
        
        for method in fallback_methods:
            try:
                logger.info(f"嘗試備援方案: {method}")
                
                if method == 'yahoo_finance':
                    data = self._fetch_yahoo_finance(start_date, end_date)
                elif method == 'local_csv':
                    data = self._fetch_local_csv(primary_service, start_date, end_date)
                elif method == 'simulation':
                    data = self._generate_fallback_simulation(primary_service, start_date, end_date)
                elif method == 'local_yield_data':
                    data = self._fetch_local_yield_data(start_date, end_date)
                elif method == 'fixed_yield_assumption':
                    data = self._generate_fixed_yield_data(start_date, end_date)
                else:
                    logger.warning(f"未知的備援方案: {method}")
                    continue
                
                if data and len(data) > 0:
                    logger.info(f"備援方案 {method} 成功獲取 {len(data)} 筆數據")
                    self.error_stats['fallback_used'] += 1
                    return data, method
                    
            except Exception as e:
                logger.warning(f"備援方案 {method} 失敗: {str(e)[:100]}")
                continue
        
        # 所有備援方案都失敗
        logger.error(f"所有{primary_service}備援方案都失敗")
        return None, None
    
    def _calculate_backoff_delay(self, attempt: int) -> float:
        """計算退避延遲時間"""
        delay = self.retry_config.base_delay * (
            self.retry_config.backoff_factor ** attempt
        )
        
        # 限制最大延遲
        delay = min(delay, self.retry_config.max_delay)
        
        # 添加隨機抖動
        jitter = random.uniform(*self.retry_config.jitter_range)
        delay += jitter
        
        return delay
    
    def _fetch_yahoo_finance(self, start_date: str, end_date: str) -> Optional[List[Dict]]:
        """Yahoo Finance備援數據獲取"""
        try:
            import yfinance as yf
            ticker = yf.Ticker("SPY")
            data = ticker.history(start=start_date, end=end_date)
            
            if data.empty:
                return None
                
            result = []
            for idx, row in data.iterrows():
                result.append({
                    'date': idx.strftime('%Y-%m-%d'),
                    'adjClose': float(row['Close']),
                    'data_source': 'yahoo_finance'
                })
            
            return result
            
        except ImportError:
            logger.warning("yfinance套件未安裝，跳過Yahoo Finance備援")
            return None
        except Exception as e:
            logger.error(f"Yahoo Finance數據獲取失敗: {e}")
            return None
    
    def _fetch_local_csv(self, service: str, start_date: str, end_date: str) -> Optional[List[Dict]]:
        """本地CSV檔案備援數據"""
        try:
            # 根據服務類型決定檔案路徑
            csv_path = f"data/{service}_backup.csv"
            
            if not os.path.exists(csv_path):
                logger.warning(f"本地備援檔案不存在: {csv_path}")
                return None
            
            df = pd.read_csv(csv_path)
            df['date'] = pd.to_datetime(df['date'])
            
            # 篩選日期範圍
            start_dt = pd.to_datetime(start_date)
            end_dt = pd.to_datetime(end_date)
            mask = (df['date'] >= start_dt) & (df['date'] <= end_dt)
            filtered_df = df.loc[mask]
            
            if filtered_df.empty:
                return None
            
            result = []
            for _, row in filtered_df.iterrows():
                data_point = {
                    'date': row['date'].strftime('%Y-%m-%d'),
                    'data_source': 'local_csv'
                }
                
                # 根據服務類型添加相應欄位
                if service == 'tiingo':
                    data_point['adjClose'] = float(row['adjClose'])
                elif service == 'fred':
                    data_point['value'] = float(row['value'])
                
                result.append(data_point)
            
            return result
            
        except Exception as e:
            logger.error(f"本地CSV數據讀取失敗: {e}")
            return None
    
    def _generate_fallback_simulation(
        self, 
        service: str, 
        start_date: str, 
        end_date: str
    ) -> Optional[List[Dict]]:
        """生成簡化模擬數據作為最終備援"""
        try:
            from src.data_sources.simulation import SimulationDataGenerator
            
            generator = SimulationDataGenerator()
            
            if service == 'tiingo':
                return generator.generate_stock_data(start_date, end_date)
            elif service == 'fred':
                return generator.generate_yield_data(start_date, end_date)
            
            return None
            
        except Exception as e:
            logger.error(f"備援模擬數據生成失敗: {e}")
            return None
    
    def _fetch_local_yield_data(self, start_date: str, end_date: str) -> Optional[List[Dict]]:
        """本地殖利率數據備援"""
        return self._fetch_local_csv('fred', start_date, end_date)
    
    def _generate_fixed_yield_data(self, start_date: str, end_date: str) -> Optional[List[Dict]]:
        """生成固定殖利率假設數據"""
        try:
            dates = pd.date_range(start=start_date, end=end_date, freq='D')
            fixed_yield = 4.0  # 假設固定4%殖利率
            
            result = []
            for date in dates:
                result.append({
                    'date': date.strftime('%Y-%m-%d'),
                    'value': str(fixed_yield),
                    'data_source': 'fixed_assumption'
                })
            
            return result
            
        except Exception as e:
            logger.error(f"固定殖利率數據生成失敗: {e}")
            return None
    
    def _update_success_rate(self):
        """更新成功率統計"""
        if self.error_stats['total_requests'] > 0:
            success_requests = (
                self.error_stats['total_requests'] - 
                self.error_stats['failed_requests']
            )
            self.error_stats['success_rate'] = success_requests / self.error_stats['total_requests']
    
    def get_stats(self) -> Dict[str, Any]:
        """獲取錯誤統計信息"""
        return self.error_stats.copy()
    
    def reset_stats(self):
        """重設錯誤統計"""
        self.error_stats = {
            'total_requests': 0,
            'failed_requests': 0,
            'retry_attempts': 0,
            'fallback_used': 0,
            'success_rate': 1.0
        }
        logger.info("錯誤統計已重設")


class DataQualityValidator:
    """
    數據品質控制與驗證器
    
    實作完整的數據品質檢查、異常值檢測與品質評分功能
    """
    
    def __init__(self, validation_rules: Optional[ValidationRules] = None):
        """
        初始化數據品質驗證器
        
        Args:
            validation_rules: 驗證規則，如果為None則使用預設規則
        """
        self.validation_rules = validation_rules or ValidationRules()
        
        # 品質檢查統計
        self.quality_stats = {
            'total_validations': 0,
            'passed_validations': 0,
            'failed_validations': 0,
            'average_quality_score': 0.0
        }
        
        logger.info("DataQualityValidator 初始化完成")
    
    def validate_market_data(
        self, 
        data: List[Dict], 
        data_type: str = 'price_data'
    ) -> Dict[str, Any]:
        """
        驗證市場數據品質
        
        Args:
            data: 市場數據列表
            data_type: 數據類型 ('price_data' 或 'yield_data')
        
        Returns:
            dict: 完整的驗證結果報告
        """
        self.quality_stats['total_validations'] += 1
        
        validation_result = {
            'is_valid': True,
            'errors': [],
            'warnings': [],
            'statistics': {},
            'data_quality_score': 0.0,
            'validation_timestamp': datetime.now().isoformat(),
            'data_type': data_type,
            'data_count': len(data) if data else 0
        }
        
        if not data or len(data) == 0:
            validation_result['is_valid'] = False
            validation_result['errors'].append("數據為空")
            self.quality_stats['failed_validations'] += 1
            return validation_result
        
        try:
            # 執行各項檢查
            self._check_data_quantity(data, data_type, validation_result)
            self._check_value_ranges(data, data_type, validation_result)
            self._check_daily_changes(data, data_type, validation_result)
            self._check_date_continuity(data, validation_result)
            self._check_missing_values(data, data_type, validation_result)
            self._calculate_statistics(data, data_type, validation_result)
            
            # 計算整體品質分數
            validation_result['data_quality_score'] = self._calculate_quality_score(
                validation_result, len(data)
            )
            
            # 更新統計
            if validation_result['is_valid']:
                self.quality_stats['passed_validations'] += 1
            else:
                self.quality_stats['failed_validations'] += 1
            
            self._update_average_quality_score(validation_result['data_quality_score'])
            
        except Exception as e:
            validation_result['is_valid'] = False
            validation_result['errors'].append(f"驗證過程發生錯誤: {str(e)}")
            self.quality_stats['failed_validations'] += 1
        
        return validation_result
    
    def _check_data_quantity(
        self, 
        data: List[Dict], 
        data_type: str, 
        result: Dict[str, Any]
    ):
        """檢查數據量"""
        rules = getattr(self.validation_rules, data_type)
        min_points = rules['min_data_points']
        
        if len(data) < min_points:
            result['errors'].append(
                f"數據點數量不足: {len(data)} < {min_points}"
            )
            result['is_valid'] = False
    
    def _check_value_ranges(
        self, 
        data: List[Dict], 
        data_type: str, 
        result: Dict[str, Any]
    ):
        """檢查數值範圍"""
        rules = getattr(self.validation_rules, data_type)
        value_field = 'adjClose' if data_type == 'price_data' else 'value'
        
        for item in data:
            if value_field in item and item[value_field] is not None:
                try:
                    value = float(item[value_field])
                    
                    if data_type == 'price_data':
                        if value < rules['min_price'] or value > rules['max_price']:
                            result['warnings'].append(
                                f"價格超出合理範圍: {value} 在 {item.get('date', 'unknown')}"
                            )
                    elif data_type == 'yield_data':
                        if value < rules['min_yield'] or value > rules['max_yield']:
                            result['warnings'].append(
                                f"殖利率超出合理範圍: {value}% 在 {item.get('date', 'unknown')}"
                            )
                            
                except (ValueError, TypeError):
                    result['errors'].append(
                        f"無效的數值格式: {item[value_field]} 在 {item.get('date', 'unknown')}"
                    )
                    result['is_valid'] = False
    
    def _check_daily_changes(
        self, 
        data: List[Dict], 
        data_type: str, 
        result: Dict[str, Any]
    ):
        """檢查日間變化"""
        if len(data) < 2:
            return
        
        rules = getattr(self.validation_rules, data_type)
        value_field = 'adjClose' if data_type == 'price_data' else 'value'
        max_change = rules['max_daily_change']
        
        # 先排序數據
        sorted_data = sorted(data, key=lambda x: x.get('date', ''))
        
        values = []
        for item in sorted_data:
            if value_field in item and item[value_field] is not None:
                try:
                    values.append((float(item[value_field]), item.get('date', 'unknown')))
                except (ValueError, TypeError):
                    continue
        
        daily_changes = []
        for i in range(1, len(values)):
            if values[i-1][0] > 0:  # 避免除以零
                change = abs((values[i][0] - values[i-1][0]) / values[i-1][0])
                daily_changes.append(change)
                
                if change > max_change:
                    result['warnings'].append(
                        f"異常的日間變化: {change:.2%} 在 {values[i][1]}"
                    )
        
        if daily_changes:
            result['statistics']['max_daily_change'] = max(daily_changes)
            result['statistics']['avg_daily_change'] = sum(daily_changes) / len(daily_changes)
    
    def _check_date_continuity(self, data: List[Dict], result: Dict[str, Any]):
        """檢查日期連續性"""
        try:
            dates = []
            for item in data:
                if 'date' in item:
                    try:
                        date_obj = datetime.strptime(item['date'], '%Y-%m-%d')
                        dates.append(date_obj)
                    except ValueError:
                        result['warnings'].append(f"無效日期格式: {item['date']}")
            
            if len(dates) < 2:
                result['statistics']['date_continuity'] = {
                    'coverage_ratio': 1.0 if dates else 0.0,
                    'gaps': [],
                    'total_days': 1 if dates else 0
                }
                return
            
            dates.sort()
            start_date = dates[0]
            end_date = dates[-1]
            total_days = (end_date - start_date).days + 1
            
            # 計算預期的交易日數量（假設約70%的日子是交易日）
            expected_trading_days = max(1, int(total_days * 0.7))
            actual_data_days = len(dates)
            coverage_ratio = min(1.0, actual_data_days / expected_trading_days)
            
            # 尋找數據缺口
            gaps = []
            max_gap_days = self.validation_rules.date_continuity['max_gap_days']
            
            for i in range(1, len(dates)):
                gap_days = (dates[i] - dates[i-1]).days
                if gap_days > max_gap_days:
                    gaps.append({
                        'start': dates[i-1].strftime('%Y-%m-%d'),
                        'end': dates[i].strftime('%Y-%m-%d'),
                        'gap_days': gap_days
                    })
            
            date_continuity = {
                'coverage_ratio': coverage_ratio,
                'gaps': gaps,
                'total_days': total_days,
                'actual_days': actual_data_days
            }
            
            result['statistics']['date_continuity'] = date_continuity
            
            # 檢查覆蓋率
            required_coverage = self.validation_rules.date_continuity['required_coverage']
            if coverage_ratio < required_coverage:
                result['warnings'].append(
                    f"數據覆蓋率不足: {coverage_ratio:.2%} < {required_coverage:.2%}"
                )
            
        except Exception as e:
            logger.error(f"日期連續性檢查失敗: {e}")
            result['statistics']['date_continuity'] = {
                'coverage_ratio': 0.0,
                'gaps': [],
                'total_days': 0
            }
    
    def _check_missing_values(
        self, 
        data: List[Dict], 
        data_type: str, 
        result: Dict[str, Any]
    ):
        """檢查缺失值"""
        value_field = 'adjClose' if data_type == 'price_data' else 'value'
        
        missing_count = 0
        total_count = len(data)
        
        for item in data:
            if value_field not in item or item[value_field] is None:
                missing_count += 1
            elif isinstance(item[value_field], str) and item[value_field].strip() in ['', '.', 'null', 'nan']:
                missing_count += 1
        
        missing_ratio = missing_count / total_count if total_count > 0 else 0
        
        result['statistics']['missing_values'] = {
            'count': missing_count,
            'ratio': missing_ratio,
            'total': total_count
        }
        
        if missing_ratio > 0.1:  # 超過10%缺失值
            result['warnings'].append(
                f"高缺失值比例: {missing_ratio:.2%} ({missing_count}/{total_count})"
            )
    
    def _calculate_statistics(
        self, 
        data: List[Dict], 
        data_type: str, 
        result: Dict[str, Any]
    ):
        """計算基本統計信息"""
        value_field = 'adjClose' if data_type == 'price_data' else 'value'
        
        values = []
        for item in data:
            if value_field in item and item[value_field] is not None:
                try:
                    if isinstance(item[value_field], str) and item[value_field] != '.':
                        values.append(float(item[value_field]))
                    elif isinstance(item[value_field], (int, float)):
                        values.append(float(item[value_field]))
                except (ValueError, TypeError):
                    continue
        
        if values:
            result['statistics'].update({
                'count': len(values),
                'min_value': min(values),
                'max_value': max(values),
                'mean_value': sum(values) / len(values),
                'value_range': max(values) - min(values)
            })
            
            # 計算標準差
            mean_val = result['statistics']['mean_value']
            variance = sum((x - mean_val) ** 2 for x in values) / len(values)
            result['statistics']['std_deviation'] = variance ** 0.5
    
    def _calculate_quality_score(self, validation_result: Dict[str, Any], data_count: int) -> float:
        """計算數據品質分數 (0-100)"""
        score = 100.0
        
        # 錯誤扣分（每個錯誤扣20分）
        score -= len(validation_result['errors']) * 20
        
        # 警告扣分（每個警告扣5分）
        score -= len(validation_result['warnings']) * 5
        
        # 數據覆蓋率加分
        if 'date_continuity' in validation_result['statistics']:
            coverage = validation_result['statistics']['date_continuity']['coverage_ratio']
            score *= coverage
        
        # 數據量加分
        if data_count >= 100:
            score += 5
        elif data_count >= 50:
            score += 2
        elif data_count >= 10:
            score += 1
        
        # 缺失值扣分
        if 'missing_values' in validation_result['statistics']:
            missing_ratio = validation_result['statistics']['missing_values']['ratio']
            score *= (1 - missing_ratio)
        
        return max(0.0, min(100.0, score))
    
    def _update_average_quality_score(self, new_score: float):
        """更新平均品質分數"""
        if self.quality_stats['total_validations'] > 0:
            current_avg = self.quality_stats['average_quality_score']
            total = self.quality_stats['total_validations']
            
            # 計算新的加權平均
            self.quality_stats['average_quality_score'] = (
                (current_avg * (total - 1) + new_score) / total
            )
    
    def get_quality_stats(self) -> Dict[str, Any]:
        """獲取品質檢查統計信息"""
        stats = self.quality_stats.copy()
        
        if stats['total_validations'] > 0:
            stats['pass_rate'] = stats['passed_validations'] / stats['total_validations']
            stats['fail_rate'] = stats['failed_validations'] / stats['total_validations']
        else:
            stats['pass_rate'] = 0.0
            stats['fail_rate'] = 0.0
        
        return stats
    
    def reset_stats(self):
        """重設品質檢查統計"""
        self.quality_stats = {
            'total_validations': 0,
            'passed_validations': 0,
            'failed_validations': 0,
            'average_quality_score': 0.0
        }
        logger.info("品質檢查統計已重設") 