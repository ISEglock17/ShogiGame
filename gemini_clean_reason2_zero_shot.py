# To run this code you need to install the following dependencies:
# pip install google-genai  (Note: This is the new client library, not google-generativeai)

import json
import os
# from google import genai  # 'genai' is now directly imported from 'google'
from google import genai # Changed to import genai as a module, not from google.genai
from google.genai import types
import re

# --- Gemini API設定 ---
# APIキーは環境変数から読み込むことを推奨します。
# export GEMINI_API_KEY="YOUR_ACTUAL_API_KEY" のように設定してください。
# もしくは、以下の行のコメントを外し、直接APIキーを記述することもできますが、非推奨です。
# os.environ["GEMINI_API_KEY"] = "YOUR_API_KEY_HERE"

# --- Geminiに渡すプロンプト定義 ---
GEMINI_PROMPT_TEMPLATE = """
次の将棋対局データに含まれる各手のコメントについて、以下のルールと入出力形式に従って整形してください。

【目的】
コメント中の棋譜解析に不要な情報（メタ情報・人物紹介・時間情報など）を削除し、盤面や指し手の解説だけを自然な文として残すこと。

【手順】
1. コメントから削除すべき情報をルールに従って判断し、削除してください。
2. 残った内容を自然な文に整形してください。
3. その結果として出力内容を次のように構成してください：
   - 1行目: `手数<N>: <整形済みのコメント>`（整形後コメントがない場合は `手数<N>:` のみで可）
   - 2行目以降: `削除理由:` に続けて、削除対象となった表現とそのルール番号を列挙

【削除対象ルール】
1. 対局者以外の人の名前・段位・門下情報（例:「高橋九段」「所司和晴七段」「カメラマン」「検討陣」など）
2. 前例や過去の対局に関する記述（例:「前例は〜」「昨年の対局では〜」など）
3. 時間情報（例:「11時9分」「43分の考慮」「ノータイム」など）
4. 対局者プロフィールや戦績、段位、棋士番号、門下（例:「先手四段」「公式戦成績〜」「所属〜」「生年月日〜」など）
5. 棋風や戦型の傾向（例:「居飛車党」「中座は〜戦法の創始者」など）
6. 対局場所・天候・ホテル等の情報（例:「甲府市で」「快晴の空の下」「控室」など）
7. 食事・休憩・再開など（例:「昼食休憩」「対局再開」など）
8. 中継・URL・棋譜公開メタ情報（例:「中継ページでは〜」「棋譜数が〜」など）

【置換ルール】
- コメントに含まれる先手・後手の実名は「先手」「後手」に置き換えてください。
- 対局者以外の名前は削除してください（置換せずに削除）。
- 将棋の指し手や局面に関する内容は、自然な解説文に整形してください。

【出力形式】
コメントに意味のある内容が残った場合：

手数<N>: <整形後コメント>

削除理由:
- 「削除対象部分」 → ルール番号
- 「〜」 → ルール番号

整形後にコメントが空になった場合でも、次のように **必ず空行を入れて**出力してください：

手数<N>:

削除理由:
- 「削除対象部分」 → ルール番号
- 「〜」 → ルール番号

【例1: 内容が残る場合】
入力:
手数15: 中座は△８五飛戦法の創始者として知られる。戦型は横歩取り。

出力:
手数15: 戦型は横歩取り。

削除理由:
- 「中座は△８五飛戦法の創始者として知られる。」 → ルール1, 5

【例2: コメント全削除の場合】
入力:
手数12: 中座の通算成績は３８４勝３３６敗（０．５３３）。C級2組は連続10期、通算17期。

出力:
手数12:

削除理由:
- 「中座の通算成績は３８４勝３３６敗（０．５３３）」 → ルール4
- 「C級2組は連続10期、通算17期」 → ルール4

---

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

def clean_comment_with_gemini(client, sente_name: str, gote_name: str, move_number: int, comment_text: str) -> tuple:
    """
    単一のコメントをGeminiを用いて整形します。
    print内容をmemo_linesとして返すように変更
    """
    memo_lines = []
    if not comment_text.strip():
        memo_lines.append(f"=== Gemini に送信するコメント===\n手数{move_number}: {comment_text}\n→  手数{move_number}: （空コメント）\n" + "="*60)
        return "", memo_lines

    prompt_text = GEMINI_PROMPT_TEMPLATE.format(
        sente_name=sente_name,
        gote_name=gote_name,
        move_number=move_number,
        comment_text=comment_text
    )
    memo_lines.append(f"=== Gemini に送信するコメント===\n手数{move_number}: {comment_text}")

    contents = [
        types.Content(
            role="user",
            parts=[
                types.Part.from_text(text=prompt_text),
            ],
        ),
    ]
    
    generate_content_config = types.GenerateContentConfig(
        thinking_config = types.ThinkingConfig(
            thinking_budget=0,
        ),
        response_mime_type="text/plain",
    )

    try:
        full_response_text = ""
        for chunk in client.models.generate_content_stream(
            model="gemini-2.5-flash-preview-05-20",
            contents=contents,
            config=generate_content_config,
        ):
            if chunk.text is not None:
                full_response_text += chunk.text

        cleaned_text = full_response_text.strip()
        cleaned_text = re.sub(r"^(?:手数\s*\d+:\s*)+", "", cleaned_text).strip()

        patterns_to_remove_programmatically = [
            r"(\S+)(四段|五段|六段|七段|八段|九段|名人|竜王|王将|王座|棋王|叡王|王位|棋聖|本因坊|永世)\S*は\d+年\d+月\d+日生まれ", # 棋士の生年月日
            r"(\S+)(四段|五段|六段|七段|八段|九段|名人|竜王|王将|王座|棋王|叡王|王位|棋聖|本因坊|永世)?は\d+年、(四段|五段|六段|七段|八段|九段)", # 棋士の昇段情報
            r"棋士番号は\d+", # 棋士番号
            r"(\S+)(四段|五段|六段|七段|八段|九段|名人|竜王|王将|王座|棋王|叡王|王位|棋聖|本因坊|永世)?門下", # 門下
            r"公式戦成績は[０-９．]+勝[０-９．]+敗（[０-９．]+）", # 公式戦成績
            r"昨年度成績は[０-９．]+勝[０-９．]+敗（[０-９．]+）", # 昨年度成績
            r"本年度成績は[０-９．]+勝[０-９．]+敗（[０-９．]+）", # 本年度成績
            r"順位戦成績は[０-９．]+勝[０-９．]+敗（[０-９．]+）", # 順位戦成績
            r"初参加は第\d+期", # 順位戦初参加
            r"降級点\d+を持つ", # 降級点
            r"本局に勝てば初の順位戦勝ち越し", # 戦績に関する未来予測
            r"対局立会人は(\S+)(四段|五段|六段|七段|八段|九段|名人|竜王|王将|王座|棋王|叡王|王位|棋聖|本因坊|永世)?が務める", # 立会人
            r"本局の中継ページのURL末尾は「\S+．ｈｔｍｌ」", # URLメタ情報
            r"名人戦棋譜速報で公開している棋譜は少なくとも\d+千局を超える", # 棋譜数に関するメタ情報
            r"\d+分(ほど)?の考慮", # 時間に関する情報
            r"\d+分使って休憩に入った", # 休憩に関する時間情報
            r"対局再開", # 対局再開
            # 今回のケースで追加: 非常に短い/不完全な棋士紹介の残骸
            r"^先手$", # 「先手四段」という文字列のみの場合
            r"^後手$", # 「後手」という文字列のみの場合
            # その他の不完全な表現が続く場合、ここに追加していく
        ]
        for pattern in patterns_to_remove_programmatically:
            cleaned_text = re.sub(pattern, "", cleaned_text).strip()

        memo_lines.append(f"→  手数{move_number}: {cleaned_text}\n" + "="*60)

        # コメントが空の場合は必ず改行を入れる
        if not cleaned_text:
            result_line = f"手数{move_number}:\n削除理由:"
            return result_line, memo_lines

        shogi_move_indicators = ['▲', '△', '同', '成', '不成', '引', '寄', '直', '上', '右', '左', '打', '寄', '引', '直']
        if len(cleaned_text) < 5 and not any(c in cleaned_text for c in shogi_move_indicators):
            result_line = f"手数{move_number}:\n削除理由:"
            return result_line, memo_lines

        # 通常のコメントの場合
        result_line = f"手数{move_number}: {cleaned_text}"
        # 万が一「手数n:削除理由:」が連続してしまう場合の正規化
        result_line = re.sub(r"(手数\d+:)(削除理由:)", r"\1\n\2", result_line)
        return result_line, memo_lines
    except Exception as e:
        memo_lines.append(f"Gemini API呼び出し中にエラーが発生しました (手数 {move_number}): {e}")
        return "", memo_lines

def process_shogi_json(client, json_data):
    sente = json_data.get('sente', '不明')
    gote = json_data.get('gote', '不明')
    processed_lines = []
    memo_lines = []

    for move in json_data.get('moves', []):
        move_number = move.get('move_number')
        comments = move.get('comments') or []

        if all(isinstance(c, str) and len(c) == 1 for c in comments):
            full_comment = ''.join(comments).strip()
            if full_comment:
                cleaned_comment, memo = clean_comment_with_gemini(client, sente, gote, move_number, full_comment)
                if cleaned_comment:
                    processed_lines.append(cleaned_comment)
                for line in memo:
                    print(line)  # 標準出力に都度表示
                memo_lines.extend(memo)
        else:
            for comment_item in comments:
                if isinstance(comment_item, str) and comment_item.strip():
                    cleaned_comment, memo = clean_comment_with_gemini(client, sente, gote, move_number, comment_item.strip())
                    if cleaned_comment:
                        processed_lines.append(cleaned_comment)
                    for line in memo:
                        print(line)  # 標準出力に都度表示
                    memo_lines.extend(memo)
    return processed_lines, memo_lines

def main():
    input_directory = './DataSet'
    output_directory = './ProcessedComments_reason_zero'
    memo_directory = './ProcessedComments_reason_memo_zero'
    os.makedirs(output_directory, exist_ok=True)
    os.makedirs(memo_directory, exist_ok=True)

    # genai.Client の初期化
    # APIキーは環境変数から読み込まれます。
    # 実行前に 'export GEMINI_API_KEY="YOUR_ACTUAL_API_KEY"' (Linux/macOS)
    # または 'set GEMINI_API_KEY=YOUR_ACTUAL_API_KEY' (Windows) を実行してください。
    try:
        api_key = os.environ.get("GEMINI_API_KEY") # ★ここが環境変数から読み込む部分です★
        if not api_key:
            raise ValueError("環境変数 'GEMINI_API_KEY' が設定されていません。")
        client = genai.Client(api_key=api_key) # ★読み込んだAPIキーをclientに渡しています★
    except Exception as e:
        print(f"Gemini Clientの初期化に失敗しました。APIキーが正しく設定されているか確認してください。エラー: {e}")
        return

    json_files = [f for f in os.listdir(input_directory) if f.endswith('.json')]

    if not json_files:
        print(f"'{input_directory}' ディレクトリにJSONファイルが見つかりませんでした。")
        return

    for json_file in json_files:
        base_name = os.path.splitext(json_file)[0]
        output_file_name = f"{base_name}_processed.txt"
        output_path = os.path.join(output_directory, output_file_name)
        memo_file_name = f"{base_name}_memo.txt"
        memo_path = os.path.join(memo_directory, memo_file_name)

        # 既に整形済みファイルが存在するかチェック
        if os.path.exists(output_path):
            print(f"スキップ中: {json_file} - 既に整形済みファイルが存在します ({output_file_name})")
            print("-" * 30)
            continue # 次のファイルへ

        file_path = os.path.join(input_directory, json_file)
        print(f"処理中: {file_path}")
        
        data = load_json_file(file_path)
        if data:
            processed_comments, memo_lines = process_shogi_json(client, data)
            with open(output_path, 'w', encoding='utf-8') as f:
                for line in processed_comments:
                    f.write(line + '\n')
            with open(memo_path, 'w', encoding='utf-8') as f:
                for line in memo_lines:
                    f.write(line + '\n')
            print(f"整形結果を保存しました: {output_path}")
            print(f"memoログを保存しました: {memo_path}")
        print("-" * 30)

if __name__ == '__main__':
    main()