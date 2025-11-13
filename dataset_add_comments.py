import json
import re
from pathlib import Path

# フォルダ設定
dataset_dir = Path("DataSet")
comments_dir = Path("ProcessedComments_batch_comments_only")
output_dir = Path("DataSetNew")
output_dir.mkdir(exist_ok=True)

# コメントファイルを順に処理
for comment_file in comments_dir.glob("*_memo_processed.txt"):
    base_id = comment_file.stem.replace("_memo_processed", "")  # 例: 1555
    json_file = dataset_dir / f"{base_id}.json"
    output_file = output_dir / f"{base_id}.json"

    # 対応するJSONが存在しなければスキップ
    if not json_file.exists():
        print(f"⚠️ {json_file.name} が見つかりません。スキップします。")
        continue

    # コメント辞書を作成
    comments_map = {}
    pattern = re.compile(r"手数(\d+)\s*[:：]\s*(.+)")
    with comment_file.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            m = pattern.match(line)
            if m:
                move_number = int(m.group(1))
                text = m.group(2).strip()
                comments_map[move_number] = text

    # JSON読み込み
    with json_file.open(encoding="utf-8") as f:
        data = json.load(f)

    # moves の comments を上書き
    for move in data.get("moves", []):
        num = move.get("move_number")
        move["comments"] = comments_map.get(num, "")

    # 出力フォルダに保存
    with output_file.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

    print(f"✅ {output_file.name} を作成しました。")

print("✅ 全ての処理が完了しました。")
