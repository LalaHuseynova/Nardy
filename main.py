# main.py

from game_state import GameState
from game_logic import NardyGame
from config import PLAYER_ONE, PLAYER_TWO, CHECKERS_PER_PLAYER
from utils import player_name


def human_vs_human():
    game = NardyGame()
    state = GameState()

    while not state.is_game_over():
        game.print_board(state)

        dice = game.roll_dice()
        print(f"Rolled dice: {dice}")

        legal_sequences = game.get_legal_move_sequences(state, dice)

        if not legal_sequences:
            print("No legal moves. Turn passes.")
            state.current_player *= -1
            continue

        print("\nLegal move sequences:")
        for i, seq in enumerate(legal_sequences, start=1):
            print(f"{i}. {seq}")

        while True:
            try:
                choice = int(input("\nChoose move number: "))
                if 1 <= choice <= len(legal_sequences):
                    break
                print("Invalid choice. Try again.")
            except ValueError:
                print("Please enter a valid number.")

        selected_sequence = legal_sequences[choice - 1]
        state = game.apply_move_sequence(state, selected_sequence)

    game.print_board(state)

    winner = player_name(PLAYER_ONE) if state.borne_off[PLAYER_ONE] == CHECKERS_PER_PLAYER else player_name(PLAYER_TWO)
    print(f"\nGame over! Winner: {winner}")


if __name__ == "__main__":
    human_vs_human()