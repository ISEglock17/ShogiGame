import subprocess
import threading
from multiprocessing import process
import time
from concurrent.futures import thread
import re
import pygame
from pygame.locals import *
import sys
from shogi_display import *

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
    executable_path = "./YaneuraOu_NNUE_halfKP256-V830Git_ZEN2.exe"
    
    play_game(executable_path)



def initialize_yaneuraou(process, response_queue):
    """やねうら王の初期化コマンドを送信"""
    initial_commands = ["usi", "isready", "usinewgame"]
    for command in initial_commands:
        send_command(process, command)
        time.sleep(0.5)  # 応答を待つ時間
    # 応答キューに "readyok" が来るまで待機
    while "readyok" not in response_queue:
        time.sleep(0.1)
        
    response_queue.pop(0)

def process_user_move(sfen, user_move, moves, process, response_queue):
    """ユーザーの指し手を処理"""
    # 入力形式を検証
    if not re.match(r"^[1-9][a-i][1-9][a-i](\+)?$|^[PLNSBRGK]\*[1-9][a-i]$", user_move):
        print("無効な指し手です。正しい形式で入力してください。")
        return sfen, False

    moves.append(user_move)
    # やねうら王に指し手を送信
    position_command = f"position startpos moves {' '.join(moves)}"
    send_command(process, position_command)    
    time.sleep(0.1)

    # 合法手かの確認
    if response_queue:
        response = response_queue.pop(0)
        if "Illegal Input Move" in response:
            print(f"エラー: {response.strip()}\n無効な指し手のため、最後の指し手を取り消します。")
            moves.pop()  # 無効な指し手をリストから削除
            display_board(sfen)  # 盤面を再表示
            print(sfen)
            return sfen, False
    
    # 指し手が有効なら盤面を更新
    if apply_move(sfen, user_move) != -1:
        sfen = apply_move(sfen, user_move)
        display_board(sfen)
        print(sfen)
        return sfen, True
    else:
        print("無効な指し手です。")
        moves.pop()  # 無効な指し手を削除
        display_board(sfen)  # 盤面を再表示
        print(sfen)
        return sfen, False


def get_engine_move(process, response_queue):
    """やねうら王の指し手を取得"""
    send_command(process, "go depth 10")
    start_time = time.time()
    
    while True:
        if response_queue:
            response = response_queue.pop(0)
            if "bestmove" in response:
                move = response.split(" ")[1]
                return move
        if time.time() - start_time > 10:  # タイムアウトの処理
            print("応答が遅延しています。再送信します。")
            send_command(process, "go depth 10")
        time.sleep(0.1)


def play_game(executable_path):
    """対局のメインループ"""
    process = None
    response_queue = []
    try:
        # やねうら王の起動と初期化
        
        process = start_yaneuraou(executable_path)
        threading.Thread(target=read_output, args=(process, response_queue), daemon=True).start()
        initialize_yaneuraou(process, response_queue)

        sfen = initialize_board()
        display_board(sfen)
        print("対局開始！指し手を入力してください (例: '7g7f')。'q' で終了。")
        moves = []

        while True:
            user_move = input("あなたの指し手: ").strip()
            if user_move.lower() == 'q':
                print("対局を終了します。")
                break

            sfen, valid = process_user_move(sfen, user_move, moves, process, response_queue)
            if not valid:
                continue

            display_board(sfen)

            engine_move = get_engine_move(process, response_queue)
            if apply_move(sfen, engine_move) != -1:
                moves.append(engine_move)
                sfen = apply_move(sfen, engine_move)
                print(f"やねうら王の指し手: {engine_move}")
                display_board(sfen)
            else:
                print("やねうら王の指し手が無効です。")
                break

    except Exception as e:
        print(f"エラーが発生しました: {e}")
    finally:
        if process:
            stop_yaneuraou(process)




#-----------------------------------------------------------------------------------
#　メインメソッド
#-----------------------------------------------------------------------------------
if __name__ == "__main__":
    main()
    
