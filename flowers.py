import random

# Цветы
BASE_FLOWERS = ['🌷', '🌹', '🌸', '🌺', '🌼']
ADVANCED_FLOWERS = ['🪻', '🪷', '🌻']
ALL_FLOWERS = BASE_FLOWERS + ADVANCED_FLOWERS

def get_random_flower(flower_count):
    if flower_count < 10:
        return random.choice(BASE_FLOWERS)
    else:
        return random.choice(ALL_FLOWERS)

def should_give_flower(total_stitches, prev_stitches):
    return total_stitches // 500 > prev_stitches // 500

def has_caterpillar():
    return random.random() < 0.1  # 10% шанс
