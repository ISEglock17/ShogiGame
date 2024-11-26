import subprocess
import threading
from multiprocessing import process
import time
from concurrent.futures import thread
import re
import pygame
from pygame.locals import *
import sys
from shogi_sub import *

"""
メモ

問題点:
・まだ合法手の判別ができない。(動かせない駒の動きは検出できるが，成れるかどうか，詰みかどうかの判定ができない)
"""


#-----------------------------------------------------------------------------------
#　関数部
#-----------------------------------------------------------------------------------
def main():
    """ メインメソッド """
    run_yaneuraou()


def run_yaneuraou():
    """ やねうら王を起動する関数 """
    # エンジンの指定
    executable_path = "./YaneuraOu_NNUE_halfKP256-V830Git_ZEN2.exe"
    
    process = subprocess.Popen(
        [executable_path], 
        stdin=subprocess.PIPE, 
        stdout=subprocess.PIPE, 
        stderr=subprocess.PIPE, 
        text=True,
        encoding='shift_jis'
    )

    # スレッドで実行
    response_queue = []
    thread1 = threading.Thread(target=read_output, args=(process, response_queue))
    thread1.start()

    # やねうら王の準備コマンド
    initial_commands = ["usi\n", "isready\n", "usinewgame\n"]
    for command in initial_commands:
        process.stdin.write(command)
        process.stdin.flush()
        time.sleep(0.5)

    # readyok待ち
    while "readyok" not in response_queue:
        time.sleep(0.1)
    
    response_queue.pop(0)
    
    sfen = initialize_board()   # 初期盤面の読み出し
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
                    print(sfen)
                    continue # ループを抜けて再入力を促す

            # 無効な指し手であれば
            if apply_move(sfen, user_move) == -1:
                moves.pop()  # 無効な指し手をリストから削除
                display_board(sfen)  # 盤面を再表示
                print(sfen)
                continue
            else:
                sfen = apply_move(sfen, user_move)
            
            # 有効な指し手であれば
            display_board(sfen)
            print(sfen)
            
            
            
            # 思考開始
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
                        
                        # 無効な指し手ならば
                        if apply_move(sfen, yaneuraou_move) == -1:
                            moves.pop()  # 無効な指し手をリストから削除
                            continue
                        else:
                            sfen = apply_move(sfen, yaneuraou_move)
                        display_board(sfen)
                        print(sfen)
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





#-----------------------------------------------------------------------------------
#　メインメソッド
#-----------------------------------------------------------------------------------
if __name__ == "__main__":
    main()
    
