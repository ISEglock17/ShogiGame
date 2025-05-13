import re

def parse_kif_file(file_path):
    with open(file_path, encoding='utf-8') as f:
        lines = f.readlines()

    sente = None
    gote = None
    moves = []
    comments = []

    for line in lines:
        line = line.strip()

        if line.startswith("先手："):
            sente = line.split("：")[1]
        elif line.startswith("後手："):
            gote = line.split("：")[1]
        elif line.startswith("*"):
            comments.append(line[1:].strip())
        elif re.match(r'^\d+[:\s]', line):
            # 例: '1: ７六歩(77)   ( 0:21/00:00:21)' or '2: ２八金打'
            # 手数部分を除去して、指し手だけを抜き出す
            move_part = re.sub(r'^\d+[:\s]+', '', line)  # 先頭の "1: " や "2 " を消す
            move_clean = re.sub(r'\(.*?\)', '', move_part).strip()  # "(77)" や時間を削除
            if move_clean:
                moves.append(move_clean)

    return {
        "sente": sente,
        "gote": gote,
        "moves": moves,
        "comments": comments
    }

# 実行
result = parse_kif_file("./ShogiData/10001.txt")

print("先手:", result["sente"])
print("後手:", result["gote"])

print("\n棋譜:")
for i, move in enumerate(result["moves"], 1):
    print(f"{i}: {move}")

print("\nコメント:")
for i, comment in enumerate(result["comments"], 1):
    print(f"{i}: {comment}")
