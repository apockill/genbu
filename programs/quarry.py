import json

import numpy as np

from cc import fs, turtle

# state.py
STATE_FILE = "state_file.json"


class StateAttr:
    def __init__(self, state_file: 'StateFile', key_name, default):
        self.key_name = key_name
        self.default = default
        self.state_file = state_file

    def read(self):
        print("Finna read")
        value = self.state_file.dict[self.key_name]
        if isinstance(self.default, np.ndarray):
            value = np.array(value)

        return value

    def write(self, value):
        print("Finna write", value)
        if isinstance(value, np.ndarray):
            value = value.tolist()
        self.state_file.dict[self.key_name] = value


class StateFile:
    """Read and write to the state file in as-safe a way as possible"""

    def __init__(self):
        self.dict = None
        """When being held, this shows all the key/value pairs of state"""
        self.being_held = 0
        """When this hits 0 on __exit__, all things are saved to the file"""

    def __enter__(self):
        """Enter a context where you might edit the dictionary, but
        upon exit you will want to save all values at once"""
        self.dict = self.read_dict()
        self.being_held += 1

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.write_dict(self.dict)
        self.being_held -= 1
        assert self.being_held >= 0

        if self.being_held == 0:
            self.dict = None

    def read_dict(self):
        self._create_state_if_nonexistent()
        with fs.open(STATE_FILE, "r") as file:
            text = file.readAll()
        return json.loads(text)

    def write_dict(self, state_dict):
        as_json = json.dumps(state_dict, indent=4)
        print("Writing as json!")
        with fs.open(STATE_FILE, "w") as file:
            file.write(as_json)

    def _create_state_if_nonexistent(self):
        if fs.exists(STATE_FILE):
            print("State file already exists!")
            return

        # Get all the defaults by temporarily creating self.dict, writing down
        # all the defaults, writing that to the state file, then setting it
        # back to None for safety.
        self.dict = {}
        for _, attr in self.__dict__.items():
            if isinstance(attr, StateAttr):
                attr.write(attr.default)
        self.write_dict(self.dict)
        self.dict = None


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
