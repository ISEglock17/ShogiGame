import json

def simplify_json(input_path, output_path):
    """
    指定された入力JSONファイルを読み込み、必要な情報だけを抽出して
    出力JSONファイルに書き出す。
    """
    # 入力ファイルを読み込み
    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # 新しい構造を作成
    simplified_data = {
        "sente": data["sente"],
        "gote": data["gote"],
        "other_comments": data["other_comments"],
        "moves": []
    }

    # 各手の情報を簡略化
    for move in data["moves"]:
        simplified_move = {
            "sfen": move["sfen"],
            "turn": move["turn"],
            "captured_pieces": move["captured_pieces"],
            "move_number": move["move_number"],
            "comments": move.get("comments", [])
        }
        simplified_data["moves"].append(simplified_move)

    # 出力ファイルに書き出し
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(simplified_data, f, ensure_ascii=False, indent=2)


def main():
    # 入力ファイルと出力ファイルのパスを設定
    input_path = "./DataSet/10006.json"   # 入力ファイルのパス
    output_path = "./PromptText/10006_parsed.json" # 出力ファイルのパス

    # JSONファイルを簡略化
    simplify_json(input_path, output_path)
    print(f"簡略化したJSONが {output_path} に保存されました。")


if __name__ == "__main__":
    main()
