import numpy as np

from fleet import (
    routines,
    Astar3D,
    StatefulTurtle,
    TurtleBlockedError,
    StateAttr)
from fleet.math_utils import sign, angle_between

    def _move_in_direction(self, move_sign: int):
        """Move forwards or backwards in the sign of direction"""
        position = self.state.position.read()
        direction = self.state.direction.read()
        new_position = np.array([
            round(move_sign * cos(radians(direction))) + position[0],
            position[1],
            round(move_sign * sin(radians(direction))) + position[2]
        ])

        with self.state:
            if move_sign == 1:
                turtle.forward()
            elif move_sign == -1:
                turtle.back()
            else:
                raise ValueError(f"Invalid value for move_sign! {move_sign}")
            self.state.position.write(new_position)

    def forward(self):
        # new_position = self.state.position.read() + self.state.direction.read()
        self._move_in_direction(1)

    def backward(self):
        self._move_in_direction(-1)

    def turn_right(self):
        self._turn(90)

    def turn_left(self):
        self._turn(-90)


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
