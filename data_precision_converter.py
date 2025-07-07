#!/usr/bin/env python3
"""
數據精度轉換工具 - 第1章需求規格合規工具

功能：
- 將從 Tiingo API 直接下載的高精度 SPY 調整收盤價數據
- 轉換為符合第1章需求規格的小數點後2位精度格式
- 確保與系統處理的數據格式一致

使用方法：
python data_precision_converter.py input_file.csv output_file.csv

作者：VA_DC_APP7 系統
版本：1.0
"""

import pandas as pd
import argparse
import sys
from decimal import Decimal, ROUND_HALF_UP

# 第1章規格：價格精度設定
PRICE_PRECISION = 2  # 價格精度：小數點後2位（美元分）

def round_price_to_spec(value):
    """
    按照第1章需求規格將價格四捨五入到小數點後2位
    
    Args:
        value: 原始價格值
        
    Returns:
        float: 符合規格的價格（小數點後2位）
    """
    if pd.isna(value) or value is None:
        return None
    
    # 使用 Decimal 確保精確的四捨五入
    return float(Decimal(str(value)).quantize(
        Decimal('0.' + '0' * PRICE_PRECISION),
        rounding=ROUND_HALF_UP
    ))

def convert_spy_data_precision(input_file, output_file):
    """
    轉換 SPY 數據精度以符合系統規格
    
    Args:
        input_file: 輸入 CSV 文件路徑
        output_file: 輸出 CSV 文件路徑
    """
    try:
        # 讀取原始數據
        print(f"正在讀取原始數據: {input_file}")
        df = pd.read_csv(input_file)
        
        # 顯示原始數據統計
        print(f"原始數據筆數: {len(df)}")
        print("原始數據列名:", list(df.columns))
        
        # 檢測價格列名（可能是 'Adj Close', 'adjClose', 'adjusted_close' 等）
        price_columns = [col for col in df.columns if 'adj' in col.lower() or 'close' in col.lower()]
        
        if not price_columns:
            print("❌ 錯誤：找不到調整收盤價列，請確認數據格式")
            return False
        
        price_column = price_columns[0]
        print(f"使用價格列: {price_column}")
        
        # 顯示轉換前後對比樣本
        print("\n=== 精度轉換對比（前10筆） ===")
        print("日期\t\t原始精度\t\t系統規格精度")
        print("-" * 60)
        
        # 應用精度轉換
        original_prices = df[price_column].copy()
        df[price_column] = df[price_column].apply(round_price_to_spec)
        
        # 顯示對比
        for i in range(min(10, len(df))):
            date_val = df.iloc[i].get('Date', df.iloc[i].get('date', f'Row {i+1}'))
            original = original_prices.iloc[i]
            converted = df[price_column].iloc[i]
            print(f"{date_val}\t{original:.10f}\t\t{converted:.2f}")
        
        # 保存轉換後的數據
        print(f"\n正在保存轉換後數據: {output_file}")
        df.to_csv(output_file, index=False)
        
        # 統計信息
        price_diff = abs(original_prices - df[price_column])
        max_diff = price_diff.max()
        avg_diff = price_diff.mean()
        
        print(f"\n=== 轉換統計 ===")
        print(f"✅ 成功轉換 {len(df)} 筆數據")
        print(f"最大精度差異: {max_diff:.10f}")
        print(f"平均精度差異: {avg_diff:.10f}")
        print(f"轉換後精度: 小數點後{PRICE_PRECISION}位（符合第1章需求規格）")
        
        return True
        
    except FileNotFoundError:
        print(f"❌ 錯誤：找不到輸入文件 {input_file}")
        return False
    except Exception as e:
        print(f"❌ 錯誤：數據轉換失敗 - {str(e)}")
        return False

def main():
    """主函數"""
    parser = argparse.ArgumentParser(
        description="數據精度轉換工具 - 將 Tiingo API 數據轉換為符合第1章需求規格的格式"
    )
    parser.add_argument("input_file", help="輸入 CSV 文件路徑")
    parser.add_argument("output_file", help="輸出 CSV 文件路徑")
    parser.add_argument("--check-only", action="store_true", help="僅檢查數據格式，不執行轉換")
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("📊 VA_DC_APP7 數據精度轉換工具")
    print("=" * 60)
    print("目標：將 Tiingo API 數據轉換為符合第1章需求規格的格式")
    print(f"規格：價格精度 {PRICE_PRECISION} 位小數（美元分）")
    print("=" * 60)
    
    if args.check_only:
        # 僅檢查數據格式
        try:
            df = pd.read_csv(args.input_file)
            print(f"✅ 數據文件格式正確")
            print(f"數據筆數: {len(df)}")
            print("數據列名:", list(df.columns))
            
            price_columns = [col for col in df.columns if 'adj' in col.lower() or 'close' in col.lower()]
            if price_columns:
                print(f"找到價格列: {price_columns[0]}")
                sample_prices = df[price_columns[0]].head(5)
                print("樣本數據:")
                for i, price in enumerate(sample_prices):
                    print(f"  {i+1}: {price}")
            else:
                print("❌ 未找到調整收盤價列")
        except Exception as e:
            print(f"❌ 數據檢查失敗: {str(e)}")
    else:
        # 執行轉換
        success = convert_spy_data_precision(args.input_file, args.output_file)
        
        if success:
            print("\n✅ 數據精度轉換完成")
            print("轉換後的數據現在與系統處理的數據精度一致")
            print("符合第1章需求規格：價格精度小數點後2位")
        else:
            print("\n❌ 數據精度轉換失敗")
            sys.exit(1)

if __name__ == "__main__":
    main() 