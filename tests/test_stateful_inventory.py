import pytest
import mock
import cc

import fleet
from fleet import StatefulTurtle, Inventory, Direction, StepFinished


class MockedInventory:
    def __init__(self, item_detail_ret=None,
                 item_count_ret=None):
        self._getItemDetail = mock.patch.object(cc.turtle, "getItemDetail")
        self._getItemCount = mock.patch.object(cc.turtle, "getItemCount")
        self._select = mock.patch.object(cc.turtle, "select")

        self._item_detail_ret = item_detail_ret or {b"name": b"cool:block"}
        self._item_count_ret = item_count_ret or 0

    def __enter__(self):
        self.getItemDetail = self._getItemDetail.__enter__()
        self.getItemCount = self._getItemCount.__enter__()
        self.select = self._select.__enter__()

        self.getItemDetail.return_value = self._item_detail_ret
        self.getItemCount.return_value = self._item_count_ret
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.getItemDetail.__exit__()
        self.getItemCount.__exit__()
        self.select.__exit__()


def test_turtle_refreshes_on_startup():
    with MockedInventory(item_detail_ret={b"name": b"cool:block"},
                         item_count_ret=10) as inv_funcs:
        assert inv_funcs.getItemDetail.call_count == 0
        assert inv_funcs.getItemCount.call_count == 0
        assert inv_funcs.select.call_count == 0

        turtle = StatefulTurtle()

        assert inv_funcs.getItemDetail.call_count == 16
        assert inv_funcs.getItemCount.call_count == 16
        assert inv_funcs.select.call_count == 1

        # Verify from_turtle respects "selected_slot" setting
        Inventory.from_turtle(selected_slot=13)
        assert inv_funcs.select.call_count == 2
        assert inv_funcs.select.call_args[0] == (13,)

        # Make sure the slots were created correctly, and the name was converted
        # from bytes to string
        for slot_id, slot in zip(range(1, 17), turtle.inventory):
            assert slot.count == 10
            assert slot.name == "cool:block"
            assert slot.confirmed
            assert slot.slot_id == slot_id


def test_select():
    with MockedInventory() as mocks:
        turtle = StatefulTurtle()
        assert turtle.inventory.selected_id == 1
        assert turtle.inventory.selected.slot_id == 1
        assert mocks.select.call_count == 1

        turtle.select(15)
        assert turtle.inventory.selected_id == 15
        assert turtle.inventory.selected.slot_id == 15
        assert mocks.select.call_count == 2
        assert mocks.select.call_args[0] == (15,)
        assert turtle.inventory.selected is turtle.inventory._slots[15]


@pytest.mark.parametrize(
    argnames=("fn_name", "raises", "args",),
    argvalues=(
            # Arbitrary tests for each function type
            ("place_in_direction", StepFinished, (Direction.up,)),
            ("place_in_direction", StepFinished, (Direction.down,)),
            ("place_in_direction", StepFinished, (Direction.front,)),
            ("drop_in_direction", StepFinished, (Direction.up, 10)),
            ("drop_in_direction", StepFinished, (Direction.down, 100)),
            ("drop_in_direction", StepFinished, (Direction.front, 59)),
            ("drop_in_direction", StepFinished, (Direction.front, 59)),

            ("refuel", StepFinished, (420,)),
            ("refuel", StepFinished, (50,))
    )
)
def test_placing_dropping_and_refueling(fn_name, raises, args):
    """Placing, dropping, sucking, and refueling methods have one thing in
    common: They all act only on the selected slot of the turtle.

    Unlike dig(), they cannot modify the count on any slot that is not selected.

    For that reason, it's api cost-effective to fully refresh the single slot
    after each of these actions.

    This test ensures that slot.reresh() is called appropriately,
    and only on the selected slot.
    """
    turtle = StatefulTurtle()
    turtle.select(3)
    turtle.inventory.selected.confirmed = False
    turtle.inventory.selected.count = 51

    with MockedInventory(item_count_ret=50) as mock_inventory:
        # Place in a direction
        if raises is not None:
            with pytest.raises(raises):
                turtle.__getattribute__(fn_name)(*args)
        else:
            turtle.__getattribute__(fn_name)(*args)

        # Ensure select was not called (it's not necessary to be called!)
        assert mock_inventory.select.call_count == 0
        # Verify slot.refresh() was called
        assert mock_inventory.getItemCount.call_count == 1
        assert mock_inventory.getItemDetail.call_count == 1
        # Verify the slot was confirmed, and the count was changed
        assert turtle.inventory.selected.count == 50
        assert turtle.inventory.selected.confirmed


@pytest.mark.parametrize(
    argnames=("fn_name", "raises", "args"),
    argvalues=(
            ("suck_in_direction", StepFinished, (Direction.up, 1)),
            ("suck_in_direction", StepFinished, (Direction.down, 5)),
            ("suck_in_direction", StepFinished, (Direction.front, 10)),
            ("dig_in_direction", StepFinished, (Direction.up,)),
            ("dig_in_direction", StepFinished, (Direction.down,)),
            ("dig_in_direction", StepFinished, (Direction.front,)),
    )
)
def test_sucking_digging(fn_name, raises, args):
    """suck*() and dig*() methods should exibit the same problem for inventory:
    They can both place blocks anywhere in the inventory, depending on whether
    a block already existed.

    To save API calls, we do not refresh on all slots, but rather, mark all
    slots as 'unconfirmed', and if an action is needed to confirm them, then
    refresh can be called selectively.
    """
    turtle = StatefulTurtle()

    # Set up some complicated state on the turtle, with a mix of most things
    for slot in turtle.inventory:
        slot.count = slot.slot_id * 2
        slot.confirmed = slot.slot_id % 2 == 0
        slot.name = "cool:block"

    with MockedInventory(item_count_ret=35) as mock_inventory:
        # Place in a direction
        with pytest.raises(raises):
            turtle.__getattribute__(fn_name)(*args)

        # Ensure that no inventory API calls were made, since dig*() should be
        # as fast as possible, and because it would take 16 api calls to truly
        # understand the state of inventory after a dig or suck call
        assert mock_inventory.select.call_count == 0
        assert mock_inventory.getItemCount.call_count == 0
        assert mock_inventory.getItemDetail.call_count == 0

        # Verify that none of the slots changed in nature, except they were
        # all marked as unconfirmed, but that it WAS marked as
        for slot in turtle.inventory:
            # This 'confirmed'' have been set to False
            assert not slot.confirmed

            # This should not have changed
            assert slot.count == slot.slot_id * 2
            assert slot.name == "cool:block"
