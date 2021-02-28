import numpy as np

from fleet import Map


def test_add_and_delete_obstacle():
    obstacles = np.array([[0, 1, 2], [3, 4, 5], [0, 1, 5], [3, 4, 2]])

    map = Map(
        position=(0, 0, 0),
        direction=0,
        obstacles=obstacles
    )
    assert (map.obstacles == obstacles).all()

    # Test obstacle removal
    map.remove_obstacle([0, 1, 5])
    assert (map.obstacles == [[0, 1, 2], [3, 4, 5], [3, 4, 2]]).all()
    map.remove_obstacle([0, 1, 2])
    assert (map.obstacles == [[3, 4, 5], [3, 4, 2]]).all()
    map.remove_obstacle([3, 4, 2])
    assert (map.obstacles == [[3, 4, 5]]).all()

    # Test adding obstacles
    map.add_obstacle([69, 42, 0])
    assert (map.obstacles == [[3, 4, 5], [69, 42, 0]]).all()


    # Test adding to an obstacle list of size(0)
    map.remove_obstacle([3, 4, 5])
    map.remove_obstacle([69, 42, 0])
    map.add_obstacle([1, 2, 3])
    assert (map.obstacles == [[1, 2, 3]]).all()
