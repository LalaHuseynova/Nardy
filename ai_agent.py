from game_state import GameState
from game_logic import NardyGame
from config import PLAYER_ONE, PLAYER_TWO, CHECKERS_PER_PLAYER

class NardyAI:
    def __init__(self, player, max_depth=3):
        self.player = player
        self.opponent = -player
        self.max_depth = max_depth
        self.game_logic = NardyGame()

    def get_best_sequence(self, state, dice):
        sequences = self.game_logic.get_legal_move_sequences(state, dice)
        if not sequences:
            return []

        best_seq = None
        best_value = float("-inf")

        for seq in sequences:
            after_ai = self.game_logic.apply_move_sequence(state, seq)

            value = self._expectiminimax(after_ai, depth=1)

            if value > best_value:
                best_value = value
                best_seq = seq

        return best_seq if best_seq is not None else []

    def _expectiminimax(self, state, depth):
        if depth >= self.max_depth or state.is_game_over():
            return self._evaluate(state)

        total = 0.0
        for dice_outcome, prob in self._dice_outcomes_with_probabilities():
            total += prob * self._decision_value(state, dice_outcome, depth)
        return total

    def _decision_value(self, state, dice, depth):
        player_to_move = state.current_player
        sequences = self.game_logic.get_legal_move_sequences(state, dice)

        if not sequences:
            passed_state = state.clone()
            passed_state.current_player *= -1
            return self._expectiminimax(passed_state, depth + 1)

        values = []

        for seq in sequences:
            after = self.game_logic.apply_move_sequence(state, seq)
            values.append(self._expectiminimax(after, depth + 1))

        if player_to_move == self.player:
            return max(values)
        else:
            return min(values)

    def _dice_outcomes_with_probabilities(self):
        outcomes = []

        for d in range(1, 7):
            outcomes.append(([d, d, d, d], 1.0 / 36.0))

        for d1 in range(1, 7):
            for d2 in range(d1 + 1, 7):
                outcomes.append(([d1, d2], 2.0 / 36.0))

        return outcomes

    def _evaluate(self, state: GameState):
        if state.borne_off[self.player] >= CHECKERS_PER_PLAYER:
            return 100000.0

        if state.borne_off[self.opponent] >= CHECKERS_PER_PLAYER:
            return -100000.0

        ai = self.player
        opp = self.opponent

        ai_pips = self._pip_count(state, ai)
        opp_pips = self._pip_count(state, opp)
        pip_score = (opp_pips - ai_pips) * 1.2

        borne_score = (state.borne_off[ai] - state.borne_off[opp]) * 20.0

        ai_blots = self._count_blots(state, ai)
        opp_blots = self._count_blots(state, opp)
        blot_score = (opp_blots - ai_blots) * 1.0

        ai_blocks = self._count_blocks(state, ai)
        opp_blocks = self._count_blocks(state, opp)
        block_score = (ai_blocks - opp_blocks) * 4.0

        ai_home = self._count_in_home(state, ai)
        opp_home = self._count_in_home(state, opp)
        home_score = (ai_home - opp_home) * 3.0

        return pip_score + borne_score + blot_score + block_score + home_score

    def _pip_count(self, state, player):
        path = self.game_logic.get_player_path(player)
        total = 0
        for idx, cnt in enumerate(state.board):
            if player == PLAYER_ONE and cnt > 0:
                count = cnt
            elif player == PLAYER_TWO and cnt < 0:
                count = -cnt
            else:
                continue

            pos = self.game_logic.get_path_position(player, idx)
            steps = len(path) - pos
            total += count * steps
        return total

    def _count_blots(self, state, player):
        blots = 0
        for idx in range(24):
            if player == PLAYER_ONE and state.board[idx] == 1:
                blots += 1
            elif player == PLAYER_TWO and state.board[idx] == -1:
                blots += 1
        return blots

    def _count_blocks(self, state, player):
        blocks = 0
        for idx in range(24):
            cnt = state.board[idx] if player == PLAYER_ONE else -state.board[idx]
            if cnt >= 2:
                blocks += 1
        return blocks

    def _count_in_home(self, state, player):
        home_points = self.game_logic.home_board_points(player)
        home_count = 0

        for idx in home_points:
            cnt = state.board[idx]

            if player == PLAYER_ONE and cnt > 0:
                home_count += cnt
            elif player == PLAYER_TWO and cnt < 0:
                home_count += -cnt

        return home_count
