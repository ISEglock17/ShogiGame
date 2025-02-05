#-----------------------------------------------------------------------------------
#　将棋の表示に関する関数
#-----------------------------------------------------------------------------------
import time
import re
from shogi_board import *
from shogi_engine import *
from setting import *

#-----------------------------------------------------------------------------------
#　ゲームの流れ
#-----------------------------------------------------------------------------------
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
    comments = []
    
    send_command(process, "go depth 10")
    
    start_time = time.time()
    
    while True:
        while response_queue:
            response = response_queue.pop(0)
            if "bestmove" in response:
                move = response.split(" ")[1]
                # bestmove が見つかった時点で直前の count 件を返却
                return move, comments
            
            # bestmove が見つかる前のレスポンスを格納
            comments.append(response)   
       
        # if response_queue:
        #     response = response_queue.pop()
        #     if "bestmove" in response:
        #         move = response.split(" ")[1]
        #         return move
        if time.time() - start_time > 10:  # タイムアウトの処理
            print("応答が遅延しています。再送信します。")
            send_command(process, "go depth 10")
        time.sleep(0.1)
        

def get_score(process, response_queue):
    """やねうら王の評価値を取得"""
    bestmoves = []
    comments = []
    scores = []
    flag = False
    send_command(process, "go depth 10")
    time.sleep(0.1)        
    # 各手に対する評価値と読み筋を保存するための辞書
    moves_info = {}
    
    while True:
        while response_queue:
            response = response_queue.pop(0)
            if "info multipv" in response:
                parts = response.split()
                move = parts[parts.index("pv") + 1]  # 手
                eval_value = parts[parts.index("score") + 2]  # 評価値
                pred_moves = parts[parts.index("pv") + 1:-1]  # 読み筋
                comments.append(response)
                
                # 手ごとに最も深い読みの情報を保存
                if move not in moves_info:
                    moves_info[move] = {
                        "eval_value": eval_value,
                        "eval_values": [eval_value],
                        "pred_moves": pred_moves
                    }
                else:
                    moves_info[move]["eval_value"] = eval_value
                    moves_info[move]["pred_moves"] = pred_moves
                    moves_info[move]["eval_values"].append(eval_value)
                
                # scores.append((move, eval_value, pred_moves))
                flag = True
            if not flag and "info depth" in response:
                # 応答を分割
                parts = response.split()
                move = parts[parts.index("pv") + 1]  # 手
                eval_value = parts[parts.index("score") + 2]  # 評価値
                pred_moves = parts[parts.index("pv") + 1:]  # 読み筋
                comments.append(response)
                
                # 手ごとに最も深い読みの情報を保存
                if move not in moves_info:
                    moves_info[move] = {
                        "eval_value": eval_value,
                        "eval_values": [eval_value],
                        "pred_moves": pred_moves
                    }
                else:
                    moves_info[move]["eval_value"] = eval_value
                    moves_info[move]["pred_moves"] = pred_moves
                    moves_info[move]["eval_values"].append(eval_value)
                
                        
            if "bestmove" in response:
                bestmove = response.split(" ")[1]
                bestmoves.append(bestmove)
                comments.append(response) 
            
        # moves_info を scores リストに変換
        scores = [(move, info['eval_value'], ' '.join(info['pred_moves']), info['eval_values']) for move, info in moves_info.items()]     
       
        return bestmoves, comments, scores
        


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


# def is_checkmate(process, response_queue, sfen, max_depth=1, timeout=3):
#     """
#     詰みかどうかを判定するメソッド
    
#     Args:
#         process: やねうら王のプロセス
#         response_queue: エンジン応答を格納するキュー
#         sfen: 現在の局面 (SFEN形式)
#         max_depth: 詰み探索の深さ (デフォルトは1手詰み)
    
#     Returns:
#         True: 詰み
#         False: 詰みでない
#     """
#     # SFEN局面を設定
#     send_command(process, f"position sfen {sfen}")
#     time.sleep(0.1)

#     # 詰み探索コマンドを送信
#     send_command(process, f"go mate {max_depth}")
#     time.sleep(0.1)

#     # タイムアウトを設定して応答を待機
#     start_time = time.time()
#     while time.time() - start_time < timeout:
#         # キューが空でないか確認
#         if response_queue:  # リストが空でない
#             response = response_queue.pop(0)  # 先頭の応答を取得
#             if "mate found" in response:  # 詰みが見つかった場合
#                 return False
#         # 応答待機時間を短縮
#         time.sleep(0.05)

#     # タイムアウト時には詰みと判断しない
#     return False

#     # タイムアウト時は詰みではないとみなす
#     return False