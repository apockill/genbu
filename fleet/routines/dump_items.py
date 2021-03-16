from cc import turtle

from fleet.navigation_turtle import NavigationTurtle, Direction


def dump_if_full(nav_turtle: NavigationTurtle, dump_spot, dump_slots):
    """Goes to a dump location if the 16th slot has an item in it, and dumps
    whatever slots are configured to be dumped
    :param nav_turtle: The turtle object
    :param dump_spot: A coordinate directly above a chest
    :param dump_slots: What slots to dump
    """
    if turtle.getItemCount(16) > 0:
        nav_turtle.move_toward(to_pos=dump_spot)
        for slot_id in dump_slots:
            item_count = turtle.getItemCount(slot_id)
            nav_turtle.select(slot_id)
            nav_turtle.drop_in_direction(Direction.down, item_count)
