# ai_agent.py – Improved Expectiminimax with Depth 3 and Better Heuristics
from game_state import GameState
from game_logic import NardyGame
from config import PLAYER_ONE, PLAYER_TWO, CHECKERS_PER_PLAYER

class NardyAI:
    def __init__(self, player, max_depth=3):
        self.player = player          # 1 or -1
        self.opponent = -player
        self.max_depth = max_depth
        self.game_logic = NardyGame()

    def get_best_sequence(self, state, dice):
        sequences = self.game_logic.get_legal_move_sequences(state, dice)
        if not sequences:
            return []

        # Optional: order sequences by a quick heuristic for better pruning
        sequences.sort(key=lambda seq: self._quick_eval(state, seq), reverse=True)

        best_seq = None
        best_value = float('-inf')

        for seq in sequences:
            after_ai = self.game_logic.apply_move_sequence(state, seq)
            value = self._expectiminimax(after_ai, depth=0)
            if value > best_value:
                best_value = value
                best_seq = seq

        return best_seq if best_seq is not None else []

    def _expectiminimax(self, state, depth):
        if depth >= self.max_depth or state.is_game_over():
            return self._evaluate(state)

        # Chance node: average over all dice outcomes
        total = 0.0
        for dice_outcome, prob in self._dice_outcomes_with_probabilities():
            total += prob * self._decision_value(state, dice_outcome, depth)
        return total

    def _decision_value(self, state, dice, depth):
        player_to_move = state.current_player
        sequences = self.game_logic.get_legal_move_sequences(state, dice)

        if not sequences:
            # Pass turn without moving
            passed_state = state.clone()
            passed_state.current_player *= -1
            return self._expectiminimax(passed_state, depth + 1)

        values = []
        for seq in sequences:
            after = self.game_logic.apply_move_sequence(state, seq)
            values.append(self._expectiminimax(after, depth + 1))

        if player_to_move == self.player:
            return max(values)
        return min(values)

    def _dice_outcomes_with_probabilities(self):
        outcomes = []
        # Doubles (11,22,33,44,55,66) each 1/36
        for d in range(1, 7):
            outcomes.append(([d, d, d, d], 1.0 / 36.0))
        # Non-doubles (d1,d2) with d1<d2, each 2/36
        for d1 in range(1, 7):
            for d2 in range(d1+1, 7):
                outcomes.append(([d1, d2], 2.0 / 36.0))
        return outcomes

    def _evaluate(self, state: GameState):
        # Terminal win/loss
        if state.borne_off[self.player] >= CHECKERS_PER_PLAYER:
            return 100000.0
        if state.borne_off[self.opponent] >= CHECKERS_PER_PLAYER:
            return -100000.0

        ai = self.player
        opp = self.opponent

        # Pip difference: more weight (was 0.5, now 1.2)
        ai_pips = self._pip_count(state, ai)
        opp_pips = self._pip_count(state, opp)
        pip_diff = (opp_pips - ai_pips) * 1.2

        # Borne-off difference (still important)
        borne_diff = (state.borne_off[ai] - state.borne_off[opp]) * 20.0

        # Blot penalty: own blots hurt, opponent blots help (scale increased)
        ai_blots = self._count_blots(state, ai)
        opp_blots = self._count_blots(state, opp)
        blot_score = (opp_blots - ai_blots) * 8.0

        # Block reward: owning 2+ checkers in a point helps control
        ai_blocks = self._count_blocks(state, ai)
        opp_blocks = self._count_blocks(state, opp)
        block_score = (ai_blocks - opp_blocks) * 4.0

        # NEW: Home board density – reward having many checkers in the last 6 points
        ai_home_count = self._count_in_home(state, ai)
        opp_home_count = self._count_in_home(state, opp)
        home_bonus = (ai_home_count - opp_home_count) * 3.0

        return pip_diff + borne_diff + blot_score + block_score + home_bonus

    def _pip_count(self, state, player):
        path = self.game_logic.get_player_path(player)
        total = 0
        for idx, cnt in enumerate(state.board):
            if (player == PLAYER_ONE and cnt > 0) or (player == PLAYER_TWO and cnt < 0):
                count = cnt if player == PLAYER_ONE else -cnt
                pos = self.game_logic.get_path_position(player, idx)
                steps = len(path) - pos
                total += count * steps
        return total

    def _count_blots(self, state, player):
        blots = 0
        for idx in range(24):
            if (player == PLAYER_ONE and state.board[idx] == 1) or (player == PLAYER_TWO and state.board[idx] == -1):
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
        """Number of player's checkers inside the home board (last 6 points on path)."""
        home_points = self.game_logic.home_board_points(player)
        home_cnt = 0
        for idx in range(24):
            if (player == PLAYER_ONE and state.board[idx] > 0) or (player == PLAYER_TWO and state.board[idx] < 0):
                if idx in home_points:
                    cnt = state.board[idx] if player == PLAYER_ONE else -state.board[idx]
                    home_cnt += cnt
        return home_cnt

    def _quick_eval(self, state, sequence):
        """Fast heuristic to order sequences before full search (optional)."""
        temp = state.clone()
        for move in sequence:
            temp = self.game_logic.apply_single_move(temp, move)
        return self._evaluate(temp)