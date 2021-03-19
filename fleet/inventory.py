from typing import Dict, List, Optional

from dataclasses import dataclass

from cc import turtle


@dataclass
class InventorySlot:
    slot_id: int
    """The ID this slot represents, same as turtle.select(slot_id)"""

    count: int = 0
    """The number here represents the number the turtle thinks the slot contains
    It should be AT LEAST this amount, but the turtle does not check values of
    slots after `turtle.dig*()` commands have been called. 
    """

    confirmed: bool = False
    """If the count is guaranteed to be exact.
    This is set to False after `turtle.dig*() commands are called.
    """

    name: Optional[str] = None
    """The block name"""

    def refresh(self):
        """Refresh information for this slot"""

        block_info = turtle.getItemDetail(self.slot_id)
        self.name = (str(block_info[b"name"], encoding="ascii")
                     if block_info else None)
        self.count = turtle.getItemCount(self.slot_id)
        self.confirmed = True


class Inventory:
    def __init__(self,
                 slots: List[InventorySlot],
                 selected_slot: int):
        """
        :param slots: A list of inventory slots
        """
        self.selected_id = selected_slot
        self._slots: Dict[int, InventorySlot] = {
            slot.slot_id: slot for slot in slots}

    @property
    def selected(self) -> InventorySlot:
        return self._slots[self.selected_id]

    def slot(self, slot_id) -> InventorySlot:
        return self._slots[slot_id]

    @classmethod
    def from_turtle(cls, selected_slot) -> "Inventory":
        turtle.select(selected_slot)
        return cls(slots=cls.generate_slots(), selected_slot=selected_slot)

    @classmethod
    def generate_slots(cls):
        slots = []
        for slot_id in range(1, 17):
            slot = InventorySlot(slot_id=slot_id)
            slots.append(slot)
            # Initialize the slot with correct values
            slot.refresh()
        return slots

    def __iter__(self):
        """Iterate over turtle inventory slots"""
        for slot in self._slots.values():
            yield slot

    def __repr__(self):
        return f"Inventory(slots=f{list(self._slots.values())})"

    def mark_all_slots_unconfirmed(self):
        """This should be done after any digging or 'suck' operation, since the
        item could have gone anywhere in the inventory
        """
        for slot in self:
            slot.confirmed = False
