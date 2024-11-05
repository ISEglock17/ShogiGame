import subprocess
import threading
import time
import re


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

    # 2. 手番の変換

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


"""
# USIプロトコルでのSFEN例
sfen = "lnsgkgsnl/1r5b1/ppppppppp/9/9/9/PPPPPPPPP/1B5R1/LNSGKGSNL"

# 駒配置をリスト形式で取得
board = sfen_to_board(sfen)

# 表示
for row in board:
    print(" ".join(row))
"""

def board_to_sfen(board, turn="b", hand_pieces=None, move_count=1):
    """ 盤面の駒配置をSFEN表記に変換 """
    sfen_board = []
    for row in board:
        empty_count = 0
        row_sfen = ""
        for cell in row:
            if cell.strip == ".":
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

def turn_to_turn_player(turn):
    # 2. 手番情報の取得 ("b" なら先手, "w" なら後手)
    turn_player = "先手" if turn == "b" else "後手"
    return turn_player

"""
# テスト用コード
board = initialize_board()
sfen = board_to_sfen(board)
display_board(board)
print("\nSFEN:", sfen)
"""

"""
# 駒を英語の略称で表現
player_pieces = {
    "歩": " P ", "香": " L ", "桂": " N ", "銀": " S ", "金": " G ", "玉": " K ", "飛": " R ", "角": " B "
}
opponent_pieces = {k: f" {v.strip().lower()} " for k, v in player_pieces.items()}  # 相手の駒は小文字で表示

# 空白は半角スペースを使用
empty_square = " . "
"""

# 盤面の初期化
def initialize_board():
    # 初期局面のSFEN表記
    initial_sfen = "lnsgkgsnl/1r5b1/ppppppppp/9/9/9/PPPPPPPPP/1B5R1/LNSGKGSNL b - 1"
    return initial_sfen

# 盤面を表示
def display_board(sfen):
    board, turn, captured_pieces, move_number = sfen_to_board(sfen)
    print("   9  8  7  6  5  4  3  2  1")
    letters = "abcdefghi"
    
    # 盤面の各行を表示
    for i, row in enumerate(board, start=1):
        row_str = f"{letters[i - 1]}  " + "  ".join(row)
        print(row_str)
    
    # 手番の表示
    print("\n手番:", turn_to_turn_player(turn))

    # 持ち駒の表示
    print("持ち駒:", end=" ")
    if captured_pieces:
        # 駒と個数を一行で表示
        print(" ".join(f"{piece}{count}" for piece, count in captured_pieces.items()))
    else:
        print("なし")

    # 手数の表示
    print("手数:", move_number)
    
# 指し手を盤面に適用
def apply_move(sfen, move):
    board, turn, captured_pieces, move_number = sfen_to_board(sfen)
    try:
        # 指し手を座標に変換
        from_row, from_col = ord(move[1]) - ord('a'), 9 - int(move[0])
        to_row, to_col = ord(move[3]) - ord('a'), 9 - int(move[2])
        
        # 駒を移動
        piece = board[from_row][from_col]
        board[from_row][from_col] = " . "
        board[to_row][to_col] = piece
        return board_to_sfen(board, turn, captured_pieces, move_number)
    
    except (ValueError, IndexError):
        print(f"無効な指し手の形式です: {move}。 '7g7f' のように入力してください。")
        return -1

# やねうら王の応答を読み取る
def read_output(process, response_queue):
    while True:
        output = process.stdout.readline()
        if output == '' and process.poll() is not None:
            break
        if output:
            print(f"やねうら王の応答: {output.strip()}")
            if any(keyword in output for keyword in ["readyok", "bestmove", "Error"]):
                response_queue.append(output.strip())

# やねうら王を起動
def run_yaneuraou():
    executable_path = "./YaneuraOu_NNUE_halfKP256-V830Git_ZEN2.exe"
    
    process = subprocess.Popen(
        [executable_path], 
        stdin=subprocess.PIPE, 
        stdout=subprocess.PIPE, 
        stderr=subprocess.PIPE, 
        text=True,
        encoding='shift_jis'
    )

    response_queue = []
    thread = threading.Thread(target=read_output, args=(process, response_queue))
    thread.start()

    # やねうら王の準備コマンド
    initial_commands = ["usi\n", "isready\n", "usinewgame\n"]
    for command in initial_commands:
        process.stdin.write(command)
        process.stdin.flush()
        time.sleep(0.5)

    while "readyok" not in response_queue:
        time.sleep(0.1)

    response_queue.pop(0)
    sfen = initialize_board()
    display_board(sfen)
    print("対局を開始します。指し手を入力してください (例: '7g7f')。'q' を入力すると終了します。")
    moves = []

    try:
        # ユーザーの指し手を適用する前に、やねうら王に問い合わせを行う
        while True:
            user_move = input("あなたの指し手: ").strip()
            if user_move.lower() == 'q':
                print("対局を終了します。")
                break

            # USI形式の指し手のバリエーション (移動, 持ち駒, 成る)
            if not re.match(r"^[1-9][a-i][1-9][a-i](\+)?$|^[PLNSBRGK]\*[1-9][a-i]$", user_move):
                print("無効な指し手です。移動は '7g7f'、持ち駒を打つ場合は 'P*5e'、成る場合は '7g7f+' の形式で入力してください。")
                continue

            # 現在の指し手をmovesに追加
            moves.append(user_move)

            # 指し手を盤面に適用してみる（エラーがないかチェック）
            position_command = f"position startpos moves {' '.join(moves)}\n"
            process.stdin.write(position_command)
            process.stdin.flush()
            time.sleep(0.1)
        
            # 合法手かの確認
            if response_queue:
                response = response_queue.pop(0)
                if "Illegal Input Move" in response:
                    print(f"エラー: {response.strip()}\n無効な指し手のため、最後の指し手を取り消します。")
                    moves.pop()  # 無効な指し手をリストから削除
                    display_board(sfen)  # 盤面を再表示
                    continue # ループを抜けて再入力を促す

            if apply_move(sfen, user_move) == -1:
                continue
            else:
                sfen = apply_move(sfen, user_move)
            display_board(sfen)
            
            process.stdin.write("go depth 10\n")
            process.stdin.flush()

            start_time = time.time()
            yaneuraou_move = None

            while True:
                if response_queue:
                    response = response_queue.pop(0)
                    print(f"やねうら王の応答: {response}")  # 応答を表示
                    if "bestmove" in response:
                        yaneuraou_move = response.split(" ")[1]
                        print(f"やねうら王の指し手: {yaneuraou_move}")
                        moves.append(yaneuraou_move)
                        
                        if apply_move(sfen, yaneuraou_move) == -1:
                            continue
                        else:
                            sfen = apply_move(sfen, yaneuraou_move)
                        display_board(sfen)
                        break
                    

                # やねうら王の応答が遅い場合
                if time.time() - start_time > 10:
                    print("やねうら王の応答が遅いため、もう一度検索します。")
                    process.stdin.write("go depth 10\n")
                    process.stdin.flush()
                    start_time = time.time()

                time.sleep(0.1)


    except Exception as e:
        print(f"エラーが発生しました: {e}")
    finally:
        process.terminate()
        thread.join()
        print("やねうら王のプロセスが終了しました。")

# 実行
if __name__ == "__main__":
    run_yaneuraou()
