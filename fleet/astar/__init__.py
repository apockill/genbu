from typing import Sequence

from fleet.math_utils import NEIGHBOR_DIRECTIONS

import numpy as np
from astar import AStar


class TurtleAstar(AStar):
    def __init__(self, obstacles: np.ndarray, e_admissibility=2):
        """
        :param obstacles: A numpy array of obstacles. Obtained by map.obstacles
        :param e_admissibility: A multiplier to significantly speed up A*.
        A value of '1' guarrentees the most optimal path, but has compute
        implications. The larger the number, the more 'admissible' the path may
        be to detours.
        """
        self.obstacles = obstacles
        self.heuristic_multiplier = e_admissibility
        super().__init__()

    def astar(self, start: Sequence, goal: Sequence, reversePath=False):
        if isinstance(start, np.ndarray):
            start = start.tolist()
        if isinstance(goal, np.ndarray):
            goal = goal.tolist()

        path = super().astar(tuple(start), tuple(goal), reversePath=reversePath)
        if path is None:
            return []
        else:
            return list(path)

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
        return 1

    def neighbors(self, node):
        """For a given node, returns (or yields) the list of its neighbors."""
        # get neighbor coordinates, checking also map limits (cell != 0 = wall)
        for md in NEIGHBOR_DIRECTIONS:
            n = (node[0] + md[0], node[1] + md[1], node[2] + md[2])

            # Compute 3D mask
            xmask = (self.obstacles[..., 0] == n[0]) \
                    & (self.obstacles[..., 1] == n[1]) \
                    & (self.obstacles[..., 2] == n[2])

            # Only return n if it isn't an obstacle
            if ~(self.obstacles[xmask].any()):
                yield n
