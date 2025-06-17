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

def main():
    input_path = './DataSet/10000.json'   # ← JSONファイルのパスを指定
    output_path = './PromptText/10000_comments.txt'       # ← 出力先テキストファイル名を指定
    data = load_json_file(input_path)
    lines = extract_comments(data)
    save_to_text_file(lines, output_path)

if __name__ == '__main__':
    main()
