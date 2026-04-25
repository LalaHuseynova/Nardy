from flask import Flask, render_template, jsonify, request
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

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/state")
def get_state():
    return jsonify({
        "board": state.board,
        "current_player": state.current_player,
        "borne_off": state.borne_off,
        "remaining_dice": remaining_dice
    })

@app.route("/api/roll")
def roll_dice():
    global remaining_dice, head_moves_used, max_head_moves
    # roll new dice
    rolled = game.roll_dice()
    remaining_dice = rolled[:]
    head_moves_used = 0
    max_head_moves = game.allowed_head_moves_in_turn(state, rolled)
    return jsonify({
        "dice": rolled,
        "remaining_dice": remaining_dice
    })

@app.route("/api/legal_moves_for_die")
def legal_moves_for_die():
    """Return all legal single moves for a given die, respecting head limit."""
    die = request.args.get("die", type=int)
    if die is None:
        return jsonify({"error": "Missing die parameter"}), 400
    
    all_moves = game.get_legal_single_moves(state, die)
    head_idx = game.head_index(state.current_player)
    
    # filter moves from head if we've already used the head limit
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
            "target": target   # None for bear_off
        })
    return jsonify({"moves": moves_json})

@app.route("/api/apply_die_move", methods=["POST"])
def apply_die_move():
    global state, remaining_dice, head_moves_used, max_head_moves
    data = request.get_json()
    die = data.get("die")
    move = data.get("move")
    if die is None or move is None:
        return jsonify({"error": "die and move are required"}), 400

    # check that this die is still available
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

    # validate the specific move
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

    # update head usage
    if move["source"] == head_idx:
        head_moves_used += 1

    # remove ONE occurrence of the used die
    remaining_dice.remove(die)

    # after the move, check if there are still dice left but no legal moves for any of them
    if remaining_dice:
        any_legal = False
        for d in remaining_dice:
            # get legal moves for this die respecting current head limit
            moves_for_d = game.get_legal_single_moves(state, d)
            for m in moves_for_d:
                _, src, _ = m
                if src == head_idx and head_moves_used >= max_head_moves:
                    continue
                any_legal = True
                break
            if any_legal:
                break
        if not any_legal:
            # turn ends
            state.current_player *= -1
            remaining_dice = []
            head_moves_used = 0
            max_head_moves = 1

    # if no dice left, switch turn
    if not remaining_dice:
        state.current_player *= -1
        head_moves_used = 0
        max_head_moves = 1

    return jsonify({
        "board": state.board,
        "current_player": state.current_player,
        "borne_off": state.borne_off,
        "remaining_dice": remaining_dice
    })

if __name__ == "__main__":
    app.run(debug=True)