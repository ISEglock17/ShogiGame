import subprocess
import threading
import time
import re

# SFEN表記の盤面をリストに変換する。
def sfen_to_board(sfen):
    # SFENを"/"で分割して各行を取得
    rows = sfen.split("/")
    board = []

    # 各行の処理
    for row in rows:
        board_row = []
        for char in row:
            if char.isdigit():
                # 数字なら、その分だけ空マスを追加
                board_row.extend([' ' for _ in range(int(char))])
            else:
                # それ以外は駒をそのまま追加
                board_row.append(char)
        board.append(board_row)
    return board


"""
# USIプロトコルでのSFEN例
sfen = "lnsgkgsnl/1r5b1/ppppppppp/9/9/9/PPPPPPPPP/1B5R1/LNSGKGSNL"

# 駒配置をリスト形式で取得
board = sfen_to_board(sfen)

# 表示
for row in board:
    print(" ".join(row))
"""

# 駒を英語の略称で表現
player_pieces = {
    "歩": " P ", "香": " L ", "桂": " N ", "銀": " S ", "金": " G ", "玉": " K ", "飛": " R ", "角": " B "
}
opponent_pieces = {k: f" {v.strip().lower()} " for k, v in player_pieces.items()}  # 相手の駒は小文字で表示

# 空白は半角スペースを使用
empty_square = " . "

# 盤面の初期化
def initialize_board():
    board = [
        [opponent_pieces["香"], opponent_pieces["桂"], opponent_pieces["銀"], opponent_pieces["金"], opponent_pieces["玉"], opponent_pieces["金"], opponent_pieces["銀"], opponent_pieces["桂"], opponent_pieces["香"]],
        [empty_square, opponent_pieces["飛"], empty_square, empty_square, empty_square, empty_square, empty_square, opponent_pieces["角"], empty_square],
        [opponent_pieces["歩"], opponent_pieces["歩"], opponent_pieces["歩"], opponent_pieces["歩"], opponent_pieces["歩"], opponent_pieces["歩"], opponent_pieces["歩"], opponent_pieces["歩"], opponent_pieces["歩"]],
        [empty_square] * 9,
        [empty_square] * 9,
        [empty_square] * 9,
        [player_pieces["歩"], player_pieces["歩"], player_pieces["歩"], player_pieces["歩"], player_pieces["歩"], player_pieces["歩"], player_pieces["歩"], player_pieces["歩"], player_pieces["歩"]],
        [empty_square, player_pieces["角"], empty_square, empty_square, empty_square, empty_square, empty_square, player_pieces["飛"], empty_square],
        [player_pieces["香"], player_pieces["桂"], player_pieces["銀"], player_pieces["金"], player_pieces["玉"], player_pieces["金"], player_pieces["銀"], player_pieces["桂"], player_pieces["香"]],
    ]
    return board

# 盤面を表示
def display_board(board):
    print("   9  8  7  6  5  4  3  2  1")
    letters = "abcdefghi"
    for i, row in enumerate(board, start=1):
        row_str = f"{letters[i - 1]} " + "".join(row)
        print(row_str)

# 指し手を盤面に適用
def apply_move(board, move, is_player):
    try:
        # 指し手を座標に変換
        from_row, from_col = ord(move[1]) - ord('a'), 9 - int(move[0])
        to_row, to_col = ord(move[3]) - ord('a'), 9 - int(move[2])
        
        # 駒を移動
        piece = board[from_row][from_col]
        board[from_row][from_col] = " . "
        board[to_row][to_col] = piece
        
        return True
    except (ValueError, IndexError):
        print(f"無効な指し手の形式です: {move}。 '7g7f' のように入力してください。")
        return False

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
    board = initialize_board()
    display_board(board)
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
                    display_board(board)  # 盤面を再表示
                    continue # ループを抜けて再入力を促す

            if not apply_move(board, user_move, is_player=True):
                continue
            display_board(board)
            
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
                        
                        if not apply_move(board, yaneuraou_move, is_player=False):
                            continue
                        display_board(board)
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
