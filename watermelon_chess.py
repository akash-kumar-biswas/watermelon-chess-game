#Watermelon Chess – Game Logic"""

import math, random

DEPTH = 8

# Adjacency list 
ADJ = {
    (0,0): [(0,1),(1,0),(1,1)],
    (0,1): [(0,0),(0,2),(0,5)],
    (0,2): [(0,1),(0,3),(0,5)],
    (0,3): [(0,2),(0,4),(0,5)],
    (0,4): [(0,3),(1,5),(1,6)],
    (0,5): [(0,1),(0,2),(0,3),(0,6)],
    (0,6): [(0,5),(1,2),(1,3),(1,4)],
    (1,0): [(0,0),(1,1),(2,0)],
    (1,1): [(0,0),(1,0),(1,2),(2,0)],
    (1,2): [(0,6),(1,1),(1,3),(2,6)],
    (1,3): [(0,6),(1,2),(1,4),(2,6)],
    (1,4): [(0,6),(1,3),(1,5),(2,6)],
    (1,5): [(0,4),(1,4),(1,6),(2,4)],
    (1,6): [(0,4),(1,5),(2,4)],
    (2,0): [(1,0),(1,1),(2,1)],
    (2,1): [(2,0),(2,2),(2,5)],
    (2,2): [(2,1),(2,3),(2,5)],
    (2,3): [(2,2),(2,4),(2,5)],
    (2,4): [(1,5),(1,6),(2,3)],
    (2,5): [(2,1),(2,2),(2,3),(2,6)],
    (2,6): [(1,2),(1,3),(1,4),(2,5)],
}

_INITIAL_BOARD = [
    [ 1,  1,  1,  1,  1,  1,  0],   # row 0  – green tokens
    [ 0,  0,  0,  0,  0,  0,  0],   # row 1  – empty
    [-1, -1, -1, -1, -1, -1,  0],   # row 2  – red tokens
]


# State 
class State:
    

    def __init__(self, board=None, player=-1):
        self.board  = [row[:] for row in (board if board is not None else _INITIAL_BOARD)]
        self.player = player  # red moves first

    def __eq__(self, other):
        return self.board == other.board and self.player == other.player

    def __hash__(self):
        return hash((tuple(tuple(r) for r in self.board), self.player))

    def __repr__(self):
        symbols = {1: "G", -1: "R", 0: "."}
        rows = ["  ".join(symbols[v] for v in row) for row in self.board]
        turn = "Red" if self.player == -1 else "Green"
        return "\n".join(rows) + f"\n[{turn}'s turn]"


#  Helper 
def _is_trapped(board, pos):
    return all(board[nr][nc] != 0 for (nr, nc) in ADJ[pos])


#  actions 
def actions(state):
   
    valid  = set()
    board  = state.board
    player = state.player

    for r in range(3):
        for c in range(7):
            if board[r][c] == player:
                for (nr, nc) in ADJ[(r, c)]:
                    if board[nr][nc] == 0:
                        valid.add(((r, c), (nr, nc)))

    return valid


#  result 
def result(state, action):
    (fr, fc), (tr, tc) = action
    player = state.player
    opponent = -player

    new_board = [row[:] for row in state.board]

    # 1. Move
    new_board[tr][tc] = player
    new_board[fr][fc] = 0

    # 2. First collect all trapped adjacent opponent tokens
    trapped_positions = []

    for (nr, nc) in ADJ[(tr, tc)]:
        if new_board[nr][nc] == opponent and _is_trapped(new_board, (nr, nc)):
            trapped_positions.append((nr, nc))

    # 3. Remove them together
    for (nr, nc) in trapped_positions:
        new_board[nr][nc] = 0

    # 4. Switch turn
    return State(new_board, opponent)


# utility 
def utility(state):

    board = state.board
    red_count   = sum(board[r][c] == -1 for r in range(3) for c in range(7))
    green_count = sum(board[r][c] ==  1 for r in range(3) for c in range(7))

    if red_count <= 2 and green_count >= 4:
        return 1    

    if green_count <= 2 and red_count >= 4:
        return -1   # red wins

    
    if red_count < 4 and green_count < 4 or not actions(state):
        return 0

    return None     # game ongoing


#  Heuristic 
def _heuristic(state):
    #Simple token-count heuristic, normalised to [-1, 1].
    board = state.board
    green = sum(board[r][c] ==  1 for r in range(3) for c in range(7))
    red   = sum(board[r][c] == -1 for r in range(3) for c in range(7))
    return (green - red) / 12.0


# Minimax with alpha-beta pruning 
def _minimax_ab(state, depth, alpha, beta):
    u = utility(state)
    if u is not None:
        return u * 1000, None          # terminal: scale large so depth matters
    if depth == 0:
        return _heuristic(state), None

    legal = list(actions(state))
    if not legal:
        return _heuristic(state), None

    best_action = legal[0]

    if state.player == 1:              # Green – maximiser
        best_val = -math.inf
        for action in legal:
            val, _ = _minimax_ab(result(state, action), depth - 1, alpha, beta)
            if val > best_val:
                best_val, best_action = val, action
            alpha = max(alpha, best_val)
            if beta <= alpha:
                break
    else:                              # Red – minimiser
        best_val = math.inf
        for action in legal:
            val, _ = _minimax_ab(result(state, action), depth - 1, alpha, beta)
            if val < best_val:
                best_val, best_action = val, action
            beta = min(beta, best_val)
            if beta <= alpha:
                break

    return best_val, best_action


def minimax(state, depth=DEPTH):
    #Return the best action for the current player using minimax + alpha-beta.
    _, action = _minimax_ab(state, depth, -math.inf, math.inf)
    return action


#  Monte Carlo (flat) 
def _simulate(start_state, max_steps=150):
    #Random playout from start_state; returns utility value.
    state = start_state
    for _ in range(max_steps):
        u = utility(state)
        if u is not None:
            return u
        legal = list(actions(state))
        if not legal:
            return 0
        state = result(state, random.choice(legal))
    return _heuristic(state)          # fallback if max_steps exceeded


def monte_carlo(state, n_simulations=300):
    #Return the best action for the current player using flat Monte Carlo.
    legal = list(actions(state))
    if not legal:
        return None

    sims_each = max(10, n_simulations // len(legal))
    scores = []

    for  action in legal:
        next_st = result(state, action)
        u = utility(next_st)
        if u is not None:              # winning/losing move: prioritise it
            scores.append((action, u * 1000))
            continue
        total = sum(_simulate(next_st) for _ in range(sims_each))
        scores.append((action, total / sims_each))

    if state.player == 1:             # Green maximises
        return max(scores, key=lambda x: x[1])[0]
    else:                             # Red minimises
        return min(scores, key=lambda x: x[1])[0]