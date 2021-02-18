import numpy as np

from fleet import Map


def test_nearest_point():
    """A sanity test"""
    map = Map(
        position=(0, 0, 0),
        direction=90,
        points=np.array([[i, i * 2, i * 3] for i in range(1000)])
    )

    pos = map.nearest_known_position((20, 30, 40))
    assert (pos == [14, 28, 42]).all()

    pos = map.nearest_known_position((800, 900, 1000))
    assert (pos == [400, 800, 1200]).all()
