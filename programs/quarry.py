import numpy as np

from fleet import (
    routines,
    Astar3D,
    StatefulTurtle,
    TurtleBlockedError,
    StateAttr)
from fleet.math_utils import sign, angle_between


# stateless_turtle.py


class NavigationMixin(StatefulTurtle):
    """Adds high-level methods helpful for moving around"""

    def move_toward_destructively(self, target_position):
        try:
            self.move_toward(target_position)
        except lua_errors.TurtleBlockedError as e:
            self.dig_towards(e.direction)

    def move_toward(self, target_position):
        """Make a move in one of these directions, turning automatically"""
        map = self.state.map.read()

    def turn_toward(self, x, y, z):
        """Turn toward whichever direction is non zero"""
        raise NotImplementedError()

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





    def explore_towards(self, target_position):
        """Moves toward the point regardless of any known points"""
        map = self.state.map.read()
        if (map.position == target_position).all():
            return
        dist = np.array(target_position) - map.position

        curr_x, curr_y, curr_z = map.position
        if dist[0] != 0:
            self.turn_toward([target_position[0], curr_y, curr_z])
            self.forward()
        elif dist[2] != 0:
            self.turn_toward([curr_x, curr_y, target_position[2]])
            self.forward()
        elif dist[1] != 0:
            assert sign(dist[1]) != 0
            self.move_vertically(sign(dist[1]))
        else:
            raise RuntimeError("How was there no move??")

    def turn_toward(self, target_position):
        """Turn toward the target_position
        """
        map = self.state.map.read()
        x_dist, _, z_dist = target_position.copy() - map.position
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
