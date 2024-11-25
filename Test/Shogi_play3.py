import subprocess
import threading
import time

# 将棋の初期盤面を設定
def initialize_board():
    board = [
        ["l", "n", "s", "g", "k", "g", "s", "n", "l"],
        [".", "r", ".", ".", ".", ".", ".", "b", "."],
        ["p", "p", "p", "p", "p", "p", "p", "p", "p"],
        [".", ".", ".", ".", ".", ".", ".", ".", "."],
        [".", ".", ".", ".", ".", ".", ".", ".", "."],
        [".", ".", ".", ".", ".", ".", ".", ".", "."],
        ["P", "P", "P", "P", "P", "P", "P", "P", "P"],
        [".", "B", ".", ".", ".", ".", ".", "R", "."],
        ["L", "N", "S", "G", "K", "G", "S", "N", "L"]
    ]
    return board

# 盤面を表示
def display_board(board):
    print("  9 8 7 6 5 4 3 2 1")
    for i, row in enumerate(board):
        row_str = f"{i+1} " + " ".join(row)
        print(row_str)
    print()

# 指し手を盤面に適用
def apply_move(board, move, is_black):
    try:
        from_square = (9 - int(move[1]), ord(move[0]) - ord('a'))
        to_square = (9 - int(move[3]), ord(move[2]) - ord('a'))
        piece = board[from_square[0]][from_square[1]]
        board[from_square[0]][from_square[1]] = "."
        board[to_square[0]][to_square[1]] = piece
    except (ValueError, IndexError) as e:
        print(f"Invalid move format: {move}. Please enter a move like '7g7f'.")

def read_output(process, response_queue):
    while True:
        output = process.stdout.readline()
        if output == '' and process.poll() is not None:
            break
        if output:
            print(f"YaneuraOu Response: {output.strip()}")
            if "readyok" in output or "bestmove" in output:
                response_queue.append(output.strip())

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

    initial_commands = [
        "usi\n",               # USIプロトコルの開始
        "isready\n",           # 準備完了の確認
        "usinewgame\n"         # 新しいゲームの開始
    ]
    
    for command in initial_commands:
        process.stdin.write(command)
        process.stdin.flush()
        time.sleep(0.5)

    # `readyok` 応答が来るまで待機
    while "readyok" not in response_queue:
        time.sleep(0.1)

    board = initialize_board()
    display_board(board)

    print("対局を開始します。指し手を入力してください (例: '7g7f')。'q' を入力すると終了します。")
    moves = []

    try:
        while True:
            user_move = input("Your move: ").strip()
            if user_move.lower() == 'q':
                print("対局を終了します。")
                break
            
            moves.append(user_move)
            apply_move(board, user_move, is_black=True)
            display_board(board)

            position_command = f"position startpos moves {' '.join(moves)}\n"
            process.stdin.write(position_command)
            process.stdin.flush()

            # やねうら王に指し手を求める
            process.stdin.write("go depth 10\n")
            process.stdin.flush()

            start_time = time.time()
            yaneuraou_move = None

            while True:
                if response_queue:
                    response = response_queue.pop(0)
                    if "bestmove" in response:
                        yaneuraou_move = response.split(" ")[1]
                        print(f"YaneuraOu's move: {yaneuraou_move}")
                        moves.append(yaneuraou_move)
                        apply_move(board, yaneuraou_move, is_black=False)
                        display_board(board)
                        break

                if time.time() - start_time > 10:
                    print("YaneuraOuが応答しませんでした。再度探索を行います。")
                    process.stdin.write("go depth 10\n")
                    process.stdin.flush()
                    start_time = time.time()
                time.sleep(0.1)

    except Exception as e:
        print(f"エラーが発生しました: {e}")
    finally:
        process.terminate()
        thread.join()
        print("YaneuraOu process terminated.")

# 実行
if __name__ == "__main__":
    run_yaneuraou()
