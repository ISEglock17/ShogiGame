import time
from google import genai

client = genai.Client()

job_name = "batches/xxxxxxxxxxxxxxxxxxxx"  # 上記で得たfile_batch_job.nameに置き換えてください

completed_states = set([
    'JOB_STATE_SUCCEEDED',
    'JOB_STATE_FAILED',
    'JOB_STATE_CANCELLED',
    'JOB_STATE_EXPIRED',
])

print(f"Polling status for job: {job_name}")
batch_job = client.batches.get(name=job_name)
while batch_job.state.name not in completed_states:
    print(f"Current state: {batch_job.state.name}")
    time.sleep(30)
    batch_job = client.batches.get(name=job_name)

print(f"Job finished with state: {batch_job.state.name}")
if batch_job.state.name == 'JOB_STATE_FAILED':
    print(f"Error: {batch_job.error}")