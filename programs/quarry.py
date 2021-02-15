import json

import numpy as np

from cc import fs, turtle

from fleet import StateFile, StateAttr

# stateful_turtle.py
from math import cos, sin, radians


class StatefulTurtle:
    """Defines a way of working with turtles where every move is tracked,
    so that the program could crash at any moment and be brought back.
    Chunk unloading or logging off should be okay with a StatefulTurtle

    Vertical: Y+

    Direction when starting: (1, 0, 0)
    X+
    |
    |
    ^___________ Z+

    Position when starting: (0, 0, 0)
    """

    def __init__(self):
        self.state = StateFile()
        self.state.position = StateAttr(self.state, "position",
                                        np.array((0, 0, 0)))
        """Representing (x, y, z) positions"""
        self.state.direction = StateAttr(self.state, "direction", 0)
        """Direction on the XZ plane in degrees. A value between 0-360 """

    def run(self):
        print("Running!")
        with self.state:
            print("Got state file!")

    def _turn(self, degrees: int):
        """Turn `degrees` amount. The direction is determined by the sign.
        Only 90 or -90 is allowed
        """
        direction = self.state.direction.read()
        new_direction = (direction + degrees) % 360
        with self.state:
            if degrees == 90:
                turtle.turnRight()
            elif degrees == -90:
                turtle.turnLeft()
            else:
                raise ValueError(f"Invalid value for degrees! {degrees}")
            self.state.direction.write(new_direction)

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
