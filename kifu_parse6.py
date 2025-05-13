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
            num_and_rest = re.sub(r'^\d+[:\s]+', '', line)

            # 指し手と時間に分ける（例：７六歩(77)   ( 0:21/00:00:21)）
            move_match = re.match(r'(.+?)\s+\(([^)]+)\)', num_and_rest)
            if move_match:
                move_part = move_match.group(1)
                time_info = move_match.group(2)
            else:
                move_part = num_and_rest
                time_info = None

            # 移動元の抽出：末尾が"(77)"のような形かどうか確認
            from_pos_match = re.search(r'(.+?)\((\d\d)\)', move_part)
            if from_pos_match and '打' not in move_part:
                move_clean = from_pos_match.group(1).replace('　', '').replace(' ', '')
                from_pos = from_pos_match.group(2)
            else:
                move_clean = move_part.replace('　', '').replace(' ', '')
                from_pos = None

            # 時間の整形
            time_spent, total_time = None, None
            if time_info and '/' in time_info:
                time_parts = time_info.split('/')
                if len(time_parts) == 2:
                    time_spent = time_parts[0].strip()
                    total_time = time_parts[1].strip()

            moves.append({
                "move": move_clean,
                "from_pos": from_pos,
                "time_spent": time_spent,
                "total_time": total_time
            })

            # コメント取得
            comment_lines = []
            j = i + 1
            while j < len(lines) and lines[j].strip().startswith("*"):
                comment_lines.append(lines[j].strip()[1:].strip())
                j += 1
            move_comments.append("\n".join(comment_lines) if comment_lines else None)
            i = j - 1

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



def kifu_to_sfen(result):
    for i, move_info in enumerate(result["moves"], 1):
        move = move_info["move"]
        from_pos = move_info["from_pos"]
        time_spent = move_info["time_spent"]
        total_time = move_info["total_time"]
        comment = result["move_comments"][i - 1]
    



# 実行
result = parse_kif_file("./ShogiData/10001.txt")

print("先手:", result["sente"])
print("後手:", result["gote"])

print("\n棋譜とコメント:")
for i, move_info in enumerate(result["moves"], 1):
    move = move_info["move"]
    from_pos = move_info["from_pos"]
    time_spent = move_info["time_spent"]
    total_time = move_info["total_time"]
    comment = result["move_comments"][i - 1]

    print(f"{i}: {move}")
    print(f"   移動元: {from_pos}, 消費時間: {time_spent}, 累積時間: {total_time}")
    if comment:
        print(f"   コメント: {comment}")

print("\nその他のコメント:")
for i, comment in enumerate(result["other_comments"], 1):
    print(f"{i}: {comment}")


print(result)