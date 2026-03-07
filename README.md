# 🍉 Watermelon Chess

A two-player abstract strategy game played on a circular watermelon-themed board, built with Python and Pygame. Supports Human vs Human, Human vs AI, and AI vs AI — with two built-in AI agents.

![Python](https://img.shields.io/badge/Python-3.9+-blue?logo=python)
![Pygame](https://img.shields.io/badge/Pygame-2.x-green)
![License](https://img.shields.io/badge/License-MIT-lightgrey)

---

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Project Structure](#project-structure)
- [Installation](#installation)
- [How to Play](#how-to-play)
- [Game Rules](#game-rules)
- [AI Agents](#ai-agents)
- [API Reference](#api-reference)
- [License](#license)

---

## Overview

Watermelon Chess is played on a **21-node circular board**. **Red** and **Green** each start with 6 tokens. Players alternate turns, sliding one token per turn along a connection to an empty node. Any opponent token that gets completely surrounded — all its neighbours occupied — is **trapped and immediately removed**. The player reduced to 2 or fewer tokens (while the opponent still has 4+) loses.

---

## Features

- 🎮 Human vs Human, Human vs AI, and AI vs AI modes
- 🤖 Two AI agents: **Minimax** (Alpha-Beta pruning, depth 8) and **Monte Carlo** (300 simulations)
- 🍉 Watermelon-themed board with a beach background
- ✨ Visual indicators:
  - **Gold ring** — selected token
  - **White filled dot** — valid destination node
  - **Yellow glow** — destination of the last move
  - **Green glow** — source of the last move
  - **Red flash** — cell where an opponent token was just trapped
- 🔁 Return to setup screen at any time with `R`

---

## Project Structure

```
Watermelon Chess/
├── play.py                  # Pygame GUI — setup screen, game loop, rendering
├── watermelon_chess.py      # Game engine — State, rules, AI agents
├── assets/
│   └── watermelon_ui_bg.png # Background image
└── README.md
```

---

## Installation

**Requirements:** Python 3.9+

```bash
pip install pygame
```

Run the game:

```bash
python play.py
```

---

## How to Play

### Setup Screen

On launch, choose a player type for **Player 1 (Red)** and **Player 2 (Green)**, then click **Start Game**.

| Option      | Description                          |
| ----------- | ------------------------------------ |
| Human       | Controlled via mouse                 |
| Minimax     | AI — Minimax with Alpha-Beta pruning |
| Monte Carlo | AI — flat Monte Carlo simulation     |

### In-Game Controls

| Action          | Input                                            |
| --------------- | ------------------------------------------------ |
| Select token    | Left-click one of your tokens                    |
| Move token      | Left-click a highlighted white dot               |
| Deselect        | Click the same token again, or click empty space |
| Return to setup | `R`                                              |
| Quit            | `ESC`                                            |

---

## Game Rules

### Board

The board has **21 nodes** arranged in a circular network:

- Outer ring and four bump arcs
- Inner ring and central cross
- All nodes connected by solid black lines

### Starting Position

- **Green** occupies the 6 nodes of the top arc (row 0)
- **Red** occupies the 6 nodes of the bottom arc (row 2)
- All middle nodes start empty

### Movement

- **Red moves first**, then players alternate
- Each turn: move **exactly one token** to an adjacent empty node
- Jumping is not allowed

### Trap Rule

After each move, every opponent token **adjacent to the destination** is checked. If all of an opponent token's neighbours are occupied, it is **trapped and immediately removed**. Multiple tokens can be removed in a single turn.

### Win Condition

A player **loses** when they have **≤ 2 tokens** remaining while the opponent has **≥ 4 tokens**.

A **draw** occurs if both players fall below the threshold simultaneously, or no legal moves remain.

---

## AI Agents

### Minimax (Alpha-Beta)

Depth-limited Minimax search with Alpha-Beta pruning.

- **Depth:** 8 plies (adjustable via `DEPTH` in `watermelon_chess.py`)
- **Terminal score:** exact `utility()` value × 1000 (prefers faster wins)
- **Heuristic:** `(green_tokens − red_tokens) / 12.0`
- Green = maximiser, Red = minimiser

### Monte Carlo

Flat (non-tree) Monte Carlo simulation.

- **300 playouts** distributed across all legal moves
- Each playout plays randomly for up to **150 steps**, then falls back to the heuristic
- Immediately selects any move leading to a known terminal state

---

## API Reference

```python
from watermelon_chess import State, actions, result, utility, minimax, monte_carlo

state = State()                      # initial board, Red moves first

moves = actions(state)               # set of ((fr,fc), (tr,tc)) tuples
new_state = result(state, action)    # apply a move, returns new State

u = utility(state)
# None  → game in progress
# 1     → Green wins
# -1    → Red wins
# 0     → Draw

action = minimax(state)              # best move via Minimax (depth 8)
action = monte_carlo(state)          # best move via Monte Carlo (300 sims)
```

**Board encoding:**

| Value | Meaning     |
| ----- | ----------- |
| `1`   | Green token |
| `-1`  | Red token   |
| `0`   | Empty node  |

---

## License

This project is released under the [MIT License](https://opensource.org/licenses/MIT).
