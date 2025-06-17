import json
import os
import google.generativeai as genai

# --- Gemini API設定 ---
# 実際にはここにあなたのGemini APIキーを設定してください。
# 環境変数から読み込むことを推奨します。
# 例: YOUR_GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
YOUR_GEMINI_API_KEY = "AIzaSyAMmyRrFWjNqHPqSfb-_kDyUij4SeGjITw"
genai.configure(api_key=YOUR_GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash') # または 'gemini-1.5-pro'
#model = "gemini-2.5-flash-preview-05-20"

# --- Geminiに渡すプロンプト定義 ---
# このプロンプトは以前の議論で改善されたものです
GEMINI_PROMPT_TEMPLATE = """
次の将棋対局データに含まれる各手のコメントから、以下のルールに従って不要な部分を最小限に削除し、文の自然さを保ちながら整形してください。

■ 目的：
手数n: <コメント>で与えられるコメントを精査し、棋譜解析に不要な情報を取り除きつつ、盤面に関する解説や指し手の意味など、有用な情報は自然な文として残してください。

■ 出力形式（プレーンテキスト）：
手数<手数>: <整形されたコメント文（1文以上）>

※コメントが全削除された場合、その手は出力不要です。
※結果のみを出力すること。

■ 削除対象：
1. 対局者以外の棋士の実名。コメント内で局面解説を行っている場合でも全て削除してください。
2. 前例や過去の対局に関する記述（例：「前例は1局」「過去には〜」「この▲１六歩で前例がなくなっている」など）。
3. 時間に関する情報（例：「11時9分」「消費時間43分」「残り時間〜」）。
4. 棋士紹介（例：「羽生九段は1500勝を達成」など）。
5. 棋風や戦型の傾向（例：「両者とも居飛車党」など）。
6. 対局場所や天候（例：「大阪の会館で快晴」など）。
7. 昼食や休憩の話題（例：「そろそろ昼食休憩」など）。

※文の一部が該当する場合は、該当箇所のみを削除し、残りを自然な文に整形してください。

■ 置換ルール：
- 対局者の名前は「先手」「後手」に置き換えてください。
- ただし，対局者以外の名前は置き換えないでください。

■ 削除対象ではないもの：
- 感想や主観的な表現（「驚きの一手」「さすが」など）
- 囲い、戦術名（「銀冠」「横歩取り」「ふんどしの桂」など）
- 局面解説、手の意味などの考察
- 現在の形勢判断（例：「形勢はやや先手有利」など）
- 各手の狙いや意味（例：「▲７七角は玉頭を圧迫する狙い」など）
- 読み筋・手の予想（例：「△８六歩は研究の一手かもしれない」など）
- 局面に対する評価や変化（例：「まだまだ中盤の難所」など）

以下に対象のコメントを示します：
先手: {sente_name}
後手: {gote_name}
手数 {move_number}: {comment_text}
"""

def load_json_file(file_path):
    """JSONファイルを読み込む"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"エラー: ファイルが見つかりません - {file_path}")
        return None
    except json.JSONDecodeError:
        print(f"エラー: 無効なJSONファイルです - {file_path}")
        return None

def clean_comment_with_gemini(sente_name: str, gote_name: str, move_number: int, comment_text: str) -> str:
    """
    単一のコメントをGeminiを用いて整形します。
    """
    if not comment_text.strip(): # コメントが空の場合は処理しない
        return ""

    prompt = GEMINI_PROMPT_TEMPLATE.format(
        sente_name=sente_name,
        gote_name=gote_name,
        move_number=move_number,
        comment_text=comment_text
    )

    try:
        response = model.generate_content(prompt)
        cleaned_text = response.text.strip()
        # Geminiがたまに余計な改行を入れることがあるので調整
        if cleaned_text.startswith(f"手数{move_number}:"):
            return cleaned_text
        else: # 期待するフォーマットでない場合は、手数情報を付加する
            return f"手数{move_number}: {cleaned_text}"
    except Exception as e:
        print(f"Gemini API呼び出し中にエラーが発生しました (手数 {move_number}): {e}")
        return "" # エラー時は空文字列を返す

def process_shogi_json(json_data):
    """
    読み込んだJSONデータから各手のコメントを抽出し、Geminiで整形します。
    """
    sente = json_data.get('sente', '不明')
    gote = json_data.get('gote', '不明')
    
    processed_lines = []

    # 先手と後手の情報を最初に付与（これは整形対象外とする）
    # processed_lines.append(f"先手: {sente}")
    # processed_lines.append(f"後手: {gote}")

    for move in json_data.get('moves', []):
        move_number = move.get('move_number')
        comments = move.get('comments') or []

        # コメントがリスト形式の場合、結合して単一の文字列にする
        if all(isinstance(c, str) and len(c) == 1 for c in comments):
            full_comment = ''.join(comments).strip()
            if full_comment:
                cleaned_comment = clean_comment_with_gemini(sente, gote, move_number, full_comment)
                if cleaned_comment:
                    processed_lines.append(cleaned_comment)
        else:
            for comment_item in comments:
                if isinstance(comment_item, str) and comment_item.strip():
                    cleaned_comment = clean_comment_with_gemini(sente, gote, move_number, comment_item.strip())
                    if cleaned_comment:
                        processed_lines.append(cleaned_comment)
    return processed_lines

def main():
    input_directory = './DataSet'  # JSONファイルがあるディレクトリ
    output_directory = './ProcessedComments' # 整形後のコメントを保存するディレクトリ

    # 出力ディレクトリが存在しない場合は作成
    os.makedirs(output_directory, exist_ok=True)

    json_files = [f for f in os.listdir(input_directory) if f.endswith('.json')]

    if not json_files:
        print(f"'{input_directory}' ディレクトリにJSONファイルが見つかりませんでした。")
        return

    for json_file in json_files:
        # 出力ファイル名を作成 (例: 10006.json -> 10006_processed.txt)
        base_name = os.path.splitext(json_file)[0]
        output_file_name = f"{base_name}_processed.txt"
        output_path = os.path.join(output_directory, output_file_name)
    
        if os.path.exists(output_path):
            print(f"スキップ中: {json_file} - 既に整形済みファイルが存在します ({output_file_name})")
            print("-" * 30)
            continue # 次のファイルへ
        
        file_path = os.path.join(input_directory, json_file)
        print(f"処理中: {file_path}")
        
        data = load_json_file(file_path)
        if data:
            processed_comments = process_shogi_json(data)
                        
            with open(output_path, 'w', encoding='utf-8') as f:
                for line in processed_comments:
                    f.write(line + '\n')
            print(f"整形結果を保存しました: {output_path}")
        print("-" * 30)

if __name__ == '__main__':
    main()