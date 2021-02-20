import numpy as np

from math import atan2, degrees

NEIGHBOR_DIRECTIONS = np.array(
    [[1, 0, 0], [0, 1, 0], [0, 0, 1], [-1, 0, 0], [0, -1, 0],
     [0, 0, -1]])
"""All possible directions a turtle could go relative to a block"""


def sign(num):
    # TODO: add tests
    if num > 0:
        return 1
    if num < 0:
        return -1
    else:
        return 0


def angle_between(pos1, pos2):
    """Give the clockwise angle between pos2 and pos1
    Where pos2 is the target, and pos1 is the current position.
    """
    # TODO: add tests
    x1, _, z1 = pos1
    x2, _, z2 = pos2
    angle = atan2(z2 - z1, x2 - x1)
    return degrees(angle)


def is_adjacent(pos1: np.ndarray, pos2: np.ndarray):
    """Returns True if pos1 is adjacent to pos2"""
    for direction in NEIGHBOR_DIRECTIONS:
        if ((pos1 + direction) == pos2).all():
            return True
    return False