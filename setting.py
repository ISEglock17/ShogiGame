import pygame
from pygame.locals import *
import pygame.mixer

#-----------------------------------------------------------------------------------
#　Pygame 初期化
#-----------------------------------------------------------------------------------

# ウィンドウサイズと座標定義
WINDOW_SIZE_X = 1600
WINDOW_SIZE_Y = 1000
BOARD_IMAGE_SIZE = 4000
BOARD_SIZE_X = 800
BOARD_SIZE_Y = 800
BOARD_POS = (145 / BOARD_IMAGE_SIZE * BOARD_SIZE_X, 152 / BOARD_IMAGE_SIZE * BOARD_SIZE_Y)  # 盤面左上
BOARD_END = (3873 / BOARD_IMAGE_SIZE * BOARD_SIZE_X, 3851 / BOARD_IMAGE_SIZE * BOARD_SIZE_Y)  # 盤面右下
CELL_SIZE = (BOARD_END[0] - BOARD_POS[0]) / 9, (BOARD_END[1] - BOARD_POS[1]) / 9  # 各マスの幅・高さ

CAPTURED_PIECES_PLACE_WIDTH, CAPTURED_PIECES_PLACE_HEIGHT = 400, 300    #駒置きの大きさ

background_color = (255, 255, 255)  # 背景色


screen = pygame.display.set_mode((WINDOW_SIZE_X, WINDOW_SIZE_Y))
pygame.display.set_caption("将棋GUI")
clock = pygame.time.Clock()
    
# 画像ロード
board_img = pygame.image.load("./image/board.png")
board_img = pygame.transform.scale(board_img, (BOARD_SIZE_X, BOARD_SIZE_Y))  # ウィンドウに合わせて縮小
piece_images = {}

# 駒画像をロード（例: ./image/pieces/P.png など）
PIECES = ["P", "+P", "L", "+L", "N", "+N", "S", "+S", "G", "B", "+B", "R", "+R", "K"]
PIECES_NAME = ["fuhyo", "to", "kyosha", "nari-kyo", "keima", "nari-kei", "ginsho", "nari-gin", "kinsho", "kakugyo", "ryuma", "hisha", "ryuou", "ousho"]
pieces_dict = dict(zip(PIECES, PIECES_NAME))
for piece in PIECES:
    image = pygame.image.load(f"./image/pieces/{pieces_dict[piece]}.png")
    piece_images[piece] = pygame.transform.scale(image, (int(CELL_SIZE[0]), int(CELL_SIZE[1]))) 

# 駒置き画像のロード
captured_pieces_place_img = pygame.image.load("./image/komaoki.png")
captured_pieces_place_img = pygame.transform.scale(captured_pieces_place_img, (CAPTURED_PIECES_PLACE_WIDTH, CAPTURED_PIECES_PLACE_HEIGHT)) # 駒置きの大きさを縮小

# マーク画像のロード
mark_img = pygame.image.load("./image/mark_frame.png")
mark_img = pygame.transform.scale(mark_img, (CELL_SIZE[0], CELL_SIZE[1])) # 駒置きの大きさを縮小
mark_img_red = pygame.image.load("./image/mark_frame2.png")
mark_img_red = pygame.transform.scale(mark_img_red, (CELL_SIZE[0], CELL_SIZE[1])) # 駒置きの大きさを縮小
mark_img2 = pygame.image.load("./image/mark_frame3.png")
mark_img2 = pygame.transform.scale(mark_img2, (CELL_SIZE[0], CELL_SIZE[1])) # 駒置きの大きさを縮小
mark_img2_red = pygame.image.load("./image/mark_frame4.png")
mark_img2_red = pygame.transform.scale(mark_img2_red, (CELL_SIZE[0], CELL_SIZE[1])) # 駒置きの大きさを縮小
legal_img = pygame.image.load("./image/mark_frame5.png")
legal_img = pygame.transform.scale(legal_img, (CELL_SIZE[0], CELL_SIZE[1])) # 駒置きの大きさを縮小
legal_img_red = pygame.image.load("./image/mark_frame6.png")
legal_img_red = pygame.transform.scale(legal_img_red, (CELL_SIZE[0], CELL_SIZE[1])) # 駒置きの大きさを縮小
system_frame_img = pygame.image.load("./image/system_frame.png")
pro_button_img = pygame.image.load("./image/pro_button.png")
not_pro_button_img = pygame.image.load("./image/not_pro_button.png")

#BGM設定
pygame.mixer.init() #初期化
beep_se = pygame.mixer.Sound("./bgm/SE/beep.mp3")
koma_se = pygame.mixer.Sound("./bgm/SE/koma_put.mp3")
pop1_se = pygame.mixer.Sound("./bgm/SE/pop1.mp3")
push_se = pygame.mixer.Sound("./bgm/SE/push.mp3")
yoroshiku_se = pygame.mixer.Sound("./bgm/SE/yoroshiku.mp3")

pygame.mixer.music.load("./bgm/battle.mp3") #読み込み
pygame.mixer.music.play(-1) #再生
pygame.mixer.music.set_volume(0.2)    

#盤面の表示
screen.fill(background_color)   # 背景を埋める
screen.blit(board_img, (0, 0))  # 盤面画像を描画
# 駒置き画像の配置
screen.blit(captured_pieces_place_img, (800, 0))    # 左側
screen.blit(captured_pieces_place_img, (800, 500))  # 右側
screen.blit(system_frame_img, (800, 300))  # 右側