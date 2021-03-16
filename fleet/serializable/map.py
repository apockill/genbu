from typing import Dict, Any, Union, Tuple, List

import numpy as np

from fleet import math_utils
from fleet.serializable.base import BaseSerializable


class Map(BaseSerializable):
    def __init__(self, position: Union[Tuple[int], List[int]],
                 direction: int,
                 obstacles: Union[np.ndarray, List[List[int]]] = None):
        """
        :param position: The current position in the map
        :param direction: The direction the turtle is facing in the map
        :param obstacles: The point cloud of all obstacles ever encountered
        """
        self.position: np.ndarray = np.array(position)
        self.obstacles: np.ndarray = (
            np.zeros(shape=(0, 3), dtype=np.int8)
            if obstacles is None or len(obstacles) == 0 else
            np.array(obstacles))
        self.direction: int = direction

    def __repr__(self):
        return f"Map(n_obstacles={len(self.obstacles)}, " \
               f"position={self.position}," \
               f"direction={self.direction})"

    def move_to(self, position: Union[np.ndarray, Tuple]):
        """Move to an adjacent block relative to the current position"""
        if math_utils.turtle_distance(position, self.position) > 2:
            msg = ("The turtle was asked to move to a non-adjacent position! "
                   f"Last known position: {self.position}, "
                   f"Move position: {position} ")
            # TODO: input() can't run on multiple turtles! Ideally, we would
            #       prompt the user or approval to continue moving.
            print(msg)
        position = np.array(position)
        self.remove_obstacle(position)
        self.position = position

    def remove_obstacle(self, position):
        """Clear an obstacle if it exists in the array"""
        delete_row = np.where((self.obstacles == position).all(axis=1))
        self.obstacles = np.delete(self.obstacles, delete_row, axis=0)

    def add_obstacle(self, position: Union[np.ndarray, List]):
        if self.is_known_obstacle(position):
            # This obstacle is already registered. No need to register it!
            return
        self.obstacles = np.vstack((self.obstacles, position))

    def is_known_obstacle(self, position: np.ndarray):
        """Returns whether this is a known obstacle"""
        return any((self.obstacles == position).all(axis=1))

    def to_dict(self) -> Dict[str, Any]:
        return {"position": self.position.tolist(),
                "direction": self.direction,
                "obstacles": self.obstacles.tolist()}

    @classmethod
    def from_dict(cls, obj: Dict[str, Any]) -> 'Map':
        return cls(obstacles=np.array(obj["obstacles"]),
                   position=obj["position"],
                   direction=obj["direction"])
