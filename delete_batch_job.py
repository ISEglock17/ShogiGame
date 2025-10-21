import os
from google import genai

# クライアント作成
client = genai.Client()

# 対象フォルダ
folder = "./ProcessedComments_batch_memo"

# 結果ログを格納するリスト
deleted_batches = []
skipped_files = []

# 各txtファイルを処理
for filename in os.listdir(folder):
    if not filename.endswith(".txt"):
        continue

    path = os.path.join(folder, filename)
    with open(path, "r", encoding="utf-8") as f:
        content = f.read().strip()

    # コメントがない場合はスキップ
    if "コメントが1件もありません" in content or not content:
        skipped_files.append(filename)
        continue

    # base_name,batch_name の形式か確認
    parts = content.split(",", 1)
    if len(parts) != 2:
        skipped_files.append(filename)
        continue

    base_name, batch_name = parts
    batch_name = batch_name.strip()

    try:
        # バッチジョブを削除
        client.batches.delete(name=batch_name)
        deleted_batches.append(batch_name)
        print(f"✅ 削除しました: {batch_name}")
    except Exception as e:
        print(f"⚠️ 削除失敗: {batch_name} ({e})")

# 結果まとめ
print("\n=== 削除結果 ===")
print(f"削除したバッチ数: {len(deleted_batches)}")
print(f"スキップしたファイル数: {len(skipped_files)}")

if deleted_batches:
    print("\n削除済みバッチ一覧:")
    for b in deleted_batches:
        print(" -", b)

if skipped_files:
    print("\nスキップされたファイル:")
    for s in skipped_files:
        print(" -", s)
