#-----------------------------------------------------------------------------------
#　将棋の表示に関する関数
#-----------------------------------------------------------------------------------
import subprocess
import threading
from multiprocessing import process
import time
from concurrent.futures import thread
import re
import pygame
from pygame.locals import *
import sys
import pygame.mixer
    
#-----------------------------------------------------------------------------------
#　Pygame 初期化
#-----------------------------------------------------------------------------------

# ウィンドウサイズと座標定義
WINDOW_SIZE_X = 1600
WINDOW_SIZE_Y = 1000
BOARD_IMAGE_SIZE = 4000
BOARD_SIZE_X = 800
BOARD_SIZE_Y = 800
BOARD_POS = (145 / BOARD_IMAGE_SIZE * BOARD_SIZE_X, 152 / BOARD_IMAGE_SIZE * BOARD_SIZE_Y)  # 盤面左上
BOARD_END = (3873 / BOARD_IMAGE_SIZE * BOARD_SIZE_X, 3851 / BOARD_IMAGE_SIZE * BOARD_SIZE_Y)  # 盤面右下
CELL_SIZE = (BOARD_END[0] - BOARD_POS[0]) / 9, (BOARD_END[1] - BOARD_POS[1]) / 9  # 各マスの幅・高さ

CAPTURED_PIECES_PLACE_WIDTH, CAPTURED_PIECES_PLACE_HEIGHT = 400, 300    #駒置きの大きさ

background_color = (255, 255, 255)  # 背景色


screen = pygame.display.set_mode((WINDOW_SIZE_X, WINDOW_SIZE_Y))
pygame.display.set_caption("将棋GUI")
clock = pygame.time.Clock()
    
# 画像ロード
board_img = pygame.image.load("./image/board.png")
board_img = pygame.transform.scale(board_img, (BOARD_SIZE_X, BOARD_SIZE_Y))  # ウィンドウに合わせて縮小
piece_images = {}

# 駒画像をロード（例: ./image/pieces/P.png など）
PIECES = ["P", "+P", "L", "+L", "N", "+N", "S", "+S", "G", "B", "+B", "R", "+R", "K"]
PIECES_NAME = ["fuhyo", "to", "kyosha", "nari-kyo", "keima", "nari-kei", "ginsho", "nari-gin", "kinsho", "kakugyo", "ryuma", "hisha", "ryuou", "ousho"]
pieces_dict = dict(zip(PIECES, PIECES_NAME))
for piece in PIECES:
    image = pygame.image.load(f"./image/pieces/{pieces_dict[piece]}.png")
    piece_images[piece] = pygame.transform.scale(image, (int(CELL_SIZE[0]), int(CELL_SIZE[1]))) 

# 駒置き画像のロード
captured_pieces_place_img = pygame.image.load("./image/komaoki.png")
captured_pieces_place_img = pygame.transform.scale(captured_pieces_place_img, (CAPTURED_PIECES_PLACE_WIDTH, CAPTURED_PIECES_PLACE_HEIGHT)) # 駒置きの大きさを縮小

# マーク画像のロード
mark_img = pygame.image.load("./image/mark_frame.png")
mark_img = pygame.transform.scale(mark_img, (CELL_SIZE[0], CELL_SIZE[1])) # 駒置きの大きさを縮小
mark_img_red = pygame.image.load("./image/mark_frame2.png")
mark_img_red = pygame.transform.scale(mark_img_red, (CELL_SIZE[0], CELL_SIZE[1])) # 駒置きの大きさを縮小
mark_img2 = pygame.image.load("./image/mark_frame3.png")
mark_img2 = pygame.transform.scale(mark_img2, (CELL_SIZE[0], CELL_SIZE[1])) # 駒置きの大きさを縮小
mark_img2_red = pygame.image.load("./image/mark_frame4.png")
mark_img2_red = pygame.transform.scale(mark_img2_red, (CELL_SIZE[0], CELL_SIZE[1])) # 駒置きの大きさを縮小
legal_img = pygame.image.load("./image/mark_frame5.png")
legal_img = pygame.transform.scale(legal_img, (CELL_SIZE[0], CELL_SIZE[1])) # 駒置きの大きさを縮小
legal_img_red = pygame.image.load("./image/mark_frame6.png")
legal_img_red = pygame.transform.scale(legal_img_red, (CELL_SIZE[0], CELL_SIZE[1])) # 駒置きの大きさを縮小
system_frame_img = pygame.image.load("./image/system_frame.png")
pro_button_img = pygame.image.load("./image/pro_button.png")
not_pro_button_img = pygame.image.load("./image/not_pro_button.png")

#BGM設定
pygame.mixer.init() #初期化
beep_se = pygame.mixer.Sound("./bgm/SE/beep.mp3")
koma_se = pygame.mixer.Sound("./bgm/SE/koma_put.mp3")
pop1_se = pygame.mixer.Sound("./bgm/SE/pop1.mp3")
push_se = pygame.mixer.Sound("./bgm/SE/push.mp3")
yoroshiku_se = pygame.mixer.Sound("./bgm/SE/yoroshiku.mp3")

pygame.mixer.music.load("./bgm/battle.mp3") #読み込み
pygame.mixer.music.play(-1) #再生
pygame.mixer.music.set_volume(0.2)    

#盤面の表示
screen.fill(background_color)   # 背景を埋める
screen.blit(board_img, (0, 0))  # 盤面画像を描画
# 駒置き画像の配置
screen.blit(captured_pieces_place_img, (800, 0))    # 左側
screen.blit(captured_pieces_place_img, (800, 500))  # 右側
screen.blit(system_frame_img, (800, 300))  # 右側


#-----------------------------------------------------------------------------------
#　盤面表示 関数
#-----------------------------------------------------------------------------------
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
            if cell.strip() == ".":
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
    """ 持ち駒の表示 """
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
            if i + 1 < len(captured_pieces) and captured_pieces[i + 1].isdigit():   # 駒の数もあるなら
                count = int(captured_pieces[i + 1])
                i += 2  # 駒と数を消費
            else:   # 駒が1個のみなら
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


def display_board(sfen):
    """ 盤面を表示するメソッド """
    board, turn, captured_pieces, move_number = sfen_to_board(sfen)
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


def move_to_coord(move, turn = "b"):
    """ 
    move(7fやP*)などを座標変換する関数
    """
    # 駒の種類と対応する from_col 値
    piece_to_col = {
        "P": 0,  # 歩
        "L": 1,  # 香車
        "N": 2,  # 桂馬
        "R": 3,  # 飛車
        "B": 4,  # 角
        "S": 5,  # 銀
        "G": 6   # 金
    }
    from_row, from_col = None, None  # from_rowとfrom_colの初期化
    
    if len(move) == 2:
        if move[0].isdigit() and 'a' <= move[1] <= 'i':
            from_row, from_col = ord(move[1]) - ord('a'), 9 - int(move[0])    
        elif move[1] == '*' and move[0].isalpha():
            if turn == "b":   #先手番なら
                from_row = -1
            else:   # 後手番なら
                from_row = -2
                    
            from_col = piece_to_col[move[0]]
    return from_row, from_col


def extract_move_suffixes(legal_moves_list, user_move1):
    """ 
    # user_move1の最初の2文字を取り出す
    # 使用例
    legal_moves_list = ['B*5g', '7g7f', 'P*7f', '5g5f']
    user_move1 = 'B*5g'

    # 該当する後半2文字をリストとして抽出
    suffixes = extract_move_suffixes(legal_moves_list, user_move1)
    print(suffixes)  # 出力例: ['5g']
    """
    # user_move1の最初の2文字を取り出す
    user_move_prefix = user_move1[:2]

    # 一致する指し手の後半部分を格納するリスト
    suffixes = []

    # legal_moves_listの中から一致する指し手を探す
    for move in legal_moves_list:
        # 指し手の最初の2文字が一致する場合
        if move[:2] == user_move_prefix:
            # 一致する場合、その後半の2文字をリストに追加
            suffixes.append(move[2:])
    
    # 一致する指し手がない場合は空のリストを返す
    return suffixes



def is_promotable(board, move1, move2):
    """ 
    成れるか判定する関数
    条件1: 動かす前の駒が成れる駒
    条件2: 動かす前の座標が敵陣地
    条件3: 動かした後の座標が敵陣地
    """
    promotable_pieces = ["P", "L", "N", "R", "B", "S"]  # 成れる駒
    move_before = move_to_coord(move1)
    move_after = move_to_coord(move2)
    
    move_before_row, move_before_col = move_to_coord(move1)
    move_after_row, move_after_col = move_to_coord(move2)
    # move_to_coordの結果が無効な場合は処理を中止
    if move_before_row is None or move_before_col is None or move_after_row is None or move_after_col is None:
        print("無効な指し手です")
        return False
    
    
    if 0 <= move_before[0] <= 8: # 動かす前のマスが盤面上か
        piece = board[move_before[0]][move_before[1]]    
        if piece.upper() in promotable_pieces:  # 動かす駒が成れる駒か
            if 0 <= move_before[0] <= 2 or 0 <= move_after[0] <= 2:
                return True
    return False


#-----------------------------------------------------------------------------------
#　Pygame 盤面表示 関数
#-----------------------------------------------------------------------------------
def convert_click_to_board(click_pos):
    """クリック位置をボード上のSFEN座標に変換"""
    x, y = click_pos
    
    # 盤面のクリックチェック        
    board_x = int((x - BOARD_POS[0]) / CELL_SIZE[0])
    board_y = int((y - BOARD_POS[1]) / CELL_SIZE[1])
    if 0 <= board_x < 9 and 0 <= board_y < 9:
        sfen_x = 9 - board_x
        sfen_y = chr(ord('a') + board_y)
        return f"{sfen_x}{sfen_y}"  # ボード内なら座標を返す
    else:
        # 持ち駒の座標範囲
        opponent_positions = {
            "P": (865, 0), "L": (955, 0), "N": (1045, 0),
            "R": (900, 100), "B": (1020, 100),
            "S": (900, 200), "G": (1020, 200),
        }
        player_positions = {
            "P": (865, 500), "L": (955, 500), "N": (1045, 500),
            "R": (900, 600), "B": (1020, 600),
            "S": (900, 700), "G": (1020, 700),
        }

        # 持ち駒のクリックチェック
        for piece, (px, py) in opponent_positions.items():
            if px <= x <= px + CELL_SIZE[0] and py <= y <= py + CELL_SIZE[1]:
                return f"{piece}*"

        for piece, (px, py) in player_positions.items():
            if px <= x <= px + CELL_SIZE[0] and py <= y <= py + CELL_SIZE[1]:
                return f"{piece}*"
            
        # 成りボタンのクリックチェック
        # ボタンの位置とサイズ
        pro_button_rect = pygame.Rect(810, 390, 120, 100)  # 成ボタンの位置とサイズ
        not_pro_button_rect = pygame.Rect(950, 390, 120, 100)  # 不成ボタンの位置とサイズ
         # クリック位置が成ボタンに含まれる場合
        if pro_button_rect.collidepoint(click_pos):
            return "+"
        
        # クリック位置が不成ボタンに含まれる場合
        if not_pro_button_rect.collidepoint(click_pos):
            return ""

            
        return None  # ボード外なら無効
    
    
    
def draw_board(board, turn = "b", captured_pieces = "-", move_number = 1, mark_cells = [], pro_flag = False):
    """
    SFEN解析済みの盤面データをもとに描画
    board: 2Dリスト形式の盤面
    turn: 手番
    captured_pieces: 持ち駒
    move_number: 手数
    mark_cells: マークするマス
    legal_mark: 合法手のマーキング
    """
    screen.blit(board_img, (0, 0))  # 盤面画像を描画
    # 駒置き画像の配置
    screen.blit(captured_pieces_place_img, (800, 0))    # 左側
    screen.blit(captured_pieces_place_img, (800, 500))  # 右側
    screen.blit(system_frame_img, (800, 300))  # 右側
    legal_mark = []
    
    # 成るボタンの描画
    if pro_flag:
        screen.blit(pro_button_img, (810, 390))  # 右側
        screen.blit(not_pro_button_img, (950, 390))  # 右側
    
    # マークの描画
    if mark_cells:
        legal_mark = [(x, y, z) for x, y, z in mark_cells if z == 5]
        mark_cells = [(x, y, z) for x, y, z in mark_cells if z != 5]
        draw_marked_cells(mark_cells)
        
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

    if legal_mark:
        draw_marked_cells(legal_mark)
    
    # 持ち駒の表示
    draw_captured(captured_pieces)
    
    font_path = "./image/07やさしさゴシック.ttf"  # フォントファイルのパス
    font = pygame.font.Font(font_path, 24)  # フォントとサイズ（変更可能）
    #font = pygame.font.Font(None, 36)  # フォントとサイズ（変更可能）
    
    # 手番の表示
    turn_text = turn_to_turn_player(turn)
    turn_surface = font.render(f"手番: {turn_text}", True, (0, 0, 15))  # 青色で描画
    screen.blit(turn_surface, (820, 320))  # (820, 320) の位置に表示

    # 手数の表示
    move_text = f"手数: {move_number}"
    move_surface = font.render(move_text, True, (0, 0, 15))  # 青色で描画
    screen.blit(move_surface, (820, 360))  # (820, 360) の位置に表示

def draw_marked_cells(mark_cells):
    """
    マークされたセルを描画
    :param mark_cells: マークするセルのリスト
    """
    # 持ち駒の座標範囲
    opponent_positions = {
        "P": (865, 0), "L": (955, 0), "N": (1045, 0),
        "R": (900, 100), "B": (1020, 100),
        "S": (900, 200), "G": (1020, 200),
    }
    player_positions = {
        "P": (865, 500), "L": (955, 500), "N": (1045, 500),
        "R": (900, 600), "B": (1020, 600),
        "S": (900, 700), "G": (1020, 700),
    }
    
    piece_to_col = {
        "P": 0,  # 歩
        "L": 1,  # 香車
        "N": 2,  # 桂馬
        "R": 3,  # 飛車
        "B": 4,  # 角
        "S": 5,  # 銀
        "G": 6   # 金
    }

    for from_row, from_col, color in mark_cells:
        
        if from_row is None or from_col is None:
            break
        
        # マスが盤上の場合
        if 0 <= from_row < 9 and 0 <= from_col < 9:
            x = int(BOARD_POS[0] + from_col * CELL_SIZE[0])
            y = int(BOARD_POS[1] + from_row * CELL_SIZE[1])
        
        # 持ち駒エリアの場合
        elif from_row == -1 or from_row == -2:
            positions = player_positions if from_row == -1 else opponent_positions
            for piece, (px, py) in positions.items():
                if piece_to_col[piece] == from_col:
                    x, y = px, py
                    break

        # マークを描画
        if color == 1:
            screen.blit(mark_img, (x, y))
        elif color == 2:
            screen.blit(mark_img_red, (x, y))
        elif color == 3:
            screen.blit(mark_img2, (x, y))
        elif color == 4:
            screen.blit(mark_img2_red, (x, y))
        elif color == 5:
            screen.blit(legal_img, (x, y))
        elif color == 6:
            screen.blit(legal_img_red, (x, y))
        else:
            pass

def draw_captured(captured_pieces):
    """ 持ち駒の画面描画 """
    # 持ち駒の個数を格納する辞書
    player_pieces = {}
    opponent_pieces = {}
    
    if captured_pieces == "-":
        pass
    
    else:
        # SFENの文字列を解析
        i = 0
        while i < len(captured_pieces):
            char = captured_pieces[i]
            if char.isdigit():
                i += 1  # 数字の次の文字に進む
                continue

            # 持ち駒の数を取得
            if i + 1 < len(captured_pieces) and captured_pieces[i + 1].isdigit():   # 駒の数もあるなら
                count = int(captured_pieces[i + 1])
                i += 2  # 駒と数を消費
            else:   # 駒が1個のみなら
                count = 1
                i += 1  # 駒のみ消費

            # 大文字：自分の駒、小文字：相手の駒
            if char.isupper():
                player_pieces[char] = player_pieces.get(char, 0) + count
            else:
                opponent_pieces[char.upper()] = opponent_pieces.get(char.upper(), 0) + count

        # 駒を描画する座標
        opponent_positions = {
            "P": (865, 0), "L": (955, 0), "N": (1045, 0),
            "R": (900, 100), "B": (1020, 100),
            "S": (900, 200), "G": (1020, 200),
        }
        player_positions = {
            "P": (865, 500), "L": (955, 500), "N": (1045, 500),
            "R": (900, 600), "B": (1020, 600),
            "S": (900, 700), "G": (1020, 700),
        }
        
        # フォントの設定
        font = pygame.font.Font(None, 30)  # フォントとサイズの設定

        # 相手の持ち駒を描画
        for piece, count in opponent_pieces.items():
            if piece in opponent_positions:
                x, y = opponent_positions[piece]
                screen.blit(piece_images[piece], (x, y))  # 駒を描画
                # 枚数を描画
                count_text = font.render(str(count), True, (224, 255, 255))  # 黒い文字
                screen.blit(count_text, (x + 65, y + 75))  # 駒の右下に表示

        # 自分の持ち駒を描画
        for piece, count in player_pieces.items():
            if piece in player_positions:
                x, y = player_positions[piece]
                screen.blit(piece_images[piece], (x, y))  # 駒を描画
                # 枚数を描画
                count_text = font.render(str(count), True, (224, 255, 255))  # 黒い文字
                screen.blit(count_text, (x + 65, y + 75))  # 駒の右下に表示        

#-----------------------------------------------------------------------------------
#　やねうら王の動作
#-----------------------------------------------------------------------------------
def start_yaneuraou(executable_path):
    """やねうら王のプロセスを起動"""
    process = subprocess.Popen(
        [executable_path],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding='shift_jis'
    )
    return process


def stop_yaneuraou(process):
    """やねうら王のプロセスを終了"""
    if process:
        process.terminate()
        process.wait()

def send_command(process, command):
    """やねうら王にコマンドを送信"""
    process.stdin.write(command + "\n")
    process.stdin.flush()


def read_output(process, response_queue):
    """ やねうら王の応答を非同期で読みとる関数 """
    while True:
        output = process.stdout.readline()
        if output == '' and process.poll() is not None:
            break
        if output:
            print(f"やねうら王の応答: {output.strip()}")
            if any(keyword in output for keyword in ["readyok", "bestmove", "multipv", "Error", "mate", "info"]):
                response_queue.append(output.strip())


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
    
    

#-----------------------------------------------------------------------------------
#　ゲームの流れ
#-----------------------------------------------------------------------------------

# def legal_moves(process, response_queue):
#     """ 合法手一覧を取得する"""
#     legal_moves = []
    
#     command = f"legal_moves"
#     send_command(process, command)    
#     time.sleep(0.1)
    
#     # 合法手かの確認
#     if response_queue:
#         response = response_queue.pop(0)
#         if "legal_moves" in response:
#             legal_moves = response.strip()
#             print(legal_moves)
#             return legal_moves[1:]


def is_checkmate(process, response_queue, sfen, max_depth=1, timeout=3):
    """
    詰みかどうかを判定するメソッド
    
    Args:
        process: やねうら王のプロセス
        response_queue: エンジン応答を格納するキュー
        sfen: 現在の局面 (SFEN形式)
        max_depth: 詰み探索の深さ (デフォルトは1手詰み)
    
    Returns:
        True: 詰み
        False: 詰みでない
    """
    # SFEN局面を設定
    send_command(process, f"position sfen {sfen}")
    time.sleep(0.1)

    # 詰み探索コマンドを送信
    send_command(process, f"go mate {max_depth}")
    time.sleep(0.1)

    # タイムアウトを設定して応答を待機
    start_time = time.time()
    while time.time() - start_time < timeout:
        # キューが空でないか確認
        if response_queue:  # リストが空でない
            response = response_queue.pop(0)  # 先頭の応答を取得
            if "mate found" in response:  # 詰みが見つかった場合
                return False
        # 応答待機時間を短縮
        time.sleep(0.05)

    # タイムアウト時には詰みと判断しない
    return False

    # タイムアウト時は詰みではないとみなす
    return False


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
            moves.pop() # moveを取り消す
            return sfen, False
    
    # 指し手が有効なら盤面を更新
    result = apply_move(sfen, user_move)
    if result != -1:
        sfen = result
        return sfen, True
    else:
        print("無効な指し手です。")
        moves.pop() # moveを取り消す
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


def process_engine_move(sfen, engine_move, moves):
    """
    やねうら王の指し手を処理する。
    合法であれば盤面を更新し、合法性を返す。
    """
    new_sfen = apply_move(sfen, engine_move)
    if new_sfen != -1:
        moves.append(engine_move)
        return new_sfen, True
    else:
        moves.pop() # moveを取り消す
        return sfen, False

