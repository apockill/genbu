from typing import List

import numpy as np

from fleet import (
    routines,
    Astar3D,
    StatefulTurtle,
    StateAttr,
    PromptStateAttr,
    lua_errors)
from fleet.math_utils import sign, angle_between, is_adjacent


class NavigationMixin(StatefulTurtle):
    """Adds high-level methods helpful for moving around"""

    def move_toward_destructively(self, to_pos):
        try:
            self.move_toward(to_pos)
        except lua_errors.TurtleBlockedError as e:
            self.dig_towards(e.direction)

    def move_toward(self, to_pos):
        """Make a move in one of these directions, turning automatically"""
        path = self.generate_path(to_pos)
        self.move_along_path(path)

    def move_along_path(self, path: List[int]):
        if len(path) == 0:
            return

        with self.state as state:
            map = state.map.read()
        curr_pos = map.position.tolist()
        if map.position.tolist() in path and len(path) > 1:
            path = path[path.index(curr_pos) + 1:]

        # Try to movZe toward that direction
        next_pos = np.array(path[0])
        dist = next_pos - curr_pos
        assert abs(dist.sum()) == 1, \
            "The move must be to an adjacent path!"

        if dist[1] != 0:
            self.move_vertically(dist[1])
        elif dist[0] != 0 or dist[2] != 0:
            self.turn_toward(next_pos)
            self.forward()

    def generate_path(self, to_pos, from_pos=None):
        """
        :param to_pos: The position to pathfind to
        :param from_pos: The position from which to pathfind to. If None, it
        will choose the turtles current position.
        :return:
        """
        with self.state as state:
            map = state.map.read()

        # Move along the shortest axis first, then the longest
        astar = Astar3D()
        nearest_known = map.nearest_known_position(target_position)
        path = astar.generate_path(
            map=map,
            end_point=nearest_known)[1:]

        if len(path) == 0 and (map.position != target_position).any():
            # If we've reached the nearest_known location already
            self.explore_towards(target_position)
        else:
            next_move = path[0]
            x, y, z = next_move
            if x == map.position[0] and z == map.position[2]:
                assert sign(y - map.position[1]) != 0
                self.move_vertically(sign(y - map.position[1]))
            else:
                self.turn_toward(next_move)
                self.forward()

        if len(path) == 0:
            path = []

        # Astar only gets you to the nearest known spot. After Astar you need
        # do some naive "exploration" along each relevant axis.
        while not len(path) or not path[-1] == to_pos:
            curr_pos = path[-1] if len(path) else from_pos
            dist = np.array(to_pos) - curr_pos
            curr_x, curr_y, curr_z = curr_pos
            if dist[0] != 0:
                path.append([curr_x + sign(dist[0]), curr_y, curr_z])
            elif dist[2] != 0:
                path.append([curr_x, curr_y, curr_z + sign(dist[2])])
            elif dist[1] != 0:
                path.append([curr_x, curr_y + sign(dist[1]), curr_z])
            else:
                raise RuntimeError(f"How was there no move?"
                                   f"{path} {curr_pos} {to_pos}")

        return path

    def turn_toward(self, to_pos):
        """Turn toward the target_position
        """
        map = self.state.map.read()
        x_dist, _, z_dist = to_pos.copy() - map.position
        if x_dist == 0 and z_dist == 0:
            return

        unit_vector = [sign(x_dist), 0, sign(z_dist)]
        turn_angle = angle_between(np.array([0, 0, 0]), unit_vector)
        turn_direction = sign(turn_angle % 360 - map.direction)

        if turn_direction != 0:
            if turn_direction > 0:
                self.turn_right()
            elif turn_direction < 0:
                self.turn_left()

QuarryTurtle().run()
