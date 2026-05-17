"""RandomAgent: selects a random legal action."""

import random
from typing import List, Tuple


class RandomAgent:
    """Dou Dizhu agent that picks a random legal action."""

    def __init__(self, position: int):
        if position not in (0, 1, 2):
            raise ValueError(f"Invalid position {position}, must be 0, 1, or 2")
        self.position = position

    def act(self, infoset) -> Tuple[List[List[int]], List[float]]:
        legal_actions = infoset.legal_actions
        if not legal_actions:
            return [[]], [0.0]
        action = random.choice(legal_actions)
        return [action], [0.0]
