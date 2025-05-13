class Square():
    """
        マスを示すクラス
        row (int): マスの行
        col (int): マスの列
        piece (str): 駒の種類
        effects (list): 利かせている位置
        effected (list): 利かされている位置
    """
    def __init__(self, row: int, col: int, piece: str):
        """
        Args:
            row (int): マスの行
            col (int): マスの列
            piece (str): 駒の種類
        """
        self.row = row  #座標
        self.col = col
        self.piece = piece
        self.effects = []
        self.effecteds = []
    
    def add_effects(self, squere):
        self.effects.append(squere)
    
    def add_effecteds(self, squere):
        self.effecteds.append(squere)
        
    def get_coord(self):
        return (self.row, self.col)
    
    def print_square(self):
        print(f"マスの行: {self.row}")
        print(f"マスの列: {self.col}")
        print(f"駒の種類: {self.piece}")
        print(f"利かせている位置: {self.effects}")
        print(f"利かされている位置: {self.effecteds}")