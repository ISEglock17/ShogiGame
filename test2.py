from google import genai

def main():
    client = genai.Client()
    print("=== 登録済みファイル一覧 ===")
    for f in client.files.list():
        print(f"名前: {f.name}")
        print(f"表示名: {f.display_name}")
        print(f"サイズ: {f.size_bytes} bytes")
        print(f"状態: {f.state}")
        print(f"作成日: {f.create_time}")
        print("-" * 40)

if __name__ == "__main__":
    main()
