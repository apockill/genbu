from typing import Dict, Any, TYPE_CHECKING

from computercraft.errors import LuaException

if TYPE_CHECKING:
    from fleet import Direction


class TurtleBlockedError(LuaException):
    """Raised when the turtles path is blocked"""

    def __init__(self, message, direction: 'Direction' = None):
        super().__init__(message)
        self.direction = direction
        """The direction of the blocking block"""


class UnbreakableBlockError(LuaException):
    """Raised when the turtle tries to mine a block it can't break"""

    def __init__(self, message, direction: 'Direction' = None):
        super().__init__(message)
        self.direction = direction
        """The direction of the unbreakable block"""


class OutOfFuelError(LuaException):
    """Raised when the turtle tries to move but is out of fuel"""


class ItemNotCombustibleError(LuaException):
    """Raised when turtle.refuel() is called on an item that isn't combustible"""


class NoItemsToCombustError(LuaException):
    """Raised when turtle.refuel() is called on an empty slot"""


FROM_LUA: Dict[str, Any] = {
    "Movement obstructed": TurtleBlockedError,
    "Unbreakable block detected": UnbreakableBlockError,
    "Out of fuel": OutOfFuelError,
    "Items not combustible": ItemNotCombustibleError,
    "No items to combust": NoItemsToCombustError,
}
"""Map LuaErrors to this libraries errors. These are mapped based on the 
messages in the LuaError, hence the key to the dict is a string representing 
the LuaError.message
"""

TO_LUA: Dict[Any, str] = {value: key for key, value in FROM_LUA.items()}
"""Useful for generating LuaExceptions in tests"""


def map_error(exc: LuaException, message=None, **kwargs):
    if exc.message in FROM_LUA:
        message = message if message else exc.message
        return FROM_LUA[exc.message](message, **kwargs)
    else:
        return exc


def run(fn, *args, **kwargs):
    """Try a function and convert any LuaExceptions"""
    try:
        fn(*args, **kwargs)
    except LuaException as e:
        raise map_error(e, message=e.message)


__all__ = ["FROM_LUA",
           "TO_LUA",
           "TurtleBlockedError"]
