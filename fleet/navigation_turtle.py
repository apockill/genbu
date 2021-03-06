from typing import List, Union

import numpy as np

from fleet import (
    astar,
    StatefulTurtle,
    Direction,
    lua_errors)
from fleet.math_utils import sign, angle_between


class NavigationTurtle(StatefulTurtle):
    """Adds high-level methods helpful for moving around"""

    def move_toward(self, to_pos: Union[List[int], np.ndarray],
                    destructive=False,
                    path_obstacle_cost=10):
        """Make a move in one of these directions, turning automatically"""
        if isinstance(to_pos, np.ndarray):
            to_pos = to_pos.tolist()
        elif isinstance(to_pos, tuple):
            to_pos = list(to_pos)
        elif not isinstance(to_pos, list):
            raise ValueError(f"Unsupported type {type(to_pos)} {to_pos}")

        ##### Get the next move
        map = self.state.map.read()
        curr_pos = map.position.tolist()

        if curr_pos == to_pos:
            # Already at position!
            return

        path, path_obstructed = astar(
            from_pos=curr_pos,
            to_pos=to_pos,
            map=map,
            obstacle_cost=path_obstacle_cost,
            e_admissibility=1.1
        )
        next_pos = np.array(path[1:][0])

        ##### Move to the next position in the path
        # Try to move toward that direction
        dist = next_pos - curr_pos
        assert abs(dist.sum()) == 1, \
            f"The move must be to an adjacent path! {next_pos}"

        try:
            if dist[1] > 0:
                self.move_in_direction(Direction.up)
            elif dist[1] < 0:
                self.move_in_direction(Direction.down)
            elif dist[0] != 0 or dist[2] != 0:
                self.turn_toward(next_pos)
                self.move_in_direction(Direction.front)
        except lua_errors.TurtleBlockedError as e:
            if destructive:
                self.dig_in_direction(e.direction)
            else:
                raise

    def turn_toward(self, to_pos):
        """Turn toward the target_position
        """
        map = self.state.map.read()
        x_dist, _, z_dist = to_pos.copy() - map.position
        if x_dist == 0 and z_dist == 0:
            return

        unit_vector = [sign(x_dist), 0, sign(z_dist)]
        turn_angle = angle_between(np.array([0, 0, 0]), unit_vector)
        turn_direction = turn_angle - map.direction

        if abs(turn_direction) >= 270:
            turn_direction = turn_direction % 360

        if turn_direction != 0:
            if turn_direction > 0:
                self.turn_right()
            elif turn_direction < 0:
                self.turn_left()
