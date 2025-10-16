import re

# --- ファイルを読み込む ---
with open("cost.txt", "r", encoding="utf-8") as f:
    text = f.read()

# --- 正規表現で該当行をすべて抽出 ---
input_tokens = [int(x) for x in re.findall(r"Input tokens:\s*(\d+)", text)]
output_tokens = [int(x) for x in re.findall(r"Output tokens:\s*(\d+)", text)]
total_tokens = [int(x) for x in re.findall(r"Total tokens:\s*(\d+)", text)]
estimated_costs = [float(x) for x in re.findall(r"Estimated cost:\s*\$([\d.]+)", text)]

# --- 件数を確認（安全に揃える） ---
count = min(len(input_tokens), len(output_tokens), len(total_tokens), len(estimated_costs))

# --- 合計と平均を計算 ---
sum_input = sum(input_tokens)
sum_output = sum(output_tokens)
sum_total = sum(total_tokens)
sum_cost = sum(estimated_costs)

avg_input = sum_input / count if count else 0
avg_output = sum_output / count if count else 0
avg_total = sum_total / count if count else 0
avg_cost = sum_cost / count if count else 0

# --- 結果を表示 ---
print("=== 集計結果 ===")
print(f"抽出件数: {count}")
print(f"Input tokens:   合計={sum_input}, 平均={avg_input:.2f}")
print(f"Output tokens:  合計={sum_output}, 平均={avg_output:.2f}")
print(f"Total tokens:   合計={sum_total}, 平均={avg_total:.2f}")
print(f"Estimated cost: 合計=${sum_cost:.6f}, 平均=${avg_cost:.6f}")
