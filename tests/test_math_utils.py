from typing import Tuple

import numpy as np
import pytest

from fleet import math_utils, Direction


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
    for direction in math_utils.NEIGHBOR_COORDS:
        assert math_utils.is_adjacent(direction, [0, 0, 0])
        assert not math_utils.is_adjacent(direction, [1, 1, 1])


def test_distance():
    """Sanity test"""
    distance = math_utils.distance(np.array([1, 2, 3]), np.array([6, 7, 12]))
    assert distance == 11.445523142259598


@pytest.mark.parametrize(
    argnames=("curr_pos", "curr_angle", "direction", "expected_output"),
    argvalues=[
        ((0, 0, 0), 0, Direction.front, (1, 0, 0)),
        ((0, 0, 0), 90, Direction.front, (0, 0, 1)),
        ((0, 0, 0), 180, Direction.front, (-1, 0, 0)),
        ((0, 0, 0), 270, Direction.front, (0, 0, -1)),
        ((0, 0, 0), 360, Direction.front, (1, 0, 0)),

        ((0, 0, 0), 0, Direction.back, (-1, 0, 0)),
        ((0, 0, 0), 90, Direction.back, (0, 0, -1)),
        ((0, 0, 0), 180, Direction.back, (1, 0, 0)),
        ((0, 0, 0), 270, Direction.back, (0, 0, 1)),
        ((0, 0, 0), 360, Direction.back, (-1, 0, 0)),

        ((0, 0, 0), 0, Direction.left, (0, 0, -1)),
        ((0, 0, 0), 90, Direction.left, (1, 0, 0)),
        ((0, 0, 0), 180, Direction.left, (0, 0, 1)),
        ((0, 0, 0), 270, Direction.left, (-1, 0, 0)),
        ((0, 0, 0), 360, Direction.left, (0, 0, -1)),

        ((0, 0, 0), 0, Direction.right, (0, 0, 1)),
        ((0, 0, 0), 90, Direction.right, (-1, 0, 0)),
        ((0, 0, 0), 180, Direction.right, (0, 0, -1)),
        ((0, 0, 0), 270, Direction.right, (1, 0, 0)),
        ((0, 0, 0), 360, Direction.right, (0, 0, 1)),

        ((0, 0, 0), 0, Direction.up, (0, 1, 0)),
        ((0, 0, 0), 90, Direction.up, (0, 1, 0)),
        ((0, 0, 0), 180, Direction.up, (0, 1, 0)),
        ((0, 0, 0), 270, Direction.up, (0, 1, 0)),
        ((0, 0, 0), 360, Direction.up, (0, 1, 0)),

        ((0, 0, 0), 0, Direction.down, (0, -1, 0)),
        ((0, 0, 0), 90, Direction.down, (0, -1, 0)),
        ((0, 0, 0), 180, Direction.down, (0, -1, 0)),
        ((0, 0, 0), 270, Direction.down, (0, -1, 0)),
        ((0, 0, 0), 360, Direction.down, (0, -1, 0)),
    ]
)
def test_coordinate_in_turtle_direction(curr_pos: Tuple[int],
                                        curr_angle: float,
                                        direction: Direction,
                                        expected_output: Tuple):
    output = math_utils.coordinate_in_turtle_direction(
        curr_pos=np.array(curr_pos),
        curr_angle=curr_angle,
        direction=direction
    )
    assert (output == expected_output).all()
