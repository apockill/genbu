from typing import Dict, Any, TYPE_CHECKING

from computercraft.errors import LuaException

if TYPE_CHECKING:
    from fleet import Direction


class TurtleBlockedError(LuaException):
    """Raised when the turtles path is blocked"""

    def __init__(self, message, direction: 'Direction'):
        super().__init__(message)
        self.direction = direction
        """The direction of the blocking block"""


class UnbreakableBlockError(LuaException):
    """Called when the turtle tries to mine a block it can't break"""

    def __init__(self, message, direction: 'Direction'):
        super().__init__(message)
        self.direction = direction
        """The direction of the unbreakable block"""


FROM_LUA: Dict[str, Any] = {
    "Movement obstructed": TurtleBlockedError,
    "Unbreakable block detected": UnbreakableBlockError
}
"""Map LuaErrors to this libraries errors. These are mapped based on the 
messages in the LuaError, hence the key to the dict is a string representing 
the LuaError.message
"""

TO_LUA: Dict[Any, str] = {value: key for key, value in FROM_LUA.items()}
"""Useful for generating LuaExceptions in tests"""


def raise_mapped_error(exc: LuaException, message=None, **kwargs):
    if exc.message in FROM_LUA:
        message = message if message else exc.message
        raise FROM_LUA[exc.message](message, **kwargs)
    else:
        raise exc


__all__ = ["FROM_LUA",
           "TO_LUA",
           "TurtleBlockedError"]
