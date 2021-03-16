from computercraft.errors import LuaException
from fleet import NavigationTurtle, Direction

FUEL_SLOT = 1


def maybe_refuel(nav_turtle: NavigationTurtle, refuel_spot):
    """Top off fuel if necessary. This function roughly predicts the distance to
    refuel and decides if it's necessary to refuel"""

    if turtle.getFuelLevel() < turtle.getFuelLimit() * 0.5:
        # Whether we are consuming fuel or getting it from a chest, we always
        # want to do so from the fuel slot
        nav_turtle.select(FUEL_SLOT)

        if nav_turtle.inventory.selected_slot.count > 1:
            nav_turtle.refuel(1)

        # Go grab fuel
        nav_turtle.move_toward(to_pos=refuel_spot)
        nav_turtle.suck_in_direction(Direction.down)
