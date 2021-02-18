from enum import Enum, auto
from typing import Tuple
from math import cos, sin, radians

import numpy as np

from cc import turtle, os, gps
from computercraft.errors import LuaException
from fleet import StateFile, StateAttr, Map, math_utils


class StepFinished(Exception):
    """Called whenever a movement is performed with the robot"""


class TurtleBlockedError(LuaException):
    """Called when the turtles path is blocked"""

    def __init__(self, *args, direction: 'Direction'):
        super().__init__(*args)
        self.direction = direction


class StateRecoveryError(Exception):
    """This exception occurs on turtle startup if it's determined that the
    state file was corrupted, or if it's unable to determine the veracity of
    the state file."""


class Direction(Enum):
    up = auto()
    down = auto()
    front = auto()
    back = auto()
    left = auto()
    right = auto()


class TurtleBlockedError(LuaException):
    """Called when the turtles path is blocked"""

    def __init__(self, *args, direction: Direction):
        super().__init__(*args)
        self.direction = direction


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
        """Representing (x, y, z) positions"""
        """Direction on the XZ plane in degrees. A value between 0-360 """
        self.state.map = StateAttr(self.state, "map",
                                   Map(position=np.array((0, 0, 0)),
                                       direction=0))

    def run(self):
        while True:
            with self.state:
                try:
                    self.step()
                    os.sleep(0.1)
                except StepFinished:
                    print(f"Finished step! {self.state}")
                except TurtleBlockedError:
                    print("Turtle is blocked!")

    def turn_degrees(self, degrees: int):
        """Turn `degrees` amount. The direction is determined by the sign.
        Only 90, 0, or -90 is allowed. 0 performs nothing
        """
        if degrees == 0:
            return
        if degrees not in (90, -90):
            raise ValueError(f"Invalid value for degrees! {degrees}")
        map = self.state.map.read()
        map.direction = (map.direction + degrees) % 360

        with self.state:
            if degrees == 90:
                turtle.turnRight()
            elif degrees == -90:
                turtle.turnLeft()
            self.state.map.write(map)
        raise StepFinished()

    def move_in_direction(self, move_sign: int):
        """Move forwards or backwards in the sign of direction"""
        if move_sign not in (1, -1):
            raise ValueError(f"Invalid value for move_sign: {move_sign}")

        map = self.state.map.read()
        new_position = np.array([
            round(move_sign * cos(radians(map.direction))) + map.position[0],
            map.position[1],
            round(move_sign * sin(radians(map.direction))) + map.position[2]
        ])
        map.set_position(new_position)

        with self.state:
            try:
                if move_sign == 1:
                    direction = Direction.front
                    turtle.forward()
                elif move_sign == -1:
                    direction = Direction.back
                    turtle.back()
            except LuaException as e:
                if e.message == "Movement obstructed":
                    raise TurtleBlockedError(
                        f"Blocked when moving in direction {move_sign}",
                        direction=direction)
                raise
            self.state.map.write(map)
        raise StepFinished()

    def move_vertically(self, move_sign: int):
        if move_sign not in (1, -1):
            raise ValueError(f"Invalid value for move_sign: {move_sign}")

        map = self.state.map.read()
        new_position = np.array([
            map.position[0],
            map.position[1] + move_sign,
            map.position[2]
        ])
        map.set_position(new_position)
        with self.state:
            try:
                if move_sign == 1:
                    direction = Direction.up
                    turtle.up()
                elif move_sign == -1:
                    direction = Direction.down
                    turtle.down()
            except LuaException as e:
                if e.message == "Movement obstructed":
                    raise TurtleBlockedError(
                        f"Blocked when moving in direction {move_sign}",
                        direction=direction)
                raise
            self.state.map.write(map)
        raise StepFinished()

    def dig_towards(self, dir: Direction):
        """Try digging towards a direction"""
        if dir is Direction.up:
            turtle.digUp()
        elif dir is Direction.down:
            turtle.digDown()
        elif dir is Direction.front:
            turtle.dig()
        elif dir in [Direction.back, Direction.left, Direction.right]:
            raise NotImplementedError("Have yet to add/test this feature!")
        raise StepFinished()

    def up(self):
        self.move_vertically(1)

    def down(self):
        self.move_vertically(-1)

    def forward(self):
        self.move_in_direction(1)

    def backward(self):
        self.move_in_direction(-1)

    def turn_right(self):
        self.turn_degrees(90)

    def turn_left(self):
        self.turn_degrees(-90)
