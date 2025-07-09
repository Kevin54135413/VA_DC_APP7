# 🌐 Streamlit Cloud 專案更新指南

## 📋 更新背景

由於GitHub倉庫已從 `VA_DC_APP7` 重新命名為 `Investment-Portfolio-Analyzer`，需要確保Streamlit Cloud上的專案也同步更新。

## 🔄 更新步驟

### 步驟1：檢查自動同步狀態

1. **登入Streamlit Cloud**
   - 前往：https://share.streamlit.io/
   - 使用您的GitHub帳號登入

2. **查看專案列表**
   - 檢查專案是否自動更新為新名稱
   - 確認專案狀態是否正常

### 步驟2：手動更新（如果需要）

如果專案沒有自動更新，請執行以下步驟：

#### 2.1 刪除舊專案
1. 在Streamlit Cloud找到舊專案 (VA_DC_APP7)
2. 點擊專案右側的 "⋮" 選單
3. 選擇 "Delete app"
4. 確認刪除

#### 2.2 重新部署新專案
1. 點擊 "New app" 按鈕
2. 選擇 "From existing repo"
3. 選擇您的GitHub帳號
4. 選擇新倉庫：`Investment-Portfolio-Analyzer`
5. 設定部署參數：
   - **Main file path**: `app.py`
   - **URL**: 選擇您偏好的URL
   - **Python version**: 3.9+ (建議)

#### 2.3 環境變數設定
如果您的應用使用API金鑰，需要重新設定：

1. 在新專案的設定中找到 "Secrets"
2. 添加以下環境變數（如果需要）：
   ```toml
   TIINGO_API_KEY = "your_tiingo_api_key_here"
   FRED_API_KEY = "your_fred_api_key_here"
   ```

### 步驟3：驗證部署

1. **檢查應用啟動**
   - 確認應用能正常載入
   - 檢查版本信息顯示正確

2. **功能測試**
   - 測試參數設定功能
   - 測試策略計算功能
   - 確認圖表顯示正常

3. **版本確認**
   - 確認顯示：`v4.0.0 - 市場模擬優化版 | 更新: 2025年7月8日`
   - 確認所有功能正常運作

## 🔗 新的Streamlit Cloud URL

部署完成後，您的新URL格式將是：
```
https://investment-portfolio-analyzer-[random-string].streamlit.app
```
或者您可以選擇自訂URL（如果可用）。

## 📊 更新確認清單

- [ ] 登入Streamlit Cloud
- [ ] 確認專案自動更新或手動重新部署
- [ ] 設定環境變數（如果需要）
- [ ] 測試應用功能
- [ ] 確認版本信息正確
- [ ] 記錄新的Streamlit Cloud URL

## 🚨 注意事項

1. **舊URL失效**: 如果重新部署，舊的Streamlit Cloud URL將失效
2. **環境變數**: 需要重新設定API金鑰（如果使用）
3. **部署時間**: 新專案首次部署可能需要幾分鐘
4. **功能測試**: 建議完整測試所有功能確保正常運作

## 💡 建議

1. **保留舊URL記錄**: 如果有分享過舊URL，建議通知用戶新URL
2. **書籤更新**: 更新您的書籤為新URL
3. **文檔更新**: 在README中更新Streamlit Cloud連結

## 🆘 故障排除

### 常見問題

**Q: 專案無法找到GitHub倉庫**
- A: 確認GitHub倉庫為公開狀態，或Streamlit Cloud有適當權限

**Q: 應用啟動失敗**
- A: 檢查 `requirements.txt` 是否包含所有必要套件

**Q: API功能不正常**
- A: 確認環境變數（Secrets）設定正確

**Q: 版本信息顯示錯誤**
- A: 確認使用的是最新的main分支代碼

---

**更新狀態**: 待執行  
**預計完成時間**: 10-15分鐘  
**建議執行時間**: 現在 