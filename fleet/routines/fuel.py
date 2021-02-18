from cc import turtle
from computercraft.errors import LuaException


def refuel():
    """Top off fuel if necessary"""
    while turtle.getFuelLevel() < 300:
        # Pick the most preferred fuel
        fuel_slots = scan_for_fuel()
        if len(fuel_slots):
            turtle.select(fuel_slots[0])
            turtle.refuel(1)
        else:
            print("No fuel found!")


def scan_for_fuel():
    """Only consume the highest-fuel slot"""
    preference = []
    """List of item slots -> preference. Coal is preferred"""

    for i in range(1, 17):
        if turtle.getItemCount(i) == 0:
            continue

        name = turtle.getItemDetail(i)[b"name"]
        whitelisted_fuels = [
            b"minecraft:coal_block",
            b"minecraft:charcoal_block",
            b"minecraft:coal",
            b"minecraft:charcoal",
        ]
        is_whitelisted = name in whitelisted_fuels

        if is_whitelisted:
            preference.append((i, 1))
            continue

        turtle.select(i)
        try:
            turtle.refuel(0)
            preference.append((i, 0))
            continue
        except LuaException as e:
            if e.message == "Items not combustible":
                # Try the next slot
                continue
            raise

    preference.sort(key=lambda i: i[1], reverse=True)
    return [p[0] for p in preference]
