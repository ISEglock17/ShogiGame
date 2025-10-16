import re
import statistics

# --- ファイルを読み込む ---
with open("cost.txt", "r", encoding="utf-8") as f:
    text = f.read()

# --- 正規表現で抽出 ---
input_tokens = [int(x) for x in re.findall(r"Input tokens:\s*(\d+)", text)]
output_tokens = [int(x) for x in re.findall(r"Output tokens:\s*(\d+)", text)]
total_tokens = [int(x) for x in re.findall(r"Total tokens:\s*(\d+)", text)]
estimated_costs = [float(x) for x in re.findall(r"Estimated cost:\s*\$([\d.]+)", text)]

# --- 件数確認 ---
count = min(len(input_tokens), len(output_tokens), len(total_tokens), len(estimated_costs))

# --- 統計計算関数 ---
def stats(values):
    if not values:
        return (0, 0, 0, 0)
    avg = statistics.mean(values)
    var = statistics.variance(values) if len(values) > 1 else 0
    stdev = statistics.stdev(values) if len(values) > 1 else 0
    return (sum(values), avg, var, stdev)

# --- 各種統計 ---
sum_in, avg_in, var_in, std_in = stats(input_tokens)
sum_out, avg_out, var_out, std_out = stats(output_tokens)
sum_total, avg_total, var_total, std_total = stats(total_tokens)
sum_cost, avg_cost, var_cost, std_cost = stats(estimated_costs)

# --- 結果表示 ---
print("=== 集計結果 ===")
print(f"抽出件数: {count}\n")

def show(name, s, a, v, sd, is_cost=False):
    if is_cost:
        print(f"{name:<15} 合計=${s:.6f}, 平均=${a:.6f}, 分散={v:.8f}, 標準偏差={sd:.8f}")
    else:
        print(f"{name:<15} 合計={s}, 平均={a:.2f}, 分散={v:.2f}, 標準偏差={sd:.2f}")

show("Input tokens",  sum_in, avg_in, var_in, std_in)
show("Output tokens", sum_out, avg_out, var_out, std_out)
show("Total tokens",  sum_total, avg_total, var_total, std_total)
show("Estimated cost", sum_cost, avg_cost, var_cost, std_cost, is_cost=True)
