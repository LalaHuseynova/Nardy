from copy import deepcopy
from config import NUM_POINTS, PLAYER_ONE, PLAYER_TWO, CHECKERS_PER_PLAYER


class GameState:
    def __init__(self):
        # Taxtada 24 nöqtə var (0-dan 23-ə qədər)
        self.board = [0] * NUM_POINTS

        # Hansı oyunçunun növbəsidir (1 və ya -1)
        self.current_player = PLAYER_ONE

        # Çölə çıxarılan daşların sayı (qalibiyyət üçün)
        self.borne_off = {
            PLAYER_ONE: 0,
            PLAYER_TWO: 0
        }

        # Oyunun başlanğıc vəziyyətini qururuq
        self.initialize_board()

    def initialize_board(self):
        """
        Başlanğıc vəziyyəti:
        Player 1 → 24-cü nöqtədə
        Player 2 → 12-ci nöqtədə
        """
        self.board = [0] * NUM_POINTS

        # Player 1 daşları 24-də
        self.board[23] = CHECKERS_PER_PLAYER

        # Player 2 daşları 12-də
        self.board[11] = -CHECKERS_PER_PLAYER

    def clone(self):
        """
        Oyunun cari vəziyyətinin surətini cixariqi.
        Bu AI üçün çox vacibdir (state-i dəyişmədən yoxlamaq üçün)
        """
        return deepcopy(self)

    def is_game_over(self):
        """
        Oyun bitibmi yoxlayiriqq.
        Əgər hər hansi oyunçu 15 dasini cixaribsa → oyun bitib
        """
        return (
            self.borne_off[PLAYER_ONE] == CHECKERS_PER_PLAYER or
            self.borne_off[PLAYER_TWO] == CHECKERS_PER_PLAYER
        )