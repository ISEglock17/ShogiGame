from google import genai

client = genai.Client()

uploaded_file_name = "files/xxxxxxxxxxxxxxxxxxxx"  # 上記で得たuploaded_file.nameに置き換えてください

file_batch_job = client.batches.create(
    model="gemini-2.5-pro-latest",
    src=uploaded_file_name,
    config={
        'display_name': "shogi-batch-job-1",
    },
)

print(f"Created batch job: {file_batch_job.name}")