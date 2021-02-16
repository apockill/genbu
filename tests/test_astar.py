import numpy as np
import random
import pytest

from fleet.serializable import Map
from fleet.astar import Astar3D

random.seed("pycraft")


def generate_map() -> Map:
    astar = Astar3D()

    map = Map(points=np.array([[0, 0, 0]]))
    for i in range(random.randint(0, 1000)):
        point = map.points[-1].copy() + random.choice(
            astar.get_neighbors_directions())
        map.add_point(point)
    return map


@pytest.mark.parametrize(
    argnames=("fuzzed_map",),
    argvalues=((generate_map(),) for _ in range(100))
)
def test_fuzzy_astar_3d(fuzzed_map: Map):
    """Generate a map then test astar can retrace its steps"""
    astar = Astar3D()
    assert (fuzzed_map.offset_points >= [0, 0, 0]).all()
    start_point = fuzzed_map.points[-1].copy()
    end_point = fuzzed_map.points[0].copy()

    path = astar.generate_path(
        map=fuzzed_map,
        start_point=start_point.tolist(),
        end_point=end_point.tolist())
    path = np.array(path)
    path += fuzzed_map.zero_offset

    # Make sure a path was output, or else
    assert len(path) != 0 or (start_point == end_point).all(), \
        "No path was found!"

    for point in path:
        direction = start_point - np.array(point)
        start_point -= direction

    assert (end_point == start_point).all()
