# Nardy AI Agent

This project is a web-based implementation of **Nardy (Long Nardy)** with two play modes:

1. **Human vs Human**
2. **Human vs AI**

The system is implemented as a **Flask application** with a **JavaScript front end** and **Python game logic**. The AI player uses an **Expectiminimax search algorithm** to choose moves under dice uncertainty.

## Project Overview

Nardy is a two-player board game played on a board with **24 points**. Each player has **15 checkers**. Players move their checkers around the board according to dice rolls and try to bear off all checkers first.

The main challenge is that dice rolls are random, so the AI must choose strong moves even though future rolls are uncertain.

## Features

- Browser-based Nardy game interface
- Human vs Human mode
- Human vs AI mode
- Opening roll to decide the starting player
- Dice rolling with doubles handled as four moves
- Legal move generation based on Nardy rules
- Head rule support
- Bearing-off logic
- AI agent using Expectiminimax
- Random AI for comparison experiments
- Script for comparing Expectiminimax AI against Random AI
- Bar chart output for AI performance results

## Rules Implemented

The project implements the main Nardy rules used by the game logic:

- The board has **24 points**.
- Each player starts with **15 checkers** on their starting head point.
- Player 1 moves from point 24 toward point 1.
- Player 2 moves from point 12 toward point 13 through the full board path.
- A player cannot move onto a point occupied by the opponent.
- Doubles are played four times.
- A player may bear off only when all their checkers are in the home board.
- Normally, only one checker may leave the head point per turn.
- On the initial position, double 3, double 4, and double 6 allow two checkers to leave the head point.
- Six-point blocking is checked to prevent fully trapping the opponent behind a complete block.

## AI Approach

The AI uses **Expectiminimax**, which is suitable for games with both player decisions and chance events.

The search includes:

- **MAX nodes**: the AI chooses the best move.
- **MIN nodes**: the opponent is assumed to choose the best response for themselves.
- **CHANCE nodes**: dice outcomes are averaged using their probabilities.

Dice outcomes are modeled as **21 distinct outcomes**:

- 6 doubles, each with probability `1/36`
- 15 non-doubles, each with probability `2/36`

## Heuristic Evaluation

Since the AI cannot search the full game tree, it evaluates board states using a heuristic function. The heuristic considers:

- Race progress
- Number of checkers borne off
- Isolated single checkers
- Controlled points with multiple checkers
- Checkers in the home board

These features help the AI estimate which board positions are better.

## Project Structure

```text
Nardy/
├── ai_agent.py              # Expectiminimax AI agent
├── app.py                   # Flask app for Human vs Human mode
├── app_ai.py                # Flask app for Human vs AI mode
├── compare_ai_agents.py     # Experiment script: Expectiminimax vs Random AI
├── config.py                # Game constants
├── game_logic.py            # Main Nardy rules and legal move logic
├── game_state.py            # Board state representation
├── main.py                  # Console Human vs Human version
├── random_ai.py             # Random AI agent
├── run_game.py              # Browser launcher for game mode selection
├── utils.py                 # Helper functions
├── static/
│   ├── script.js            # Front-end logic for Human vs Human mode
│   ├── script_ai.js         # Front-end logic for Human vs AI mode
│   ├── style.css            # Page styling
│   └── dice/                # Dice images
└── templates/
    ├── index.html           # Human vs Human page
    ├── index_ai.html        # Human vs AI page
    └── mode_select.html     # Mode selection page
```
## GitHub Repository
Repository Link: 
https://github.com/LalaHuseynova/Nardy

## Installation

### 1. Clone or download the project

Download the project folder and open it in a terminal.

### 2. Create a virtual environment

```bash
python3 -m venv .venv
```

### 3. Activate the virtual environment

On macOS or Linux:

```bash
source .venv/bin/activate
```

On Windows:

```bash
.venv\Scripts\activate
```

### 4. Install dependencies

```bash
pip install flask matplotlib
```

## How to Run the Browser Game

Run:

```bash
python3 run_game.py
```

Then open the link shown in the terminal, usually:

```text
http://127.0.0.1:5050/
```

Choose one of the modes:

- **Human vs Human**
- **Human vs AI**

## How to Run the Console Version

Run:

```bash
python3 main.py
```

This starts a simple console-based Human vs Human game.

## How to Run AI Comparison Experiments

Run:

```bash
python3 compare_ai_agents.py
```

This compares the Expectiminimax AI against the Random AI. After the games finish, the script prints the results and saves a chart named:

```text
ai_performance_results.png
```


