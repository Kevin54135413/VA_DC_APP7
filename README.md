# 投資策略比較系統 v2.6.0

基於第一章需求規格實現的 Value Averaging (VA) vs Dollar Cost Averaging (DCA) 投資策略比較系統。

## 專案概述

本系統旨在提供一個互動式平台，比較定期定值(VA)與定期定額(DCA)兩種投資策略的績效表現。系統支援歷史數據回測與模擬情境分析，提供完整的績效比較與數據下載功能。

### v2.6.0 新功能 🆕

✅ **完整模擬數據查核系統**
- 六階段驗證流程：數據生成審查 → 品質分析 → 計算驗證 → 邊界測試 → 一致性驗證 → 最終文檔
- 全面的數據品質指標和技術合規性驗證

✅ **直觀模擬數據重新生成控制**
- 專用重新生成按鈕，隨時刷新模擬數據
- 隨機種子控制（自動生成/手動設定）
- 市場情境偏好（隨機組合/偏向牛市/偏向熊市/平衡市場）
- 波動性水準調整（低/中/高波動）

✅ **清楚的數據識別標記**
- 生成時間戳和隨機種子顯示
- 詳細的模擬配置與市場配置資訊
- 市場週期組成分析表格
- 數據品質指標統計（價格變動、殖利率變動、完整性確認）

## 系統架構

### 第一章實現：數據源與資訊流定義

已完成第一章的所有核心功能模組：

#### 1. 數據模型 (`src/models/data_models.py`)
- `MarketDataPoint`: 單日市場數據結構
- `AggregatedPeriodData`: 期間聚合數據結構  
- `StrategyResult`: 策略計算結果結構
- `DataModelFactory`: 數據模型工廠類

#### 2. API安全機制 (`src/utils/api_security.py`)
- 多層級API金鑰獲取策略 (Streamlit Secrets → 環境變數 → .env文件)
- API金鑰格式驗證
- API連通性測試
- 安全請求與重試機制

#### 3. 交易日處理 (`src/utils/trading_days.py`)
- 美國股市假期管理
- 交易日驗證與調整
- 模擬時間軸生成
- 期間日期計算

#### 4. API客戶端 (`src/data_sources/api_clients.py`)
- **TiingoAPIClient**: SPY股票數據獲取
- **FREDAPIClient**: 1年期國債殖利率數據獲取
- **MarketDataProvider**: 統一市場數據介面
- 優化的批次數據獲取功能

#### 5. 模擬數據生成 (`src/data_sources/simulation.py`)
- **MarketSimulator**: 使用幾何布朗運動生成股票價格
- **Vasicek模型**: 生成債券殖利率
- 牛熊市場情境模擬
- **SimulationDataProvider**: 完整模擬數據提供者

#### 6. 統一數據管理 (`src/data_manager.py`)
- **DataManager**: 統一數據管理介面
- 自動數據源選擇 (API優先，降級到模擬)
- 數據品質驗證
- 期間數據聚合

## 安裝與設定

### 1. 安裝依賴套件

```bash
pip install -r requirements.txt
```

### 2. 設定API金鑰 (可選)

複製 `config/env_example.txt` 的內容到專案根目錄的 `.env` 文件：

```bash
# .env
TIINGO_API_KEY=your_tiingo_api_key_here
FRED_API_KEY=your_fred_api_key_here
```

**取得API金鑰：**
- [Tiingo API](https://api.tiingo.com/) - 免費註冊即可取得股票數據API金鑰
- [FRED API](https://fred.stlouisfed.org/docs/api/api_key.html) - 免費註冊即可取得經濟數據API金鑰

**注意：** 如果沒有設定API金鑰，系統會自動使用模擬數據，功能完全正常。

### 3. 測試系統功能

```bash
python test_chapter1.py
```

此測試腳本會驗證所有第一章功能：
- API安全機制
- 交易日處理
- 模擬時間軸生成
- 模擬數據生成
- API數據獲取 (如果可用)
- 期間數據聚合

## 主要特色

### 🔐 多層級安全機制
- 支援 Streamlit Cloud Secrets (雲端部署)
- 環境變數配置 (伺服器部署)
- .env檔案配置 (本地開發)
- API金鑰格式驗證與連通性測試

### 📊 智慧數據源管理
- **API優先策略**: 優先使用真實市場數據
- **自動降級**: API不可用時自動切換到模擬數據
- **批次優化**: 減少API調用次數，提升效能
- **數據驗證**: 完整的數據品質檢查機制

### 🗓️ 精確交易日處理
- 美國股市假期管理
- 非交易日自動調整
- 支援多種投資頻率 (每月/每季/每半年/每年)
- 完整的時間軸生成與驗證

### 🎲 高品質模擬引擎
- **幾何布朗運動**: 股票價格模擬
- **Vasicek模型**: 債券殖利率模擬
- **情境切換**: 牛市熊市自動轉換
- **可重現結果**: 支援隨機種子設定

### 📈 數據源多樣性
- **Tiingo API**: SPY股票歷史數據
- **FRED API**: 美國國債殖利率數據
- **模擬引擎**: 未來情境數據生成
- **混合模式**: 自動選擇最佳數據源

## 目錄結構

```
VA_DC_APP7/
├── src/                      # 源代碼目錄
│   ├── models/              # 數據模型
│   │   └── data_models.py   # 核心數據結構
│   ├── utils/               # 工具模組
│   │   ├── api_security.py  # API安全機制
│   │   └── trading_days.py  # 交易日處理
│   ├── data_sources/        # 數據源模組
│   │   ├── api_clients.py   # API客戶端
│   │   └── simulation.py    # 模擬數據生成
│   └── data_manager.py      # 統一數據管理
├── config/                  # 配置文件
│   └── env_example.txt     # 環境變數範例
├── requirements.txt         # 依賴套件
├── test_chapter1.py        # 第一章功能測試
├── requirements.md         # 完整需求規格
└── README.md              # 本文件
```

## 使用範例

### 基本數據獲取

```python
from src.data_manager import DataManager

# 初始化數據管理器
data_manager = DataManager()

# 獲取市場數據 (自動選擇最佳數據源)
market_data = data_manager.get_market_data(
    start_date="2023-01-01",
    end_date="2023-12-31"
)

print(f"獲取了 {len(market_data)} 筆市場數據")
```

### 期間數據聚合

```python
# 獲取季度投資數據
period_data = data_manager.get_period_data(
    investment_years=3,
    frequency='quarterly',
    data_source='auto'  # 自動選擇
)

for period in period_data:
    print(f"第{period.period}期: {period.period_return:.2%} 報酬率")
```

### 模擬數據生成

```python
# 強制使用模擬數據
simulation_data = data_manager.get_market_data(
    start_date="2026-01-01",
    end_date="2028-12-31",
    data_source="simulation"
)

print(f"生成了 {len(simulation_data)} 筆模擬數據")
```

## 系統狀態檢查

```python
# 檢查數據源狀態
status = data_manager.get_data_source_status()
print(f"推薦數據源: {status['recommended_source']}")
print(f"可用API: {status['available_sources']}")

# 數據品質驗證
quality_report = data_manager.validate_data_quality(market_data)
print(f"數據完整度: {quality_report['statistics']['data_completeness']}")
```

## 下一階段開發

第一章的數據基礎架構已完成，接下來將實現：

- **第二章**: 表格與圖表架構與公式模組
  - VA/DCA策略計算引擎
  - 績效指標計算
  - 圖表生成與視覺化

- **第三章**: Streamlit用戶介面
  - 參數輸入控制
  - 即時計算與圖表顯示
  - 數據下載功能

## 技術規格

- **Python 3.8+**
- **數據處理**: pandas, numpy
- **API調用**: requests
- **日期處理**: python-dateutil, holidays
- **視覺化**: altair, plotly (待實現)
- **UI框架**: streamlit (待實現)

## 授權聲明

本專案依據需求規格文件開發，僅供學習和研究使用。 # VA_DC_APP7
