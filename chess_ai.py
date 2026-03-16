"""
chess_ai.py — Highly optimized Iterative-deepening minimax with transposition table.
Fixed board state restore bug using try-finally.
"""
import chess
import random
import time

# ── Piece values ───────────────────────────────────────────────────────────
PIECE_VALUES = {
    chess.PAWN:   100,
    chess.KNIGHT: 320,
    chess.BISHOP: 330,
    chess.ROOK:   500,
    chess.QUEEN:  900,
    chess.KING:   20000,
}

# ── Piece-Square Tables ───────────────────────────────────────────────────
PAWN_TABLE = [
    0,  0,  0,  0,  0,  0,  0,  0,
    5, 10, 10,-20,-20, 10, 10,  5,
    5, -5,-10,  0,  0,-10, -5,  5,
    0,  0,  0, 20, 20,  0,  0,  0,
    5,  5, 10, 25, 25, 10,  5,  5,
    10, 10, 20, 30, 30, 20, 10, 10,
    50, 50, 50, 50, 50, 50, 50, 50,
    0,  0,  0,  0,  0,  0,  0,  0,
]
KNIGHT_TABLE = [
    -50,-40,-30,-30,-30,-30,-40,-50,
    -40,-20,  0,  5,  5,  0,-20,-40,
    -30,  5, 10, 15, 15, 10,  5,-30,
    -30,  0, 15, 20, 20, 15,  0,-30,
    -30,  5, 15, 20, 20, 15,  5,-30,
    -30,  0, 10, 15, 15, 10,  0,-30,
    -40,-20,  0,  0,  0,  0,-20,-40,
    -50,-40,-30,-30,-30,-30,-40,-50,
]
BISHOP_TABLE = [
    -20,-10,-10,-10,-10,-10,-10,-20,
    -10,  5,  0,  0,  0,  0,  5,-10,
    -10, 10, 10, 10, 10, 10, 10,-10,
    -10,  0, 10, 10, 10, 10,  0,-10,
    -10,  5,  5, 10, 10,  5,  5,-10,
    -10,  0,  5, 10, 10,  5,  0,-10,
    -10,  0,  0,  0,  0,  0,  0,-10,
    -20,-10,-10,-10,-10,-10,-10,-20,
]
ROOK_TABLE = [
    0,  0,  0,  5,  5,  0,  0,  0,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    5, 10, 10, 10, 10, 10, 10,  5,
    0,  0,  0,  0,  0,  0,  0,  0,
]
QUEEN_TABLE = [
    -20,-10,-10, -5, -5,-10,-10,-20,
    -10,  0,  5,  0,  0,  0,  0,-10,
    -10,  5,  5,  5,  5,  5,  0,-10,
    0,  0,  5,  5,  5,  5,  0, -5,
    -5,  0,  5,  5,  5,  5,  0, -5,
    -10,  0,  5,  5,  5,  5,  0,-10,
    -10,  0,  0,  0,  0,  0,  0,-10,
    -20,-10,-10, -5, -5,-10,-10,-20,
]
KING_TABLE = [
    20, 30, 10,  0,  0, 10, 30, 20,
    20, 20,  0,  0,  0,  0, 20, 20,
    -10,-20,-20,-20,-20,-20,-20,-10,
    -20,-30,-30,-40,-40,-30,-30,-20,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
]

TABLES = {
    chess.PAWN: PAWN_TABLE,
    chess.KNIGHT: KNIGHT_TABLE,
    chess.BISHOP: BISHOP_TABLE,
    chess.ROOK: ROOK_TABLE,
    chess.QUEEN: QUEEN_TABLE,
    chess.KING: KING_TABLE,
}

TIME_LIMITS = {1: 0.1, 2: 0.4, 3: 1.0, 4: 2.5, 5: 6.0}

_deadline = 0.0
_transposition_table = {}

class _Timeout(Exception):
    pass

def _check_time():
    if time.time() >= _deadline:
        raise _Timeout()

def evaluate(board):
    if board.is_checkmate():
        return -100000 if board.turn == chess.WHITE else 100000
    if board.is_stalemate() or board.is_insufficient_material():
        return 0
    
    score = 0
    for sq, p in board.piece_map().items():
        val = PIECE_VALUES[p.piece_type]
        idx = sq if p.color == chess.WHITE else sq ^ 56
        bonus = TABLES[p.piece_type][idx]
        if p.color == chess.WHITE:
            score += val + bonus
        else:
            score -= val + bonus
    return score

def _move_score(board, move):
    if board.is_capture(move):
        victim = board.piece_at(move.to_square)
        attacker = board.piece_at(move.from_square)
        if victim and attacker:
            return 10 * PIECE_VALUES[victim.piece_type] - PIECE_VALUES[attacker.piece_type]
    return 0

def _alphabeta(board, depth, alpha, beta, maximizing):
    _check_time()

    z_hash = board.fen()
    if z_hash in _transposition_table:
        tt_entry = _transposition_table[z_hash]
        if tt_entry['depth'] >= depth:
            return tt_entry['value']

    if depth == 0 or board.is_game_over():
        return evaluate(board)

    moves = sorted(board.legal_moves, key=lambda m: _move_score(board, m), reverse=True)
    res = 0

    if maximizing:
        best = float('-inf')
        for m in moves:
            board.push(m)
            try:
                val = _alphabeta(board, depth - 1, alpha, beta, False)
                best = max(best, val)
                alpha = max(alpha, best)
            finally:
                board.pop()
            if beta <= alpha:
                break
        res = best
    else:
        best = float('inf')
        for m in moves:
            board.push(m)
            try:
                val = _alphabeta(board, depth - 1, alpha, beta, True)
                best = min(best, val)
                beta = min(beta, best)
            finally:
                board.pop()
            if beta <= alpha:
                break
        res = best

    if len(_transposition_table) < 50000:
        _transposition_table[z_hash] = {'value': res, 'depth': depth}
    
    return res

def get_ai_move(board, difficulty=3):
    global _deadline, _transposition_table
    _transposition_table = {}

    if board.is_game_over():
        return None

    moves = list(board.legal_moves)
    if not moves:
        return None

    if difficulty == 1 and random.random() < 0.7:
        return random.choice(moves)

    time_limit = TIME_LIMITS.get(difficulty, 1.0)
    _deadline = time.time() + time_limit

    maximizing = (board.turn == chess.WHITE)
    best_move = random.choice(moves)

    for depth in range(1, 10):
        try:
            candidate = None
            curr_best_val = float('-inf') if maximizing else float('inf')
            ordered = sorted(moves, key=lambda m: _move_score(board, m), reverse=True)

            for move in ordered:
                board.push(move)
                try:
                    val = _alphabeta(board, depth - 1, float('-inf'), float('inf'), not maximizing)
                finally:
                    board.pop()

                if maximizing and val > curr_best_val:
                    curr_best_val = val
                    candidate = move
                elif not maximizing and val < curr_best_val:
                    curr_best_val = val
                    candidate = move

            if candidate:
                best_move = candidate
            
            if depth >= 4 and difficulty < 5:
                break

        except _Timeout:
            break

    return best_move
