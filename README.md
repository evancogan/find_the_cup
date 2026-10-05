# Find the Cup

A shell game. I'm using this simple game to try some Test-Driven Development (TDD) techniques.

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

The way I approached testing was to use a test-first approach, where I would write a test before writing the code to make it pass. This method of goal based development helped me to focus on the functionality I needed to implement, cutting through confusion and uncertainty, and giving me a clear goal to hit while programming. It's especially helpful in contexts where you don't have access to the internet or an LLM for assistance. Setting small goals and then achieving them one by one is a great way to build momentum and confidence, and nothing is quite like seeing your own written tests pass or fail.

## What I learned

TTD (Or, test driven development) gives feedback during development. It's a lot of fun to turn a test green! Test first seems to suit my development style. I like that you have a top down view, a goal-based-approach also helps to cut through writer's block. To test well, I found you need to test behavior over appearance (some tests turning green are just for show, and don't actually test the functionality). Tests can be examples, or invariants. Example tests are written for a specific bug, while invariant tests are more broad and test the system overall. I learned to extract methods as a debug step, which helps to isolate and understand the problem. Extracting methods is as easy as naming a method explicitly, and using a debugger or print statement to see the value of the method. The other important thing about testing is to ensure you're testing for something you can measure, no magic numbers or vague tests should be written. 

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.
