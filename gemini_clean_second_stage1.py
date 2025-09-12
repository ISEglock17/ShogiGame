import os
import re
from google import genai
from google.genai import types

# 再利用するプロンプトテンプレート（簡略化版）
GEMINI_PROMPT_TEMPLATE = """
次の将棋のコメントを自然な日本語の解説文として整形してください。
文法の誤りや不自然な言い回しがあれば直し、解説の意図がより伝わるようにしてください。

■ 処理内容：
- 文の構造を整えて、口語調の棋譜解説風の自然な文章にしてください。
- 不要な言い換えは避け、元の文の意図・情報はなるべく残してください。
- 対局者の名前が含まれる場合は「先手」「後手」に置き換えてください（他の人名はそのまま）。
- 「〜だろうか」「〜のようだ」など解説者の語調を加えても構いません。

■ 入力形式：
手数 (move_number): (削除済みのコメント)

■ 出力形式（プレーンテキスト）：
手数 (move_number): (整形後のコメント)
または（削除済みのみだった場合）
（空行）

---
入力:
手数 25: 先手は飛車を浮いた。△８四飛は△３三金と比較した手なのかもしれない。

出力:
手数 25: 先手は飛車を浮かせた。△８四飛は△３三金と比較した手だったのかもしれない。
---

以下に対象のコメントを示します：

対象コメント:
手数 {move_number}: {comment_text}
"""

def clean_comment_with_gemini(client, move_number: int, comment_text: str) -> str:
    prompt_text = GEMINI_PROMPT_TEMPLATE.format(
        move_number=move_number,
        comment_text=comment_text.strip()
    )
    
    print(f"=== Gemini に送信するコメント===")
    print(f'手数{move_number}: {comment_text}')

    contents = [
        types.Content(
            role="user",
            parts=[types.Part.from_text(text=prompt_text)],
        ),
    ]

    generate_content_config = types.GenerateContentConfig(
        thinking_config=types.ThinkingConfig(thinking_budget=0),
        response_mime_type="text/plain",
    )

    try:
        full_response_text = ""
        for chunk in client.models.generate_content_stream(
            model="gemini-2.5-flash-preview-05-20",
            contents=contents,
            config=generate_content_config,
        ):
            if chunk.text:
                full_response_text += chunk.text

        cleaned = full_response_text.strip()
        cleaned = re.sub(r"^(?:手数\s*\d+:\s*)+", "", cleaned).strip()

        print(f'→  手数{move_number}: {cleaned}')
        print("=" * 60)

        if not cleaned:
            return f"手数{move_number}: {cleaned}"
        if len(cleaned) < 5 and not any(c in cleaned for c in ['▲', '△', '同', '成']):
            return ""

        return f"手数{move_number}: {cleaned}"

    except Exception as e:
        print(f"エラー（手数 {move_number}）: {e}")
        return ""

def reclean_processed_comments(input_dir='./ProcessedComments_10', output_dir='./ProcessedComments_11'):
    os.makedirs(output_dir, exist_ok=True)

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise EnvironmentError("環境変数 'GEMINI_API_KEY' が設定されていません。")

    client = genai.Client(api_key=api_key)
    txt_files = [f for f in os.listdir(input_dir) if f.endswith('.txt')]

    for file_name in txt_files:
        input_path = os.path.join(input_dir, file_name)
        output_path = os.path.join(output_dir, file_name)

        if os.path.exists(output_path):
            print(f"スキップ: {file_name}（すでに存在）")
            continue

        print(f"処理中: {file_name}")
        with open(input_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        reprocessed = []
        for line in lines:
            line = line.strip()
            if not line:
                continue
            match = re.match(r"手数\s*(\d+):\s*(.*)", line)
            if match:
                move_number = int(match.group(1))
                comment = match.group(2)
                cleaned = clean_comment_with_gemini(client, move_number, comment)
                if cleaned:
                    reprocessed.append(cleaned)

        with open(output_path, 'w', encoding='utf-8') as f:
            for line in reprocessed:
                f.write(line + "\n")
        print(f"保存完了: {output_path}")
        print("-" * 30)

if __name__ == "__main__":
    reclean_processed_comments()
