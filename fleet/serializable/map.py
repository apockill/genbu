from typing import Dict, Any, Union, Tuple

import numpy as np
from scipy.spatial import cKDTree

from fleet.serializable.base import BaseSerializable


class Map(BaseSerializable):
    def __init__(self, position: tuple,
                 direction: int,
                 points: np.ndarray = None):
        """
        :param position: The current position in the map
        :param direction: The direction the turtle is facing in the map
        :param points: The point cloud of all points ever traveled
        """
        self.position = np.array(position)
        self.points = np.array([position]) if points is None else points
        self.direction = direction

    def __repr__(self):
        return f"Map(n_points={len(self.points)}, " \
               f"position={self.position}," \
               f"direction={self.direction})"

    @property
    def shape(self) -> np.ndarray:
        return np.amax(self.points, axis=0) - np.amin(self.points, axis=0)

    @property
    def offset_points(self):
        return self.points.copy() - self.zero_offset

    @property
    def zero_offset(self):
        return np.amin(self.points, axis=0)

    def nearest_known_position(self, position: np.ndarray):
        """Returns the nearest known position"""
        tree = cKDTree(self.points)
        dist, indexes = tree.query(position)
        return self.points[indexes]

    def is_known_position(self, position: np.ndarray):
        """Returns whether this is a known point"""
        return any((self.points == position).all(1))

    def set_position(self, position: np.ndarray):
        self.add_point(position)
        self.position = position

    def add_point(self, position: np.ndarray):
        if self.is_known_position(position):
            # This point is already registered. No need to register it!
            return
        self.points = np.vstack((self.points, position))

    def to_dict(self) -> Dict[str, Any]:
        return {"points": self.points.tolist(),
                "position": self.position.tolist(),
                "direction": self.direction}

    @classmethod
    def from_dict(cls, obj: Dict[str, Any]) -> 'Map':
        return cls(points=np.array(obj["points"]),
                   position=np.array(obj["position"]),
                   direction=obj["direction"])
