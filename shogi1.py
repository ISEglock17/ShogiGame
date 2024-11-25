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


def play_game(executable_path):
    """対局のメインループ"""
    process = None
    response_queue = []
    try:
        # やねうら王の起動と初期化
        
        process = start_yaneuraou(executable_path) # やねうら王のプロセス定義
        threading.Thread(target=read_output, args=(process, response_queue), daemon=True).start()   # スレッドの準備
        initialize_yaneuraou(process, response_queue)   #  やねうら王の初期化

        sfen = initialize_board()   # 盤面の初期化
        display_board(sfen) # 盤面の表示
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
    
