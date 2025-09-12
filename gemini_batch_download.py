from google import genai

client = genai.Client()

job_name = "batches/xxxxxxxxxxxxxxxxxxxx"  # 上記で得たfile_batch_job.nameに置き換えてください
batch_job = client.batches.get(name=job_name)

if batch_job.state.name == 'JOB_STATE_SUCCEEDED':
    if batch_job.dest and batch_job.dest.file_name:
        result_file_name = batch_job.dest.file_name
        print(f"Results are in file: {result_file_name}")
        file_content = client.files.download(file=result_file_name)
        with open("shogi_batch_results.jsonl", "wb") as f:
            f.write(file_content)
        print("結果をshogi_batch_results.jsonlに保存しました")
    else:
        print("No results found (neither file nor inline).")
else:
    print(f"Job did not succeed. Final state: {batch_job.state.name}")
    if batch_job.error:
        print(f"Error: {batch_job.error}")