import queue
import threading
import pygame
from pygame.locals import *
import pygame.mixer
from shogi_sub import *         # ゲームの流れに関する関数を読み込み
from shogi_board import *       # 盤面解析に関する関数を読み込み
from shogi_engine import *      # 将棋エンジンに関する関数を読み込み
from setting import *           # Pygameなどの設定に関する変数や関数を読み込み
from draw import *              # Pygameの描画を読み込み

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
                    command_queue.put(click_pos)  # キューに送信

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
    
    # もし終了ボタンを押していたら
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

            #----------------------------------------------------------------------------------------------------------------
            #  変数定義
            #----------------------------------------------------------------------------------------------------------------
            sfen = initialize_board()   # 盤面の初期化
            moves = [] # 棋譜を入れるリスト
            mark_cells = [] # マークする座標を入れるリスト
            winner = None
            
            
            #----------------------------------------------------------------------------------------------------------------
            #  ゲーム展開
            #----------------------------------------------------------------------------------------------------------------
            print("対局開始！指し手を入力してください (例: '7g7f')。'q' で終了。")
            yoroshiku_se.play()
            
            while True:
                """
                # プレイヤーのターン
                sfen, flag = player_turn(sfen, moves, process, response_queue, command_queue, mark_cells, pop1_se, beep_se, koma_se)
                if flag == 'q':
                    break
                elif flag == 1:
                    winner = 1
                    break
                
                # mark_cells = [(x, y, z) for x, y, z in mark_cells if z not in (2, 4, 5)]

                
                # プレイヤーのターン
                sfen, flag = player_turn(sfen, moves, process, response_queue, command_queue, mark_cells, pop1_se, beep_se, koma_se)
                if flag == 'q':
                    break
                elif flag == 1:
                    winner = 0
                    break
                """
                
                
                # コンピューターのターン
                sfen, flag = computer_turn(sfen, moves, process, response_queue, command_queue, mark_cells, koma_se)
                if flag == 'q':
                    break
                if flag == 1:
                    winner = 1
                    break
                
                # コンピューターのターン
                sfen, flag = computer_turn(sfen, moves, process, response_queue, command_queue, mark_cells, koma_se)
                if flag == 'q':
                    break
                if flag == 1:
                    winner = 0
                    break
                
            
            if winner == 0:
                print("あなたの勝ちです。")
                font_path = "./image/07やさしさゴシック.ttf"  # フォントファイルのパス
                font = pygame.font.Font(font_path, 128)  # フォントとサイズ（変更可能）
                
                turn_surface = font.render("あなたの勝ちです。", True, (0, 0, 15))  # 青色で描画
                screen.blit(turn_surface, (300, 300))  
  
            elif winner == 1:
                print("あなたの負けです。")
                
                font_path = "./image/07やさしさゴシック.ttf"  # フォントファイルのパス
                font = pygame.font.Font(font_path, 128)  # フォントとサイズ（変更可能）
                
                turn_surface = font.render("あなたの負けです。", True, (0, 0, 15))  # 青色で描画
                screen.blit(turn_surface, (300, 300))  
  
        except Exception as e:
            print(f"エラーが発生しました: {e}")
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
        
        

def player_turn(sfen, moves, process, response_queue, command_queue, mark_cells, pop1_se, beep_se, koma_se):
    """ プレイヤーのターンを処理 """
    phase = 1       # フェイズの定義(1: 駒選択，2: 動かす先選択, 3: 成るかどうか)
    
    while True:
        # 合法手取得
        print(sfen)
        board2 = Board()    # cshogi用のボード
        board2.set_sfen(sfen)
        legal_moves_list = [move_to_usi(move) for move in board2.legal_moves]
        print(legal_moves_list)

        # SFENから盤面情報を解析
        board, turn, captured_pieces, move_number = sfen_to_board(sfen)
        
        # 盤面マークの削除
        if turn == 'b':
            mark_cells = [(x, y, z) for x, y, z in mark_cells if z not in (1, 3, 5)] # 先手の場合 先手マークを消す
        else:
            mark_cells = [(x, y, z) for x, y, z in mark_cells if z not in (2, 4, 6)] # 後手の場合 後手マークを消す
        
        # 盤面の描画
        draw_board(board, turn, captured_pieces, move_number, mark_cells)
        display_board(sfen)
        
        if not legal_moves_list:  # 詰み判定    
            return sfen, 1  # ターンを終了
        
        # 駒選択フェイズ
        if phase == 1:
            print("どの駒を?")
                                    
            while True:
                if not command_queue.empty():  
                    command = command_queue.get() 
                    if command == 'q':
                        print("対局を終了します。")
                        return sfen, 'q'
                    elif command == 'r':     # 右クリックした場合
                        continue 
                    
                    user_move1 = convert_click_to_board(command)

                    if user_move1 is None:    # クリックした場所の盤面情報が拾えなかった場合
                        continue
                    elif not can_move(legal_moves_list, user_move1): # 動かせない駒の場合
                        print("そこの駒は動かせません。")
                        continue
                    else:       # 動かせる駒をタッチした場合
                        break

            x, y = move_to_coord(user_move1)
            if turn == 'b':
                mark_cells.append((x, y, 1))
            else:
                mark_cells.append((x, y, 2))

            suffixes = extract_move_suffixes(legal_moves_list, user_move1)
            for suffix in suffixes:
                x, y = move_to_coord(suffix)
                if turn == 'b':
                    mark_cells.append((x, y, 5))
                else:
                    mark_cells.append((x, y, 6))

            draw_board(board, turn, captured_pieces, move_number, mark_cells)
            pop1_se.play()
            phase = 2

        # 動き先フェイズ
        if phase == 2:
            print("どこに動かす?")
            while True:
                if not command_queue.empty():  
                    command = command_queue.get() 
                    if command == 'q':
                        print("対局を終了します。")
                        return sfen, 'q'
                    elif command == 'r':     # 右クリックした場合
                        phase = 1
                        break
                    
                    user_move2 = convert_click_to_board(command)

                    if user_move2 is None:    # クリックした場所の盤面情報が拾えなかった場合
                        continue
                    else:       # 動かせる駒をタッチした場合
                        if user_move2 not in suffixes:  # 動かせるかどうかの判定
                            beep_se.play()
                            phase = 1
                            continue

                        x, y = move_to_coord(user_move2)
                        if turn == 'b':
                            mark_cells.append((x, y, 3))
                        else:
                            mark_cells.append((x, y, 4))
                            
                        user_move3 = ""
                        if is_promotable(board, user_move1, user_move2, turn):
                            phase = 3
                            break
                        else:
                            phase = 0
                            break

        # 成るかどうか
        if phase == 3:
            draw_board(board, turn, captured_pieces, move_number, mark_cells, pro_flag=True)
            
            while True:
                if not command_queue.empty():  
                    command = command_queue.get()
                    if  command == 'q':
                        print("対局を終了します。")
                        return sfen, 'q'
                    elif command == 'r':     # 右クリックした場合
                        phase = 1
                        break
                    
                    user_move3 = convert_click_to_board(command)
                 
                    if user_move3 not in ("+", ""):
                        continue
                    else:       # 動かせる駒をタッチした場合
                        phase = 0
                        break
        
        # 駒の動き入力完了
        if phase == 0:
            user_move = f"{user_move1}{user_move2}{user_move3}"
            sfen, valid = process_user_move(sfen, user_move, moves, process, response_queue)
            if not valid:
                beep_se.play()
                phase = 1
                continue
            else:
                koma_se.play()
                if turn == 'b':
                    mark_cells = [(x, y, z) for x, y, z in mark_cells if z not in (2, 4, 5)]
                else:
                    mark_cells = [(x, y, z) for x, y, z in mark_cells if z not in (1, 3, 6)]
                draw_board(board, turn, captured_pieces, move_number, mark_cells)
                return sfen, None


def computer_turn(sfen, moves, process, response_queue, command_queue, mark_cells, koma_se):
    """ コンピューターのターンを処理 """
    while True:
        print(sfen)
        board2 = Board()
        board2.set_sfen(sfen)
        legal_moves_list = [move_to_usi(move) for move in board2.legal_moves]
        print(legal_moves_list)
        if not legal_moves_list:  # 詰み判定
            return sfen, 1

        board, turn, captured_pieces, move_number = sfen_to_board(sfen)
        draw_board(board, turn, captured_pieces, move_number)
        display_board(sfen)

        # やねうら王に指し手を送信
        position_command = f"position startpos moves {' '.join(moves)}"
        send_command(process, position_command)    
        print(f"やねうら王への送信: {position_command}")
        time.sleep(0.1)
        
        engine_move = get_engine_move(process, response_queue)
        sfen, valid = process_engine_move(sfen, engine_move, moves)
        
        if not command_queue.empty():  
            command = command_queue.get() 
            if command == 'q':
                print("対局を終了します。")
                return sfen, 'q'
                    
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



#-----------------------------------------------------------------------------------
#　メインメソッド
#-----------------------------------------------------------------------------------
if __name__ == "__main__":
    main()
    
    
    
