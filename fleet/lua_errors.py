from typing import Dict, Any, TYPE_CHECKING, Callable

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


class BlockNotPlaceableError(LuaException):
    """This can occur if the space is already taken by another block"""


class NoItemsToPlaceError(LuaException):
    """Occurs if the turtle is trying to place an item but there's nothing on
    the slot that is selected"""


class NoItemToDigError(LuaException):
    """When you dig in a direction where there is nothing"""


FROM_LUA: Dict[str, Any] = {
    "Movement obstructed": TurtleBlockedError,
    "Unbreakable block detected": UnbreakableBlockError,
    "Out of fuel": OutOfFuelError,
    "Items not combustible": ItemNotCombustibleError,
    "No items to combust": NoItemsToCombustError,
    "Cannot place block here": BlockNotPlaceableError,
    "No items to place": NoItemsToPlaceError,
    "Nothing to dig here": NoItemToDigError,
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


def run(fn: Callable, *args, **kwargs):
    """Try a function and convert any LuaExceptions"""
    try:
        return fn(*args, **kwargs)
    except LuaException as e:
        raise map_error(e, message=e.message)


__all__ = ["FROM_LUA",
           "TO_LUA",
           "TurtleBlockedError"]
