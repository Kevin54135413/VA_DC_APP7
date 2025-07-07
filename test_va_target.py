import sys
sys.path.append('.')

from src.models.calculation_formulas import calculate_va_target_value, convert_annual_to_period_parameters

# 用戶提供的參數
C0 = 10000  # 初始投入
annual_investment = 12000  # 年度投入
annual_growth_rate = 13  # 13%
annual_inflation_rate = 2  # 2%
frequency = "Monthly"

# 轉換為月度參數
params = convert_annual_to_period_parameters(
    annual_investment, annual_growth_rate, annual_inflation_rate, 
    30, frequency  # 假設30年投資期間
)

print("=== 參數轉換結果 ===")
print(f"C0 (初始投入): ${C0:,.2f}")
print(f"C_period (每月基準投入): ${params['C_period']:,.2f}")
print(f"r_period (每月成長率): {params['r_period']:.6f} ({params['r_period']*100:.4f}%)")
print(f"g_period (每月通膨率): {params['g_period']:.6f} ({params['g_period']*100:.4f}%)")

print("\n=== VA_Target 計算結果 ===")
print("期數  VA_Target")
print("-" * 20)

for period in range(1, 11):
    va_target = calculate_va_target_value(
        C0, params['C_period'], params['r_period'], params['g_period'], period
    )
    print(f"{period:2d}    ${va_target:,.2f}")
