from cc import turtle

from fleet.navigation_turtle import NavigationTurtle, Direction, lua_errors


def dump_if_full(nav_turtle: NavigationTurtle, dump_spot, dump_slots,
                 trigger_slot=16):
    """Goes to a dump location if the 16th slot has an item in it, and dumps
    whatever slots are configured to be dumped
    :param nav_turtle: The turtle object
    :param dump_spot: A coordinate directly above a chest
    :param dump_slots: What slots to dump
    :param trigger_slot: If this slot has an item, then the turtle will dump.
    """
    # Try to get the item count without making any API calls
    item_count_at_least = nav_turtle.inventory.slot(trigger_slot).count
    if (nav_turtle.inventory.slot(trigger_slot).confirmed or
            item_count_at_least > 0):
        trigger_slot_item_count = item_count_at_least
    else:
        # Make the API call if necessary
        trigger_slot_item_count = lua_errors.run(turtle.getItemCount,
                                                 trigger_slot)

    if trigger_slot_item_count > 0:
        nav_turtle.move_toward(to_pos=dump_spot)
        for slot_id in dump_slots:
            item_count = lua_errors.run(turtle.getItemCount, slot_id)
            nav_turtle.select(slot_id)
            # Don't end the step here so in one fell swoop all slots can be
            # cleared. Otherwise we'd have to keep state as to which slot has
            # been cleared thus far.
            nav_turtle.drop_in_direction(Direction.down, item_count,
                                         end_step=False)

        # Always default to selecting 1, because any 'suck' or 'dig' operation
        # after this will go right into the trigger slot
        nav_turtle.select(1)
