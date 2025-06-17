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
次の将棋対局データに含まれる各手のコメントから、以下のルールに従って不要な部分を最小限に削除し、文の自然さを保ちながら整形してください。

■ 目的：
手数n: <コメント>で与えられるコメントを精査し、棋譜解析に不要な情報を取り除きつつ、盤面に関する解説や指し手の意味など、有用な情報は自然な文として残してください。

■ 出力形式（プレーンテキスト）：
<整形されたコメント文>

※コメントが全て削除対象の情報のみで構成される場合は、その手数行は一切出力しないでください。
※結果のみを出力すること。余計な説明や前後の文脈は不要です。

■ 削除対象：
1.  対局者以外の棋士の実名。（例：「高橋九段」「畠山鎮七段」「所司和晴七段」など）コメント内で局面解説を行っている場合でも全て削除してください。
2.  前例や過去の対局に関する記述（例：「前例は1局」「過去には〜」「この▲１六歩で前例がなくなっている」など）。
3.  時間に関する情報（例：「11時9分」「消費時間43分」「残り時間〜」「11分の考慮」「33分使って休憩に入った」など）。
4.  棋士紹介、またはその一部。対局者であっても、棋士のプロフィール、経歴、成績（公式戦成績、順位戦成績、勝敗数など）、所属、誕生日、段位、棋士番号、門下に関する記述は全て削除してください。（例：「大平 武洋六段は1977年5月11日生まれ」「先手の公式戦成績は２２７勝２４７敗」「後手の順位戦成績は１１４勝１０５敗」「先手四段」「後手は加瀬純一七段門下」など）
5.  棋風や戦型の傾向（例：「両者とも居飛車党」など）。
6.  対局場所や天候（例：「大阪の会館で快晴」など）。
7.  昼食や休憩の話題、対局の再開に関する記述。（例：「そろそろ昼食休憩」「対局再開」など）
8.  中継ページ、URL、棋譜公開に関するメタ情報（例：「本局の中継ページのURL末尾は「１００００．ｈｔｍｌ」」「名人戦棋譜速報で公開している棋譜は少なくとも9千局を超える」など）。

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

def clean_comment_with_gemini(client, sente_name: str, gote_name: str, move_number: int, comment_text: str) -> str:
    """
    単一のコメントをGeminiを用いて整形します。
    """
    if not comment_text.strip(): # コメントが空の場合は処理しない
        return ""

    prompt_text = GEMINI_PROMPT_TEMPLATE.format(
        sente_name=sente_name,
        gote_name=gote_name,
        move_number=move_number,
        comment_text=comment_text
    )

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
        # ここで `chunk.text` が None になる可能性を考慮
        for chunk in client.models.generate_content_stream(
            model="gemini-2.5-flash-preview-05-20",
            contents=contents,
            config=generate_content_config,
        ):
            if chunk.text is not None: # ★追加: chunk.text が None でないことを確認★
                full_response_text += chunk.text
            # else:
            #     print(f"警告: 手数 {move_number} の処理中に空のチャンクを受け取りました。") # デバッグ用

        cleaned_text = full_response_text.strip()
        
        # 1. LLMが返した可能性のある余計な「手数X:」プレフィックスを全て除去
        # モデルが「手数X: 手数X:」と返したり、「手数X:」だけ返したりする場合に対応
        # まず、LLMが意図せず付与した可能性のある「手数X:」を全て除去し、生のコメント部分だけにする
        # r"^(?:手数\s*\d+:\s*)+" は「手数 数字: 」というパターンが先頭に1回以上続く場合にマッチ
        # ?: は非キャプチャグループ（マッチするが結果には含まれない）
        cleaned_text = re.sub(r"^(?:手数\s*\d+:\s*)+", "", cleaned_text).strip()

        # 2. 棋士紹介、戦績、メタ情報などのパターンをプログラム側でさらに確実に除去
        # （前回のリストを再掲。必要に応じて、今回のエラーで残ったパターンを追加してください）
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

        # 3. 最終的に空になったコメント、または意味のない短いコメントを完全に除去
        # 全ての削除処理を行った結果、テキストが空になった場合
        if not cleaned_text:
            return f"手数{move_number}:"

        # 非常に短い（例: 数文字以下）で、かつ将棋の指し手を示唆する記号を含まないコメントも除去
        # （「。」や「！」だけが残った場合など）
        # ここは調整が必要です。あまり厳しくしすぎると、本当に残したい短いコメントも消してしまう可能性があります。
        shogi_move_indicators = ['▲', '△', '同', '成', '不成', '引', '寄', '直', '上', '右', '左', '打', '寄', '引', '直']
        if len(cleaned_text) < 5 and not any(c in cleaned_text for c in shogi_move_indicators):
            # 棋譜の指し手を示す記号が含まれていない、かつ非常に短い場合は削除
            return f"手数{move_number}:"

        # 4. 最終的な出力フォーマット調整: 必ず「手数X: 」を先頭に付与
        # ここまでで元のコメントから不必要な部分が除去されているはずなので、
        # 最後に適切な「手数X: 」を付与して整形済みコメントとして返す
        return f"手数{move_number}: {cleaned_text}"
            
    except Exception as e:
        print(f"Gemini API呼び出し中にエラーが発生しました (手数 {move_number}): {e}")
        return "" # エラー時は空文字列を返す。これで 'NoneType' が返されることはないはず。

def process_shogi_json(client, json_data):
    """
    読み込んだJSONデータから各手のコメントを抽出し、Geminiで整形します。
    """
    sente = json_data.get('sente', '不明')
    gote = json_data.get('gote', '不明')
    
    processed_lines = []

    for move in json_data.get('moves', []):
        move_number = move.get('move_number')
        comments = move.get('comments') or []

        # コメントがリスト形式の場合、結合して単一の文字列にする
        if all(isinstance(c, str) and len(c) == 1 for c in comments):
            full_comment = ''.join(comments).strip()
            if full_comment:
                # client オブジェクトを渡すように変更
                cleaned_comment = clean_comment_with_gemini(client, sente, gote, move_number, full_comment)
                if cleaned_comment:
                    processed_lines.append(cleaned_comment)
        else:
            for comment_item in comments:
                if isinstance(comment_item, str) and comment_item.strip():
                    # client オブジェクトを渡すように変更
                    cleaned_comment = clean_comment_with_gemini(client, sente, gote, move_number, comment_item.strip())
                    if cleaned_comment:
                        processed_lines.append(cleaned_comment)
    return processed_lines

def main():
    input_directory = './DataSet'  # JSONファイルがあるディレクトリ
    output_directory = './ProcessedComments' # 整形後のコメントを保存するディレクトリ

    # 出力ディレクトリが存在しない場合は作成
    os.makedirs(output_directory, exist_ok=True)

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

        # 既に整形済みファイルが存在するかチェック
        if os.path.exists(output_path):
            print(f"スキップ中: {json_file} - 既に整形済みファイルが存在します ({output_file_name})")
            print("-" * 30)
            continue # 次のファイルへ

        file_path = os.path.join(input_directory, json_file)
        print(f"処理中: {file_path}")
        
        data = load_json_file(file_path)
        if data:
            # client オブジェクトを渡すように変更
            processed_comments = process_shogi_json(client, data) 
            
            with open(output_path, 'w', encoding='utf-8') as f:
                for line in processed_comments:
                    f.write(line + '\n')
            print(f"整形結果を保存しました: {output_path}")
        print("-" * 30)

if __name__ == '__main__':
    main()