from cc import turtle

from computercraft.errors import LuaException
from fleet import math_utils, NavigationTurtle, lua_errors, StepFinished

FUEL_SLOT = 1


def maybe_refuel(nav_turtle: NavigationTurtle, refuel_spot):
    """Top off fuel if necessary. This function roughly predicts the distance to
    refuel and decides if it's necessary to refuel"""

    if turtle.getFuelLevel() < turtle.getFuelLimit() * 0.5:
        # Whether we are consuming fuel or getting it from a chest, we always
        # want to do so from the fuel slot
        turtle.select(FUEL_SLOT)

        # Try to consume fuel
        if turtle.getItemCount(FUEL_SLOT) > 1:
            try:
                lua_errors.run(turtle.refuel, 1)
                raise StepFinished
            except lua_errors.ItemNotCombustibleError as e:
                print("OH NO!", e)

        # Go grab fuel
        nav_turtle.move_toward(to_pos=refuel_spot)
        turtle.suckDown()
