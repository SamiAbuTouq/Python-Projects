"""
Tic Tac Toe - a 2-player command-line game.
Run with:  python tic_tac_toe.py
"""
import os
import sys

# Makes ANSI colours work in the Windows terminal too
os.system("")

# ---------- Colours ----------
RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
RED = "\033[91m"
CYAN = "\033[96m"
YELLOW = "\033[93m"
GREEN = "\033[92m"
MAGENTA = "\033[95m"
WIN_BG = "\033[42;30m"  # green background, black text

COLORS = {"X": RED, "O": CYAN}

WIN_LINES = [
    (0, 1, 2), (3, 4, 5), (6, 7, 8),  # rows
    (0, 3, 6), (1, 4, 7), (2, 5, 8),  # columns
    (0, 4, 8), (2, 4, 6),             # diagonals
]

LOGO = f"""{MAGENTA}{BOLD}
 ████████╗██╗ ██████╗    ████████╗ █████╗  ██████╗    ████████╗ ██████╗ ███████╗
 ╚══██╔══╝██║██╔════╝    ╚══██╔══╝██╔══██╗██╔════╝    ╚══██╔══╝██╔═══██╗██╔════╝
    ██║   ██║██║            ██║   ███████║██║            ██║   ██║   ██║█████╗
    ██║   ██║██║            ██║   ██╔══██║██║            ██║   ██║   ██║██╔══╝
    ██║   ██║╚██████╗       ██║   ██║  ██║╚██████╗       ██║   ╚██████╔╝███████╗
    ╚═╝   ╚═╝ ╚═════╝       ╚═╝   ╚═╝  ╚═╝ ╚═════╝       ╚═╝    ╚═════╝ ╚══════╝
{RESET}"""


def clear():
    # Only clear in a real terminal. In PyCharm's Run console, "cls" just
    # prints a stray form-feed character (the little box).
    if sys.stdout.isatty():
        os.system("cls" if os.name == "nt" else "clear")


def find_winner(board):
    """Return (symbol, winning_line) or (None, None)."""
    for line in WIN_LINES:
        a, b, c = line
        if board[a] != " " and board[a] == board[b] == board[c]:
            return board[a], line
    return None, None


def render_cell(board, i, win_line):
    if board[i] == " ":
        return f"{DIM}{i + 1}{RESET}"
    symbol = f"{BOLD}{COLORS[board[i]]}{board[i]}{RESET}"
    if win_line and i in win_line:
        return f"{WIN_BG}{BOLD}{board[i]}{RESET}"
    return symbol


def draw_screen(board, names, scores, message="", win_line=None):
    clear()

    # Scoreboard
    x_score = f"{RED}{BOLD}X{RESET} {names['X']}: {YELLOW}{scores['X']}{RESET}"
    o_score = f"{CYAN}{BOLD}O{RESET} {names['O']}: {YELLOW}{scores['O']}{RESET}"
    print(f"   {x_score}     {DIM}|{RESET}     {o_score}     {DIM}|{RESET}     Draws: {YELLOW}{scores['draw']}{RESET}\n")

    c = [render_cell(board, i, win_line) for i in range(9)]
    pad = "                    "
    print(f"{pad}{MAGENTA}╔═══╦═══╦═══╗{RESET}")
    print(f"{pad}{MAGENTA}║{RESET} {c[0]} {MAGENTA}║{RESET} {c[1]} {MAGENTA}║{RESET} {c[2]} {MAGENTA}║{RESET}")
    print(f"{pad}{MAGENTA}╠═══╬═══╬═══╣{RESET}")
    print(f"{pad}{MAGENTA}║{RESET} {c[3]} {MAGENTA}║{RESET} {c[4]} {MAGENTA}║{RESET} {c[5]} {MAGENTA}║{RESET}")
    print(f"{pad}{MAGENTA}╠═══╬═══╬═══╣{RESET}")
    print(f"{pad}{MAGENTA}║{RESET} {c[6]} {MAGENTA}║{RESET} {c[7]} {MAGENTA}║{RESET} {c[8]} {MAGENTA}║{RESET}")
    print(f"{pad}{MAGENTA}╚═══╩═══╩═══╝{RESET}\n")

    if message:
        print(f"   {message}\n")


def get_names():
    clear()
    print(LOGO)
    x = input(f"   Player 1 ({RED}{BOLD}X{RESET}) name: ").strip() or "Player 1"
    o = input(f"   Player 2 ({CYAN}{BOLD}O{RESET}) name: ").strip() or "Player 2"
    return {"X": x, "O": o}


def ask_move(board, player, names):
    color = COLORS[player]
    while True:
        raw = input(f"   {color}{BOLD}{names[player]}{RESET} ({color}{player}{RESET}), pick a square (1-9) or 'q' to quit: ").strip().lower()
        if raw == "q":
            return None
        if not raw.isdigit() or not 1 <= int(raw) <= 9:
            print(f"   {YELLOW}Please enter a number from 1 to 9.{RESET}")
            continue
        move = int(raw) - 1
        if board[move] != " ":
            print(f"   {YELLOW}That square is taken. Try another!{RESET}")
            continue
        return move


def play_round(names, scores, first):
    """Play one round. Returns False if a player quit."""
    board = [" "] * 9
    player = first
    message = f"{GREEN}{names[player]} goes first. Good luck!{RESET}"

    while True:
        draw_screen(board, names, scores, message)
        move = ask_move(board, player, names)
        if move is None:
            return False
        board[move] = player

        winner, line = find_winner(board)
        if winner:
            scores[winner] += 1
            draw_screen(board, names, scores,
                        f"{GREEN}{BOLD}🏆  {names[winner]} ({winner}) wins!{RESET}", line)
            return True
        if " " not in board:
            scores["draw"] += 1
            draw_screen(board, names, scores, f"{YELLOW}{BOLD}🤝  It's a draw!{RESET}")
            return True

        player = "O" if player == "X" else "X"
        message = ""


def main():
    names = get_names()
    scores = {"X": 0, "O": 0, "draw": 0}
    first = "X"

    while True:
        if not play_round(names, scores, first):
            break
        again = input("   Play again? (y/n): ").strip().lower()
        if again != "y":
            break
        first = "O" if first == "X" else "X"  # alternate who starts

    clear()
    print(f"   {BOLD}Final score{RESET}")
    print(f"   {RED}X{RESET} {names['X']}: {scores['X']}   "
          f"{CYAN}O{RESET} {names['O']}: {scores['O']}   Draws: {scores['draw']}\n")
    print(f"   {MAGENTA}Thanks for playing! 👋{RESET}\n")


if __name__ == "__main__":
    main()