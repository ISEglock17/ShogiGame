import re

def parse_kif_file(file_path):
    with open(file_path, encoding='utf-8') as f:
        lines = f.readlines()

    sente = None
    gote = None
    moves = []
    move_comments = []
    other_comments = []

    for i, line in enumerate(lines):
        line = line.strip()

        if line.startswith("先手："):
            sente = line.split("：")[1]
        elif line.startswith("後手："):
            gote = line.split("：")[1]
        elif line.startswith("*"):
            other_comments.append(line[1:].strip())
        elif re.match(r'^\d+[:\s]', line):
            # 例: '1: ７六歩(77)   ( 0:21/00:00:21)' or '2: ２八金打'
            # 手数部分を除去して、指し手だけを抜き出す
            move_part = re.sub(r'^\d+[:\s]+', '', line)  # 先頭の "1: " や "2 " を消す
            move_clean = re.sub(r'\(.*?\)', '', move_part).strip()  # "(77)" や時間を削除
            move_clean = move_clean.replace('　', '')  # 全角スペースをなくす
            move_clean = move_clean.strip()

            if move_clean:
                moves.append(move_clean)

                # もし次の行にコメントがあれば、それを対応する指し手のコメントとして追加
                if i + 1 < len(lines) and lines[i + 1].startswith('*'):
                    move_comments.append(lines[i + 1][1:].strip())
                else:
                    move_comments.append(None)  # コメントなしの場合はNone

    return {
        "sente": sente,
        "gote": gote,
        "moves": moves,
        "move_comments": move_comments,
        "other_comments": other_comments
    }

# 実行
result = parse_kif_file("./ShogiData/10001.txt")

print("先手:", result["sente"])
print("後手:", result["gote"])

print("\n棋譜:")
for i, move in enumerate(result["moves"], 1):
    comment = result["move_comments"][i - 1]
    print(f"{i}: {move}  {comment if comment else ''}")

print("\nその他のコメント:")
for i, comment in enumerate(result["other_comments"], 1):
    print(f"{i}: {comment}")
