import json

import numpy as np
from cc import fs

from fleet.serializable import BaseSerializable

STATE_FILE = "state_file.json"


class StateNotAcquiredError(Exception):
    """Raised when an action is performed that requires the statefile"""


class StateAttr:
    def __init__(self, state_file: 'StateFile', key_name, default):
        self.key_name = key_name
        self.default = default
        self.state_file = state_file

    def read(self):
        if self.state_file.dict is None:
            raise StateNotAcquiredError(
                "You must run this action within a statefile context manager!")
        value = self.state_file.dict[self.key_name]
        if isinstance(self.default, np.ndarray):
            value = np.array(value)
        elif isinstance(self.default, BaseSerializable):
            value = type(self.default).from_dict(value)
        return value

    def write(self, value):
        if self.state_file.dict is None:
            raise StateNotAcquiredError(
                "You must run this action within a statefile context manager!")
        assert isinstance(value, type(self.default))

        if isinstance(value, np.ndarray):
            value = value.tolist()
        elif isinstance(value, BaseSerializable):
            value = value.to_dict()
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
        if self.dict is None:
            # Only refresh state if no one is currently 'holding' state
            self.dict = self.read_dict()

        # Keep track of state holders
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
        with fs.open(STATE_FILE, "w") as file:
            file.write(as_json)

    def _create_state_if_nonexistent(self):
        if fs.exists(STATE_FILE):
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
