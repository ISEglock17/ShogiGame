from google import genai
import time

# クライアントを初期化
client = genai.Client()

# --- 1. バッチジョブを一覧取得 ---
print("📋 現在のバッチジョブ一覧を取得中...")
batches = client.batches.list()
batch_jobs = list(batches)

print(f"🔍 検出されたバッチジョブ数: {len(batch_jobs)}")

if not batch_jobs:
    print("✅ バッチジョブは存在しません。")
    exit()

# --- 2. バッチジョブ情報を表示 ---
for job in batch_jobs:
    print(f"- {job.name} | 状態: {job.state} | 作成日: {job.create_time}")

# --- 3. 削除確認 ---
confirm = input("\n⚠️ すべてのバッチジョブを削除します。よろしいですか？ (yes/no): ")
if confirm.lower() != "yes":
    print("キャンセルしました。")
    exit()

# --- 4. 各バッチジョブを削除 ---
for job in batch_jobs:
    try:
        print(f"🗑️ バッチ削除中: {job.name} ...")
        client.batches.delete(name=job.name)
        time.sleep(0.2)  # 少し間を空ける（API制限対策）
    except Exception as e:
        print(f"❌ {job.name} の削除中にエラー発生: {e}")

print("✅ すべての削除が完了しました。")
