import os
import openai

# OpenAI APIキーを環境変数から取得
openai.api_key = os.getenv("")


# GPT解析関数
def analyze_with_gpt(position_command, comments, bestmove):
    """GPT-3.5/4を使って人間らしいコメントを生成"""
    # 読み筋を箇条書きにフォーマット
    formatted_comments = "\n".join([f"- {comment}" for comment in comments])

    # プロンプトの生成
    prompt = f"""
    以下は将棋AIの解析結果です。この情報をもとに、人間らしい解説をしてください。
    
    盤面の状態:
    {position_command}

    AIの読み筋:
    {formatted_comments}

    最善手:
    {bestmove}

    解説:
    1. 盤面の状況に応じた戦略的な考えを説明。
    2. 読み筋の中で興味深い点を指摘。
    3. 最善手の意図を解説。
    """

    try:
        # OpenAI GPT-3.5-turboを使って人間らしい解説を生成
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",  # 使用するモデル
            messages=[
                {"role": "system", "content": "あなたは将棋の専門家で、人間に分かりやすい解説を行います。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,  # 解説を柔らかくするために少しランダム性を追加
            max_tokens=200  # 解説の長さ（必要に応じて調整）
        )
        
        # GPTからの応答（解説）を取得
        analysis = response['choices'][0]['message']['content'].strip()  # 応答の内容を取得
        return analysis

    except Exception as e:
        print(f"エラーが発生しました: {e}")
        return "解析に失敗しました。再試行してください。"
