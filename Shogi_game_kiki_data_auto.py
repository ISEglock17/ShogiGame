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
from ai_comments import *       # aiのコメントに関する関数を読み込み
from openai import OpenAI, ChatCompletion
from cshogi import *    #やねうら王の補助プログラム
from board import *     #利き情報のクラス

from kifu_parse6 import *   #棋譜情報を解析する関数
from jp_record_2_sfen import *  #棋譜をSFENに変換する関数
import sys  # sysモジュールをインポート

import json
import time



"""
メモ:
利き情報を管理するためのプログラム

問題点:

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
        # イベント処理
        for event in pygame.event.get():
            if event.type == pygame.QUIT:  # バツボタンが押された場合
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
                
        # 表示の更新
        pygame.display.flip()
        # FPS制御
        clock.tick(60)
            
    # やねうら王スレッドの終了を待つ
    if game_thread.is_alive():
        game_thread.join()
    
    pygame.quit()
    sys.exit()  # プログラムを終了


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
            mark_cells = [] # 駒の移動先をマークするリスト
            winner = None
            running = True
            
            #----------------------------------------------------------------------------------------------------------------
            #  ゲーム展開
            #----------------------------------------------------------------------------------------------------------------
            print("対局開始！指し手を入力してください (例: '7g7f')。'q' で終了。")
            
            while running:    
                
                # 自動棋譜再生
                result = parse_kif_file("./ShogiData/10001.txt")

                print("先手:", result["sente"])
                print("後手:", result["gote"])

                print("\n棋譜とコメント:")
                for i, move_info in enumerate(result["moves"], 1):
                    jp_move = move_info["move"]
                    from_pos = move_info["from_pos"]
                    time_spent = move_info["time_spent"]
                    total_time = move_info["total_time"]
                    comment = result["move_comments"][i - 1]

                        
                    print(f"{i}: {jp_move}")
                    print(f"   移動元: {from_pos}, 消費時間: {time_spent}, 累積時間: {total_time}")
                    if comment:
                        print(f"   コメント: {comment}")

                    
                    # 自動入力のターン
                    sfen, flag = auto_input_turn(sfen, moves, process, response_queue, command_queue, mark_cells, pop1_se, beep_se, koma_se, jp_move, from_pos)
                    if flag == 'q':
                        print("対局を終了します。")
                        running = False
                        break
                    elif flag == 1 or flag == 2:
                        # 投了、中断、持将棋、千日手の処理
                        winner = i % 2
                        running = False
                        break
                if not running:
                    break

                print("\nその他のコメント:")
                for i, comment in enumerate(result["other_comments"], 1):
                    print(f"{i}: {comment}")
                
            if winner == 1:
                print("先手の勝ち！")
            elif winner == 0:
                print("後手の勝ち！")
                
        except Exception as e:
            print(f"エラーが発生しました: {e}")
            return
            
        finally:
            if process:
                # やねうら王のプロセスを終了
                stop_yaneuraou(process)
                print("やねうら王を終了しました。") 
        
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

def auto_input_turn(sfen, moves, process, response_queue, command_queue, mark_cells, pop1_se, beep_se, koma_se, jp_move, from_pos):
    """ 
        自動棋譜入力モード
        sfen: 盤面情報, 
        moves: 棋譜, 
        process, 
        response_queue, 
        command_queue, 
        mark_cells, 
        pop1_se, 
        beep_se, 
        koma_se,
        move,
        from_pos
    """
    
    if not command_queue.empty():  
        command = command_queue.get() 
        if command == 'q':
            print("対局を終了します。")
            return sfen, 'q'

    # 合法手取得
    print(sfen)
    board2 = Board()  # cshogi用のボード
    board2.set_sfen(sfen)
    legal_moves_list = [move_to_usi(move) for move in board2.legal_moves]
    print(legal_moves_list)
    if not legal_moves_list:  # 詰み判定
        return sfen, 1

    # SFENから盤面情報を解析
    board, turn, captured_pieces, move_number = sfen_to_board(sfen)
    
    #利き情報の出力
    ef = EffectBoard(board)
    ef.print_effect()

    # やねうら王にMultiPV設定を送信
    send_command(process, "setoption name MultiPV value 10")
    
    # メイン処理
    position_command = f"position startpos moves {' '.join(moves)}"
    send_command(process, position_command)
    print(f"やねうら王への送信: {position_command}")
    time.sleep(0.1)

   # 最善手とMultiPV情報を取得
    bestmoves, comments, legal_moves_evaluations = get_score(process, response_queue)
    if bestmoves:
        bestmove = bestmoves[0]
    else:
        bestmove = None
        
    for move, eval_value, pred_moves, eval_values in legal_moves_evaluations:
        print(f"手: {move}, 評価値: {eval_value}, 読み筋: {pred_moves}, 評価値変化: {eval_values}")
    print(f"最善手: {bestmove}")


    # 画面に描画
            
    # 盤面マークの削除
    if turn == 'b':
        mark_cells = [(x, y, z) for x, y, z in mark_cells if z not in (1, 3, 5)] # 先手の場合 先手マークを消す
    else:
        mark_cells = [(x, y, z) for x, y, z in mark_cells if z not in (2, 4, 6)] # 後手の場合 後手マークを消す
    
    # 盤面の描画
    draw_board(board, turn, captured_pieces, move_number, mark_cells)
    display_board(sfen)

    # 自動入力
    if moves:
        user_move = convert_to_sfen(jp_move, ef, last_to_sq=moves[-1], turn=turn, legal_moves_list=legal_moves_list, from_num=from_pos)    
        print(f"{jp_move}を変換して{user_move}になった。")
        if jp_move in ["投了", "中断", "持将棋", "千日手"]:
            print(f"特殊な指し手をスキップ: {jp_move}")
            if turn == 'b':
                return sfen, 1
            else:
                return sfen, 2
    else:
        user_move = convert_to_sfen(jp_move, ef, last_to_sq="", turn=turn, legal_moves_list=legal_moves_list, from_num=from_pos)    
        print(f"{jp_move}を変換して{user_move}になった。")
               


    sfen, valid = process_user_move(sfen, user_move, moves, process, response_queue)

    if not valid:
        print(f"不正な手: {user_move}")
        return sfen, None
    else:
        koma_se.play()
        draw_board(board, turn, captured_pieces, move_number, mark_cells)
        return sfen, None
    
        

#-----------------------------------------------------------------------------------
#　メインメソッド
#-----------------------------------------------------------------------------------
if __name__ == "__main__":
    main()



