from enum import Enum, auto
from typing import Tuple
from math import cos, sin, radians

import numpy as np

from cc import turtle, os, gps
from computercraft.errors import LuaException
from fleet import StateFile, StateAttr, Map, math_utils, lua_errors


class StepFinished(Exception):
    """Called whenever a movement is performed with the robot"""


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


class StatefulTurtle:
    """Defines a way of working with turtles where every move is tracked,
    so that the program could crash at any moment and be brought back.
    Chunk unloading or logging off should be okay with a StatefulTurtle

    Vertical: Y+
    Position:
        The turtle will determine its position using GPS upon every start. If
        GPS is not available, a StateRecoveryError will be raised.
    Direction:
        When starting, direction defaults to 0 degrees, but upon the first
        movement the turtle will verify it's true direction, record that to the
        statefile, and move appropriately to correct any bad assumptions.

          0 degrees: towards +X
         90 degrees: towards +Z
        180 degrees: towards -X
        270 degrees: towards -Z
    X+
    |
    |
    |___________ Z+



    """

    def __init__(self):
        # First, ensure state is retrieved via GPS initially
        gps_loc = gps.locate()
        if gps_loc is None:
            raise StateRecoveryError(
                "The turtle must have a wireless modem and be "
                "within range of GPS sattellites!")

        self.state = StateFile()
        """Representing (x, y, z) positions"""
        """Direction on the XZ plane in degrees. A value between 0-360 """
        self.state.map = StateAttr(self.state, "map",
                                   Map(position=gps_loc,
                                       direction=0))
        self.direction_verified = False
        """This is set to True if the Turtle ever moves and is able to verify 
        that the angle it thinks is pointing is actually the angle it is 
        pointing. It uses GPS to verify two points before and after a move to 
        do this. """

        self._maybe_recover_location(gps_loc)

    def _maybe_recover_location(self, gps_loc: Tuple[int, int, int]):
        """Validate state based on GPS data"""
        with self.state:
            # Check if any crash recovery needs to be done here
            map = self.state.map.read()
            last_known_location = map.position
            if (last_known_location != gps_loc).any():

                print("Warning! State file is out of sync!")
                if not math_utils.is_adjacent(last_known_location, gps_loc):
                    msg = ("The statefile is out of sync! GPS reports a pos of "
                           f"{gps_loc} but state pos is {last_known_location}")
                    raise StateRecoveryError(msg)
                map.move_to(gps_loc)
                self.state.map.write(map)

    def run(self):
        while True:
            with self.state:
                try:
                    self.step()
                    os.sleep(0.1)
                except StepFinished:
                    pass
                except lua_errors.TurtleBlockedError:
                    print("Turtle is Blocked!")

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
        old_position = map.position
        new_position = np.array([
            round(move_sign * cos(radians(map.direction))) + map.position[0],
            map.position[1],
            round(move_sign * sin(radians(map.direction))) + map.position[2]
        ])

        with self.state:
            try:
                if move_sign == 1:
                    direction = Direction.front
                    turtle.forward()
                elif move_sign == -1:
                    direction = Direction.back
                    turtle.back()
            except LuaException as e:
                lua_errors.raise_mapped_error(
                    e, f"Blocked when moving in direction {direction}",
                    direction=direction)
            if not self.direction_verified:
                gps_position = gps.locate()
                # If the move_sign is negative, flip the order of to/from
                # to represent a move backwards
                to_from = (old_position, gps_position)[::move_sign]
                verified_direction = math_utils.get_direction(*to_from)
                new_position = gps_position
                map.direction = verified_direction

                # Flag the turtle as super verified and ready to roll
                self.direction_verified = True

            map.move_to(new_position)
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
        map.move_to(new_position)
        with self.state:
            try:
                if move_sign == 1:
                    direction = Direction.up
                    turtle.up()
                elif move_sign == -1:
                    direction = Direction.down
                    turtle.down()
            except LuaException as e:
                lua_errors.raise_mapped_error(
                    e, f"Blocked when moving in direction {direction}",
                    direction=direction)

            self.state.map.write(map)
        raise StepFinished()

    def dig_towards(self, dir: Direction):
        """Try digging towards a direction"""
        try:
            if dir is Direction.up:
                turtle.digUp()
            elif dir is Direction.down:
                turtle.digDown()
            elif dir is Direction.front:
                turtle.dig()
            elif dir in [Direction.back, Direction.left, Direction.right]:
                raise ValueError("Have yet to add/test this feature!")
        except LuaException as e:
            lua_errors.raise_mapped_error(
                e, f"Tried to break unbreakable block in direction {dir}",
                direction=dir)
        raise StepFinished()

    def dig_up(self):
        self.dig_towards(Direction.up)

    def dig_down(self):
        self.dig_towards(Direction.down)

    def dig_front(self):
        self.dig_towards(Direction.front)

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
