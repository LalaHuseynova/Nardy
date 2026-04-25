# game_logic.py

import random
from game_state import GameState
from config import PLAYER_ONE, PLAYER_TWO


class NardyGame:
    def roll_dice(self):
        """
        2 zər atır.
        Əgər qoşa düşərsə, 4 dəfə oynanılır.
        """
        d1 = random.randint(1, 6)
        d2 = random.randint(1, 6)

        if d1 == d2:
            return [d1, d1, d1, d1]

        return [d1, d2]

    def print_board(self, state: GameState):
        """
        Taxtanı konsolda göstərir.
        """
        print("\n" + "=" * 70)
        print(f"Current player: {'Player 1 (+)' if state.current_player == PLAYER_ONE else 'Player 2 (-)'}")
        print(f"Borne off -> Player 1: {state.borne_off[PLAYER_ONE]}, Player 2: {state.borne_off[PLAYER_TWO]}")
        print("-" * 70)

        print("Top row (points 13 -> 24):")
        for i in range(12, 24):
            print(f"{i+1:>2}:{state.board[i]:>3}", end="   ")
        print("\n")

        print("Bottom row (points 12 -> 1):")
        for i in range(11, -1, -1):
            print(f"{i+1:>2}:{state.board[i]:>3}", end="   ")
        print()

        print("=" * 70)

    # =========================================================
    # PATH / BOARD MAPPING
    # =========================================================

    def get_player_path(self, player):
        """
        Hər oyunçu üçün hərəkət yolu.

        Player 1 (ağ):
            24 -> 23 -> 22 -> ... -> 1

        Player 2 (qara):
            12 -> 11 -> 10 -> ... -> 1 -> 24 -> 23 -> ... -> 13
        """
        if player == PLAYER_ONE:
            return [
                23, 22, 21, 20, 19, 18,
                17, 16, 15, 14, 13, 12,
                11, 10, 9, 8, 7, 6,
                5, 4, 3, 2, 1, 0
            ]

        return [
            11, 10, 9, 8, 7, 6,
            5, 4, 3, 2, 1, 0,
            23, 22, 21, 20, 19, 18,
            17, 16, 15, 14, 13, 12
        ]

    def head_index(self, player):
        """
        Baş nöqtə:
        Ağ -> 24 (index 23)
        Qara -> 12 (index 11)
        """
        return 23 if player == PLAYER_ONE else 11

    def home_board_points(self, player):
        """
        Daş çıxarma üçün son 6 nöqtə.
        Path-in axırdakı 6 nöqtəsi ev zonası sayılır.
        """
        path = self.get_player_path(player)
        return set(path[-6:])

    def get_path_position(self, player, board_index):
        """
        Verilən board index-in həmin oyunçunun yolunda neçəinci
        yerdə olduğunu qaytarır.
        """
        path = self.get_player_path(player)
        return path.index(board_index)

    # =========================================================
    # SADƏ YARDIMÇI FUNKSİYALAR
    # =========================================================

    def has_checker(self, state: GameState, point: int, player: int):
        """
        Verilən nöqtədə həmin oyunçunun daşı var?
        """
        if point < 0 or point > 23:
            return False

        if player == PLAYER_ONE:
            return state.board[point] > 0
        return state.board[point] < 0

    def checker_count(self, state: GameState, point: int, player: int):
        """
        Verilən nöqtədə həmin oyunçunun neçə daşı var?
        """
        if not (0 <= point <= 23):
            return 0

        if player == PLAYER_ONE:
            return max(0, state.board[point])
        return max(0, -state.board[point])

    def is_blocked(self, state: GameState, target: int, player: int):
        """
        Uzun nərd qaydası:
        rəqibin hər hansı daşı olan nöqtəyə girmək olmaz.
        """
        if target < 0 or target > 23:
            return False

        value = state.board[target]

        if player == PLAYER_ONE:
            return value < 0
        return value > 0

    def all_in_home(self, state: GameState, player: int):
        """
        Bütün daşlar ev zonasındadırsa True qaytarır.
        """
        home_points = self.home_board_points(player)

        for i, value in enumerate(state.board):
            if player == PLAYER_ONE and value > 0 and i not in home_points:
                return False

            if player == PLAYER_TWO and value < 0 and i not in home_points:
                return False

        return True

    def is_initial_position(self, state: GameState):
        """
        Oyun başlanğıc vəziyyətindədir?
        Bu, ilk gedişdə xüsusi qoşa istisnasını yoxlamaq üçündür.
        """
        if state.borne_off[PLAYER_ONE] != 0 or state.borne_off[PLAYER_TWO] != 0:
            return False

        for i, value in enumerate(state.board):
            if i == 23:
                if value != 15:
                    return False
            elif i == 11:
                if value != -15:
                    return False
            else:
                if value != 0:
                    return False

        return True

    def allowed_head_moves_in_turn(self, state: GameState, dice: list[int]):
        """
        Normal qayda:
            bir turn-də head-dən yalnız 1 daş çıxarmaq olar.

        İstisna:
            bəzi uzun nərd variantlarında ilk gedişdə
            qoşa 3, 4, 6 gələndə head-dən 2 daş çıxarmağa icazə verilir.
        """
        if len(dice) == 4 and len(set(dice)) == 1:
            die = dice[0]
            if self.is_initial_position(state) and die in {3, 4, 6}:
                return 2

        return 1

    # =========================================================
    # 6-LIQ BLOK QAYDASI
    # =========================================================

    def creates_illegal_six_block(self, state: GameState, player: int):
        """
        Uzun nərddə 6 ardıcıl blok yaratmaq olar,
        amma rəqibin bütün daşlarını həmin blokun arxasında tam bağlamaq olmaz.

        Sadə yoxlama:
        - cari oyunçunun yolunda 6 ardıcıl dolu nöqtə varsa
        - və həmin 6-lıq blokdan irəlidə heç bir rəqib daşı yoxdursa
          bu vəziyyəti qeyri-qanuni sayırıq
        """
        path = self.get_player_path(player)
        opponent = PLAYER_TWO if player == PLAYER_ONE else PLAYER_ONE

        occupied = [self.has_checker(state, p, player) for p in path]

        for start in range(len(path) - 5):
            window = occupied[start:start + 6]

            # 6 ardıcıl dolu nöqtə tapıldısa
            if all(window):
                after_window_points = path[start + 6:]

                opponent_ahead_exists = False
                for p in after_window_points:
                    if self.has_checker(state, p, opponent):
                        opponent_ahead_exists = True
                        break

                # Əgər blokdan irəlidə heç bir rəqib daşı yoxdursa,
                # bu blok rəqibi tam bağlayır deməkdir
                if not opponent_ahead_exists:
                    return True

        return False

    # =========================================================
    # TƏK ZƏR ÜÇÜN LEGAL MOVES
    # =========================================================

    def get_legal_single_moves(self, state: GameState, die: int):
        """
        Tək bir zər üçün bütün legal gedişləri tapır.

        Format:
            ("move", source_index, target_index)
            ("bear_off", source_index, None)
        """
        player = state.current_player
        path = self.get_player_path(player)
        moves = []

        for source in range(24):
            # Bu nöqtədə cari oyunçunun daşı yoxdursa keç
            if not self.has_checker(state, source, player):
                continue

            source_pos = self.get_path_position(player, source)
            target_pos = source_pos + die

            # =========================
            # normal move
            # =========================
            if target_pos < len(path):
                target = path[target_pos]

                # Hədəf blokdursa keç
                if self.is_blocked(state, target, player):
                    continue

                move = ("move", source, target)
                candidate_state = self.apply_single_move(state, move)

                # 6-lıq tam blok yaranırsa bu move qanunsuzdur
                if self.creates_illegal_six_block(candidate_state, player):
                    continue

                moves.append(move)

            # =========================
            # bear off
            # =========================
            else:
                # Hamı evdə deyilsə daş çıxarmaq olmaz
                if not self.all_in_home(state, player):
                    continue

                # Source ev zonasındadırsa davam et
                if source not in self.home_board_points(player):
                    continue

                # Tam dəqiq çıxış
                if target_pos == len(path):
                    move = ("bear_off", source, None)
                    candidate_state = self.apply_single_move(state, move)

                    if self.creates_illegal_six_block(candidate_state, player):
                        continue

                    moves.append(move)

                # Böyük zərlə çıxış:
                # yalnız source-dan daha uzaqda daş yoxdursa olar
                elif target_pos > len(path):
                    farther_positions = path[source_pos + 1:]

                    has_farther_checker = False
                    for p in farther_positions:
                        if self.has_checker(state, p, player):
                            has_farther_checker = True
                            break

                    if not has_farther_checker:
                        move = ("bear_off", source, None)
                        candidate_state = self.apply_single_move(state, move)

                        if self.creates_illegal_six_block(candidate_state, player):
                            continue

                        moves.append(move)

        return moves

    # =========================================================
    # MOVE TƏTBİQİ
    # =========================================================

    def apply_single_move(self, state: GameState, move):
        """
        Bir move-u tətbiq edir və yeni state qaytarır.
        Orijinal state dəyişmir.
        """
        new_state = state.clone()
        move_type, source, target = move
        player = new_state.current_player

        # Mənbədən 1 daş götür
        if player == PLAYER_ONE:
            new_state.board[source] -= 1
        else:
            new_state.board[source] += 1

        # Hərəkəti et
        if move_type == "move":
            if player == PLAYER_ONE:
                new_state.board[target] += 1
            else:
                new_state.board[target] -= 1

        elif move_type == "bear_off":
            new_state.borne_off[player] += 1

        return new_state

    # =========================================================
    # ZƏRLƏR ÜÇÜN BÜTÜN SEQUNSLAR
    # =========================================================

    def get_legal_move_sequences(self, state: GameState, dice: list[int]):
        """
        Verilmiş zərlər üçün bütün mümkün tam gediş ardıcıllıqlarını tapır.

        Burada bu qaydalar nəzərə alınır:
        - head-dən turn ərzində yalnız 1 daş çıxarmaq olar
        - bəzi ilk qoşa hallarda 2 daş head-dən çıxarma istisnası var
        - mümkün olduqca maksimum sayda zər istifadə olunmalıdır
        - yalnız 1 zər işlənə bilirsə böyük zər seçilməlidir
        - eyni final nəticə verən sequence-lər bir dəfə göstərilir
        """
        all_sequences_info = []
        current_player = state.current_player
        head_idx = self.head_index(current_player)
        max_head_moves = self.allowed_head_moves_in_turn(state, dice)

        def backtrack(current_state, remaining_dice, current_sequence, used_dice, head_count):
            # Bütün zərlər bitibsə hazır sequence-dir
            if not remaining_dice:
                all_sequences_info.append((current_sequence[:], used_dice[:]))
                return

            die = remaining_dice[0]
            legal_moves = self.get_legal_single_moves(current_state, die)

            filtered_moves = []
            for move in legal_moves:
                _, source, _ = move

                # head-dən çıxma limiti aşılırsa bu move olmaz
                new_head_count = head_count + (1 if source == head_idx else 0)
                if new_head_count > max_head_moves:
                    continue

                filtered_moves.append(move)

            # Bu zər oynana bilmirsə növbəti zərə keç
            if not filtered_moves:
                backtrack(
                    current_state,
                    remaining_dice[1:],
                    current_sequence,
                    used_dice,
                    head_count
                )
                return

            for move in filtered_moves:
                next_state = self.apply_single_move(current_state, move)
                current_sequence.append(move)
                used_dice.append(die)

                new_head_count = head_count + (1 if move[1] == head_idx else 0)

                backtrack(
                    next_state,
                    remaining_dice[1:],
                    current_sequence,
                    used_dice,
                    new_head_count
                )

                current_sequence.pop()
                used_dice.pop()

        # əsas sıra ilə yoxla
        backtrack(state, dice, [], [], 0)

        # zərlər fərqlidirsə tərs sıranı da yoxla
        if len(dice) == 2 and dice[0] != dice[1]:
            backtrack(state, dice[::-1], [], [], 0)

        # ------------------------------------------
        # 1) TAM EYNİ sequence-ləri sil
        # ------------------------------------------
        unique_map = {}
        for seq, used in all_sequences_info:
            key = tuple(seq)
            if key not in unique_map:
                unique_map[key] = used[:]

        unique_sequences_info = [(list(key), used) for key, used in unique_map.items()]

        if not unique_sequences_info:
            return []

        # ------------------------------------------
        # 2) Maksimum neçə move istifadə olunubsa onu saxla
        # ------------------------------------------
        max_len = max(len(seq) for seq, _ in unique_sequences_info)
        unique_sequences_info = [
            (seq, used)
            for seq, used in unique_sequences_info
            if len(seq) == max_len
        ]

        # ------------------------------------------
        # 3) Əgər yalnız 1 zər işlənə bilirsə böyük zər məcburidir
        # ------------------------------------------
        if len(dice) == 2 and dice[0] != dice[1] and max_len == 1:
            bigger_die = max(dice)

            bigger_die_sequences = [
                (seq, used)
                for seq, used in unique_sequences_info
                if used and used[0] == bigger_die
            ]

            if bigger_die_sequences:
                unique_sequences_info = bigger_die_sequences

        # ------------------------------------------
        # 4) EYNİ final nəticə verən sequence-ləri birləşdir
        # ------------------------------------------
        final_unique_sequences = []
        seen_final_states = set()

        for seq, used in unique_sequences_info:
            temp_state = state.clone()

            for move in seq:
                temp_state = self.apply_single_move(temp_state, move)

            # Eyni nəticəni müəyyən etmək üçün
            # board vəziyyəti + çıxarılan daşların sayı + növbə
            state_key = (
                tuple(temp_state.board),
                temp_state.borne_off[PLAYER_ONE],
                temp_state.borne_off[PLAYER_TWO]
            )

            if state_key not in seen_final_states:
                seen_final_states.add(state_key)
                final_unique_sequences.append(seq)

        return final_unique_sequences
    # =========================================================
    # TAM TURN TƏTBİQİ
    # =========================================================

    def apply_move_sequence(self, state: GameState, sequence):
        """
        Tam turn ardıcıllığını tətbiq edir və növbəni dəyişir.
        """
        new_state = state.clone()

        for move in sequence:
            new_state = self.apply_single_move(new_state, move)

        new_state.current_player *= -1
        return new_state