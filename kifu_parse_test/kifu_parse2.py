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
        elif re.match(r'^\d+\s', line):  # 「10 同　歩(23)」など
            match = re.match(r'^(\d+)\s+(.+?)(?:\([0-9]+\))?\s*$', line)
            if match:
                move_num = match.group(1)
                move = match.group(2).strip()
                moves.append(move)

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
