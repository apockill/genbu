import numpy as np

from math import atan2, degrees, cos, sin, radians

from fleet.direction import Direction

NEIGHBOR_COORDS = np.array(
    [[1, 0, 0], [0, 1, 0], [0, 0, 1], [-1, 0, 0], [0, -1, 0],
     [0, 0, -1]])
"""All possible directions a turtle could go relative to a block"""

ANGLES = {
    (1, 0): 0,
    (0, 1): 90,
    (-1, 0): 180,
    (0, -1): 270
}
"""Vectors representing the directions a turtle can face to their angle 
representation"""


def get_angle(from_pos: np.ndarray, to_pos: np.ndarray):
    """Get the direction of a vector going from that position to the next
    This function is purposely simply for perf and the nicety of having clear
    errors if I misuse this.
    """
    x, _, z = to_pos - from_pos
    diff = (x, z)
    return ANGLES[diff]


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
    for direction in NEIGHBOR_COORDS:
        if ((pos1 + direction) == pos2).all():
            return True
    return False


def distance(pos1: np.ndarray, pos2: np.ndarray):
    """Returns the exact distance between two points"""
    return np.linalg.norm(pos1 - pos2)


def turtle_distance(pos1: np.ndarray, pos2: np.ndarray):
    """Returns the non-diagonal movement distance for a turtle"""
    return np.abs(pos1 - pos2).sum()


def coordinate_in_turtle_direction(curr_pos: np.ndarray,
                                   curr_angle: float,
                                   direction: Direction) -> np.ndarray:
    curr_x, curr_y, curr_z = curr_pos

    if direction is Direction.up:
        return np.array((curr_x, curr_y + 1, curr_z))
    elif direction is Direction.down:
        return np.array((curr_x, curr_y - 1, curr_z))
    else:
        move_sign = 1
        if direction is Direction.right:
            curr_angle += 90
        elif direction is Direction.left:
            curr_angle -= 90
        elif direction is Direction.back:
            move_sign = -1

        return np.array([
            round(move_sign * cos(radians(curr_angle))) + curr_x,
            curr_y,
            round(move_sign * sin(radians(curr_angle))) + curr_z
        ])
