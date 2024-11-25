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
            if "bestmove" in output:
                response_queue.append(output.strip())


def run_yaneuraou():
    # やねうら王の実行ファイルパスを指定（適宜変更）
    executable_path = "./YaneuraOu/windows/YaneuraOu_MATE/YaneuraOu_MATE-tournament-clang++-avx2.exe"
    
    # やねうら王のプロセスを起動（UTF-8エンコード指定）
    process = subprocess.Popen(
        [executable_path], 
        stdin=subprocess.PIPE, 
        stdout=subprocess.PIPE, 
        stderr=subprocess.PIPE, 
        text=True,
        encoding='utf-8'
    )

    # 出力を読み取るためのスレッドを起動
    thread = threading.Thread(target=read_output, args=(process,))
    thread.start()

    # USIプロトコルの初期化コマンドを送信
    initial_commands = [
        "usi\n",               # USIプロトコルの開始
        "isready\n",           # 準備完了の確認
        "usinewgame\n",        # 新しいゲームの開始
        "position startpos\n"  # 初期局面を設定
    ]
    
    for command in initial_commands:
        process.stdin.write(command)
        process.stdin.flush()
        time.sleep(0.5)

    # 人対やねうら王の対局を開始
    print("対局を開始します。指し手を入力してください (例: '7g7f')。'q' を入力すると終了します。")
    moves = []

    try:
        while True:
            # 人の指し手を入力
            user_move = input("Your move: ").strip()
            if user_move.lower() == 'q':
                print("対局を終了します。")
                break
            
            moves.append(user_move)
            # やねうら王に現在の局面と人の指し手を送信
            position_command = f"position startpos moves {' '.join(moves)}\n"
            process.stdin.write(position_command)
            process.stdin.flush()

            # やねうら王に指し手を求める
            process.stdin.write("go\n")
            process.stdin.flush()
            
            # 応答を少し待つ
            time.sleep(1)
            
            # 応答から指し手を取得してリストに追加（出力がどのように返されるかにより調整が必要）
            # この部分はやねうら王の標準出力の形式によって適宜変更する
            output = process.stdout.readline().strip()
            if "bestmove" in output:
                yaneuraou_move = output.split(" ")[1]
                print(f"YaneuraOu's move: {yaneuraou_move}")
                moves.append(yaneuraou_move)
            else:
                print("やねうら王からの応答を受信できませんでした。")
                break

    except Exception as e:
        print(f"エラーが発生しました: {e}")
    finally:
        # プロセスを終了
        process.terminate()
        thread.join()  # スレッドの終了を待機
        print("YaneuraOu process terminated.")

# 実行
if __name__ == "__main__":
    run_yaneuraou()
