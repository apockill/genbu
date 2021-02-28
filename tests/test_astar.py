import random
from typing import List

import numpy as np
import pytest

from fleet.astar import astar
from fleet.serializable import Map


@pytest.mark.parametrize(
    argnames=("from_dest", "to_dest", "expected_n_moves", "obstacles",
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
    )
)
def test_astar_3d_as_2d(from_dest: List[int],
                        to_dest: List[int],
                        expected_n_moves: int,
                        obstacles: List[List[int]],
                        obstructed: bool):
    """This is a more opinionated test for validating astar3D with exact
    parameters"""
    map = Map(
        position=from_dest,
        direction=0,
        obstacles=obstacles
    )

    path, path_obstructed = astar(
        from_pos=map.position,
        to_pos=to_dest,
        map=map,
        obstacle_cost=10
    )

    assert obstructed == path_obstructed
    print(path, obstacles)

    # Make sure the path never leads over any obstacles
    for pos in path:
        assert pos not in obstacles

    # Ensure the path actually gets you to the end location
    if len(path):
        from_dest = np.array(from_dest)
        to_dest = np.array(to_dest)
        for point in path:
            direction = from_dest - np.array(point)
            from_dest -= direction
        assert (to_dest == from_dest).all()
    assert len(path) == expected_n_moves
