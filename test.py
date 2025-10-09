from google import genai
import google.genai.types as types

def main():
    # クライアント作成
    client = genai.Client()

    print("=== 登録済みバッチジョブ一覧 ===")

    # バッチジョブを順に出力
    for batch in client.batches.list():
        print(f"ジョブ名: {batch.name}")
        print(f"状態: {batch.state}")
        print(f"モデル: {batch.model}")
        print(f"作成時刻: {batch.create_time}")
        print("-" * 40)

if __name__ == "__main__":
    main()
