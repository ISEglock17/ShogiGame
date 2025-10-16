from google import genai

client = genai.Client()

print("=== 現在のバッチジョブ一覧 ===")
for job in client.batches.list():
    print(f"{job.name} | state={job.state} | created={job.create_time}")
