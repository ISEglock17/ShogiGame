import subprocess
import threading
import time
import re

# 将棋の初期盤面を設定
def initialize_board():
    board = [
        ["香", "桂", "銀", "金", "王", "金", "銀", "桂", "香"],
        [".", "飛", ".", ".", ".", ".", ".", "角", "."],
        ["歩", "歩", "歩", "歩", "歩", "歩", "歩", "歩", "歩"],
        [".", ".", ".", ".", ".", ".", ".", ".", "."],
        [".", ".", ".", ".", ".", ".", ".", ".", "."],
        [".", ".", ".", ".", ".", ".", ".", ".", "."],
        ["歩", "歩", "歩", "歩", "歩", "歩", "歩", "歩", "歩"],
        [".", "角", ".", ".", ".", ".", ".", "飛", "."],
        ["香", "桂", "銀", "金", "玉", "金", "銀", "桂", "香"]
    ]
    return board

# 盤面を表示
def display_board(board):
    print("    ９ ８ ７ ６ ５ ４ ３ ２ １")
    for i, row in enumerate(board):
        row_str = f"{i+1} " + " ".join(row)
        print(row_str)
    print()

# 指し手を盤面に適用
def apply_move(board, move, is_black):
    try:
        # 文字列の指し手を行番号と列番号に変換
        from_square = (9 - int(move[1]), ord(move[0]) - ord('a'))
        to_square = (9 - int(move[3]), ord(move[2]) - ord('a'))
        
        # 盤面更新
        piece = board[from_square[0]][from_square[1]]
        board[from_square[0]][from_square[1]] = "."
        board[to_square[0]][to_square[1]] = piece
    except (ValueError, IndexError) as e:
        print(f"無効な指し手の形式です: {move}。 '7g7f' のように入力してください。")

# やねうら王の応答を読み取る関数
def read_output(process, response_queue):
    while True:
        output = process.stdout.readline()
        if output == '' and process.poll() is not None:
            break
        if output:
            print(f"やねうら王の応答: {output.strip()}")
            if "readyok" in output or "bestmove" in output:
                response_queue.append(output.strip())

def run_yaneuraou():
    # やねうら王の実行ファイルパス
    executable_path = "./YaneuraOu_NNUE_halfKP256-V830Git_ZEN2.exe"
    
    process = subprocess.Popen(
        [executable_path], 
        stdin=subprocess.PIPE, 
        stdout=subprocess.PIPE, 
        stderr=subprocess.PIPE, 
        text=True,
        encoding='utf-8'
    )

    # やねうら王の応答を保存するキュー
    response_queue = []
    thread = threading.Thread(target=read_output, args=(process, response_queue))
    thread.start()

    # 初期コマンドを送信してやねうら王をセットアップ
    initial_commands = [
        "usi\n",               # USIプロトコルの開始
        "isready\n",           # 準備完了の確認
        "usinewgame\n"         # 新しいゲームの開始
    ]
    
    for command in initial_commands:
        process.stdin.write(command)
        process.stdin.flush()
        time.sleep(0.5)

    # `readyok` 応答を待機
    while "readyok" not in response_queue:
        time.sleep(0.1)

    # 初期盤面の設定
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
            
            # プレイヤーの指し手を検証
            if not re.match(r"^[1-9][a-i][1-9][a-i]$", user_move):
                print("無効な指し手です。 '7g7f' の形式で入力してください。")
                continue

            moves.append(user_move)
            apply_move(board, user_move, is_black=True)
            display_board(board)

            # 現在の局面をやねうら王に設定
            position_command = f"position startpos moves {' '.join(moves)}\n"
            process.stdin.write(position_command)
            process.stdin.flush()

            # やねうら王に指し手を求める
            process.stdin.write("go depth 10\n")
            process.stdin.flush()

            start_time = time.time()
            yaneuraou_move = None

            # やねうら王の応答を待機
            while True:
                if response_queue:
                    response = response_queue.pop(0)
                    if "bestmove" in response:
                        yaneuraou_move = response.split(" ")[1]
                        print(f"やねうら王の指し手: {yaneuraou_move}")
                        moves.append(yaneuraou_move)
                        apply_move(board, yaneuraou_move, is_black=False)
                        display_board(board)
                        break

                # やねうら王の応答が遅い場合
                if time.time() - start_time > 10:
                    print("やねうら王が応答しませんでした。再度探索を行います。")
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
