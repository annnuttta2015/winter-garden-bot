import random
from typing import List

# Цветы
BASE_FLOWERS: List[str] = ['🌷', '🌹', '🌸', '🌺', '🌼']
ADVANCED_FLOWERS: List[str] = ['🪻', '🪷', '🌻']
ALL_FLOWERS: List[str] = BASE_FLOWERS + ADVANCED_FLOWERS

def get_random_flower(flower_count: int) -> str:
    """Returns a random flower based on the current flower count.

    Args:
        flower_count (int): The total number of flowers a user has.

    Returns:
        str: An emoji string representing a random flower.
    """
    if flower_count < 10:
        return random.choice(BASE_FLOWERS)
    else:
        return random.choice(ALL_FLOWERS)

def should_give_flower(total_stitches: int, prev_stitches: int) -> bool:
    """Determines if a new flower should be given based on stitch count.

    Args:
        total_stitches (int): The total number of stitches after adding.
        prev_stitches (int): The number of stitches before adding.

    Returns:
        bool: True if a new flower should be given, False otherwise.
    """
    return total_stitches // 500 > prev_stitches // 500

def has_caterpillar() -> bool:
    """Determines if a caterpillar appears.

    Returns:
        bool: True if a caterpillar appears (10% chance), False otherwise.
    """
    return random.random() < 0.1  # 10% шанс
