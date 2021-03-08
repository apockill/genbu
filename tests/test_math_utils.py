import numpy as np

from fleet import math_utils


def test_sign():
    assert math_utils.sign(70) == 1
    assert math_utils.sign(-2983) == -1
    assert math_utils.sign(0) == 0


def test_angle_between():
    assert math_utils.angle_between([0, 0, 0], [58, 0, 0]) == 0
    assert math_utils.angle_between([0, 0, 0], [-62, 0, 0]) == 180
    assert math_utils.angle_between([0, 0, 0], [0, 34, 0]) == 0
    assert math_utils.angle_between([0, 0, 0], [0, 0, 72]) == 90
    assert math_utils.angle_between([0, 0, 0], [0, 0, -43]) == -90


def test_is_adjacent():
    """Returns True if pos1 is adjacent to pos2"""
    for direction in math_utils.NEIGHBOR_DIRECTIONS:
        assert math_utils.is_adjacent(direction, [0, 0, 0])
        assert not math_utils.is_adjacent(direction, [1, 1, 1])


def test_distance():
    """Sanity test"""
    distance = math_utils.distance(np.array([1, 2, 3]), np.array([6, 7, 12]))
    assert distance == 11.445523142259598
