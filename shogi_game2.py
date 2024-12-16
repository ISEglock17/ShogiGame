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
from cshogi import *

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
                if event.button == 3:   # 右クリックした場合
                    command_queue.put("r")  # キューに送信
                else:
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
                break
            # elif response == 'r':
            #     break
        
        # 表示の更新
        pygame.display.flip()
        # FPS制御
        clock.tick(60)
    
    # やねうら王スレッドの終了を待つ
    if game_thread.is_alive():
        game_thread.join()
            
    if event.type == QUIT:
        pygame.quit()
    # pygame.mixer.music.stop() #終了
    # if event.type != QUIT:
    #     input1 = input("もう一度やりますか(y/n)")
    #     if input1 == "y":
    #         pygame.mixer.music.play(-1) #再生
    #         main()
    #     else:
    #         pygame.quit()
    #         print("終了しました。")
    # else:
    #     pygame.quit()
    #     print("終了しました。")
            


def player_turn(sfen, board2, moves, process, response_queue, command_queue, mark_cells, phase, pop1_se, beep_se, koma_se):
    """ プレイヤーのターンを処理 """
    while True:
        # 合法手取得
        print(sfen)
        board2.set_sfen(sfen)
        legal_moves_list = [move_to_usi(move) for move in board2.legal_moves]
        print(legal_moves_list)

        # SFENから盤面情報を解析
        board, turn, captured_pieces, move_number = sfen_to_board(sfen)
        mark_cells = [(x, y, z) for x, y, z in mark_cells if z not in (1, 3, 5)]
        draw_board(board, turn, captured_pieces, move_number, mark_cells)
        display_board(sfen)
        if not legal_moves_list:  # 詰み判定
            return sfen, 1  # ターンを終了

        # 駒選択フェイズ
        if phase == 1:
            print("どの駒を?")
            while command_queue.empty():
                pass
            user_move1 = command_queue.get()
            if user_move1 == 'q':
                print("対局を終了します。")
                return sfen, 'q'
            elif user_move1 == 'r':
                phase = 1
                continue

            x, y = move_to_coord(user_move1)
            mark_cells.append((x, y, 1))

            suffixes = extract_move_suffixes(legal_moves_list, user_move1)
            for suffix in suffixes:
                x, y = move_to_coord(suffix)
                mark_cells.append((x, y, 5))

            draw_board(board, turn, captured_pieces, move_number, mark_cells)
            pop1_se.play()
            phase = 2

        # 動き先フェイズ
        if phase == 2:
            print("どこに動かす?")
            while command_queue.empty():
                pass
            user_move2 = command_queue.get()
            if user_move2 == 'q':
                print("対局を終了します。")
                return sfen, 'q'
            elif user_move2 == 'r':
                phase = 1
                continue

            if user_move2 not in suffixes:
                beep_se.play()
                phase = 1
                mark_cells = [(x, y, z) for x, y, z in mark_cells if z != 5]
                continue

            x, y = move_to_coord(user_move2)
            mark_cells.append((x, y, 3))
            user_move3 = ""
            if is_promotable(board, user_move1, user_move2):
                phase = 3

            if phase == 3:
                draw_board(board, turn, captured_pieces, move_number, mark_cells, pro_flag=True)
                while command_queue.empty():
                    pass
                user_move3 = command_queue.get()
                if user_move3 not in ("+", "") and user_move3 != 'r':
                    continue

            user_move = f"{user_move1}{user_move2}{user_move3}"
            sfen, valid = process_user_move(sfen, user_move, moves, process, response_queue)
            if not valid:
                beep_se.play()
                phase = 1
                mark_cells = [(x, y, z) for x, y, z in mark_cells if z != 5]
                continue
            else:
                koma_se.play()
                mark_cells = [(x, y, z) for x, y, z in mark_cells if z not in (2, 4, 5)]
                draw_board(board, turn, captured_pieces, move_number, mark_cells)
                return sfen, None


def computer_turn(sfen, board2, moves, process, response_queue, mark_cells, koma_se):
    """ コンピューターのターンを処理 """
    while True:
        print(sfen)
        board2.set_sfen(sfen)
        legal_moves_list = [move_to_usi(move) for move in board2.legal_moves]
        print(legal_moves_list)
        if not legal_moves_list:  # 詰み判定
            return sfen, 0

        board, turn, captured_pieces, move_number = sfen_to_board(sfen)
        draw_board(board, turn, captured_pieces, move_number)
        display_board(sfen)

        engine_move = get_engine_move(process, response_queue)
        sfen, valid = process_engine_move(sfen, engine_move, moves)
        if not valid:
            print("エンジンが非合法な手を打ちました。")
            continue
        else:
            print(f"やねうら王の指し手: {engine_move}")
            koma_se.play()
            x, y = move_to_coord(engine_move[0:2])
            mark_cells.append((x, y, 2))
            x, y = move_to_coord(engine_move[2:4])
            mark_cells.append((x, y, 4))
            return sfen, None



def play_game(executable_path, state_queue, command_queue):
    """対局のメインループ"""
    while True:
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
            board2 = Board()
            phase = 1
            print("対局開始！指し手を入力してください (例: '7g7f')。'q' で終了。")
            yoroshiku_se.play()
            
            while True:
                # プレイヤーのターン
                sfen, flag = player_turn(sfen, board2, moves, process, response_queue, command_queue, mark_cells, phase, pop1_se, beep_se, koma_se)
                if flag == 'q':
                    break
                elif flag == 1:
                    winner = 1
                    break
                
                mark_cells = [(x, y, z) for x, y, z in mark_cells if z not in (2, 4, 5)]

                # コンピューターのターン
                sfen, flag = computer_turn(sfen, board2, moves, process, response_queue, mark_cells, koma_se)
                if flag == 0:
                    winner = 0
                    break

            
            if winner == 0:
                print("あなたの勝ちです。")
  
            elif winner == 1:
                print("あなたの負けです。")
  
        except Exception as e:
            print(f"エラーが発生しました: {e}")
            pygame.quit()
            return
            
        finally:
            pygame.mixer.music.stop() #終了
            stop_yaneuraou(process)
        
        if flag == 'q':
            return
        else:    
            print("もう一度やりますか。")
            while command_queue.empty():
                pass
            user_move1 = command_queue.get()           
            if user_move1 == 'q':
                print("対局を終了します。")
                return 
            elif len(user_move1) < 2:
                print("終了しました。")
                state_queue.put("q")
                return
            else:
                pygame.mixer.music.play(-1) #再生
                state_queue.put("r")
        
        
            # input1 = input("もう一度やりますか(y/n)")
            # if input1 == "y":
            #     pygame.mixer.music.play(-1) #再生
            #     state_queue.put("r")
            # else:
            #     pygame.quit()
            #     print("終了しました。")
            #     state_queue.put("q")
            #     return
        
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
    
    
    
