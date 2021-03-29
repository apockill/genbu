from cc import turtle

from fleet import NavigationTurtle, Direction, lua_errors

FUEL_SLOT = 1
TURTLE_FUEL_LIMIT = 100000


def maybe_refuel(nav_turtle: NavigationTurtle, refuel_spot, destructive=False):
    """Top off fuel if necessary. This function roughly predicts the distance to
    refuel and decides if it's necessary to refuel"""
    fuel_level = lua_errors.run(turtle.getFuelLevel)

    if fuel_level < TURTLE_FUEL_LIMIT * 0.5:
        # Whether we are consuming fuel or getting it from a chest, we always
        # want to do so from the fuel slot
        nav_turtle.select(FUEL_SLOT)

        if nav_turtle.inventory.selected.count > 1:
            nav_turtle.refuel(1)

        # Go grab fuel
        nav_turtle.move_toward(to_pos=refuel_spot, destructive=destructive)
        nav_turtle.suck_in_direction(Direction.down, end_step=False)
        nav_turtle.inventory.slot(FUEL_SLOT).refresh()
