"""
    生成されたコメントファイルから、手数コメントを抽出して新しいファイルに保存するスクリプト    
"""


import os
import re

input_dir = './ProcessedComments_think'

txt_files = [f for f in os.listdir(input_dir) if f.endswith('.txt')]

if not txt_files:
    print(f"{input_dir} に TXT ファイルが見つかりません。")
else:
    for txt_file in txt_files:
        input_path = os.path.join(input_dir, txt_file)
        output_path = os.path.join(input_dir, f"{os.path.splitext(txt_file)[0]}_comments.txt")

        with open(input_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        comments = []
        current_comment = ""
        inside_comment = False

        for line in lines:
            line = line.strip()
            # 「手数n: 」で始まる行
            if re.match(r'^手数\d+:', line):
                # すでにコメントを作っていたら追加
                if current_comment:
                    comments.append(current_comment)
                current_comment = line  # 新しい手数コメント開始
                inside_comment = True
            # 「削除理由:」で始まる行はスキップ
            elif line.startswith('削除理由:'):
                inside_comment = False
            # 削除理由の中の行もスキップ
            elif inside_comment:
                current_comment += " " + line  # コメントに追加
            # 削除理由の中は何もしない
            else:
                continue

        # 最後のコメントを追加
        if current_comment:
            comments.append(current_comment)

        # 出力ファイルに書き込む
        with open(output_path, 'w', encoding='utf-8') as f:
            for comment in comments:
                f.write(comment + "\n")

        print(f"Processed and saved: {output_path}")
