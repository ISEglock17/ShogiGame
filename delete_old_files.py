from google import genai

client = genai.Client()

print("=== ACTIVEファイル一覧 ===")
for f in client.files.list():
    if f.state == "ACTIVE":
        print(f"削除中: {f.name} ({f.display_name}, {f.size_bytes} bytes)")
        client.files.delete(name=f.name)
print("完了しました。")
