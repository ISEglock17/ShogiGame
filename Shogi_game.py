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

"""
メモ

問題点:
・まだ合法手の判別ができない。(動かせない駒の動きは検出できるが，成れるかどうか，詰みかどうかの判定ができない)
"""
executable_path = "./YaneuraOu_NNUE_halfKP256-V830Git_ZEN2.exe"

pygame.init()
    
    
# ウィンドウサイズと座標定義
WINDOW_SIZE = 800
BOARD_IMAGE_SIZE = 4000
BOARD_POS = (145 / BOARD_IMAGE_SIZE * WINDOW_SIZE, 152 / BOARD_IMAGE_SIZE * WINDOW_SIZE)  # 盤面左上
BOARD_END = (3873 / BOARD_IMAGE_SIZE * WINDOW_SIZE, 3851 / BOARD_IMAGE_SIZE * WINDOW_SIZE)  # 盤面右下
CELL_SIZE = (BOARD_END[0] - BOARD_POS[0]) / 9, (BOARD_END[1] - BOARD_POS[1]) / 9  # 各マスの幅・高さ


screen = pygame.display.set_mode((WINDOW_SIZE, WINDOW_SIZE))
pygame.display.set_caption("将棋GUI")
clock = pygame.time.Clock()


    
# 画像ロード
board_img = pygame.image.load("./image/board.png")
board_img = pygame.transform.scale(board_img, (WINDOW_SIZE, WINDOW_SIZE))  # ウィンドウに合わせて縮小
piece_images = {}

# 駒画像をロード（例: ./image/pieces/P.png など）
PIECES = ["P", "+P", "L", "+L", "N", "+N", "S", "+S", "G", "B", "+B", "R", "+R", "K"]
PIECES_NAME = ["fuhyo", "to", "kyosha", "nari-kyo", "keima", "nari-kei", "ginsho", "nari-gin", "kinsho", "kakugyo", "ryuma", "hisha", "ryuou", "ousho"]
pieces_dict = dict(zip(PIECES, PIECES_NAME))
for piece in PIECES:
    image = pygame.image.load(f"./image/pieces/{pieces_dict[piece]}.png")
    piece_images[piece] = pygame.transform.scale(image, (int(CELL_SIZE[0]), int(CELL_SIZE[1]))) 
    
#-----------------------------------------------------------------------------------
#　関数部
#-----------------------------------------------------------------------------------
def main():
    """ メインメソッド """

    
    state_queue = queue.Queue()    # SFEN状態の共有
    command_queue = queue.Queue()  # ユーザー指し手や入力の共有
    
    engine_thread = threading.Thread(target=play_game, args=(executable_path, state_queue, command_queue), daemon=True)
    engine_thread.start()

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
                command_queue.put(board_pos)  # キューに送信

        # エンジンからの応答を非ブロッキングで取得
        while not state_queue.empty():
            response = state_queue.get()
            print(f"state_queue: {response}")
            if response == 'q':
                running = False
        
        pygame.display.flip()
        # FPS制御
        clock.tick(60)
    
      # やねうら王スレッドの終了を待つ
    if engine_thread.is_alive():
        engine_thread.join()
        
    pygame.quit()
    print("終了しました。")
            


def convert_click_to_board(click_pos):
    """クリック位置をボード上の座標に変換"""
    x, y = click_pos
    board_x = int((x - BOARD_POS[0]) / CELL_SIZE[0])
    board_y = int((y - BOARD_POS[1]) / CELL_SIZE[1])
    if 0 <= board_x < 9 and 0 <= board_y < 9:
        sfen_x = 9 - board_x
        sfen_y = chr(ord('a') + board_y)
        return f"{sfen_x}{sfen_y}"  # ボード内なら座標を返す
    else:
        return None  # ボード外なら無効
    
def draw_board(board):
    """
    SFEN解析済みの盤面データをもとに描画
    :param board: 2Dリスト形式の盤面
    """
    screen.blit(board_img, (0, 0))  # 盤面画像を描画
    for row in range(9):
        for col in range(9):
            piece = board[row][col]
            if piece != ".":
                piece_image = piece_images.get(piece.upper(), None)
                if piece.islower():  # 小文字 => 後手の駒
                        piece_image = pygame.transform.flip(piece_image, False, True)  # 後手の駒は上下反転
                if piece_image:
                    x = int(BOARD_POS[0] + col * CELL_SIZE[0])
                    y = int(BOARD_POS[1] + row * CELL_SIZE[1])
                    # 駒を描画
                    screen.blit(piece_image, (x, y))
                    


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
        print("対局開始！指し手を入力してください (例: '7g7f')。'q' で終了。")
        moves = []

        winner = None
        
        while True:
            if winner != None:
                break
            # プレイヤーのターン
            while True:
                #state_queue.put(sfen)
                board, _, _, _ = sfen_to_board(sfen)
                draw_board(board)
                display_board(sfen)
                print(sfen)
                # 指し手の入力待ち
                # user_move = input("あなたの指し手: ").strip()
                print("どの駒を?")
                while command_queue.empty():
                    pass
                user_move1 = command_queue.get()
                if user_move1 == 'q':
                    print("対局を終了します。")
                    winner = 0
                    break
                print(user_move1)
                print("どこに動かす?")
                while command_queue.empty():
                    pass
                user_move2 = command_queue.get()
                if user_move2 == 'q':
                    print("対局を終了します。")
                    winner = 0
                    break
                print(user_move2)
                
                user_move = f"{user_move1}{user_move2}"
                if user_move == 'q':
                    print("対局を終了します。")
                    winner = 0
                    break
                
                
                #user_move = input("あなたの指し手: ").strip()
                if user_move.lower() == 'q':
                    print("対局を終了します。")
                    winner = 0
                    break
                
                sfen, valid = process_user_move(sfen, user_move, moves, process, response_queue)    # プレイヤーの指し手を適用
                if not valid:
                    continue
                else:
                    break
                
            # エンジンのターン
            while True:
                #state_queue.put(sfen)
                board, _, _, _ = sfen_to_board(sfen)
                draw_board(board)
                display_board(sfen)
                print(sfen)
                
                engine_move = get_engine_move(process, response_queue)  
                sfen, valid = process_engine_move(sfen, engine_move, moves) # エンジンの指し手を適用
                if not valid:
                    continue
                else:
                    print(f"やねうら王の指し手: {engine_move}")
                    break


    except Exception as e:
        print(f"エラーが発生しました: {e}")
    finally:
        state_queue.put("q")
        stop_yaneuraou(process)
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
    
