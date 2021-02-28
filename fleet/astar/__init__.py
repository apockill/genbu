from typing import Sequence

from fleet.math_utils import NEIGHBOR_DIRECTIONS
from fleet import Map

import numpy as np
from astar import AStar


class TurtleAstar(AStar):
    def __init__(self, map: Map, e_admissibility: float, obstacle_cost: int):
        """
        :param obstacles: A numpy array of obstacles. Obtained by map.obstacles
        :param e_admissibility: A multiplier to significantly speed up A*.
        A value of '1' guarrentees the most optimal path, but has compute
        implications. The larger the number, the more 'admissible' the path may
        be to detours.
        :param obstacle_cost: Think of this as "how many blocks would I rather
        move around instead of breaking a block"
        """
        self.map = map
        self.heuristic_multiplier = e_admissibility
        self.obstacle_cost = obstacle_cost
        super().__init__()

    def is_goal_reached(self, current, goal):
        """ returns true when we can consider that 'current' is the goal"""
        return current == goal

    def heuristic_cost_estimate(self, current, goal):
        """Computes the estimated (rough) distance between a node and the goal.
        The second parameter is always the goal."""
        return np.abs(
            np.array(goal) - current).sum() * self.heuristic_multiplier

    def distance_between(self, n1, n2):
        """Gives the real distance between two adjacent nodes n1 and n2
        (i.e n2 belongs to the list of n1's neighbors).
        n2 is guaranteed to belong to the list returned by the call to
        neighbors(n1).
        """
        if self.map.is_known_obstacle(n1) or self.map.is_known_obstacle(n2):
            return self.obstacle_cost
        else:
            return 1

    def neighbors(self, node):
        """For a given node, returns (or yields) the list of its neighbors."""
        return ((node[0] + md[0], node[1] + md[1], node[2] + md[2])
                for md in NEIGHBOR_DIRECTIONS)

def astar(from_pos: Sequence,
          to_pos: Sequence,
          map: Map,
          obstacle_cost=10,
          e_admissibility=2):
    if isinstance(from_pos, np.ndarray):
        from_pos = from_pos.tolist()
    if isinstance(to_pos, np.ndarray):
        to_pos = to_pos.tolist()

    path = (TurtleAstar(map=map,
                        e_admissibility=e_admissibility,
                        obstacle_cost=obstacle_cost)
        .astar(
        start=tuple(from_pos),
        goal=tuple(to_pos)))

    path = list(path)
    for pos in path:
        if map.is_known_obstacle(pos):
            return path, True

    return path, False


__all__ = ["astar"]
