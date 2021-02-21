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
#








            for i in range(4):
                self.forward()
                self.turn_right()
                self.forward()

            self.turn_left()
            self.backward()


QuarryTurtle().run()
