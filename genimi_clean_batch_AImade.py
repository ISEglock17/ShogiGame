# バッチモードで将棋の対局コメントをGemini APIで整形するスクリプト

# To run this code you need to install the following dependencies:
# pip install google-genai  (Note: This is the new client library, not google-generativeai)

import json
import os
# from google import genai  # 'genai' is now directly imported from 'google'
from google import genai # Changed to import genai as a module, not from google.genai
from google.genai import types
import re
import argparse

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
1. 対局者以外の棋士の名前・段位・門下情報（例:「高橋九段」「所司和晴七段」など）
2. 前例や過去の対局に関する記述（例:「前例は〜」「昨年の対局では〜」など）
3. 時間情報（例:「11時9分」「43分の考慮」など）
4. 対局者プロフィールや戦績、段位、棋士番号、門下（例:「先手四段」「公式戦成績〜」「所属〜」「生年月日〜」など）
5. 棋風や戦型の傾向（例:「居飛車党」「中座は〜戦法の創始者」など）
6. 対局場所・天候・ホテル等の情報（例:「甲府市で」「快晴の空の下」など）
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
手数 28: 後手陣に金銀の浮き駒がなくなった。こうしておけば３三角が動いた後に▲３二飛成がない。後手の狙い筋のひとつには、△１五歩▲同歩△８八角成▲同銀に△５四角があるだろうか。「△３一金以外に待つ手が難しかったのかもしれません。△７二玉は玉飛接近の形になりますし、△７二銀も飛車が動いた後に８二の空間が気になりました」（所司七段）

出力16:
後手陣に金銀の浮き駒がなくなった。こうしておけば３三角が動いた後に▲３二飛成がない。後手の狙い筋のひとつには、△１五歩▲同歩△８八角成▲同銀に△５四角があるだろうか。△３一金以外に待つ手が難しかったのかもしれない。△７二玉は玉飛接近の形になるし、△７二銀も飛車が動いた後に８二の空間が気になる。

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

以下に対象のコメントを示します：
先手: {sente_name}
後手: {gote_name}
手数 {move_number}: {comment_text}
"""

def load_json_file(file_path):
    """JSONファイルを読み込む。JSONDecodeError の場合は周辺表示と簡易修復を試みる。"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"エラー: ファイルが見つかりません - {file_path}")
        return None
    except json.JSONDecodeError as e:
        print(f"JSONDecodeError in {file_path}: {e.msg} (line {e.lineno} col {e.colno} pos {getattr(e, 'pos', 'N/A')})")
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        except Exception as e2:
            print(f"Failed to read file for recovery: {e2}")
            return None

        pos = getattr(e, 'pos', 0)
        start = max(0, pos - 200)
        end = min(len(content), pos + 200)
        snippet = content[start:end]
        print("--- JSON error context ---")
        print(snippet.replace('\n', '\\n'))
        print("--- end context ---")

        # attempt a few heuristics to fix common issues
        attempts = []

        # 1) remove control chars
        s1 = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", content)
        attempts.append(("remove-control-chars", s1))

        # 2) remove trailing commas
        s2 = re.sub(r",\s*(?=[}\]])", "", s1)
        attempts.append(("remove-trailing-commas", s2))

        # 3) python literals -> json literals
        s3 = re.sub(r"\bTrue\b", "true", s2)
        s3 = re.sub(r"\bFalse\b", "false", s3)
        s3 = re.sub(r"\bNone\b", "null", s3)
        attempts.append(("py-literals", s3))

        # 4) naive single-quote to double-quote conversion for value strings
        def _single_quote_repl(m):
            prefix = m.group('prefix')
            body = m.group('body')
            # escape any double quotes in the body
            body_escaped = body.replace('"', '\\"')
            return prefix + '"' + body_escaped + '"'

        s4 = re.sub(r"(?P<prefix>[:\s,\[{])'(?P<body>[^']*)'", _single_quote_repl, s3)
        attempts.append(("single-quotes-heuristic", s4))

        # 5) quote unquoted object keys: { key: value } -> { "key": value }
        s5 = re.sub(r'([\{,]\s*)([A-Za-z_][A-Za-z0-9_]*)\s*:', r'\1"\2":', s4)
        attempts.append(("quote-unquoted-keys", s5))

        for tag, txt in attempts:
            try:
                parsed = json.loads(txt)
                print(f"Recovered JSON by: {tag}")
                return parsed
            except Exception as e3:
                print(f"Attempt {tag} failed: {type(e3).__name__}: {e3}")

        print(f"All recovery attempts failed for {file_path}; skipping file.")
        return None
    except Exception as e:
        print(f"Error reading JSON file ({file_path}): {e}")
        return None


def file_may_have_comments(file_path, search_bytes=5*1024*1024):
    """高速チェック: ファイル中に '"comments"' が出現するかを探索する。
    JSON 全体をパースせずに存在を確認するための軽量スキャン。
    search_bytes: 最初に読むバイト数（デフォルト1MB）。ファイルが大きくても
    最初の範囲で見つからなければ追加でストリーム的に探す。
    """
    needle = '"comments"'
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            # Read in chunks and search; keep overlap for boundary matches
            chunk_size = 64 * 1024
            total_read = 0
            prev_tail = ''
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                total_read += len(chunk)
                hay = prev_tail + chunk
                if needle in hay:
                    return True
                # keep tail to match across boundary
                prev_tail = hay[-len(needle):]
                # stop early if we've read enough bytes
                if total_read >= search_bytes:
                    break
        return False
    except Exception:
        # On error, be conservative and return True so we attempt parse
        return True
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
    print(f"=== Gemini に送信するコメント===")
    print(f'手数{move_number}: {comment_text}')

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

        print(f'→  手数{move_number}: {cleaned_text}')
        print("=" * 60)

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
                if isinstance(comment_item, str) and comment_item.strip() and comment_item != 'config':
                    # client オブジェクトを渡すように変更
                    cleaned_comment = clean_comment_with_gemini(client, sente, gote, move_number, comment_item.strip())
                    if cleaned_comment:
                        processed_lines.append(cleaned_comment)
    return processed_lines


def run_request_via_models(client, request_obj, model_name):
    """
    Run a single GenerateContentRequest-like dict via the models.generate_content_stream
    and return the concatenated text response. This avoids using the Batches API for
    inline processing and prevents errors where the Batch client expects a different
    src shape.
    request_obj: dict with keys 'contents' (list of dicts with 'role' and 'parts')
    """
    try:
        contents = []
        for c in request_obj.get('contents', []):
            parts = []
            for p in c.get('parts', []):
                text = p.get('text') if isinstance(p, dict) else p
                parts.append(types.Part.from_text(text=text))
            contents.append(types.Content(role=c.get('role', 'user'), parts=parts))

        cfg = request_obj.get('config', {}) or {}
        response_mime = cfg.get('response_mime_type', 'text/plain')
        generate_content_config = types.GenerateContentConfig(
            thinking_config=types.ThinkingConfig(thinking_budget=0),
            response_mime_type=response_mime,
        )

        full_text = ''
        for chunk in client.models.generate_content_stream(
            model=model_name,
            contents=contents,
            config=generate_content_config,
        ):
            if getattr(chunk, 'text', None):
                full_text += chunk.text

        return full_text
    except Exception as e:
        # If the error indicates the model is not found or unsupported for generateContent,
        # try to list available models and pick a sensible fallback, then retry once.
        err_str = str(e)
        if 'NOT_FOUND' in err_str or 'is not found' in err_str or 'not supported for generateContent' in err_str:
            print(f"Model {model_name} not found/supported for generateContent: {e}")
            try:
                print("Listing available models to find a fallback...")
                ml = client.models.list()
                candidates = []
                # ml may provide a .models attribute or be an iterable
                if hasattr(ml, 'models'):
                    for m in ml.models:
                        if hasattr(m, 'name'):
                            candidates.append(m.name)
                        else:
                            candidates.append(str(m))
                else:
                    for m in ml:
                        candidates.append(getattr(m, 'name', str(m)))

                print(f"Found models: {candidates[:10]}{'...' if len(candidates)>10 else ''}")
                pick = None
                for c in candidates:
                    if any(k in c for k in ('flash', 'preview', 'generate', '2.5', 'text')):
                        pick = c
                        break
                if not pick and candidates:
                    pick = candidates[0]

                if pick and pick != model_name:
                    print(f"Retrying with fallback model: {pick}")
                    return run_request_via_models(client, request_obj, pick)
            except Exception as e2:
                print(f"Failed to list models or retry: {e2}")
        # re-raise original exception if we couldn't recover
        raise

def main():
    parser = argparse.ArgumentParser(description='Gemini batch cleaning script')
    parser.add_argument('--inline', type=int, default=0, help='Send first N games as inline batch requests (for testing)')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose fast-scan logging')
    args = parser.parse_args()
    inline_count = args.inline
    verbose = args.verbose

    # バッチ実行モード: input_directory にある上位100局をまとめて処理
    input_directory = './DataSet'  # JSONファイルがあるディレクトリ
    output_directory = './ProcessedComments_reason_batch' # 整形後のコメントを保存するディレクトリ
    os.makedirs(output_directory, exist_ok=True)

    # genai.Client の初期化
    try:
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("環境変数 'GEMINI_API_KEY' が設定されていません。")
        client = genai.Client(api_key=api_key)
    except Exception as e:
        print(f"Gemini Clientの初期化に失敗しました。APIキーが正しく設定されているか確認してください。エラー: {e}")
        return

    # 入力ディレクトリの解決: カレントワーキングディレクトリの './DataSet' を優先し、
    # なければスクリプト本体と同じディレクトリにある 'DataSet' を試す
    script_dir = os.path.dirname(os.path.abspath(__file__))
    candidate1 = os.path.join(os.getcwd(), 'DataSet')
    candidate2 = os.path.join(script_dir, 'DataSet')

    resolved_input = None
    if os.path.isdir(candidate1):
        resolved_input = candidate1
    elif os.path.isdir(candidate2):
        resolved_input = candidate2
    else:
        # どちらにも存在しない場合は、スクリプトディレクトリに作成してユーザーに案内
        try:
            os.makedirs(candidate2, exist_ok=True)
            print(f"入力ディレクトリが見つかりませんでした。新しく作成しました: {candidate2}")
            print("DataSet に対局JSONファイルを配置してから再実行してください。")
        except Exception as e:
            print(f"入力ディレクトリの作成に失敗しました: {e}")
        return

    input_directory = resolved_input
    print(f"使用する入力ディレクトリ: {input_directory}")

    # 入力ディレクトリから上位100個のJSONファイルを取得（アルファベット順）
    # Prefer an explicit list of files that contain comments (one filename per line)
    # placed in DataSet/commented_file_list.txt. Each line may be a basename or
    # a relative/absolute path. If the file is absent or yields no valid files,
    # fall back to scanning the input directory for JSON files.
    # Look for commented_file_list.txt in the input directory first, then
    # in the script directory (where this script resides). Use the first
    # valid list found. Fall back to scanning the directory for JSON files.
    commented_list_candidates = [
        os.path.join(input_directory, 'commented_file_list.txt'),
    ]
    # script_dir is defined earlier when resolving input directory
    if 'script_dir' in locals():
        commented_list_candidates.append(os.path.join(script_dir, 'commented_file_list.txt'))

    json_files = []
    found_list = None
    for commented_list_path in commented_list_candidates:
        if os.path.isfile(commented_list_path):
            found_list = commented_list_path
            print(f"Found commented file list: {commented_list_path}. Using it to select files.")
            try:
                with open(commented_list_path, 'r', encoding='utf-8') as cf:
                    for ln in cf:
                        name = ln.strip()
                        if not name:
                            continue
                        if os.path.isabs(name):
                            candidate = name
                        else:
                            candidate = os.path.join(input_directory, name)

                        if os.path.isfile(candidate):
                            json_files.append(os.path.basename(candidate))
                        else:
                            if not candidate.lower().endswith('.json'):
                                candidate2 = candidate + '.json'
                                if os.path.isfile(candidate2):
                                    json_files.append(os.path.basename(candidate2))
            except Exception as e:
                print(f"Failed to read commented file list ({commented_list_path}): {e}")
            break

    if not json_files:
        if found_list is None:
            print("No commented_file_list.txt found; scanning directory for JSON files.")
        else:
            print("No valid entries found in commented_file_list.txt; scanning directory for JSON files.")
        json_files = sorted([f for f in os.listdir(input_directory) if f.endswith('.json')])
    if not json_files:
        print(f"'{input_directory}' ディレクトリにJSONファイルが見つかりませんでした。")
        return

    # JSONL 形式で1ファイルにまとめる。各行は1局分のプロンプト（局情報 + comments_block）を含むJSONオブジェクトとする。
    upload_lines = []
    mapping = []  # アップロード順 -> ローカルファイル名マッピング

    # For debugging: find the first file that actually has comments and
    # use an inline batch request for that single game. This avoids file
    # upload problems while iterating on format.
    first_game_inline_obj = None
    first_game_mapping = None
    for json_file in json_files:
        file_path = os.path.join(input_directory, json_file)
        # base_name is used in multiple places; define it immediately to avoid
        # UnboundLocalError when moves/comments are absent.
        base_name = os.path.splitext(json_file)[0]
        # Fast-scan for the string "comments" before attempting full JSON parse.
        if not file_may_have_comments(file_path):
            if verbose:
                print(f"fast-scan: comments not found, skipping parse: {json_file}")
            # ensure empty output file is created (same behavior as before)
            out_path = os.path.join(output_directory, f"{base_name}_batch_processed.txt")
            with open(out_path, 'w', encoding='utf-8') as f:
                f.write('')
            continue

        if verbose:
            print(f"fast-scan: candidate may contain comments; parsing: {json_file}")
        data = load_json_file(file_path)
        if not data:
            continue

        sente = data.get('sente', '不明')
        gote = data.get('gote', '不明')

        # moves をまとめて comments_block を作成
        moves_comments = []
        for move in data.get('moves', []):
            move_number = move.get('move_number')
            comments = move.get('comments') or []
            if isinstance(comments, str):
                comments = [comments]
            for comment in comments:
                if isinstance(comment, str) and comment.strip():
                    moves_comments.append((move_number, comment.strip()))

        if not moves_comments:
            # コメントがなければ出力ファイルは空にしておく
            base_name = os.path.splitext(json_file)[0]
            out_path = os.path.join(output_directory, f"{base_name}_batch_processed.txt")
            with open(out_path, 'w', encoding='utf-8') as f:
                f.write('')
            print(f"コメントがないためスキップ（空ファイル作成）: {json_file}")
            continue

        comments_block = ''
        for move_number, comment_text in moves_comments:
            comments_block += f"手数 {move_number}: {comment_text}\n"

        # Build the full prompt for this game using the template
        prompt_text = GEMINI_PROMPT_TEMPLATE.format(
            sente_name=sente,
            gote_name=gote,
            move_number='N/A',
            comment_text='',
        )
        # Replace the placeholder comments block by injecting it at the end of the prompt
        # (GEMINI_PROMPT_TEMPLATE ends with a place for comments_block in some templates)
        # For safety, append the comments block explicitly
        prompt_with_comments = prompt_text + "\n以下に対象のコメントを示します：\n" + comments_block

        # Each JSONL line must be {"key": "...", "request": <GenerateContentRequest>}
        # Build a GenerateContentRequest-like dict per line
        request_obj = {
            'contents': [
                {
                    'parts': [{ 'text': prompt_with_comments }],
                    'role': 'user'
                }
            ],
                'config': {
                    'response_mime_type': 'text/plain'
                }
        }

        line_obj = {
            'key': base_name,
            'request': request_obj
        }

        # Save to upload_lines/mapping for batch-file path
        upload_lines.append(json.dumps(line_obj, ensure_ascii=False))
        mapping.append((json_file, base_name))

        # If we haven't yet captured a first-game-for-inline, keep this one
        if first_game_inline_obj is None:
            first_game_inline_obj = line_obj['request']
            first_game_mapping = (json_file, base_name)

    if not upload_lines:
        print("アップロードするデータがありませんでした。")
        return

    # 一時アップロードファイルを作成
    tmp_upload_path = os.path.join(output_directory, 'tmp_shogi_batch_upload.jsonl')
    with open(tmp_upload_path, 'w', encoding='utf-8') as f:
        for line in upload_lines:
            f.write(line + '\n')

    # For quick debugging, prefer inline execution of the first game that
    # actually contained comments. This avoids uploading and lets us verify
    # the model and request shape quickly.
    if first_game_inline_obj is not None:
        try:
            print("Running inline request for first game with comments:", first_game_mapping)
            # Use direct models.generate_content_stream to avoid batches.create list/dict issues
            full_text = run_request_via_models(client, first_game_inline_obj, model_name='gemini-2.5-pro-latest')
            print("Inline request completed. Response length:", len(full_text))
            out_file = os.path.join(output_directory, f"{first_game_mapping[1]}_batch_processed.txt")
            with open(out_file, 'w', encoding='utf-8') as of:
                of.write(full_text + '\n')
            print(f"Saved inline output to: {out_file}")
            return
        except Exception as e:
            print(f"Inline request failed: {e}. Will fall back to file upload path.")

    # ファイルをアップロードしてバッチジョブを作成
    print(f"アップロードファイルを作成しました: {tmp_upload_path} （{len(upload_lines)} 件）")
    try:
        # client.files.upload を使用（既存の例に合わせる）
        uploaded = client.files.upload(
            file=tmp_upload_path,
            config=types.UploadFileConfig(display_name='shogi-batch-requests', mime_type='application/jsonl')
        )
        print(f"アップロード完了: {uploaded.name}")
    except Exception as e:
        print(f"ファイルアップロードに失敗しました: {e}")
        return

    # デバッグ情報: uploaded.name と tmp ファイルの先頭を表示
    print(f"uploaded.name = {uploaded.name}")
    try:
        with open(tmp_upload_path, 'r', encoding='utf-8') as tf:
            for i in range(5):
                line = tf.readline()
                if not line:
                    break
                print(f"tmp line {i+1}: {line.strip()}")
    except Exception as e:
        print(f"tmp ファイルの先頭読み込みに失敗: {e}")

    # モデルは環境変数でオーバーライド可能
    default_model = os.environ.get('GEMINI_BATCH_MODEL', 'gemini-2.5-flash')

    # デバッグ: uploaded オブジェクトの詳細を出力して中身を確認
    try:
        print("uploaded repr:", repr(uploaded))
        try:
            if hasattr(uploaded, 'to_json'):
                print("uploaded.to_json():", uploaded.to_json())
            if hasattr(uploaded, '__dict__'):
                print("uploaded.__dict__:", uploaded.__dict__)
        except Exception:
            pass
    except Exception:
        print("(unable to fully repr uploaded object)")

    # 試行する src 候補を複数用意する
    # batches.create expects a string-like source; passing dicts caused
    # "'dict' object has no attribute 'startswith'". Try string candidates
    # only: uploaded.name (short resource name) and uploaded.uri (full URL).
    src_candidates = [
        uploaded.name,
        (uploaded.uri if getattr(uploaded, 'uri', None) else uploaded.name),
    ]

    batch_job = None
    last_exception = None
    for idx, src_candidate in enumerate(src_candidates):
        try:
            print(f"Trying batches.create with src candidate #{idx+1}: {src_candidate}")
            batch_job = client.batches.create(
                model=default_model,
                src=src_candidate,
                config={'display_name': f'shogi-clean-batch-job-candidate-{idx+1}'},
            )
            print(f"Created batch job: {batch_job.name} (model={default_model}, src_candidate={idx+1})")
            break
        except Exception as e:
            last_exception = e
            print(f"batches.create attempt #{idx+1} failed: {e}")

    if batch_job is None:
        # すべての src 候補で失敗した場合、'Unsupported source' が返っていれば別モデルで最後の再試行
        if last_exception and 'Unsupported source' in str(last_exception):
            alt_model = 'gemini-2.5-flash'
            print(f"Unsupported source が全ての src 候補で返されたため、モデルを {alt_model} に切替えて最終再試行します...")
            try:
                batch_job = client.batches.create(
                    model=alt_model,
                    src=uploaded.name,
                    config={'display_name': 'shogi-clean-batch-job-alt-final'},
                )
                print(f"Created batch job with alternate model: {batch_job.name} (model={alt_model})")
            except Exception as e2:
                print(f"Alternate model retry failed: {e2}")
                print("All batch creation attempts failed. See last error for details.")
                # Fall back to per-game inline processing: read the tmp JSONL and
                # create a separate inline batch (src=[request]) for each game.
                print("Falling back to sequential per-game inline processing (slower).")
                try:
                    with open(tmp_upload_path, 'r', encoding='utf-8') as tf:
                        request_lines = [json.loads(l) for l in tf if l.strip()]
                except Exception as e3:
                    print(f"Failed to read tmp upload JSONL for inline fallback: {e3}")
                    return

                for idx, item in enumerate(request_lines):
                    key = item.get('key') or f'game_{idx}'
                    req = item.get('request')
                    if not req:
                        print(f"No request for {key}, skipping")
                        continue
                    print(f"[fallback] Running inline request for {key} ({idx+1}/{len(request_lines)}) using models.generate_content_stream")
                    try:
                        resp_text = run_request_via_models(client, req, model_name=default_model)
                    except Exception as e4:
                        print(f"Inline request failed for {key} with model {default_model}: {e4}")
                        try:
                            resp_text = run_request_via_models(client, req, model_name='gemini-2.5-flash')
                        except Exception as e5:
                            print(f"Alternate inline request failed for {key}: {e5}. Skipping.")
                            continue

                    out_file = os.path.join(output_directory, f"{key}_batch_processed.txt")
                    try:
                        with open(out_file, 'w', encoding='utf-8') as of:
                            of.write(resp_text + '\n')
                        print(f"Saved inline fallback output to: {out_file}")
                    except Exception as e7:
                        print(f"Failed to save output for {key}: {e7}")
                    # small pause between jobs
                    import time as _time
                    _time.sleep(1)

                print("Sequential inline fallback processing complete.")
                return
        else:
            print("All batch creation attempts failed. Last error:", last_exception)
            # same fallback as above when not Unsupported source
            print("Falling back to sequential per-game inline processing (slower).")
            try:
                with open(tmp_upload_path, 'r', encoding='utf-8') as tf:
                    request_lines = [json.loads(l) for l in tf if l.strip()]
            except Exception as e3:
                print(f"Failed to read tmp upload JSONL for inline fallback: {e3}")
                return

            completed_states_local = set(['JOB_STATE_SUCCEEDED', 'JOB_STATE_FAILED', 'JOB_STATE_CANCELLED', 'JOB_STATE_EXPIRED'])
            for idx, item in enumerate(request_lines):
                key = item.get('key') or f'game_{idx}'
                req = item.get('request')
                if not req:
                    print(f"No request for {key}, skipping")
                    continue
                print(f"[fallback] Running inline request for {key} ({idx+1}/{len(request_lines)}) using models.generate_content_stream")
                try:
                    resp_text = run_request_via_models(client, req, model_name=default_model)
                except Exception as e4:
                    print(f"Inline request failed for {key} with model {default_model}: {e4}")
                    try:
                        resp_text = run_request_via_models(client, req, model_name='gemini-2.5-flash')
                    except Exception as e5:
                        print(f"Alternate inline request failed for {key}: {e5}. Skipping.")
                        continue

                out_file = os.path.join(output_directory, f"{key}_batch_processed.txt")
                try:
                    with open(out_file, 'w', encoding='utf-8') as of:
                        of.write(resp_text + '\n')
                    print(f"Saved inline fallback output to: {out_file}")
                except Exception as e7:
                    print(f"Failed to save output for {key}: {e7}")
                # small pause between jobs
                import time as _time
                _time.sleep(1)

            print("Sequential inline fallback processing complete.")
            return

    # ポーリング
    import time
    completed_states = set(['JOB_STATE_SUCCEEDED', 'JOB_STATE_FAILED', 'JOB_STATE_CANCELLED', 'JOB_STATE_EXPIRED'])
    print(f"バッチジョブのステータスをポーリングします: {batch_job.name}")
    bj = client.batches.get(name=batch_job.name)
    while bj.state.name not in completed_states:
        print(f"Current state: {bj.state.name}")
        time.sleep(30)
        bj = client.batches.get(name=batch_job.name)

    print(f"Job finished with state: {bj.state.name}")
    if bj.state.name != 'JOB_STATE_SUCCEEDED':
        print(f"バッチ処理に失敗しました: {bj.state.name}")
        if hasattr(bj, 'error') and bj.error:
            print(f"Error: {bj.error}")
        return

    # 結果を取得
    if bj.dest and getattr(bj.dest, 'file_name', None):
        result_file_name = bj.dest.file_name
        print(f"結果ファイル: {result_file_name} をダウンロードします")
        content = client.files.download(file=result_file_name)
        # content は bytes
        result_path = os.path.join(output_directory, 'shogi_batch_results.jsonl')
        with open(result_path, 'wb') as f:
            f.write(content)
        print(f"結果を保存しました: {result_path}")

        # 結果は jsonl で各行がモデルの応答（プレーンテキスト）になっている想定
        # 各行を対応する入力ファイルごとに分割して保存する
        with open(result_path, 'r', encoding='utf-8') as f:
            lines = [l.strip() for l in f if l.strip()]

        if len(lines) != len(mapping):
            print(f"警告: 応答行数({len(lines)})とアップロード件数({len(mapping)})が一致しません。")

        for idx, (json_file, base_name) in enumerate(mapping):
            out_file = os.path.join(output_directory, f"{base_name}_batch_processed.txt")
            resp_line = lines[idx] if idx < len(lines) else ''
            # モデルはそのままテキストを返す想定。必要ならここで更に分割して個別の手にマッピング可能。
            with open(out_file, 'w', encoding='utf-8') as of:
                of.write(resp_line + '\n')
            print(f"出力を保存しました: {out_file}")
    else:
        print("バッチは成功しましたが、結果ファイルが見つかりませんでした。")

if __name__ == '__main__':
    main()