import re
from board import *  

def classify_kif_move(move):
    """ 
        パターン分けする関数
         A': r'^[1-9][一二三四五六七八九](成)?[歩香桂銀金角飛と馬竜玉王]$', #通常指し手(2六歩, 3二成銀)
        'B': r'^同(成)?[歩香桂銀金角飛と馬竜玉王]$',    #同マス(同角)
        'C': r'(右|左|直|引|上|寄)',    #方向指定(右, 左, 上, 引, 直, 寄)
        'D': r'打',     #打ち駒(打)
        'E': r'(成|不成)$', #成り/不成(成, 不成)
    """
    patterns = {
        'A': r'^[1-9][一二三四五六七八九](成)?[歩香桂銀金角飛と馬竜玉王]$', #通常指し手(2六歩, 3二成銀)
        'B': r'^同(成)?[歩香桂銀金角飛と馬竜玉王]$',    #同マス(同角)
        'C': r'(右|左|直|引|上|寄)',    #方向指定(右, 左, 上, 引, 直, 寄)
        'D': r'打',     #打ち駒(打)
        'E': r'(成|不成)$', #成り/不成(成, 不成)
    }

    result = []

    # パターンB（同）かどうか
    if re.match(patterns['B'], move):
        result.append('B')
    # パターンA（通常）かどうか
    elif re.match(patterns['A'], move):
        result.append('A')
    
    # 以下はサブ要素として複合チェック
    if re.search(patterns['C'], move):
        result.append('C')
    if re.search(patterns['D'], move):
        result.append('D')
    if re.search(patterns['E'], move) and 'E' not in result:
        result.append('E')

    if not result:
        result.append("不明")

    return result

def to_sfen_coord(row, col):
    file = 9 - col  # SFENでは右が1
    rank = chr(ord('a') + row)  # a〜i
    return f"{file}{rank}"

kanji_nums = {'一': 0, '二': 1, '三': 2, '四': 3, '五': 4, '六': 5, '七': 6, '八': 7, '九': 8}

def parse_japanese_coord(jstr):
    if len(jstr) != 2: return None
    file = int(jstr[0])
    rank = kanji_nums.get(jstr[1], None)
    if rank is None: return None
    col = 9 - file
    row = rank
    return (row, col)


def extract_piece_name(move):
    for p in ['と', '成銀', '成桂', '成香', '成歩', '馬', '竜', '歩', '香', '桂', '銀', '金', '角', '飛', '玉', '王']:
        if p in move:
            return convert_piece_to_sfen_symbol(p)
    return None

def normalize_piece(piece):
    return piece.upper().replace('+', '')

def convert_piece_to_sfen_symbol(piece_name):
    table = {
        '歩': 'P', '香': 'L', '桂': 'N', '銀': 'S', '金': 'G',
        '角': 'B', '飛': 'R', '玉': 'K', '王': 'K',
        'と': '+P', '成香': '+L', '成桂': '+N', '成銀': '+S', '成歩': '+P',
        '馬': '+B', '竜': '+R'
    }
    return table.get(piece_name, '?')

kanji_nums = {'一': 0, '二': 1, '三': 2, '四': 3, '五': 4, '六': 5, '七': 6, '八': 7, '九': 8}

def get_target_coord(move):
    """
    日本語棋譜の指し手から (row, col) を返す
    例: '7七角' → (6, 2)
    """
    if move.startswith("同"):
        # 「同」の処理には履歴が必要（ここでは仮に None を返す）
        return None
    
    # 指し手から座標部分（例: "7七"）を抽出
    for i in range(len(move)-1):
        if move[i].isdigit() and move[i+1] in kanji_nums:
            file = int(move[i])
            rank = kanji_nums[move[i+1]]
            col = 9 - file
            row = rank
            return (row, col)
    
    return None  # 該当しない場合

def direction_filter(candidates, target, direction_text, player):
    filtered = []

    for c in candidates:
        d_row = c.row - target[0] 
        d_col = c.col - target[1] 

        if direction_text == '右' and ((player == 'b' and d_col > 0) or (player == 'w' and d_col < 0)):
            filtered.append(c)
            print(c.print_square())
        elif direction_text == '左' and ((player == 'b' and d_col < 0) or (player == 'w' and d_col > 0)):
            filtered.append(c)
        elif direction_text == '直' and ((player == 'b' and d_row > 0) or (player == 'w' and d_row < 0)):
            filtered.append(c)
        elif direction_text == '引' and ((player == 'b' and d_row < 0) or (player == 'w' and d_row > 0)):
            filtered.append(c)
        elif direction_text == '上' and ((player == 'b' and d_row > 0) or (player == 'w' and d_row < 0)):
            filtered.append(c)
        elif direction_text == '寄' and d_row == 0:
            filtered.append(c)

    return filtered

def convert_to_sfen(japanese_move, effect_board, last_to_sq=None, turn='b', legal_moves_list=None):
    """ 
        棋譜(日本語表記)をSFENに変換する関数
        japanese_move: 棋譜(日本語表記)
        effect_board: 利き情報付き盤面情報
        last_to_sq: 最後に動かした手(SFEN)
        turn
    """
    patterns = classify_kif_move(japanese_move)

    is_same = japanese_move.startswith("同")
    is_drop = 'D' in patterns
    is_promotion = 'E' in patterns and ('成' in japanese_move and '不成' not in japanese_move)
    piece = extract_piece_name(japanese_move)
    
    # ターゲット座標を決定（"同" のときは直前の移動先を使用）
    if is_same:
        if last_to_sq is None:
            print(f"同〇の処理に失敗（直前手なし）: {japanese_move}")
            return None
        else:
            # 例: last_to_sq = "7f7g"
            to_sq_str = last_to_sq[2:]  # "7g"

            # "7g" → col = 9 - 7 = 2, row = ord('g') - ord('a') = 6
            file = int(to_sq_str[0])  # '7' → 7
            rank_char = to_sq_str[1]  # 'g'
            col = 9 - file            # SFENでは右が1、左が9
            row = ord(rank_char) - ord('a')  # 'a'〜'i' → 0〜8

            target_coord = (row, col)  # → (6, 2)
    else:
        target_coord = get_target_coord(japanese_move)

    if target_coord is None:
        print(f"不正な棋譜です: {japanese_move}")
        return None

    to_sq = to_sfen_coord(*target_coord)

    if is_drop:
        return f"{piece}*{to_sq}"

    effecteds = effect_board.effect_board[target_coord[0]][target_coord[1]].effecteds
    candidates = [sq for sq in effecteds if sq.piece == piece]

    # パターンCの方向指定があれば、さらに絞り込み
    if 'C' in patterns:
        for direction in ['右', '左', '直', '引', '上', '寄']:
            if direction in japanese_move:
                candidates = direction_filter(candidates, target_coord, direction, turn)
                break

    if len(candidates) == 1:
        from_sq = candidates[0]
        from_coord = to_sfen_coord(from_sq.row, from_sq.col)
        return f"{from_coord}{to_sq}{'+' if is_promotion else ''}"
    elif len(candidates) > 1:
        print(f"考えられる手が複数あります: {japanese_move}, 候補手: {[to_sfen_coord(c.row, c.col) for c in candidates]}")
        return None
    else:
        print(f"候補手がありません: {japanese_move}")
        return None


def main():    
    """        
        与えられるべき変数
        board: 盤面情報
        turn: 現在の手番
        last_move: 最後に動かした手(SFEN)
        legal_moves_list: 合法手リスト
    """    
    board = [  # SFEN的な9x9リスト
    ['l','n','s','g','k','g','s','n','l'],
    ['.','r','.','.','.','.','.','.','.'],
    ['p','p','p','p','p','p','p','p','p'],
    ['.','.','.','.','.','b','.','.','.'],
    ['.','.','.','+B','.','.','.','.','.'],
    ['.','.','p','.','.','.','.','.','.'],
    ['P','P','.','G','P','P','P','.','P'],
    ['.','B','.','.','.','.','.','R','.'],
    ['L','N','S','G','K','G','S','N','L']
]

    ef = EffectBoard(board)
    
    # japanese_move = "7七角"
    print('利き情報は')
    ef.print_effect()
    turn = input('現在の手番は(b/w): ')
    japanese_move = input('棋譜を入力してください: ')
    last_move_coord = input('最後に打った手のSFENを入力してください: ')
    
    sfen_move = convert_to_sfen(japanese_move, ef, last_to_sq=last_move_coord, turn=turn)
    print(sfen_move)  # 例: 8h7g

"""
    test_moves = [
        "2六歩",      # A
        "3二成銀",    # A, E
        "同角",       # B
        "6八銀右",    # A, C
        "5六金打",    # A, D
        "2三歩成",    # A, E
        "同銀左成",   # B, C, E
        "3四桂打成",  # A, D, E（※実戦ではまれ）
    ]

    for move in test_moves:
        print(f"{move} → パターン: {classify_kif_move(move)}")

   
    # 出力例: 
    # 2六歩 → パターン: ['A']
    # 3二成銀 → パターン: ['A']
    # 同角 → パターン: ['B']
    # 6八銀右 → パターン: ['C']
    # 5六金打 → パターン: ['D']
    # 2三歩成 → パターン: ['E']
    # 同銀左成 → パターン: ['C', 'E']
    # 3四桂打成 → パターン: ['D', 'E']
   
"""

if __name__ == "__main__":
    main()
    