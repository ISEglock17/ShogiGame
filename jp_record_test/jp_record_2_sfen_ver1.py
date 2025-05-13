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

def get_target_coord(move, effect_board=None):
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


def convert_to_sfen(japanese_move, effect_board):
    patterns = classify_kif_move(japanese_move)
    
    is_same = japanese_move.startswith("同")
    is_drop = 'D' in patterns
    is_promotion = 'E' in patterns and ('成' in japanese_move and '不成' not in japanese_move)
    piece = extract_piece_name(japanese_move)  # 駒種の抽出
    target_coord = get_target_coord(japanese_move, effect_board)

    if is_same:
        print(f"同〇のため，棋譜の履歴が必要です: {japanese_move}")
        return None

    if target_coord is None:
        print(f"不正な棋譜です: {japanese_move}")
        return None

    to_sq = to_sfen_coord(*target_coord)

    if is_drop:
        return f"{piece}*{to_sq}"  # 打ち手：P*7f のような形式

    # 利きから移動元を特定
    effecteds = effect_board.effect_board[target_coord[0]][target_coord[1]].effecteds
    candidates = [sq for sq in effecteds if normalize_piece(sq.piece) == piece]

    # 条件に合う駒をさらに絞り込む（方向指定なども反映可能）
    if len(candidates) == 1:
        from_sq = candidates[0]
        from_coord = to_sfen_coord(from_sq.row, from_sq.col)
        return f"{from_coord}{to_sq}{'+' if is_promotion else ''}"
    elif len(candidates) > 1:
        print(f"Ambiguous move: {japanese_move}, candidates: {[to_sfen_coord(c.row, c.col) for c in candidates]}")
        # 方向指定の判別ロジックなどでさらに絞り込む処理を追加可能
        return None
    else:
        print(f"No candidate found for move: {japanese_move}")
        return None


def main():    
    board = [  # SFEN的な9x9リスト
    ['l','n','s','g','k','g','s','n','l'],
    ['.','r','.','.','.','.','.','b','.'],
    ['p','p','p','p','p','p','p','p','p'],
    ['.','.','.','.','.','.','.','.','.'],
    ['.','.','.','.','.','.','.','.','.'],
    ['.','.','p','.','.','.','.','.','.'],
    ['P','P','.','P','P','P','P','.','P'],
    ['.','B','.','.','.','.','.','R','.'],
    ['L','N','S','G','K','G','S','N','L']
]

    ef = EffectBoard(board)
    
    # japanese_move = "7七角"
    japanese_move = input('棋譜を入力してください: ')
    sfen_move = convert_to_sfen(japanese_move, ef)
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
    