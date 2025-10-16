import os
import json

def load_json_file(file_path):
    """JSONファイルを読み込む"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def extract_comments(data):
    """手数とコメントを抽出し、文ごとにまとめる"""
    lines = []
    lines.append(f"先手: {data.get('sente', '不明')}")
    lines.append(f"後手: {data.get('gote', '不明')}")
    for move in data.get('moves', []):
        move_number = move.get('move_number')
        comments = move.get('comments') or []

        # 文字のリスト（例: ['あ', 'い', 'う']）になっている場合は結合
        if all(isinstance(c, str) and len(c) == 1 for c in comments):
            full_comment = ''.join(comments).strip()
            if full_comment:
                lines.append(f'手数 {move_number}: {full_comment}')
        else:
            for comment in comments:
                if isinstance(comment, str) and comment.strip():
                    lines.append(f'手数 {move_number}: {comment.strip()}')
    return lines

def save_to_text_file(lines, output_path):
    """抽出したコメントをテキストファイルに保存"""
    with open(output_path, 'w', encoding='utf-8') as f:
        for line in lines:
            f.write(line + '\n')

def process_json_files(input_dir, output_dir, target_files=None):
    """指定されたJSONファイル群を処理してコメントテキストを出力"""
    os.makedirs(output_dir, exist_ok=True)  # 出力フォルダがなければ作成

    # target_filesがNoneならDataSet内の全ファイルを処理
    all_files = [f for f in os.listdir(input_dir) if f.endswith('.json')]
    if target_files:
        all_files = [f"{name}.json" for name in target_files if f"{name}.json" in all_files]

    if not all_files:
        print("処理対象のファイルが見つかりません。")
        return

    for filename in all_files:
        input_path = os.path.join(input_dir, filename)
        basename = os.path.splitext(filename)[0]
        output_path = os.path.join(output_dir, f"{basename}_comments.txt")

        try:
            data = load_json_file(input_path)
            lines = extract_comments(data)
            save_to_text_file(lines, output_path)
            print(f"✅ {filename} → {output_path}")
        except Exception as e:
            print(f"⚠️ {filename} の処理中にエラー発生: {e}")

def main():
    input_dir = './DataSet'       # JSONファイルのあるディレクトリ
    output_dir = './DataSetComments'  # コメントテキストの出力先ディレクトリ
    
    # 処理したいファイル名（拡張子なし）をリストで指定（例: [10006, 10007]）
    target_files = None  # 例: ['10006', '10010'] など。Noneなら全ファイル処理。
    process_json_files(input_dir, output_dir, target_files=target_files)

if __name__ == '__main__':
    main()
