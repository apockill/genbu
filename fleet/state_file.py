import json
import copy
from pathlib import Path
from typing import Any, Callable

from atomicwrites import atomic_write
import numpy as np
from cc import fs, os

from fleet.serializable import BaseSerializable
from fleet import lua_errors

STATE_FILE = "state_file.json"
STATE_DIR = Path(".statefiles")


class StateNotAcquiredError(Exception):
    """Raised when an action is performed that requires the statefile"""


class StateAttr:
    def __init__(self, state_file: 'StateFile',
                 key_name: str,
                 default: Any):
        self.key_name = key_name
        self.default = default
        self.state_file = state_file

    def read(self):
        if self.state_file.being_held == 0:
            raise StateNotAcquiredError(
                "You must run this action within a statefile context manager!")

        if self.key_name not in self.state_file.dict:
            """This must be a new addition"""
            return self.default
        else:
            value = self.state_file.dict[self.key_name]

        if isinstance(self.default, BaseSerializable):
            value = type(self.default).from_dict(value)
        elif isinstance(self.default, np.ndarray):
            value = np.array(value)

        return value

    def write(self, value):
        if self.state_file.being_held == 0:
            raise StateNotAcquiredError(
                "You must run this action within a statefile context manager!")
        assert isinstance(value, type(self.default))

        if isinstance(value, np.ndarray):
            value = value.tolist()
        elif isinstance(value, BaseSerializable):
            value = value.to_dict()

        self.state_file.dict[self.key_name] = value


class PromptStateAttr(StateAttr):
    """This is a StateAttr but the default is pulled by the user if the state
    file doesn't exist or have that value yet"""

    def __init__(
            self, state_file: 'StateFile',
            key_name: str,
            parser: Callable,
            default: Any,
    ):
        with state_file:
            if key_name not in state_file.dict:
                user_val = input(f"Enter {key_name}:\nDefault: {default}\n")
                user_val = parser(user_val) if user_val != "" else default
                assert isinstance(user_val, type(default))
                default = user_val

        super().__init__(state_file, key_name, default)


class StateFile:
    """Read and write to the state file in as-safe a way as possible"""

    def __init__(self, computer_id: int = None):
        self.dict = None
        """When being held, this shows all the key/value pairs of state"""

        self._last_saved_dict = None
        """Used to prevent saving to the StateFile when it's deemed unnecessary
        """

        self.being_held = 0
        """When this hits 0 on __exit__, all things are saved to the file"""

        computer_id = computer_id or lua_errors.run(os.getComputerID)
        self._state_path = STATE_DIR / str(computer_id) / STATE_FILE
        """The location to cache all the turtles states. The reason the 
        CC filesystem isn't used is because it's unreliable during program 
        startup and shutdown, leading to inconsistent states."""
        self._state_path.parent.mkdir(exist_ok=True, parents=True)

    def __repr__(self):
        return f"State({self.dict})"

    def __enter__(self):
        """Enter a context where you might edit the dictionary, but
        upon exit you will want to save all values at once"""

        if self.dict is None:
            # Only refresh state if no one is currently 'holding' state
            self.dict = self.read_dict()
            self._last_saved_dict = copy.deepcopy(self.dict)

        # Keep track of state holders
        self.being_held += 1
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):

        self.being_held -= 1
        assert self.being_held >= 0

        if self.being_held == 0:
            if self.dict != self._last_saved_dict:
                self.write_dict(self.dict)
                self._last_saved_dict = copy.deepcopy(self.dict)

    def __setattr__(self, key, value):
        super().__setattr__(key, value)
        if isinstance(value, StateAttr):
            with self:
                # If this key wasn't in the statefile before, write it
                if value.key_name not in self.dict:
                    value.write(value.default)

    def read_dict(self):
        self._create_state_if_nonexistent()

        with self._state_path.open("r") as file:
            text = file.read()
        return json.loads(text)

    def write_dict(self, state_dict):
        as_json = json.dumps(state_dict)
        with atomic_write(self._state_path, overwrite=True) as file:
            file.write(as_json)

    def _create_state_if_nonexistent(self):
        if self._state_path.is_file():
            return

        # Create a clean-slate statefile
        self.write_dict({})
