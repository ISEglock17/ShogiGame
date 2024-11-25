from multiprocessing import process
from pygame.locals import *
import subprocess
import threading
import time
import re
import pygame
import sys

"""
メモ

問題点:
・まだ合法手の判別ができない。(動かせない駒の動きは検出できるが，成れるかどうか，詰みかどうかの判定ができない)
"""

def sfen_to_board(sfen):
    """ SFEN表記を解析し、盤面、手番、持ち駒、手数を返す関数 """
    # SFEN表記をスペースで分割して、各情報を取得
    board_sfen, turn, captured_pieces, move_count = sfen.split(" ")

    # 1. 盤面部分の変換
    rows = board_sfen.split("/")
    board = []
    for row in rows:
        board_row = []
        i = 0
        while i < len(row):
            char = row[i]
            if char.isdigit():
                # 数字なら、その分だけ空マスを追加
                board_row.extend(['.' for _ in range(int(char))])
                i += 1
            elif char == '+':
                # 成駒（+付き）の場合、+と次の駒を結合して一つの要素とする
                board_row.append('+' + row[i + 1])
                i += 2  # +と次の駒を一度に消費
            else:
                # それ以外は駒をそのまま追加
                board_row.append(char)
                i += 1
        board.append(board_row)


    # 2. 手番の変換

    # 3. 持ち駒の変換

    # 4. 手数の取得
    move_number = int(move_count)

    return board, turn, captured_pieces, move_number


"""
# USIプロトコルでのSFEN例
sfen = "lnsgkgsnl/1r5b1/ppppppppp/9/9/9/PPPPPPPPP/1B5R1/LNSGKGSNL"

# 駒配置をリスト形式で取得
board = sfen_to_board(sfen)

# 表示
for row in board:
    print(" ".join(row))
"""

def board_to_sfen(board, turn="b", captured_pieces=None, move_count=1):
    """ 盤面の駒配置をSFEN表記に変換 """
    # 1. 盤面を表現
    sfen_board = []
    for row in board:
        empty_count = 0
        row_sfen = ""
        for cell in row:
            if cell.strip == ".":
                empty_count += 1
            else:
                if empty_count > 0:
                    row_sfen += str(empty_count)
                    empty_count = 0
                # 駒をSFEN用に変換
                piece = cell.strip()  # 前後のスペースを取り除く
                if piece[0] == '+':
                    row_sfen += '+'
                    piece = piece[1]
                if piece.isupper():  # Player側の駒
                    row_sfen += piece[0]
                else:  # Opponent側の駒は小文字
                    row_sfen += piece[0].lower()
        if empty_count > 0:
            row_sfen += str(empty_count)
        sfen_board.append(row_sfen)

    # 盤面行ごとに '/' で区切る
    sfen_board_str = "/".join(sfen_board)

    # 2. 持ち駒を表現
        
    # 3. 最終SFEN文字列を構築
    sfen_str = f"{sfen_board_str} {turn} {captured_pieces} {move_count}"
    return sfen_str

def turn_to_turn_player(turn):
    """ 手番を先手，後手の表記に変換するメソッド """
    # 2. 手番情報の取得 ("b" なら先手, "w" なら後手)
    turn_player = "先手" if turn == "b" else "後手"
    return turn_player

def captured_display(captured_pieces):
    # 駒の種類と日本語名称
    piece_names = {
        'P': '歩', 'L': '香', 'N': '桂', 'S': '銀', 'G': '金', 'K': '玉', 'R': '飛', 'B': '角'
    }

    # 持ち駒の個数を格納する辞書
    player_pieces = {}
    opponent_pieces = {}
    
    if captured_pieces == "-":
        return "自分の持ち駒: なし / 相手の持ち駒: なし"
    
    else:
        # SFENの文字列を解析
        i = 0
        while i < len(captured_pieces):
            char = captured_pieces[i]
            if char.isdigit():
                i += 1  # 数字の次の文字に進む
                continue

            # 持ち駒の数を取得
            if i + 1 < len(captured_pieces) and captured_pieces[i + 1].isdigit():
                count = int(captured_pieces[i + 1])
                i += 2  # 駒と数を消費
            else:
                count = 1
                i += 1  # 駒のみ消費

            # 大文字：自分の駒、小文字：相手の駒
            if char.isupper():
                player_pieces[piece_names[char]] = player_pieces.get(piece_names[char], 0) + count
            else:
                opponent_pieces[piece_names[char.upper()]] = opponent_pieces.get(piece_names[char.upper()], 0) + count

        # テキスト形式に整形
        def pieces_to_text(pieces_dict):
            if pieces_dict:
                return "、".join([f"{name}{count}枚" for name, count in pieces_dict.items()])
            else:
                return "なし"

        player_text = pieces_to_text(player_pieces)
        opponent_text = pieces_to_text(opponent_pieces)

        return f"先手の持ち駒: {player_text} / 後手の持ち駒: {opponent_text}"        

# 盤面の初期化
def initialize_board():
    # 初期局面のSFEN表記
    initial_sfen = "lnsgkgsnl/1r5b1/ppppppppp/9/9/9/PPPPPPPPP/1B5R1/LNSGKGSNL b - 1"
    return initial_sfen



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
                if piece_image:
                    x = int(BOARD_POS[0] + col * CELL_SIZE[0])
                    y = int(BOARD_POS[1] + row * CELL_SIZE[1])
                    # 駒を描画
                    screen.blit(piece_image, (x, y))

def display_board(sfen):
    """ 盤面を表示するメソッド """
    board, turn, captured_pieces, move_number = sfen_to_board(sfen)

    """
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

    """
    # 盤面描画
    draw_board(board)
    pygame.display.flip()
    clock.tick(60)

    # pygame.quit()
    
    
    """
    print("    9   8   7   6   5   4   3   2   1")
    letters = "abcdefghi"
    
    # 盤面の各行を表示
    for i, row in enumerate(board, start=1):
        row_str = f"{letters[i - 1]}  "  # 初期の行ラベルにスペースを2つ加える
        for piece in row:
            if '+' in piece:
                row_str += piece + "  "  # +が含まれている場合は通常通り追加
            else:
                row_str += " " + piece + "  "  # +が含まれていない場合は前にスペースを追加
        print(row_str)
    """
    
    # 手番の表示
    print("\n手番:", turn_to_turn_player(turn))

    # 持ち駒の表示
    print(captured_display(captured_pieces))

    # 手数の表示
    print("手数:", move_number)


"""
def get_legal_moves():
    #合法手を取得
    # 現在の盤面情報をやねうら王に送信
    process.stdin.write("d\n")
    process.stdin.flush()

    # やねうら王の出力から合法手を取得
    legal_moves = []
    while True:
        output = process.stdout.readline().strip()
        if "Legal moves" in output:
            legal_moves_line = output.split(":")[1].strip()
            legal_moves = legal_moves_line.split()
            break
    return legal_moves



def validate_move(user_move):
    #有効手か調べる
    legal_moves = get_legal_moves()
    if user_move not in legal_moves:
        messagebox.showerror("Invalid Move", "This move is not legal. Please try again.")
        return False
    return True
"""


def apply_move(sfen, move):
    """ 指し手を盤面に適用し、駒を取る・成り動作・持ち駒のSFEN表記更新・打ち駒に対応するメソッド """
    board, turn, captured_pieces_sfen, move_number = sfen_to_board(sfen)
    
    # SFEN形式の持ち駒を辞書に変換する
    captured_pieces = {}
    i = 0
    if captured_pieces_sfen != '-':
        while i < len(captured_pieces_sfen):
            char = captured_pieces_sfen[i]
            if char.isdigit():
                i += 1
                continue
            if i + 1 < len(captured_pieces_sfen) and captured_pieces_sfen[i + 1].isdigit():
                count = int(captured_pieces_sfen[i + 1])
                i += 2
            else:
                count = 1
                i += 1
            captured_pieces[char] = captured_pieces.get(char, 0) + count

    try:
        # 成りの指示があるかを判定
        is_promotion = move[-1] == '+'
        if is_promotion:
            move = move[:-1]  # 成り記号を除去

        # 打ち駒の判定（例：P*7f のような形式か確認）
        is_drop = '*' in move
        if is_drop:
            piece = move[0].upper() if turn == "b" else move[0].lower()
            to_row, to_col = ord(move[3]) - ord('a'), 9 - int(move[2])

            # 持ち駒から駒を減らす
            if piece in captured_pieces:
                captured_pieces[piece] -= 1
                if captured_pieces[piece] == 0:
                    del captured_pieces[piece]
            else:
                print(f"エラー: {piece}を持ち駒に持っていません。")
                return -1

            # 駒を盤面に打つ
            board[to_row][to_col] = f" {piece.upper()} " if turn == "b" else f" {piece.lower()} "
        
        else:
            # 指し手を座標に変換
            from_row, from_col = ord(move[1]) - ord('a'), 9 - int(move[0])
            to_row, to_col = ord(move[3]) - ord('a'), 9 - int(move[2])
            
            # 駒を取得して移動元を空にする
            piece = board[from_row][from_col]
            board[from_row][from_col] = " . "
            
            # 移動先に駒があれば捕獲する
            captured_piece = board[to_row][to_col].strip()
            if captured_piece and captured_piece != ".":
                if captured_piece[0] == '+':
                    captured_piece = captured_piece[1]
                captured_piece_name = captured_piece.upper() if turn == "b" else captured_piece.lower()
                count = captured_pieces.get(captured_piece_name, 0) + 1
                captured_pieces[captured_piece_name] = count
            
            # 成り処理
            if is_promotion:
                piece = f"+{piece.strip()}"
            
            # 駒を移動先に配置
            board[to_row][to_col] = piece
                
        # 持ち駒を SFEN 形式に変換
        if not captured_pieces:  # 持ち駒が空の場合
            captured_pieces_str = "-"
        else:
            captured_pieces_str = ""
            for piece, count in sorted(captured_pieces.items(), key=lambda x: x[0]):
                if count > 1:
                    captured_pieces_str += f"{piece}{count}"
                else:
                    captured_pieces_str += piece

        
        # 次の手番に切り替え
        turn = "b" if turn == "w" else "w"
        move_number += 1
        
        # 新しいSFENを生成して返す
        return board_to_sfen(board, turn, captured_pieces_str, move_number)
    
    except (ValueError, IndexError):
        print(f"無効な指し手の形式です: {move}。 '7g7f' または 'P*7f' のように入力してください。")
        return -1


# やねうら王の応答を読み取る
def read_output(process, response_queue):
    while True:
        output = process.stdout.readline()
        if output == '' and process.poll() is not None:
            break
        if output:
            print(f"やねうら王の応答: {output.strip()}")
            if any(keyword in output for keyword in ["readyok", "bestmove", "Error"]):
                response_queue.append(output.strip())

# やねうら王を起動
def run_yaneuraou():
    executable_path = "./YaneuraOu_NNUE_halfKP256-V830Git_ZEN2.exe"
    
    process = subprocess.Popen(
        [executable_path], 
        stdin=subprocess.PIPE, 
        stdout=subprocess.PIPE, 
        stderr=subprocess.PIPE, 
        text=True,
        encoding='shift_jis'
    )

    response_queue = []
    thread = threading.Thread(target=read_output, args=(process, response_queue))
    thread.start()

    # やねうら王の準備コマンド
    initial_commands = ["usi\n", "isready\n", "usinewgame\n"]
    for command in initial_commands:
        process.stdin.write(command)
        process.stdin.flush()
        time.sleep(0.5)

    while "readyok" not in response_queue:
        time.sleep(0.1)

    response_queue.pop(0)
    sfen = initialize_board()
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

            if apply_move(sfen, user_move) == -1:
                continue
            else:
                sfen = apply_move(sfen, user_move)
            display_board(sfen)
            print(sfen)
            
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
                        
                        if apply_move(sfen, yaneuraou_move) == -1:
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
        
    





                    

#**********************************************
#　　　　初期化
#**********************************************
import pygame

# ウィンドウサイズと座標定義
WINDOW_SIZE = 800
BOARD_IMAGE_SIZE = 4000
BOARD_POS = (145 / BOARD_IMAGE_SIZE * WINDOW_SIZE, 152 / BOARD_IMAGE_SIZE * WINDOW_SIZE)  # 盤面左上
BOARD_END = (3873 / BOARD_IMAGE_SIZE * WINDOW_SIZE, 3851 / BOARD_IMAGE_SIZE * WINDOW_SIZE)  # 盤面右下
CELL_SIZE = (BOARD_END[0] - BOARD_POS[0]) / 9, (BOARD_END[1] - BOARD_POS[1]) / 9  # 各マスの幅・高さ

#**********************************************
#　　　　メイン処理
#**********************************************
if __name__ == "__main__":
    # 初期化と設定
    pygame.init()
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
        
    run_yaneuraou()
    
    
    #イベント処理
    for event in pygame.event.get():
        if event.type == QUIT: #閉じるボタンが押されたら終了
            pygame.quit() #Pygameの終了(画面閉じられる)
            sys.exit()

