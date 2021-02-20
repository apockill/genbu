from typing import Dict, Any

from computercraft.errors import LuaException


class TurtleBlockedError(LuaException):
    """Called when the turtles path is blocked"""


ERROR_MAPPINGS: Dict[str, Any] = {
    "Movement obstructed": TurtleBlockedError
}
"""Map LuaErrors to this libraries errors. These are mapped based on the 
messages in the LuaError, hence the key to the dict is a string representing 
the LuaError.message
"""


def raise_mapped_error(exc: LuaException, message=None):
    if exc.message in ERROR_MAPPINGS:
        message = message if message else exc.message
        raise ERROR_MAPPINGS[exc.message](message)
    else:
        raise exc


__all__ = ["ERROR_MAPPINGS",
           "TurtleBlockedError"]
