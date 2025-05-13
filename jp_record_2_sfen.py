import re
from board import *  
from shogi_board import *       # 盤面解析に関する関数を読み込み
from cshogi import *    #やねうら王の補助プログラム


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


def extract_piece_name(move, turn):
    for p in ['と', '成銀', '成桂', '成香', '成歩', '馬', '竜', '龍', '歩', '香', '桂', '銀', '金', '角', '飛', '玉', '王']:
        if p in move:
            return convert_piece_to_sfen_symbol(p, turn)
    return None

def normalize_piece(piece):
    return piece.upper().replace('+', '')

def convert_piece_to_sfen_symbol(piece_name, turn='b'):
    table = {
        '歩': 'P', '香': 'L', '桂': 'N', '銀': 'S', '金': 'G',
        '角': 'B', '飛': 'R', '玉': 'K', '王': 'K',
        'と': '+P', '成香': '+L', '成桂': '+N', '成銀': '+S', '成歩': '+P',
        '馬': '+B', '竜': '+R', '龍': '+R'
    }

    symbol = table.get(piece_name)
    if symbol is None:
        return '?'

    if turn == 'w':
        # 後手の場合はすべて小文字（+記号はそのまま）
        if symbol.startswith('+'):
            return '+' + symbol[1].lower()
        else:
            return symbol.lower()
    else:
        # 先手はそのまま（大文字）
        return symbol

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
    filtered = candidates  # 最初は全候補

    if '右' in direction_text:
        filtered = [
            c for c in filtered
            if (player == 'b' and c.col > target[1]) or (player == 'w' and c.col < target[1])
        ]
    if '左' in direction_text:
        filtered = [
            c for c in filtered
            if (player == 'b' and c.col < target[1]) or (player == 'w' and c.col > target[1])
        ]
    if '直' in direction_text:
        filtered = [
            c for c in filtered
            if (player == 'b' and c.row > target[0] and c.col == target[1]) or (player == 'w' and c.row < target[0] and c.col == target[1])
        ]
    if '引' in direction_text:
        filtered = [
            c for c in filtered
            if (player == 'b' and c.row < target[0]) or (player == 'w' and c.row > target[0])
        ]
    if '上' in direction_text:
        filtered = [
            c for c in filtered
            if (player == 'b' and c.row > target[0]) or (player == 'w' and c.row < target[0])
        ]
    if '寄' in direction_text:
        filtered = [c for c in filtered if c.row == target[0]]

    return filtered

def num_to_sq(num):
    if num is None or num == "":
        return None
    try:
        num = int(num)
    except ValueError:
        return None
    if not (11 <= num <= 99):
        return None
    file = num // 10  # 9 → 1
    rank = chr(ord('a') + (num % 10) - 1)  # 1 → a, 9 → i
    return f"{file}{rank}"


def convert_to_sfen(japanese_move, effect_board, last_to_sq=None, turn='b', legal_moves_list=None, from_num=None):
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
    piece = extract_piece_name(japanese_move, turn)
    
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
        # 打ち駒の手を確認して合法手リストに追加
        move_str = f"{piece.upper()}*{to_sq}"
        if move_str not in legal_moves_list:
            print(f"不正な打ち駒: {move_str}")
            return None
        return move_str

    
    effecteds = effect_board.effect_board[target_coord[0]][target_coord[1]].effecteds
    candidates = [sq for sq in effecteds if sq.piece == piece]
    
    # 打ち駒を候補に追加（合法手で、piece * target に一致するもの）
    drop_candidate = f"{piece.upper()}*{to_sq}"
    if legal_moves_list is not None and drop_candidate in legal_moves_list:
        # 打ち駒の位置情報を仮に持ったオブジェクトを作って追加（from_sqの再現に必要）
        class Drop:
            def __init__(self, piece):
                self.row = -1  # 架空の位置
                self.col = -1
                self.piece = piece
                self.is_drop = True
        candidates.append(Drop(piece))

    # パターンCの方向指定があれば、さらに絞り込み
    if 'C' in patterns:
        # 複合方向文字をすべて含んだ文字列を作成
        direction_text = ''.join([d for d in ['右', '左', '直', '引', '上', '寄'] if d in japanese_move])
        if direction_text:
            candidates = direction_filter(candidates, target_coord, direction_text, turn)


    """
    print(f"手番: {turn}")
    print(f"ターゲット: {target_coord}, 移動元候補: {[ (c.row, c.col, c.piece) for c in candidates ]}")
    print(legal_moves_list)
    """

    if len(candidates) == 1:
        from_sq = candidates[0]
            
        if hasattr(from_sq, 'is_drop') and from_sq.is_drop:
                    move_str = f"{piece.upper()}*{to_sq}"
        else:
            from_coord = to_sfen_coord(from_sq.row, from_sq.col)
            move_str = f"{from_coord}{to_sq}{'+' if is_promotion else ''}"

        if legal_moves_list is not None and move_str not in legal_moves_list:
            print(f"不正な指し手: {move_str}")
            return None
                
        return move_str        
    elif len(candidates) > 1:
        if from_num is not None:
            for cand in candidates:
                from_sq = cand
            
                if hasattr(from_sq, 'is_drop') and from_sq.is_drop:
                            move_str = f"{piece.upper()}*{to_sq}"
                else:
                    from_coord = to_sfen_coord(from_sq.row, from_sq.col)
                    move_str = f"{from_coord}{to_sq}{'+' if is_promotion else ''}"

                if len(move_str) >= 4 and move_str[:2] == num_to_sq(from_num):
                    return move_str  # from_sqが一致する候補があればそれを返す
            
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
    ['.','r','.','.','g','.','.','.','.'],
    ['p','p','p','S','S','S','p','p','p'],
    ['.','.','.','G','.','G','.','.','.'],
    ['.','.','.','S','S','S','.','.','.'],
    ['.','.','p','.','.','.','.','.','.'],
    ['P','P','.','G','P','P','P','.','P'],
    ['.','B','.','.','.','.','.','R','.'],
    ['L','N','S','G','K','G','S','N','L']
]
 
    
    ef = EffectBoard(board)
    # japanese_move = "7七角"
    """
    print('利き情報は')
    ef.print_effect()
    """
    turn = input('現在の手番は(b/w): ')
    japanese_move = input('棋譜を入力してください: ')
    last_move_coord = input('最後に打った手のSFENを入力してください: ')
    from_num = input('移動元があれば入力してください: ')
    captured_pieces = 'S2Pb3p'
    
    sfen = board_to_sfen(board, turn=turn, captured_pieces=captured_pieces)
    # print(sfen)
    # sfen = "lnsgkgsnl/1r5b1/ppppppppp/9/9/9/PPPPPPPPP/1B5R1/LNSGKGSNL b - 1"
    # print(sfen)
    board2 = Board()  # cshogi用のボード
    board2.set_sfen(sfen)
    legal_moves_list = [move_to_usi(move) for move in board2.legal_moves]
    
    sfen_move = convert_to_sfen(japanese_move, ef, last_to_sq=last_move_coord, turn=turn, legal_moves_list=legal_moves_list, from_num=from_num)
    if sfen_move is not None:
        print(f"{japanese_move}を変換すると，{sfen_move}")  # 例: 8h7g
    
    """
    print()
    print("―補足情報―")
    print(board)
    print(f"合法手リストは，{legal_moves_list}")
    """    

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
    