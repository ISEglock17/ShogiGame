import pygame
from pygame.locals import *
import pygame.mixer
from shogi_board import *
from setting import *

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
        legal_mark = [(x, y, z) for x, y, z in mark_cells if z in (5, 6)]
        mark_cells = [(x, y, z) for x, y, z in mark_cells if z not in (5, 6)]
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
    move_text = f"手数: {move_number - 1}"
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

    