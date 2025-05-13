import re

def parse_kif_file(file_path):
    with open(file_path, encoding='utf-8') as f:
        lines = f.readlines()

    sente = None
    gote = None
    moves = []
    move_comments = []
    other_comments = []

    i = 0
    while i < len(lines):
        line = lines[i].strip()

        if line.startswith("先手："):
            sente = line.split("：")[1]
        elif line.startswith("後手："):
            gote = line.split("：")[1]
        elif re.match(r'^\d+[:\s]', line):
            # 棋譜行： '1: ７六歩(77)' など
            move_part = re.sub(r'^\d+[:\s]+', '', line)
            move_clean = re.sub(r'\(.*?\)', '', move_part).strip()
            move_clean = move_clean.replace('　', '')  # 全角スペースを消す

            moves.append(move_clean)

            # 次の行に続けて * コメントがある場合すべて連結
            comment_lines = []
            j = i + 1
            while j < len(lines) and lines[j].strip().startswith("*"):
                comment_line = lines[j].strip()[1:].strip()
                comment_lines.append(comment_line)
                j += 1
            if comment_lines:
                move_comments.append("\n".join(comment_lines))
                i = j - 1  # コメント行分をスキップ
            else:
                move_comments.append(None)
        elif line.startswith("*"):
            other_comments.append(line[1:].strip())

        i += 1

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

print("\n棋譜とコメント:")
for i, move in enumerate(result["moves"], 1):
    comment = result["move_comments"][i - 1]
    print(f"{i}: {move}")
    if comment:
        print(f"   コメント: {comment}")

print("\nその他のコメント:")
for i, comment in enumerate(result["other_comments"], 1):
    print(f"{i}: {comment}")
