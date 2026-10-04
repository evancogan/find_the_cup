# Find the Cup

A shell game. I'm using this simple game to try some Test-Driven Development (TDD) techniques.

<img width="797" height="594" alt="image" src="https://github.com/user-attachments/assets/efd47e4e-381b-4cf1-a15d-85da637a3cd5" />


## How to play

1. Click **START**.
2. The cups lift to show which one is hiding the ball, then lower again.
3. The cups shuffle. Keep your eye on the one with the ball.
4. When they stop, click the cup you think has the ball. The positions are labelled Cup 1, Cup 2 and Cup 3, from left to right.
5. Find out if you were right. If not, the game tells you where the ball was.
6. Click **RESTART** to play again.

## Getting started

Requires Python 3 and pygame.

```bash
pip install pygame pytest
python find_the_cup.py
```

## Running the tests

```bash
python -m pytest tests -v
```

_WIP: how I approached testing (test-first, red to green) and what the tests cover._

## What I learned

_WIP: the things I'm proudest of figuring out._

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.
