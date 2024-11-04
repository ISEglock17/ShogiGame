import subprocess
import threading
import time

def read_output(process, response_queue):
    """ やねうら王の出力を読み取り、必要に応じて応答をキューに格納 """
    while True:
        output = process.stdout.readline()
        if output == '' and process.poll() is not None:
            break
        if output:
            print(f"YaneuraOu Response: {output.strip()}")
            # `bestmove` 応答をキューに追加
            if "bestmove" in output:
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

    print("対局を開始します。指し手を入力してください (例: '7g7f')。'q' を入力すると終了します。")
    moves = []

    try:
        while True:
            user_move = input("Your move: ").strip()
            if user_move.lower() == 'q':
                print("対局を終了します。")
                break
            
            moves.append(user_move)
            position_command = f"position startpos moves {' '.join(moves)}\n"
            process.stdin.write(position_command)
            process.stdin.flush()

            # 探索コマンド（深さ10に制限）
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
                        break
                # タイムアウト設定（10秒）
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
