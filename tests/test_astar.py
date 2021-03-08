import random
from typing import Tuple

import numpy as np
import pytest

from fleet import astar
from fleet.serializable import Map


@pytest.mark.parametrize(
    argnames=("from_pos", "to_pos", "expected_n_moves", "obstacles",
              "obstructed"),
    argvalues=(
            # Test single obstacles
            ((0, 0, 0), (4, 0, 1), 6, [[1, 0, 0]], False),
            ((0, 0, 0), (4, 0, 1), 8, [[1, 0, 0], [0, 0, 1]], False),
            # Test cornered against 0 grid (the path should work, and travel
            # into the negative direction!)
            ((0, 0, 0), (4, 0, 1), 8, [[1, 0, 0], [0, 0, 1], [0, 1, 0]], False),
            # Test being completely blocked leads to no path
            ((0, 0, 0), (4, 4, 4), 13,
             [[1, 0, 0], [0, 0, 1], [0, 1, 0], [0, -1, 0], [-1, 0, 0],
              [0, 0, -1]], True),
            ((2, 2, 2), (-4, -4, -4), 19,
             [[3, 2, 2], [2, 2, 3], [2, 3, 2], [2, 1, 2], [1, 2, 2],
              [2, 2, 1]], True),
            # Test when the end goal itself is completely enveloped
            ((5, 5, 5), (0, 0, 0), 16,
             [[1, 0, 0], [0, 0, 1], [0, 1, 0], [0, -1, 0], [-1, 0, 0],
              [0, 0, -1]], True),
            # Test cases with no obstacles
            ((0, 0, 0), (4, 4, 4), 13, [], False),
            ((0, 0, 0), (4, 0, 0), 5, [], False),
            ((0, 0, 0), (0, 0, 4), 5, [], False),
            ((0, 0, 0), (0, 4, 4), 9, [], False),
            # Test cases that will have from/to points outside of the obstacle
            # min/mx
            ((-5, -4, -3), (30, 30, 30), 103, [[-4, -4, -3], [-3, -4, -3]],
             False),
            # Test when the end-goal is an obstacle a path is still yielded
            ((0, 0, 0), (1, 0, 0), 2, [[1, 0, 0]], True),
            ((0, 0, 0), (1, 1, 1), 4, [[1, 1, 1]], True),
            # Test something super far away doesn't take long, because of
            # e_admissibility (it used to never complete!)
            ((0, 0, 0), (1000, 3000, 2500), 6501,
             [[i, i, i] for i in range(1, 1000)] +
             [[i - 1, i - 1, i - 1] for i in range(2, 1000)],
             False),
    )
)
def test_astar_3d_as_2d(from_pos: Tuple[int],
                        to_pos: Tuple[int],
                        expected_n_moves: int,
                        obstacles: Tuple[Tuple[int]],
                        obstructed: bool):
    """This is a more opinionated test for validating astar3D with exact
    parameters"""
    map = Map(
        position=from_pos,
        direction=0,
        obstacles=obstacles
    )

    path, path_obstructed = astar(
        from_pos=map.position,
        to_pos=to_pos,
        map=map,
        obstacle_cost=10,
        e_admissibility=2
    )

    assert obstructed == path_obstructed

    # Ensure the path actually gets you to the end location
    if len(path):
        from_pos = np.array(from_pos)
        to_pos = np.array(to_pos)
        for point in path:
            direction = from_pos - np.array(point)
            from_pos -= direction
        assert (to_pos == from_pos).all()
    assert len(path) == expected_n_moves


@pytest.mark.parametrize(
    argnames=(
            "block_center", "radius", "from_pos", "to_pos", "expected_n_moves",
            "obstacle_cost", "obstructed"),
    argvalues=[
        # Test that with an obstacle cost of 1, the straightest path is taken
        ((0, 0, 0), 1, (-2, 0, 0), (2, 0, 0), 5, 1, True),
        # Test that with an obstacle cost of less than or equal to 1, going
        # through obstacles is totally A-OK!
        ((0, 0, 0), 1, (-2, -2, -2), (2, 2, 2), 13, 0, True),
        ((0, 0, 0), 1, (-2, -2, -2), (2, 2, 2), 13, 1, True),
        ((0, 0, 0), 1, (-2, -2, -2), (2, 2, 2), 13, 1.1, False),
        # Test that with an obstacle cost of 2 or below, the path routes
        # through the blockage, and at over 4, it goes direct
        ((0, 0, 0), 1, (-2, 0, 0), (2, 0, 0), 5, 2, True),
        ((0, 0, 0), 1, (-2, 0, 0), (2, 0, 0), 9, 2.01, False),
        # Here we have a block of 13 in diameter.
        ((0, 0, 0), 6, (-14, 0, 0), (14, 0, 0), 29, 1, True),
        ((0, 0, 0), 6, (-14, 0, 0), (14, 0, 0), 29, 1.999, True),
        ((0, 0, 0), 6, (-14, 0, 0), (14, 0, 0), 43, 2, False),
        ((0, 0, 0), 6, (-14, 0, 0), (14, 0, 0), 43, 2.001, False),
    ]
)
def test_obstacle_cost(
        block_center: Tuple[int],
        radius: int,
        from_pos: Tuple[int],
        to_pos: Tuple[int],
        expected_n_moves: int,
        obstacle_cost: int,
        obstructed: bool):
    obstacles = generate_obstacle_block(
        center=block_center,
        radius=radius)
    map = Map(
        position=from_pos,
        direction=0,
        obstacles=obstacles
    )

    path, path_obstructed = astar(
        from_pos=map.position,
        to_pos=to_pos,
        map=map,
        obstacle_cost=obstacle_cost,
        e_admissibility=1
    )

    assert path_obstructed == obstructed
    assert expected_n_moves == len(path)

    print(path)


def generate_obstacle_block(center, radius):
    """Generates a block of obstacles surrounding a center, optionally
    excluding the center
    """
    obstacles = []

    for x in range(center[0] - radius, center[0] + radius + 1):
        for y in range(center[1] - radius, center[1] + radius + 1):
            for z in range(center[2] - radius, center[2] + radius + 1):
                obstacles.append([x, y, z])

    assert len(obstacles) == (radius * 2 + 1) ** 3
    return obstacles
