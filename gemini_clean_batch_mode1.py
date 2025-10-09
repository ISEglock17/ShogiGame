"""
    gemini_clean_reason2の派生版
    バッチモードを有効にするためのバックアップ版
    まだ一手ごとに処理を行っているため，ここから改良する。
"""

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

以下に対象コメントを示します：
手数{move_number}: {comment_text}

■ 入出力例: 
---
入力コメント1:
手数 1: 大平 武洋六段は1977年5月11日生まれ、東京都北区出身。桐谷広人七段門下。2002年、四段。2016年、六段。棋士番号は243。

出力1:
（空行）
理由: 棋士の情報は不要なため。

---
入力コメント2:
手数 2: 後手は加瀬純一七段門下。

出力2:
（空行）
理由: 棋士の情報は不要なため。

---
入力コメント3:
手数 3: 先手の公式戦成績は２２７勝２４７敗（０．４７９）、昨年度成績は８勝２０敗（０．２８６）、本年度成績は１１勝１２敗（０．４７８）です。

出力3:
（空行）
理由: 戦績情報は不要なため。

---
入力コメント4:
手数 12: 常磐ホテルの見どころは日本庭園。春の桜や秋の紅葉など、四季折々の美しさを見せてくれる趣のある景色に心が揺さぶられる。
アメリカで発行されている『ジャーナル・オブ・ジャパニーズ・ガーデニング』という日本庭園・日本建築の専門誌が行っている日本庭園ランキングでは２０１２年と２０１３年に常磐ホテルの日本庭園が３位に選ばれている。このランキングは、庭園の知名度や由緒に関わらず、純粋に庭園の質で選出することが最大の特徴で、常磐ホテルの庭園が、歴史的価値を考慮に入れなくとも素晴らしいものであることを示している。

出力4:
（空行）
理由: 対局場所は不要。
---
入力コメント5:
手数 16: １１時４１分、佐藤は５４分の長考で飛車を浮いた。これで前例に合流している。
前例は昨年１０月に行われた▲佐々木勇気五段−△山本真也六段戦（竜王戦４組昇級者決定戦）。結果は先手が勝っている。

※局後の感想※
「△８四飛の長考は△３三金と比較しました」と佐藤。

出力5:
先手は飛車を浮いた。△８四飛は△３三金と比較した手なのかもしれない。
理由: 時間，前例に関する内容を削除した。局後の感想は，アドバイス，解説をするときの文体に変更した。

---
入力コメント6:
手数 7: 東京の対局立会人は所司和晴七段が務める。

出力6:
（空行）
理由: 棋士以外の人の情報，対局会場の情報は不要。

---
入力コメント7:
手数 8: 本局の中継ページのURL末尾は「１００００．ｈｔｍｌ」。名人戦棋譜速報で公開している棋譜は少なくとも9千局を超える。

出力7:
（空行）
理由: メタ情報は不要。

---
入力コメント8:
手数 15: 戦型は横歩取り。中座は△８五飛戦法の創始者として知られる。

出力8:
戦型は横歩取り。
理由: 棋士の情報は不要。戦法に言及していても，対局の盤面情報には関係ないから。

---
入力コメント9:
手数 18: △６二玉は比較的珍しい手。後手の作戦に注目したい。

出力9:
△６二玉は比較的珍しい手。後手の作戦に注目したい。

---
入力コメント10:
手数 19: 11分の考慮。

出力10:
（空行）
理由: 時間に関する内容は不要。

---
入力コメント11:
手数 20: 後手の代名詞ともいえる△８五飛。もっとも、一般的な△８五飛戦法とはすでに離れている。

出力11:
（空行）
理由: 棋士の過去データに基づく戦略は不要。また，一般的な△８五飛戦法という文は過去の前例に基づくものなので不要。

---
入力コメント12:
手数 21: 今月２日の竜王戦ランキング戦２組、▲橋本崇載八段−△佐藤天彦名人戦。以下の進行は△４二銀▲９六歩△９四歩△４八銀△２五飛▲２七歩。

出力12:
（空行）
理由: 前例に関する言及なため不要。以下の進行は以降も前例に基づく内容なので不要。

---
入力コメント13:
手数 22: 11時9分の着手。△4二銀までの消費時間は、先手25分、後手43分。

出力13:
（空行）
理由: 時間に関する内容なため不要。

---
入力コメント14:
手数 24: ここで先手が33分使って休憩に入った。

出力14:
（空行）

---
入力コメント15:
手数 25: 対局再開。

出力15:
（空行）

---
入力コメント16:
手数 28: 後手陣に金銀の浮き駒がなくなった。こうしておけば３三角が動いた後に▲３二飛成がない。後手の狙い筋のひとつには、△１五歩▲同歩△８八角成▲同銀に△５四角があるだろうか。「△３一金以外に待つ手が難しかったのかもしれません。△７二玉は玉飛接近の形になりますし、△７二銀も飛車が動いた後に８２の空間が気になりました」（所司七段）

出力16:
後手陣に金銀の浮き駒がなくなった。こうしておけば３三角が動いた後に▲３二飛成がない。後手の狙い筋のひとつには、△１五歩▲同歩△８八角成▲同銀に△５四角があるだろうか。△３一金以外に待つ手が難しかったのかもしれない。△７二玉は玉飛接近の形になるし、△７二銀も飛車が動いた後に８２の空間が気になる。

---
入力コメント17:
手数 29: １４時１８分の着手。▲２七歩までの消費時間は、先手２時間２８分、後手１時間８分。

出力17:
（空行）

---
入力コメント18:
手数 34: 後手は美濃囲いに収まった。３筋と４筋にも同じ形の防壁がある。

出力18:
後手は美濃囲いに収まった。３筋と４筋にも同じ形の防壁がある。

---
入力コメント19:
手数 35: 8五飛型は▲7七桂が常に飛車取りになる。もっとも、この場合は後手も玉飛接近の懸念を解消できる面がある。

出力19:
8五飛型は▲7七桂が常に飛車取りになる。もっとも、この場合は後手も玉飛接近の懸念を解消できる面がある。

---
入力コメント20:
手数 39: 先手は１歩を犠牲にして飛車を転換。横歩取りは序盤に先手が１歩得になるので、１枚渡しても駒割りは互角だ。

出力20:
先手は１歩を犠牲にして飛車を転換。横歩取りは序盤に先手が１歩得になるので、１枚渡しても駒割りは互角だ。

---
入力コメント21:
手数 41: 先手は馬を作りにいく。後手は受けにくい。

出力21:
先手は馬を作りにいく。後手は受けにくい。

---
入力コメント22:
手数25: 昼食休憩後の指し手。

出力22:
（空行）
理由: 休憩に関する内容は不要。

---
入力コメント23:
手数62: △９五歩▲同飛を入れた効果がまだわかっていない。先手は時間を使っている。

出力23:
△９五歩▲同飛を入れた効果がまだわかっていない。
理由: 時間に関する内容は不要。

---
入力コメント24:
手数4: Ｃ級２組は上位３人が昇級する。藤井聡太六段が前節までに昇級を決め、残り２枠を７人が争っている。後手の昇級条件は「自身が勝ち、都成竜馬四段、増田康宏五段、石井健太郎五段のうち２人が敗れること」。

出力24:
（空行）
理由: 大会情報，昇給条件に関する内容は不要。

---
入力コメント25:
手数10: 現局面で先手の成績は１１勝３０敗１持将棋。持将棋を挟んで１６連敗中と苦戦している。後手の成績は２勝６敗。

出力25:
（空行）
理由: 成績に関する内容は不要。

---
入力コメント26:
手数9: ３０秒とかけずに横歩を取った。

出力26:
横歩を取った。
理由: 時間に関する内容は不要。

---
入力コメント27:
手数37: ▲６六角は９筋の突き合いがない形で過去に指されている。△８二飛は▲３三角成△同銀▲２一飛成と侵入される。手筋は△７五歩だ。

出力27:
△８二飛は▲３三角成△同銀▲２一飛成と侵入される。手筋は△７五歩だ。
理由: 過去の前例に関する内容は不要。

---
入力コメント28:
手数 18: 関係者一行は昨日１６時前に現地に到着。初めに厳重な持ち物チェックが行われ、続いて１６時５０分頃から行われた検分は滞りなく数分で終わった。検分の開始前には、立会人の高橋九段が両者に気さくに話しかける場面が見られた。
１８時からは関係者による夕食会が行われた。冒頭で来賓の岸川仁和・甲府市副市長から歓迎の挨拶があり、その後は両対局者をまじえて、ゆっくりと常磐ホテルの料理を楽しんだ。

出力28:
（空行）
理由: 対局場所や関係者の情報は不要。

---
入力コメント29:
手数25: １３時３０分を回り、対局再開。
盤の前で再開を待っていた稲葉は、再開が告げられるとすぐに角を上がった。
稲葉が指してから１分ほどして佐藤が入室。記録係から「指されました」と告げられ、「はい」と歯切れよく返事をした。

出力29
先手は角を上がった。
理由: 「１３時３０分を回り、対局再開。」は時間に関する内容なので，不要。「盤の前で再開を待っていた」は盤面と関係ない対局状況なので不要。「再開が告げられるとすぐに角を上がった。」は角を上がった以外，盤面と関係ない情報なので，削除した。「稲葉が指してから１分ほどして佐藤が入室。記録係から「指されました」と告げられ、「はい」と歯切れよく返事をした。」は盤面状況と関係ない対局室での様子なので削除した。

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

def clean_comment_with_gemini(client, sente_name: str, gote_name: str, moves_list: list) -> tuple:
    """
    moves_list: List[Tuple[move_number:int, comment_text:str]]
    受け取った全手のペアを引数として受け取るが、実際にAPIへ投げて処理するのは
    moves_list の最初の要素のみとする。
    戻り値: (result_line_or_empty:str, memo_lines:List[str])
    """
    print(moves_list)

    memo_lines = []
    if not moves_list:
        memo_lines.append("== 一手もデータがありません ==")
        return "", memo_lines

    # 全受け取り件数をメモに残す
    memo_lines.append(f"=== 総手数: {len(moves_list)} ===")

    # 最初の手だけ取り出す
    move_number, comment_text = moves_list[0]

    if not isinstance(comment_text, str) or not comment_text.strip():
        memo_lines.append(f"=== Gemini に送信するコメント===\n手数{move_number}: (空コメント)\n" + "="*60)
        return "", memo_lines

    # プロンプトは従来どおり最初の手を用いる（必要なら全体コンテキストを含めるよう拡張可能）
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
            model="gemini-2.5-flash",
            contents=contents,
            config=generate_content_config,
        ):
            if chunk.text is not None:
                full_response_text += chunk.text

        cleaned_text = full_response_text.strip()
        cleaned_text = re.sub(r"^(?:手数\s*\d+:\s*)+", "", cleaned_text).strip()

        # 既存の自動削除パターンを適用
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

        # コメントが空の場合の補完出力
        if not cleaned_text:
            result_line = f"手数{move_number}:\n削除理由:"
            return result_line, memo_lines

        shogi_move_indicators = ['▲', '△', '同', '成', '不成', '引', '寄', '直', '上', '右', '左', '打', '寄', '引', '直']
        if len(cleaned_text) < 5 and not any(c in cleaned_text for c in shogi_move_indicators):
            result_line = f"手数{move_number}:\n削除理由:"
            return result_line, memo_lines

        result_line = f"手数{move_number}: {cleaned_text}"
        result_line = re.sub(r"(手数\d+:)(削除理由:)", r"\1\n\2", result_line)
        return result_line, memo_lines

    except Exception as e:
        memo_lines.append(f"Gemini API呼び出し中にエラーが発生しました (手数 {move_number}): {e}")
        return "", memo_lines

def process_shogi_json(client, json_data):
    """
    1ファイル内の全手をまとめて clean_comment_with_gemini に渡すように変更。
    clean_comment_with_gemini は受け取った全ペアのうち最初の手だけを処理して返す。
    """
    sente = json_data.get('sente', '不明')
    gote = json_data.get('gote', '不明')
    processed_lines = []
    memo_lines = []

    # まずファイル内の全手ペアを収集
    moves_comments = []
    for move in json_data.get('moves', []):
        move_number = move.get('move_number')
        comments = move.get('comments') or []
        if isinstance(comments, str):
            comments = [comments]
        for comment_item in comments:
            if isinstance(comment_item, str) and comment_item.strip():
                moves_comments.append((move_number, comment_item.strip()))

    if not moves_comments:
        return processed_lines, memo_lines

    # 全手ペアを一度に渡す（関数内で最初の手のみ処理される）
    cleaned_comment, memo = clean_comment_with_gemini(client, sente, gote, moves_comments)
    
    if cleaned_comment:
        processed_lines.append(cleaned_comment)
    for line in memo:
        print(line)
    memo_lines.extend(memo)

    return processed_lines, memo_lines

def main():
    input_directory = './DataSet'
    output_directory = './ProcessedComments_reason'
    memo_directory = './ProcessedComments_reason_memo'
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