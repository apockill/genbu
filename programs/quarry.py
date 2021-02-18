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

    def move_relative(self, x, y, z):
        """Make a move in one of these directions, turning automatically"""
        raise NotImplementedError()

    def turn_toward(self, x, y, z):
        """Turn toward whichever direction is non zero"""
        raise NotImplementedError()


# quarry.py
class QuarryTurtle(NavigationMixin):
    def run(self):
        with self.state:
            self.forward()
            self.turn_right()

            for i in range(4):
                self.forward()
                self.turn_right()
                self.forward()

            self.turn_left()
            self.backward()


QuarryTurtle().run()
