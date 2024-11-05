def sfen_to_board(sfen):
    """ SFEN表記を解析し、盤面、手番、持ち駒、手数を返す関数 """
    # SFEN表記をスペースで分割して、各情報を取得
    board_sfen, turn, captured_pieces, move_count = sfen.split(" ")

    # 1. 盤面部分の変換
    rows = board_sfen.split("/")
    board = []
    for row in rows:
        board_row = []
        for char in row:
            if char.isdigit():
                # 数字なら、その分だけ空マスを追加
                board_row.extend(['.' for _ in range(int(char))])
            else:
                # それ以外は駒をそのまま追加
                board_row.append(char)
        board.append(board_row)

    # 3. 持ち駒の変換
    pieces_count = {}
    if captured_pieces != "-":  # "-" は持ち駒がないことを示す
        count = ""
        for char in captured_pieces:
            if char.isdigit():
                count += char  # 数字を読み取る
            else:
                pieces_count[char] = int(count) if count else 1  # 駒とその数を追加
                count = ""  # 次の駒に備えてリセット

    # 4. 手数の取得
    move_number = int(move_count)

    return board, turn, pieces_count, move_number

def turn_to_turn_player(turn):
    # 2. 手番情報の取得 ("b" なら先手, "w" なら後手)
    turn_player = "先手" if turn == "b" else "後手"
    return turn_player

# 初期局面のSFEN表記
initial_sfen = "lnsgkgsnl/1r5b1/ppppppppp/9/9/9/PPPPPPPPP/1B5R1/LNSGKGSNL b - 1"
board, turn, captured_pieces, move_number = sfen_to_board(initial_sfen)

# 盤面の表示
def display_board(board):
    print("   9  8  7  6  5  4  3  2  1")
    letters = "abcdefghi"
    for i, row in enumerate(board, start=1):
        row_str = f"{letters[i - 1]}  " + "  ".join(row)
        print(row_str)

display_board(board)
print(f"手番: {turn_to_turn_player(turn)}")
print(f"持ち駒: {captured_pieces}")
print(f"手数: {move_number}")
print(board)


def board_to_sfen(board, turn="b", hand_pieces=None, move_count=1):
    """ 盤面の駒配置をSFEN表記に変換 """
    sfen_board = []
    for row in board:
        empty_count = 0
        row_sfen = ""
        for cell in row:
            if cell.strip() == ".":
                empty_count += 1
            else:
                if empty_count > 0:
                    row_sfen += str(empty_count)
                    empty_count = 0
                # 駒をSFEN用に変換
                piece = cell.strip()  # 前後のスペースを取り除く
                if piece.isupper():  # Player側の駒
                    row_sfen += piece[0]
                else:  # Opponent側の駒は小文字
                    row_sfen += piece[0].lower()
        if empty_count > 0:
            row_sfen += str(empty_count)
        sfen_board.append(row_sfen)

    # 盤面行ごとに '/' で区切る
    sfen_board_str = "/".join(sfen_board)

    # 2. 持ち駒を表現
    if not hand_pieces:
        hand_pieces_str = "-"
    else:
        hand_pieces_str = ""
        for piece, count in hand_pieces.items():
            hand_piece = piece[0].upper() if count > 0 else piece[0].lower()
            hand_pieces_str += f"{hand_piece}{count}" if count > 1 else hand_piece

    # 3. 最終SFEN文字列を構築
    sfen_str = f"{sfen_board_str} {turn} {hand_pieces_str} {move_count}"
    return sfen_str

sfen = board_to_sfen(board, turn, captured_pieces, move_number)
print(sfen)