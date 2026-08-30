#!/usr/bin/env python3
import argparse
import curses
import random
import time

WIDTH = 10
HEIGHT = 20
COLORS = "ABCD"


def new_piece():
    return {"x": WIDTH // 2 - 1, "y": 0, "tokens": [random.choice(COLORS) for _ in range(3)]}


def cells(piece, y=None, x=None):
    base_y = piece["y"] if y is None else y
    base_x = piece["x"] if x is None else x
    return [(base_y + index, base_x, token) for index, token in enumerate(piece["tokens"])]


def fits(board, piece, y=None, x=None):
    for row, column, _ in cells(piece, y, x):
        if column < 0 or column >= WIDTH or row < 0 or row >= HEIGHT or board[row][column] != ".":
            return False
    return True


def settle(board, piece):
    for row, column, token in cells(piece):
        if 0 <= row < HEIGHT and 0 <= column < WIDTH:
            board[row][column] = token


def clear_matches(board):
    seen = set()
    remove = set()
    for row in range(HEIGHT):
        for column in range(WIDTH):
            if board[row][column] == "." or (row, column) in seen:
                continue
            token = board[row][column]
            group = []
            stack = [(row, column)]
            seen.add((row, column))
            while stack:
                current_row, current_column = stack.pop()
                group.append((current_row, current_column))
                for next_row, next_column in ((current_row - 1, current_column), (current_row + 1, current_column), (current_row, current_column - 1), (current_row, current_column + 1)):
                    if 0 <= next_row < HEIGHT and 0 <= next_column < WIDTH and (next_row, next_column) not in seen and board[next_row][next_column] == token:
                        seen.add((next_row, next_column))
                        stack.append((next_row, next_column))
            if len(group) >= 3:
                remove.update(group)
    for row, column in remove:
        board[row][column] = "."
    if not remove:
        return 0
    for column in range(WIDTH):
        values = [board[row][column] for row in range(HEIGHT) if board[row][column] != "."]
        for row in range(HEIGHT):
            board[row][column] = values[row - (HEIGHT - len(values))] if row >= HEIGHT - len(values) else "."
    return len(remove)


def draw(screen, board, piece, score, paused):
    screen.erase()
    screen.addstr(0, 0, "COLUMN FALL  A/D move  S drop  Space slam  C rotate  P pause  Q quit")
    screen.addstr(1, 0, "Score: " + str(score) + ("  PAUSED" if paused else ""))
    screen.addstr(2, 0, "+" + "--" * WIDTH + "+")
    for row in range(HEIGHT):
        screen.addstr(3 + row, 0, "|")
        for column in range(WIDTH):
            token = board[row][column]
            for piece_row, piece_column, piece_token in cells(piece):
                if piece_row == row and piece_column == column:
                    token = piece_token
            screen.addstr(3 + row, 1 + column * 2, token + " ")
        screen.addstr(3 + row, 1 + WIDTH * 2, "|")
    screen.addstr(3 + HEIGHT, 0, "+" + "--" * WIDTH + "+")
    screen.refresh()


def game(screen):
    curses.curs_set(0)
    screen.nodelay(True)
    screen.keypad(True)
    board = [["." for _ in range(WIDTH)] for _ in range(HEIGHT)]
    piece = new_piece()
    score = 0
    paused = False
    last_fall = time.monotonic()
    while True:
        if curses.LINES < HEIGHT + 5 or curses.COLS < WIDTH * 2 + 2:
            screen.erase()
            screen.addstr(0, 0, "Resize the terminal to at least 23 rows and 23 columns.")
            screen.refresh()
            time.sleep(0.2)
            continue
        key = screen.getch()
        if key in (ord("q"), ord("Q")):
            return
        if key in (ord("p"), ord("P")):
            paused = not paused
        if not paused:
            if key in (curses.KEY_LEFT, ord("a"), ord("A")) and fits(board, piece, x=piece["x"] - 1):
                piece["x"] -= 1
            elif key in (curses.KEY_RIGHT, ord("d"), ord("D")) and fits(board, piece, x=piece["x"] + 1):
                piece["x"] += 1
            elif key in (ord("c"), ord("C")):
                rotated = piece["tokens"][1:] + piece["tokens"][:1]
                if fits(board, {**piece, "tokens": rotated}):
                    piece["tokens"] = rotated
            elif key in (ord("s"), ord("S")):
                while fits(board, piece, y=piece["y"] + 1):
                    piece["y"] += 1
            if time.monotonic() - last_fall >= 0.55 or key == ord(" "):
                last_fall = time.monotonic()
                if fits(board, piece, y=piece["y"] + 1):
                    piece["y"] += 1
                else:
                    settle(board, piece)
                    cleared = clear_matches(board)
                    score += cleared * 10
                    piece = new_piece()
                    if not fits(board, piece):
                        draw(screen, board, piece, score, False)
                        screen.nodelay(False)
                        screen.addstr(HEIGHT + 5, 0, "Game over. Press any key to leave.")
                        screen.getch()
                        return
        draw(screen, board, piece, score, paused)
        time.sleep(0.03)


def build_parser():
    parser = argparse.ArgumentParser(description="Play a small falling-column matching game in the terminal.")
    parser.add_argument("--demo", action="store_true", help="print controls and exit without opening the game")
    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()
    if args.demo:
        print("COLUMN FALL")
        print("Match groups of three or more equal letters.")
        print("Controls: A/D move, S soft drop, Space slam, C rotate, P pause, Q quit.")
        return 0
    curses.wrapper(game)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
