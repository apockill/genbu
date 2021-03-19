from typing import Tuple

import pytest
import mock
import numpy as np

from fleet import NavigationTurtle


@pytest.mark.parametrize(
    argnames=("map_pos", "to_pos", "map_dir", "turn_direction"),
    argvalues=[
        ((0, 0, 0), (1, 0, 0), 0, None),
        ((0, 0, 0), (-1, 0, 0), 0, "either"),
        ((0, 0, 0), (0, 1, 0), 0, None),
        ((0, 0, 0), (0, -1, 0), 0, None),
        ((0, 0, 0), (0, 0, 1), 0, "right"),
        ((0, 0, 0), (0, 0, -1), 0, "left"),

        ((0, 0, 0), (1, 0, 0), 90, "left"),
        ((0, 0, 0), (-1, 0, 0), 90, "right"),
        ((0, 0, 0), (0, 1, 0), 90, None),
        ((0, 0, 0), (0, -1, 0), 90, None),
        ((0, 0, 0), (0, 0, 1), 90, None),
        ((0, 0, 0), (0, 0, -1), 90, "either"),

        ((0, 0, 0), (-1, 0, 0), 180, None),
        ((0, 0, 0), (1, 0, 0), 180, "either"),
        ((0, 0, 0), (0, 1, 0), 180, None),
        ((0, 0, 0), (0, -1, 0), 180, None),
        ((0, 0, 0), (0, 0, 1), 180, "left"),
        ((0, 0, 0), (0, 0, -1), 180, "right"),

        ((0, 0, 0), (-1, 0, 0), 270, "left"),
        ((0, 0, 0), (1, 0, 0), 270, "right"),
        ((0, 0, 0), (0, 1, 0), 270, None),
        ((0, 0, 0), (0, -1, 0), 270, None),
        ((0, 0, 0), (0, 0, -1), 270, None),
        ((0, 0, 0), (0, 0, 1), 270, "either"),
    ]
)
def test_turn_toward(map_pos: Tuple[int],
                     to_pos: Tuple[int],
                     map_dir: int,
                     turn_direction: int):
    """
    :param map_pos: Starting position
    :param to_pos: Position to turn towards
    :param map_dir:  Direction the map has recorded
    :param turn_direction: -1: turn_left
                            0: No turn called
                            1: turn_right
    :return:
    """
    turtle = NavigationTurtle()
    with turtle.state as state:
        map = state.map.read()

        map.position = np.array(map_pos)
        map.direction = map_dir
        state.map.write(map)

    with turtle.state as state:
        with mock.patch.object(turtle, "turn_left") as turn_left, \
                mock.patch.object(turtle, "turn_right") as turn_right:
            # Ensure state before the test starts
            map = state.map.read()
            assert (map.position == map_pos).all()
            assert map.direction == map_dir

            # Run the function in question
            turtle.turn_toward(np.array(to_pos))

            # Validate the right function was called (and nothing else)
            if turn_direction is None:
                assert turn_left.call_count == 0
                assert turn_right.call_count == 0
            elif turn_direction == "left":
                assert turn_left.call_count == 1
                assert turn_right.call_count == 0
            elif turn_direction == "right":
                assert turn_left.call_count == 0
                assert turn_right.call_count == 1
            elif turn_direction == "either":
                assert turn_left.call_count + turn_right.call_count == 1
