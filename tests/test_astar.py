import random

import numpy as np
import pytest

from fleet.astar import TurtleAstar
from fleet.serializable import Map


@pytest.mark.parametrize(
    argnames=("from_dest", "to_dest", "expected_n_moves", "obstacles"),
    argvalues=(
            # Test single obstacles
            ((0, 0, 0), (4, 0, 1), 6, [[1, 0, 0]]),
            ((0, 0, 0), (4, 0, 1), 8, [[1, 0, 0], [0, 0, 1]]),
            # Test cornered against 0 grid (the path should work, and travel
            # into the negative direction!)
            ((0, 0, 0), (4, 0, 1), 8, [[1, 0, 0], [0, 0, 1], [0, 1, 0]]),
            # Test being completely blocked leads to no path
            ((0, 0, 0), (4, 4, 4), 0,
             [[1, 0, 0], [0, 0, 1], [0, 1, 0], [0, -1, 0], [-1, 0, 0],
              [0, 0, -1]]),
            ((2, 2, 2), (4, 4, 4), 0,
             [[3, 2, 2], [2, 2, 3], [2, 3, 2], [2, 1, 2], [1, 2, 2],
              [2, 2, 1]]),
            # Test cases with no obstacles
            ((0, 0, 0), (4, 4, 4), 13, []),
            ((0, 0, 0), (4, 0, 0), 5, []),
            ((0, 0, 0), (0, 0, 4), 5, []),
            ((0, 0, 0), (0, 4, 4), 9, []),
            # Test cases that will have from/to points outside of the obstacle
            # min/mx
            ((-5, -4, -3), (30, 30, 30), 103, [[-4, -4, -3], [-3, -4, -3]]),
    )
)
def test_astar_3d_as_2d(from_dest, to_dest, expected_n_moves, obstacles):
    """This is a more opinionated test for validating astar3D with exact
    parameters"""
    map = Map(
        position=from_dest,
        direction=0,
        obstacles=obstacles
    )

    path = TurtleAstar(map.obstacles).astar(
        map.position,
        to_dest
    )

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
