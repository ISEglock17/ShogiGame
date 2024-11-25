import subprocess
import threading
import time
import re

# 駒の略称（英語）
player_pieces = {
    "歩": " P ", "香": " L ", "桂": " N ", "銀": " S ", "金": " G ", "玉": " K ", "飛": " R ", "角": " B "
}
opponent_pieces = {k: f" {v.strip().lower()} " for k, v in player_pieces.items()}  # 相手の駒は小文字で表示

# 空白のマスの表記
empty_square = " . "

# 盤面の初期化
def initialize_board():
    board = [
        [opponent_pieces["香"], opponent_pieces["桂"], opponent_pieces["銀"], opponent_pieces["金"], opponent_pieces["玉"], opponent_pieces["金"], opponent_pieces["銀"], opponent_pieces["桂"], opponent_pieces["香"]],
        [empty_square, opponent_pieces["飛"], empty_square, empty_square, empty_square, empty_square, empty_square, opponent_pieces["角"], empty_square],
        [opponent_pieces["歩"], opponent_pieces["歩"], opponent_pieces["歩"], opponent_pieces["歩"], opponent_pieces["歩"], opponent_pieces["歩"], opponent_pieces["歩"], opponent_pieces["歩"], opponent_pieces["歩"]],
        [empty_square] * 9,
        [empty_square] * 9,
        [empty_square] * 9,
        [player_pieces["歩"], player_pieces["歩"], player_pieces["歩"], player_pieces["歩"], player_pieces["歩"], player_pieces["歩"], player_pieces["歩"], player_pieces["歩"], player_pieces["歩"]],
        [empty_square, player_pieces["角"], empty_square, empty_square, empty_square, empty_square, empty_square, player_pieces["飛"], empty_square],
        [player_pieces["香"], player_pieces["桂"], player_pieces["銀"], player_pieces["金"], player_pieces["玉"], player_pieces["金"], player_pieces["銀"], player_pieces["桂"], player_pieces["香"]],
    ]
    return board

# 盤面を表示する関数
def display_board(board):
    print("    a  b  c  d  e  f  g  h  i")
    for i, row in enumerate(board):
        print(f"{9 - i}  " + "".join(row))

# USI形式の指し手を座標に変換する関数
def parse_usi_move(move):
    if not re.match(r'^[1-9][a-i][1-9][a-i]$', move):
        raise ValueError("Invalid move format.")
    
    from_pos = (9 - int(move[1]) + 1, ord(move[0]) - ord('a'))
    to_pos = (9 - int(move[3]) + 1, ord(move[2]) - ord('a'))
    return from_pos, to_pos

# 指し手を処理し盤面を更新する関数
def make_move(board, move, player="player"):
    try:
        from_pos, to_pos = parse_usi_move(move)
        piece = board[from_pos[0]][from_pos[1]]
        
        # プレイヤーが動かせない駒が選択された場合のエラーハンドリング
        if player == "player" and piece not in player_pieces.values():
            print("Invalid move: Cannot move opponent's piece.")
            return False

        # 指定のマスに駒を移動
        board[from_pos[0]][from_pos[1]] = empty_square
        board[to_pos[0]][to_pos[1]] = piece
        return True
    except Exception as e:
        print(f"Error while moving: {e}")
        return False

# メイン関数
def run_game():
    board = initialize_board()
    display_board(board)
    
    while True:
        move = input("Enter your move (e.g., 7g7f) or 'q' to quit: ")
        if move == 'q':
            print("Game ended.")
            break

        if not re.match(r'^[1-9][a-i][1-9][a-i]$', move):
            print("Invalid move format. Please enter move in the format '7g7f'.")
            continue

        # プレイヤーの指し手を実行
        if make_move(board, move):
            display_board(board)

            # やねうら王に次の手を要求（仮の処理）
            # ここでやねうら王の応答処理を挿入
            # やねうら王の指し手に応じて `make_move(board, move, player="opponent")` を呼び出す
            yaneuraou_move = "2g2f"  # ダミーの指し手（例）
            print("YaneuraOu's move:", yaneuraou_move)
            make_move(board, yaneuraou_move, player="opponent")
            display_board(board)

run_game()
