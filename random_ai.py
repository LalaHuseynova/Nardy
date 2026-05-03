# random_ai_agent.py

import random
from game_logic import NardyGame


class RandomAI:
    def __init__(self, player):
        self.player = player
        self.game_logic = NardyGame()

    def get_best_sequence(self, state, dice):
        legal_sequences = self.game_logic.get_legal_move_sequences(state, dice)

        if not legal_sequences:
            return []

        return random.choice(legal_sequences)