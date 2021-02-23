import random

import numpy as np
import pytest

from fleet.astar import Astar3D
from fleet.serializable import Map

random.seed("pycraft")


def generate_map() -> Map:
    astar = Astar3D()

    map = Map(position=(0, 0, 0), direction=0)
    for i in range(random.randint(0, 1000)):
        point = map.points[-1].copy() + random.choice(
            astar.get_neighbors_directions())
        map._add_point(point)
    return map


@pytest.mark.parametrize(
    argnames=("fuzzed_map",),
    argvalues=((generate_map(),) for _ in range(25))
)
def test_fuzzy_astar_3d(fuzzed_map: Map):
    """Generate a map then test astar can retrace its steps"""
    astar = Astar3D()
    assert (fuzzed_map.offset_points >= [0, 0, 0]).all()
    start_point = fuzzed_map.points[-1].copy()
    end_point = fuzzed_map.points[0].copy()

    path = astar.generate_path(
        map=fuzzed_map,
        from_pos=start_point.tolist(),
        to_pos=end_point.tolist())

    # Make sure a path was output, or else
    assert len(path) != 0 or (start_point == end_point).all(), \
        "No path was found!"

    for point in path:
        direction = start_point - np.array(point)
        start_point -= direction

    assert (end_point == start_point).all()


def test_no_path_found():
    astar = Astar3D()
    map = Map(position=(0, 0, 0),
              direction=0,
              points=np.array([(22, 22, 22), (22, 23, 22)]))

    # Test pathfinding fails when unreachable state is requested
    path = astar.generate_path(map, (22, 23, 22))
    assert (path == np.array([])).all()
    assert len(path) == 0

    # Test pathfinding does work on this same map, with a different
    # start location
    path = astar.generate_path(map, (22, 23, 22), from_pos=(22, 22, 22))
    assert (path == [[22, 22, 22], [22, 23, 22]]).all()
