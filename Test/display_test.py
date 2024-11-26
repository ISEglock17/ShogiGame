import subprocess
import threading
import time
import re

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


def apply_move(sfen, move):
    """ 指し手を盤面に適用し、駒を取る・成り動作・持ち駒のSFEN表記更新・打ち駒に対応するメソッド """
    board, turn, captured_pieces_sfen, move_number = sfen_to_board(sfen)
    
    # SFEN形式の持ち駒を辞書に変換する
    captured_pieces = {}
    i = 0
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


sfen = initialize_board()
sfen = "lnsgkgsnl/1r5b1/ppppppppp/9/9/9/PPPPPPPPP/9/LNSGKGSNL b BR 1"
print(sfen)
display_board(sfen)

while True:
    move = input("駒の動きは: ")
    if move != 'q':
        sfen = apply_move(sfen, move)
        display_board(sfen)
        print(sfen)
        continue
    else:
        break