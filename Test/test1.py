def a(board_x, board_y):
    if 0 <= board_x < 9 and 0 <= board_y < 9:
        sfen_x = 9 - board_x
        sfen_y = chr(ord('a') + board_y)
        return f"{board_x}{board_y}"  # ボード内なら座標を返す
    else:
        return None  # ボード外なら無効
    
print(a(2, 7))