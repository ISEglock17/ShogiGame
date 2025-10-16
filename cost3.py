#!/usr/bin/env python3
# recalc_costs.py
# cost.txt を読み、段階制料金で再計算 → エントリごとの修正コストと統計を出力

import re
import statistics
from pathlib import Path
import csv

# --- 料金（1M tokens あたり、USD）: 提示された段階制に基づく ---
INPUT_RATE_LOW  = 0.625   # prompt <= 200k
INPUT_RATE_HIGH = 1.25    # prompt > 200k
OUTPUT_RATE_LOW  = 5.00   # prompt <= 200k
OUTPUT_RATE_HIGH = 7.50   # prompt > 200k

THRESHOLD_PROMPT = 200_000  # 200k tokens を閾値に判定

# --- ファイル読み込み ---
infile = "cost.txt"
text = Path(infile).read_text(encoding="utf-8")

# --- 正規表現で抽出（順序を保持） ---
input_tokens_list = [int(x) for x in re.findall(r"Input tokens:\s*(\d+)", text)]
output_tokens_list = [int(x) for x in re.findall(r"Output tokens:\s*(\d+)", text)]
total_tokens_list = [int(x) for x in re.findall(r"Total tokens:\s*(\d+)", text)]
estimated_costs_list = [float(x) for x in re.findall(r"Estimated cost:\s*\$([\d.]+)", text)]

# --- 安全のため最小長に切り揃え ---
n_entries = min(len(input_tokens_list), len(output_tokens_list),
                len(total_tokens_list), len(estimated_costs_list))

if n_entries == 0:
    print("エントリが見つかりません。cost.txt の形式を確認してください。")
    raise SystemExit(1)

input_tokens_list = input_tokens_list[:n_entries]
output_tokens_list = output_tokens_list[:n_entries]
total_tokens_list = total_tokens_list[:n_entries]
estimated_costs_list = estimated_costs_list[:n_entries]

# --- 個々のエントリを再計算 ---
corrected_costs = []
differences = []

rows = []
for i in range(n_entries):
    inp = input_tokens_list[i]
    out = output_tokens_list[i]
    total = total_tokens_list[i]
    orig = estimated_costs_list[i]

    # 閾値判定は「プロンプト（input tokens）に基づく」
    if inp <= THRESHOLD_PROMPT:
        rate_in = INPUT_RATE_LOW
        rate_out = OUTPUT_RATE_LOW
        tier = "LOW (<=200k)"
    else:
        rate_in = INPUT_RATE_HIGH
        rate_out = OUTPUT_RATE_HIGH
        tier = "HIGH (>200k)"

    cost_in = inp / 1_000_000 * rate_in
    cost_out = out / 1_000_000 * rate_out
    corrected = cost_in + cost_out
    diff = corrected - orig

    corrected_costs.append(corrected)
    differences.append(diff)

    rows.append({
        "index": i+1,
        "input_tokens": inp,
        "output_tokens": out,
        "total_tokens": total,
        "orig_estimated_cost_usd": orig,
        "corrected_cost_usd": corrected,
        "difference_usd": diff,
        "tier_used": tier,
        "rate_input_per_1M": rate_in,
        "rate_output_per_1M": rate_out
    })

# --- 統計量（合計・平均・分散・標準偏差）関数 ---
def summarize(values):
    s = sum(values)
    mean = statistics.mean(values) if values else 0
    var = statistics.variance(values) if len(values) > 1 else 0
    stdev = statistics.stdev(values) if len(values) > 1 else 0
    return s, mean, var, stdev

sum_in, avg_in, var_in, std_in = summarize(input_tokens_list)
sum_out, avg_out, var_out, std_out = summarize(output_tokens_list)
sum_total, avg_total, var_total, std_total = summarize(total_tokens_list)
sum_orig_cost, avg_orig_cost, var_orig_cost, std_orig_cost = summarize(estimated_costs_list)
sum_corr_cost, avg_corr_cost, var_corr_cost, std_corr_cost = summarize(corrected_costs)
sum_diff, avg_diff, var_diff, std_diff = summarize(differences)

# --- 結果表示（個別行＋要約） ---
print("=== エントリ別（修正後コストと差分） ===")
for r in rows:
    print(f"[{r['index']:>2}] inp={r['input_tokens']:>6}, out={r['output_tokens']:>6}, total={r['total_tokens']:>6} "
          f"orig=${r['orig_estimated_cost_usd']:.6f}, corr=${r['corrected_cost_usd']:.6f}, "
          f"diff=${r['difference_usd']:.6f}, tier={r['tier_used']}")

print("\n=== 集計サマリ ===")
print(f"件数: {n_entries}")
print(f"Input tokens   合計={sum_in}, 平均={avg_in:.2f}, 分散={var_in:.2f}, 標準偏差={std_in:.2f}")
print(f"Output tokens  合計={sum_out}, 平均={avg_out:.2f}, 分散={var_out:.2f}, 標準偏差={std_out:.2f}")
print(f"Total tokens   合計={sum_total}, 平均={avg_total:.2f}, 分散={var_total:.2f}, 標準偏差={std_total:.2f}")
print(f"Original cost  合計=${sum_orig_cost:.6f}, 平均=${avg_orig_cost:.6f}, 分散={var_orig_cost:.8f}, 標準偏差={std_orig_cost:.8f}")
print(f"Corrected cost 合計=${sum_corr_cost:.6f}, 平均=${avg_corr_cost:.6f}, 分散={var_corr_cost:.8f}, 標準偏差={std_corr_cost:.8f}")
print(f"Difference     合計=${sum_diff:.6f}, 平均=${avg_diff:.6f}, 分散={var_diff:.8f}, 標準偏差={std_diff:.8f}")


"""
# --- CSV にも保存（任意） ---
out_csv = "costs_corrected_by_tier.csv"
with open(out_csv, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=[
        "index","input_tokens","output_tokens","total_tokens",
        "orig_estimated_cost_usd","corrected_cost_usd","difference_usd",
        "tier_used","rate_input_per_1M","rate_output_per_1M"
    ])
    writer.writeheader()
    for r in rows:
        writer.writerow(r)

print(f"\n個別結果を CSV に保存しました: {out_csv}")
"""