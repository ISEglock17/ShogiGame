import os
import re

# 入出力ディレクトリの設定
input_directory = './ProcessedComments_reason_moves'
output_directory = './ProcessedComments_reason_comments_moves'
os.makedirs(output_directory, exist_ok=True)

# 正規表現パターン
tessu_header_pattern = re.compile(r'^手数\d+:')
削除見出し_pattern = re.compile(r'^削除理由[:：]')

# ファイルごとに処理
for filename in os.listdir(input_directory):
    if not filename.endswith('.txt'):
        continue

    input_path = os.path.join(input_directory, filename)
    output_path = os.path.join(output_directory, filename)

    with open(input_path, 'r', encoding='utf-8') as infile:
        lines = infile.readlines()

    output_blocks = []
    current_block = []
    collecting = False
    skipping = False  # 削除理由以降をスキップするフラグ

    for line in lines:
        stripped = line.strip()

        # 「手数n: 削除理由:」のような行は「手数n:」だけ抽出してブロック開始＆即終了
        if tessu_header_pattern.match(stripped) and '削除理由' in stripped:
            tessu_only = stripped.split('削除理由')[0].strip()
            if tessu_only:
                if current_block:
                    output_blocks.append('\n'.join(current_block))
                    current_block = []
                output_blocks.append(tessu_only)  # ここで直接ブロックとして追加
                collecting = False
                skipping = False
            continue

        # 「手数n:」で新しいブロック開始
        if tessu_header_pattern.match(stripped):
            if current_block:
                output_blocks.append('\n'.join(current_block))
                current_block = []
            current_block.append(stripped)
            collecting = True
            skipping = False
            continue

        # 「削除理由:」で以降をスキップ（次の手数n:まで）
        if 削除見出し_pattern.match(stripped):
            collecting = False
            skipping = True
            if current_block:
                output_blocks.append('\n'.join(current_block))
                current_block = []
            continue

        # 手数n:が来るまでスキップ
        if skipping:
            continue

        # 空行でブロック終了
        if collecting and not stripped:
            collecting = False
            if current_block:
                output_blocks.append('\n'.join(current_block))
                current_block = []
            continue

        # コメント行を追加
        if collecting:
            current_block.append(stripped)

    # 最後に残っていれば追加
    if current_block:
        output_blocks.append('\n'.join(current_block))

    # 出力
    with open(output_path, 'w', encoding='utf-8') as outfile:
        for block in output_blocks:
            outfile.write(block + '\n\n')

    print(f"{filename} → コメント抽出完了 → {output_path}")
