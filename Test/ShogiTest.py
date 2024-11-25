import subprocess
import threading
import time

def read_output(process):
    while True:
        output = process.stdout.readline()
        if output == '' and process.poll() is not None:
            break
        if output:
            print(f"YaneuraOu Response: {output.strip()}")

def run_yaneuraou():
    # やねうら王の実行ファイル名を指定（環境に応じて適宜変更）
    executable_path = "./YaneuraOu/windows/YaneuraOu_MATE/YaneuraOu_MATE-tournament-clang++-avx2.exe"
    
    # やねうら王のプロセスを起動（UTF-8エンコードを指定）
    process = subprocess.Popen(
        [executable_path], 
        stdin=subprocess.PIPE, 
        stdout=subprocess.PIPE, 
        stderr=subprocess.PIPE, 
        text=True,  # テキストモードで入出力
        encoding='utf-8'  # UTF-8エンコードを使用
    )

    # 出力を読み取るためのスレッドを起動
    thread = threading.Thread(target=read_output, args=(process,))
    thread.start()

    # エンジンとやり取りするためのコマンドを定義
    commands = [
        "usi\n",               # USIプロトコルの開始
        "isready\n",           # 準備完了の確認
        "usinewgame\n",        # 新しいゲームの開始
        "position startpos\n", # 初期局面を設定
        "d\n",                 # 現在の局面を表示
        "go depth 10\n"        # 探索の開始（深さ10）
    ]

    # コマンドを1つずつ送信
    try:
        for command in commands:
            print(f"Sending command: {command.strip()}")
            process.stdin.write(command)
            process.stdin.flush()
            
            # 少し待つことで応答を取得
            time.sleep(0.5)

    except Exception as e:
        print(f"Error: {e}")
    finally:
        # プロセスを終了
        process.terminate()
        thread.join()  # スレッドが終了するのを待機
        print("YaneuraOu process terminated.")

# 実行
if __name__ == "__main__":
    run_yaneuraou()
