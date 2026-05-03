# compare_ai_agents.py

import random
from game_state import GameState
from game_logic import NardyGame
from config import PLAYER_ONE, PLAYER_TWO
from ai_agent import NardyAI
from random_ai import RandomAI


NUM_GAMES = 5
MAX_TURNS = 150


def roll_dice():
    d1 = random.randint(1, 6)
    d2 = random.randint(1, 6)

    if d1 == d2:
        return [d1, d1, d1, d1]

    return [d1, d2]


def play_one_game():
    game = NardyGame()
    state = GameState()

    expect_ai = NardyAI(PLAYER_ONE, max_depth=2)
    random_ai = RandomAI(PLAYER_TWO)

    for turn in range(MAX_TURNS):
        print(f"Turn {turn + 1}/{MAX_TURNS}, player = {state.current_player}")

        dice = roll_dice()
        print("Dice:", dice)

        if state.current_player == PLAYER_ONE:
            sequence = expect_ai.get_best_sequence(state, dice)
            print("Expectiminimax sequence:", sequence)
        else:
            sequence = random_ai.get_best_sequence(state, dice)
            print("Random sequence:", sequence)

        if sequence:
            state = game.apply_move_sequence(state, sequence)
        else:
            # Only switch manually if no move was made
            state.current_player *= -1

        if state.is_game_over():
            break

    print("Final borne off:", state.borne_off)

    if state.borne_off[PLAYER_ONE] > state.borne_off[PLAYER_TWO]:
        return "expectiminimax"
    elif state.borne_off[PLAYER_TWO] > state.borne_off[PLAYER_ONE]:
        return "random"
    else:
        return "draw"


def compare_agents():
    expect_wins = 0
    random_wins = 0
    draws = 0

    for i in range(NUM_GAMES):
        print(f"\nStarting game {i + 1}/{NUM_GAMES}")
        winner = play_one_game()

        if winner == "expectiminimax":
            expect_wins += 1
        elif winner == "random":
            random_wins += 1
        else:
            draws += 1

        print(f"Game {i + 1}/{NUM_GAMES}: winner = {winner}")

    print("\nComparison Results")
    print("------------------")
    print(f"Games played: {NUM_GAMES}")
    print(f"Expectiminimax wins: {expect_wins}")
    print(f"Random AI wins: {random_wins}")
    print(f"Draws: {draws}")


if __name__ == "__main__":
    compare_agents()