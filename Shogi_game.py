import queue
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
import pygame.mixer

"""
メモ

問題点:
・まだ合法手の判別ができない。(動かせない駒の動きは検出できるが，成れるかどうか，詰みかどうかの判定ができない)
"""
#-----------------------------------------------------------------------------------
#　初期化
#-----------------------------------------------------------------------------------
executable_path = "./YaneuraOu_NNUE_halfKP256-V830Git_ZEN2.exe"

pygame.init()

#-----------------------------------------------------------------------------------
#　関数部
#-----------------------------------------------------------------------------------
def main():
    """ メインメソッド """
    state_queue = queue.Queue()    # SFEN状態の共有
    command_queue = queue.Queue()  # ユーザー指し手や入力の共有
    
    game_thread = threading.Thread(target=play_game, args=(executable_path, state_queue, command_queue), daemon=True)
    game_thread.start()

    running = True
    
    while running:
        #イベント処理
        for event in pygame.event.get():            
            if event.type == QUIT: #閉じるボタンが押されたら終了
                running = False
                command_queue.put("q")
            elif event.type == pygame.MOUSEBUTTONDOWN:
                # クリック位置を取得
                click_pos = pygame.mouse.get_pos()
                board_pos = convert_click_to_board(click_pos)  # クリック位置をボード上の座標に変換
                print(f"クリック位置: {board_pos}")
                if board_pos is not None:
                    command_queue.put(board_pos)  # キューに送信

        # エンジンからの応答を非ブロッキングで取得
        while not state_queue.empty():
            response = state_queue.get()
            print(f"state_queue: {response}")
            if response == 'q':
                running = False
        
        # 表示の更新
        pygame.display.flip()
        # FPS制御
        clock.tick(60)
    
    # やねうら王スレッドの終了を待つ
    if game_thread.is_alive():
        game_thread.join()
        
    pygame.mixer.music.stop() #終了
    pygame.quit()
    print("終了しました。")
            

def play_game(executable_path, state_queue, command_queue):
    """対局のメインループ"""
    process = None
    response_queue = []
    try:
        # やねうら王の起動と初期化
        
        process = start_yaneuraou(executable_path) # やねうら王のプロセス定義
        yaneura_thread = threading.Thread(target=read_output, args=(process, response_queue), daemon=True)   # スレッドの準備
        yaneura_thread.start()
        
        initialize_yaneuraou(process, response_queue)   #  やねうら王の初期化

        sfen = initialize_board()   # 盤面の初期化
        moves = [] # 棋譜を入れるリスト
        mark_cells = [] # マークする座標を入れるリスト
        winner = None
        
        print("対局開始！指し手を入力してください (例: '7g7f')。'q' で終了。")
        yoroshiku_se.play()
        
        while True:
            # if is_checkmate(process, response_queue, sfen):
            #     print("詰みです。あんたの負けです。")
            #     break
            if winner != None:
                break
            
            # プレイヤーのターン
            while True:
                #state_queue.put(sfen)
                board, turn, captured_pieces, move_number= sfen_to_board(sfen)
                draw_board(board, turn, captured_pieces, move_number, mark_cells)
                display_board(sfen)
                print(sfen)

                print("どの駒を?")
                while command_queue.empty():
                    pass
                user_move1 = command_queue.get()
                if user_move1 == 'q':
                    print("対局を終了します。")
                    winner = 0
                    break
                elif user_move1 == "+" or user_move1 == "":
                    continue
                if len(mark_cells) >= 2:
                    mark_cells = []
                x, y = move_to_coord(user_move1)
                mark_cells.append((x, y, 1))
                
                draw_board(board, turn, captured_pieces, move_number, mark_cells)
                print(user_move1)
                pop1_se.play()

                print("どこに動かす?")
                while command_queue.empty():
                    pass
                user_move2 = command_queue.get()
                if user_move2 == 'q':
                    print("対局を終了します。")
                    winner = 0
                    break
                elif user_move2 == "+" or user_move2 == "":
                    user_move2 = None

                x, y = move_to_coord(user_move2)
                mark_cells.append((x, y, 3))                
                user_move3 = ""
                if is_promotable(board, user_move1, user_move2):    # 成れる場合
                    draw_board(board, turn, captured_pieces, move_number, mark_cells, pro_flag = True)
                    while command_queue.empty():
                        pass
                    user_move3 = command_queue.get()
                    if user_move3 == "+":  # 成る場合
                        pass
                    elif user_move3 == "": # 成らない場合
                        pass
                    else:
                        continue
                draw_board(board, turn, captured_pieces, move_number, mark_cells)
                print(user_move2)
                pop1_se.play()
                
                user_move = f"{user_move1}{user_move2}{user_move3}"
                if user_move == 'q':
                    print("対局を終了します。")
                    winner = 0
                    break
                
                if user_move.lower() == 'q':
                    print("対局を終了します。")
                    winner = 0
                    break
                
                sfen, valid = process_user_move(sfen, user_move, moves, process, response_queue)    # プレイヤーの指し手を適用
                if not valid:
                    beep_se.play()
                    continue
                else:
                    koma_se.play()
                    break
                
            if winner != None:
                break
                
            # エンジンのターン
            while True:
                #state_queue.put(sfen)
                board, turn, captured_pieces, move_number = sfen_to_board(sfen)
                draw_board(board, turn, captured_pieces, move_number)
                display_board(sfen)
                print(sfen)
                
                engine_move = get_engine_move(process, response_queue)  
                sfen, valid = process_engine_move(sfen, engine_move, moves) # エンジンの指し手を適用
                if not valid:   # 有効てでない場合
                    beep_se.play()
                    continue
                else:   # 有効手な場合
                    print(f"やねうら王の指し手: {engine_move}")
                    koma_se.play()
                    if len(mark_cells) >= 2:
                        mark_cells = []
                    x, y = move_to_coord(engine_move[0:2])
                    mark_cells.append((x, y, 2))
                    x, y = move_to_coord(engine_move[2:4])
                    mark_cells.append((x, y, 4))
                    break


    except Exception as e:
        print(f"エラーが発生しました: {e}")
    finally:
        state_queue.put("q")
        stop_yaneuraou(process)
        pygame.mixer.music.stop() #終了
        """
        # スレッドの終了を待つ
        if yaneura_thread:
            yaneura_thread.join()  # スレッドが終了するのを待つ
        """

#-----------------------------------------------------------------------------------
#　メインメソッド
#-----------------------------------------------------------------------------------
if __name__ == "__main__":
    main()
    
    
