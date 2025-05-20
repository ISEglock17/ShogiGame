from square import Square

class EffectBoard:
    def __init__(self, board):
        """
        Args:
            board (list[list[str]]): 9x9の将棋盤 (SFEN形式)
        """
        self.board = board
        self.effect_board = []
        self._initialize_effect_board()
        self.update_effects()

    def _initialize_effect_board(self):
        """board の駒配置を基に effect_board を初期化"""
        for row in range(len(self.board)):
            row_list = []
            for col in range(len(self.board[row])):
                piece = self.board[row][col]
                row_list.append(Square(row, col, piece))
            self.effect_board.append(row_list)

    def update_effects(self):
        """すべての駒の利きを更新"""
        # まず全マスの利き情報をクリア
        for row in range(9):
            for col in range(9):
                square = self.effect_board[row][col]
                square.effects.clear()
                square.effecteds.clear()

        # 各駒の利きを計算
        for row in range(9):
            for col in range(9):
                square = self.effect_board[row][col]
                if square.piece != '.':  # 駒がある場合のみ処理
                    self._calculate_effects(square)

    def _calculate_effects(self, square):
        """指定された駒の利きを計算し、effects/effecteds に登録"""
        piece = square.piece
        row, col = square.row, square.col
        directions = []
        slide = False  # 遠距離移動の駒かどうか

        if piece.lower() == 'p':  # 歩
            directions = [(-1, 0)] if piece.isupper() else [(1, 0)]
        elif piece.lower() == 'l':  # 香車
            slide = True
            directions = [(-1, 0)] if piece.isupper() else [(1, 0)]
        elif piece.lower() == 'n':  # 桂馬
            directions = [(-2, -1), (-2, 1)] if piece.isupper() else [(2, -1), (2, 1)]
        elif piece.lower() == 's':  # 銀
            directions = [(-1, -1), (-1, 0), (-1, 1), (1, -1), (1, 1)] if piece.isupper() else [(1, -1), (1, 0), (1, 1), (-1, -1), (-1, 1)]
        elif piece.lower() in ['g', 'k', '+p', '+n', '+l', '+s']:  # 金 or 王
            directions = [(-1, 0), (0, -1), (0, 1), (1, 0)]
            if piece not in ['g', '+p', '+n', '+l', '+s']:
                directions += [(-1, -1), (-1, 1)]
            if piece not in ['G', '+P', '+N', '+L', '+S']:
                directions += [(1, -1), (1, 1)]
        elif piece.lower() in ['b', '+b']:  # 角
            slide = True
            directions += [(1, 1), (-1, -1), (1, -1), (-1, 1)]
            if piece.lower() == '+b':  # 成角
                directions += [(-1, 0), (0, -1), (1, 0), (0, 1)]
        elif piece.lower() in ['r', '+r']:  # 飛車
            slide = True
            directions += [(1, 0), (-1, 0), (0, 1), (0, -1)]
            if piece.lower() == '+r':  # 成飛車
                directions += [(-1, -1), (-1, 1), (1, -1), (1, 1)]

        # 計算した利きを登録（障害物検知あり）
        for dr, dc in directions:
            nr, nc = row + dr, col + dc
            while 0 <= nr < 9 and 0 <= nc < 9:
                target_square = self.effect_board[nr][nc]
                square.add_effects(target_square)  # この駒が利かせるマス
                target_square.add_effecteds(square)  # そのマスが影響を受ける

                if slide:  # 遠距離移動の駒は障害物で停止
                    if target_square.piece != '.':  # 他の駒があればストップ
                        break
                    nr += dr
                    nc += dc
                else:  # 1マス移動の駒は1回だけ処理
                    break
                
    def print_effect(self):
        """各駒の利きを表示"""
        for row in self.effect_board:
            for square in row:
                if square.piece != '.':
                    effect_positions = [f"{self.coord_to_sfen(s.row, s.col)}({s.piece})" for s in square.effects]
                    print(f"{self.coord_to_sfen(square.row, square.col)}({square.piece}) -> {effect_positions}")
                
    def collect_effect_data(self):
        """
        各駒の利き情報をデータセット形式で収集
        例: 4i(G) -> ['4h(.)', '5i(K)', '3i(S)', '5h(.)', '3h(.)']
        
        {
            "4i(G)": ["4h(.)", "5i(K)", "3i(S)", "5h(.)", "3h(.)"],
            "3i(S)": ["4h(.)", "3h(.)", "2h(R)"],
            "2i(N)": ["3g(P)", "1g(P)"],
            "1i(L)": ["1h(.)", "1g(P)"],
            ...
        }
        """
        effect_data = {}
        for row in self.effect_board:
            for square in row:
                if square.piece != '.':  # 駒がある場合のみ処理
                    # 現在の駒の位置と種類
                    current_position = self.coord_to_sfen(square.row, square.col)
                    current_piece = square.piece
                    key = f"{current_position}({current_piece})"

                    # 利き先の情報を収集
                    effect_positions = [
                        f"{self.coord_to_sfen(s.row, s.col)}({s.piece})" for s in square.effects
                    ]
                    effect_data[key] = effect_positions
        return effect_data

    def coord_to_sfen(self, board_row, board_col):
        """
            座標からSFEN形式に変換する
            例: 9a(l) -> ['9b(.)', '9c(p)']
        """
        if 0 <= board_row < 9 and 0 <= board_col < 9:
            sfen_x = 9 - board_col
            sfen_y = chr(ord('a') + board_row)
        return f"{sfen_x}{sfen_y}"
                
    def print_effect2(self):
        """
            各駒の利きを表示
            デバッグ向けに，マスの(row, col)を表示する。
            例: l (0, 0) -> [('.', 1, 0), ('p', 2, 0)]
        """
        for row in self.effect_board:
            for square in row:
                if square.piece != '.':
                    effect_positions = [(s.piece, s.row, s.col) for s in square.effects]
                    print(f"{square.piece} ({square.row}, {square.col}) -> {effect_positions}")

def main():
    board = [['l', 'n', 's', 'g', 'k', 'g', 's', 'n', 'l'], ['.', 'r', '.', '.', '.', '.', '.', 'b', '.'], ['p', 'p', 'p', 'p', 'p', 'p', 'p', 'p', 'p'], ['.', '.', '.', '.', '.', '.', '.', '.', '.'], ['.', '.', '.', '.', '.', '.', '.', '.', '.'], ['.', '.', '.', '.', '.', '.', '.', '.', '.'], ['P', 'P', 'P', 'P', 'P', 'P', 'P', 'P', 'P'], ['.', 'B', '.', '.', '.', '.', '.', 'R', '.'], ['L', 'N', 'S', 'G', 'K', 'G', 'S', 'N', 'L']]         
    ef = EffectBoard(board)
    ef.print_effect()

    import json
    # 利き情報を収集
    effect_data = ef.collect_effect_data()

    # 利き情報を表示（デバッグ用）
    print("利き情報:")
    for key, value in effect_data.items():
        print(f"{key} -> {value}")

    # 利き情報をJSON形式で保存
    output_path = "effect_dataset.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(effect_data, f, ensure_ascii=False, indent=4)

    print(f"利き情報を {output_path} に保存しました。")


if __name__ == "__main__":
    main()
    