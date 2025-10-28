import pandas as pd

# CSVファイルを読み込み
df = pd.read_csv("gemini_usage_log.csv")

# 数値列だけを抽出
numeric_cols = [
    "input_tokens",
    "output_tokens",
    "thinking_tokens",
    "total_tokens",
    "cost_usd",
    "cost_jpy"
]

# データ数
count = len(df)

# 合計と平均を計算
totals = df[numeric_cols].sum()
averages = df[numeric_cols].mean()

# 表示フォーマット設定（科学記法を無効化）
pd.options.display.float_format = "{:,.3f}".format  # 小数3桁で桁区切り付き

# 結果を表示
print("=== 集計結果 ===")
print(f"データ数: {count}")
print("\n--- 合計 ---")
print(totals.to_string())
print("\n--- 平均 ---")
print(averages.to_string())

# 必要なら別ファイルに出力
summary_df = pd.DataFrame({
    "metric": numeric_cols,
    "total": totals.values,
    "average": averages.values
})
summary_df.to_csv("batch_summary.csv", index=False, encoding="utf-8-sig")
print("\n集計結果を 'batch_summary.csv' に保存しました。")
