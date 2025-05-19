import json
import time
from cshogi import Board
from board import EffectBoard
from shogi_engine import start_yaneuraou, stop_yaneuraou, send_command, get_score
from kifu_parse6 import parse_kif_file
from shogi_sub import process_user_move

def load_kif_data(filepath):
    """棋譜データを読み込む"""
    with open(filepath, 'r', encoding='utf-8') as f:
        kif_data = f.readlines()
    return parse_kif_file(kif_data)

def generate_dataset(kif_data, process, response_queue):
    """
    棋譜データをもとにデータセットを生成
    """
    dataset = []
    sfen = "lnsgkgsnl/1r5b1/ppppppppp/9/9/9/PPPPPPPPP/1B5R1/LNSGKGSNL b - 1"  # 初期盤面
    moves = []  # 棋譜リスト

    for i, move_info in enumerate(kif_data["moves"]):
        jp_move = move_info["move"]
        from_pos = move_info["from_pos"]

        # SFEN形式に変換
        board = Board()
        board.set_sfen(sfen)
        ef = EffectBoard(board)  # 利き情報
        legal_moves_list = [move for move in board.legal_moves]

        # やねうら王に指し手を送信して評価値と読み筋を取得
        position_command = f"position startpos moves {' '.join(moves)}"
        send_command(process, position_command)
        send_command(process, "setoption name MultiPV value 10")
        time.sleep(0.1)
        bestmoves, comments, legal_moves_evaluations = get_score(process, response_queue)

        # データ構造に追加
        dataset.append({
            "turn": "b" if i % 2 == 0 else "w",  # 手番
            "sfen": sfen,
            "legal_moves": [move.usi() for move in legal_moves_list],
            "effect_board": ef.effect_board,  # 利き情報
            "evaluation": legal_moves_evaluations,  # 評価値リスト
            "bestmove": bestmoves[0] if bestmoves else None,  # 最善手
            "reading": comments  # 読み筋
        })

        # 次の手を処理
        sfen, valid = process_user_move(sfen, jp_move, moves, process, response_queue)
        if not valid:
            print(f"不正な手: {jp_move}")
            break

    return dataset

def save_dataset(dataset, output_path):
    """データセットをJSON形式で保存"""
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(dataset, f, ensure_ascii=False, indent=4)

def main():
    """メイン処理"""
    # 棋譜データの読み込み
    kif_data = load_kif_data("./ShogiData/kif_clean/10001.txt")

    # やねうら王のプロセスを起動
    process = start_yaneuraou("./YaneuraOu_NNUE_halfKP256-V830Git_ZEN2.exe")
    response_queue = []
    
    # データセットを生成
    dataset = generate_dataset(kif_data, process, response_queue)

    # データセットを保存
    save_dataset(dataset, "./ShogiData2/dataset.json")

    # やねうら王のプロセスを終了
    stop_yaneuraou(process)

if __name__ == "__main__":
    main()