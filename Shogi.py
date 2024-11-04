import subprocess
import threading
import time
import re

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
    print("    a b c d e f g h i")
    for i, row in enumerate(board, start=1):
        row_str = f"{9 - i}  " + "".join(row)
        print(row_str)

# 指し手を盤面に適用
def apply_move(board, move, is_player):
    try:
        # 指し手を座標に変換
        from_row, from_col = 9 - int(move[1]), ord(move[0]) - ord('a')
        to_row, to_col = 9 - int(move[3]), ord(move[2]) - ord('a')
        
        # 駒を移動
        piece = board[from_row][from_col]
        board[from_row][from_col] = "."
        board[to_row][to_col] = piece
    except (ValueError, IndexError):
        print(f"無効な指し手の形式です: {move}。 '7g7f' のように入力してください。")

# やねうら王の応答を読み取る
def read_output(process, response_queue):
    while True:
        output = process.stdout.readline()
        if output == '' and process.poll() is not None:
            break
        if output:
            print(f"やねうら王の応答: {output.strip()}")
            if "readyok" in output or "bestmove" in output:
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
        encoding='utf-8'
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

    board = initialize_board()
    display_board(board)
    print("対局を開始します。指し手を入力してください (例: '7g7f')。'q' を入力すると終了します。")
    moves = []

    try:
        while True:
            user_move = input("あなたの指し手: ").strip()
            if user_move.lower() == 'q':
                print("対局を終了します。")
                break

            # 入力がUSI形式に従っているか確認
            if not re.match(r"^[1-9][a-i][1-9][a-i]$", user_move):
                print("無効な指し手です。 '7g7f' の形式で入力してください。")
                continue

            moves.append(user_move)
            apply_move(board, user_move, is_player=True)
            display_board(board)

            position_command = f"position startpos moves {' '.join(moves)}\n"
            process.stdin.write(position_command)
            process.stdin.flush()

            process.stdin.write("go depth 10\n")
            process.stdin.flush()

            start_time = time.time()
            yaneuraou_move = None

            while True:
                if response_queue:
                    response = response_queue.pop(0)
                    if "bestmove" in response:
                        yaneuraou_move = response.split(" ")[1]
                        print(f"やねうら王の指し手: {yaneuraou_move}")
                        moves.append(yaneuraou_move)
                        apply_move(board, yaneuraou_move, is_player=False)
                        display_board(board)
                        break

                # ヒント表示機能（無効な指し手の場合）
                if time.time() - start_time > 10:
                    print("やねうら王の応答が遅いため、ヒントを表示します。")
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
