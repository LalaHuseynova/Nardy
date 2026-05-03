from flask import Flask, render_template, jsonify, request
import random
from game_state import GameState
from game_logic import NardyGame

app = Flask(__name__)

game = NardyGame()
state = GameState()

# remaining dice for the current turn (list of integers)
remaining_dice = []
# how many times the head has been used this turn
head_moves_used = 0
# maximum allowed head moves for this turn (1 normally, 2 for initial double 3/4/6)
max_head_moves = 1
game_started = False
opening_roll = None

def is_game_over():
    return state.borne_off[1] == 15 or state.borne_off[-1] == 15

def has_legal_remaining_move():
    if not remaining_dice:
        return False

    head_idx = game.head_index(state.current_player)
    for die in remaining_dice:
        moves = game.get_legal_single_moves(state, die)
        for move in moves:
            _, src, _ = move
            if src == head_idx and head_moves_used >= max_head_moves:
                continue
            return True
    return False

def pass_turn():
    global remaining_dice, head_moves_used, max_head_moves
    state.current_player *= -1
    remaining_dice = []
    head_moves_used = 0
    max_head_moves = 1

def skip_turn_if_no_legal_moves():
    if remaining_dice and not has_legal_remaining_move():
        pass_turn()
        return True
    return False

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/state")
def get_state():
    skip_turn_if_no_legal_moves()
    return jsonify({
        "board": state.board,
        "current_player": state.current_player,
        "borne_off": state.borne_off,
        "remaining_dice": remaining_dice,
        "game_started": game_started,
        "opening_roll": opening_roll,
        "game_over": is_game_over(),
        "winner": 1 if state.borne_off[1] == 15 else (-1 if state.borne_off[-1] == 15 else None)
    })

@app.route("/api/opening_roll", methods=["POST"])
def opening_roll_to_start():
    global game_started, opening_roll
    if game_started:
        return jsonify({
            "current_player": state.current_player,
            "game_started": game_started,
            "opening_roll": opening_roll
        })

    rolls = []
    while True:
        player_one_die = random.randint(1, 6)
        player_two_die = random.randint(1, 6)
        rolls.append({
            "player_one": player_one_die,
            "player_two": player_two_die
        })
        if player_one_die != player_two_die:
            break

    state.current_player = 1 if player_one_die > player_two_die else -1
    opening_roll = {
        "rolls": rolls,
        "winner": state.current_player
    }
    game_started = True
    return jsonify({
        "current_player": state.current_player,
        "game_started": game_started,
        "opening_roll": opening_roll
    })

@app.route("/api/roll")
def roll_dice():
    global remaining_dice, head_moves_used, max_head_moves
    if not game_started:
        return jsonify({"error": "Roll one die to decide who starts first"}), 400
    if remaining_dice:
        return jsonify({"error": "Finish your current dice before rolling again"}), 400
    if is_game_over():
        return jsonify({"error": "Game already over"}), 400

    rolled = game.roll_dice()
    remaining_dice = rolled[:]
    head_moves_used = 0
    max_head_moves = game.allowed_head_moves_in_turn(state, rolled)
    turn_skipped = skip_turn_if_no_legal_moves()
    return jsonify({
        "dice": rolled,
        "remaining_dice": remaining_dice,
        "current_player": state.current_player,
        "turn_skipped": turn_skipped
    })

@app.route("/api/legal_moves_for_die")
def legal_moves_for_die():
    """Return legal single moves for a die, respecting head limit."""
    die = request.args.get("die", type=int)
    if die is None:
        return jsonify({"error": "Missing die parameter"}), 400

    all_moves = game.get_legal_single_moves(state, die)
    head_idx = game.head_index(state.current_player)

    filtered_moves = []
    for move in all_moves:
        _, source, _ = move
        if source == head_idx and head_moves_used >= max_head_moves:
            continue
        filtered_moves.append(move)

    moves_json = []
    for move in filtered_moves:
        move_type, source, target = move
        moves_json.append({
            "type": move_type,
            "source": source,
            "target": target
        })
    return jsonify({"moves": moves_json})

@app.route("/api/legal_dice_for_source")
def legal_dice_for_source():
    """Return which remaining dice can legally move the given source point."""
    source = request.args.get("source", type=int)
    if source is None:
        return jsonify({"error": "Missing source parameter"}), 400

    legal_dice = []
    head_idx = game.head_index(state.current_player)
    for die in remaining_dice:
        moves = game.get_legal_single_moves(state, die)
        for move in moves:
            _, src, _ = move
            if src == source:
                # respect head limit
                if src == head_idx and head_moves_used >= max_head_moves:
                    continue
                legal_dice.append(die)
                break  # one die enough
    return jsonify({"legal_dice": list(set(legal_dice))})

@app.route("/api/apply_die_move", methods=["POST"])
def apply_die_move():
    global state, remaining_dice, head_moves_used, max_head_moves
    if is_game_over():
        return jsonify({"error": "Game already over"}), 400

    data = request.get_json()
    die = data.get("die")
    move = data.get("move")
    if die is None or move is None:
        return jsonify({"error": "die and move are required"}), 400

    if die not in remaining_dice:
        return jsonify({"error": "This die is not available any more"}), 400

    # get legal moves for this die (with current head limit)
    all_moves = game.get_legal_single_moves(state, die)
    head_idx = game.head_index(state.current_player)
    valid_moves = []
    for m in all_moves:
        m_type, src, tgt = m
        if src == head_idx and head_moves_used >= max_head_moves:
            continue
        valid_moves.append(m)

    valid = False
    for m in valid_moves:
        m_type, src, tgt = m
        if (m_type == move["type"] and src == move["source"] and
            (tgt == move.get("target") or (move.get("target") is None and tgt is None))):
            valid = True
            break
    if not valid:
        return jsonify({"error": "Illegal move for this die"}), 400

    # apply the move
    move_tuple = (move["type"], move["source"], move.get("target"))
    state = game.apply_single_move(state, move_tuple)

    if move["source"] == head_idx:
        head_moves_used += 1

    # remove used die
    remaining_dice.remove(die)

    # check for legal moves with remaining dice
    turn_skipped = skip_turn_if_no_legal_moves()

    if not remaining_dice and not turn_skipped:
        pass_turn()

    return jsonify({
        "board": state.board,
        "current_player": state.current_player,
        "borne_off": state.borne_off,
        "remaining_dice": remaining_dice,
        "game_started": game_started,
        "opening_roll": opening_roll,
        "game_over": is_game_over(),
        "winner": 1 if state.borne_off[1] == 15 else (-1 if state.borne_off[-1] == 15 else None)
    })

if __name__ == "__main__":
    app.run(debug=True,port=5001)
