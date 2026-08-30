# column_fall

A small playable terminal game inspired by falling-column puzzlers. Three colored letters fall as a vertical piece; connect three or more equal letters to clear them and score points.

## Installation

Requires Python 3.9 or newer, a terminal, and a working curses implementation. Python on most Linux and macOS systems includes curses. No third-party packages are needed.

```bash
python3 -m venv .venv
. .venv/bin/activate
python3 column_fall.py --help
```

## Usage

The exact command help is:

```text
usage: column_fall.py [-h] [--demo]

Play a small falling-column matching game in the terminal.

options:
  -h, --help  show this help message and exit
  --demo      print controls and exit without opening the game
```

## Examples

```bash
python3 column_fall.py --demo
python3 column_fall.py
```

Inside the game, use `A` and `D` to move, `S` to soft drop, Space to slam, `C` to rotate the piece, `P` to pause, and `Q` to quit.

## Audience

Terminal-game fans, Python learners studying a real-time loop, and anyone wanting a small distraction that does not need graphics or a network.

## Limitations

The game needs an interactive terminal at least 23 rows by 23 columns. It does not save scores, offer sound, or support multiplayer. Windows users may need a curses-compatible terminal package such as windows-curses.

## Safety notes

The program is local-only and reads keyboard input while it is running. It does not create files, access the network, or execute shell commands. Quit with `Q` before closing a terminal window to leave the terminal display cleanly.
