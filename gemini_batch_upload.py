from google import genai
from google.genai import types

client = genai.Client()

uploaded_file = client.files.upload(
    file='shogi_batch_requests.jsonl',
    config=types.UploadFileConfig(display_name='shogi-batch-requests', mime_type='jsonl')
)

print(f"Uploaded file: {uploaded_file.name}")