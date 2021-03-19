from typing import Tuple, Optional, Dict

from cc import turtle, os, gps

from fleet import StateFile, StateAttr, Map, math_utils, lua_errors, block_info, \
    Direction, Inventory


class StepFinished(Exception):
    """Called whenever a movement is performed with the robot"""


class StateRecoveryError(Exception):
    """This exception occurs on turtle startup if it's determined that the
    state file was corrupted, or if it's unable to determine the veracity of
    the state file."""


class MinedBlacklistedBlockError(Exception):
    """This exception is raised when a turtle tries to mine a blacklisted block
    """


class StatefulTurtle:
    """Defines a way of working with turtles where every move is tracked,
    so that the program could crash at any moment and be brought back.
    Chunk unloading or logging off should be okay with a StatefulTurtle

    Vertical: Y+
    Position:
        The turtle will determine its position using GPS upon every start. If
        GPS is not available, a StateRecoveryError will be raised.
    Direction:
        When starting, direction defaults to 0 degrees, but upon the first
        movement the turtle will verify it's true direction, record that to the
        statefile, and move appropriately to correct any bad assumptions.

          0 degrees: towards +X
         90 degrees: towards +Z
        180 degrees: towards -X
        270 degrees: towards -Z
    X+
    |
    |
    |___________ Z+



    """

    def __init__(self):
        # First, ensure state is retrieved via GPS initially
        gps_loc = gps.locate()
        if gps_loc is None:
            raise StateRecoveryError(
                "The turtle must have a wireless modem and be "
                "within range of GPS satellites!")

        self.state = StateFile()
        """Representing (x, y, z) positions"""
        """Direction on the XZ plane in degrees. A value between 0-360 """
        self.state.map = StateAttr(self.state, "map",
                                   Map(position=gps_loc,
                                       direction=0))
        self.direction_verified = False
        """This is set to True if the Turtle ever moves and is able to verify 
        that the angle it thinks is pointing is actually the angle it is 
        pointing. It uses GPS to verify two points before and after a move to 
        do this. """

        self.inventory = Inventory.from_turtle(selected_slot=1)
        """This will scan the entire inventory and record the contents, and 
        leave the turtle with selected_slot selected"""

        self._maybe_recover_location(gps_loc)

    def _maybe_recover_location(self, gps_loc: Tuple[int, int, int]):
        """Validate state based on GPS data"""
        with self.state as state:
            # Check if any crash recovery needs to be done here
            map = state.map.read()
            last_known_location = map.position
            if (last_known_location != gps_loc).any():
                print("Warning! State file is out of sync!")
                map.move_to(gps_loc)
                state.map.write(map)

    def run(self):
        print("Starting main loop!")

        while True:
            # Let other turtles have a chance
            os.sleep(0.1)
            try:
                with self.state as state:
                    self.step(state)
            except StepFinished:
                pass
            except lua_errors.TurtleBlockedError as e:
                print(f"Turtle is Blocked! Direction: {e.direction}")

    def step(self, state: StateFile):
        """This is the main logic of the turtle, to be implemented by a
        subclass."""
        raise NotImplementedError()

    def turn_degrees(self, degrees: int):
        """Turn `degrees` amount. The direction is determined by the sign.
        Only 90, 0, or -90 is allowed. 0 performs nothing
        """
        if degrees == 0:
            return
        if degrees not in (90, -90):
            raise ValueError(f"Invalid value for degrees! {degrees}")
        map = self.state.map.read()
        map.direction = (map.direction + degrees) % 360

        with self.state:
            if degrees == 90:
                turtle.turnRight()
            elif degrees == -90:
                turtle.turnLeft()
            self.state.map.write(map)
        raise StepFinished

    def move_in_direction(self, direction: Direction):
        """Move forwards or backwards in the sign of direction"""
        direction_mapping = {
            Direction.front: turtle.forward,
            Direction.back: turtle.back,
            Direction.up: turtle.up,
            Direction.down: turtle.down,
        }
        if direction not in direction_mapping:
            raise ValueError(f"You can't move in the direction: {direction}")

        map = self.state.map.read()
        old_position = map.position
        new_position = math_utils.coordinate_in_turtle_direction(
            curr_pos=map.position,
            curr_angle=map.direction,
            direction=direction
        )

        with self.state as state:

            try:
                lua_errors.run(direction_mapping[direction])
            except lua_errors.TurtleBlockedError as e:
                # TODO: Think of something smart to do when direction isn't
                #   verified but the turtle is still blocked!
                map.add_obstacle(new_position)
                state.map.write(map)
                e.direction = direction
                raise e

            horizontal_dirs = (Direction.front, Direction.back)
            if not self.direction_verified and direction in horizontal_dirs:
                gps_position = gps.locate()
                # If the move_sign is negative, flip the order of to/from
                # to represent a move backwards
                sign = 1 if direction is Direction.front else -1
                to_from = (old_position, gps_position)[::sign]
                verified_direction = math_utils.get_angle(*to_from)
                new_position = gps_position
                map.direction = verified_direction

                # Flag the turtle as super verified and ready to roll
                self.direction_verified = True

            map.move_to(new_position)
            state.map.write(map)
        raise StepFinished

    def dig_in_direction(self, direction: Direction):
        """Try digging towards a direction"""
        dig_mapping = {
            Direction.up: turtle.digUp,
            Direction.down: turtle.digDown,
            Direction.front: turtle.dig
        }

        if direction not in dig_mapping:
            raise ValueError(f"You can't dig in the direction: {direction}")

        # Inspect the block about to be dug to verify it's not blacklisted
        inspected_block_info = self.inspect_in_direction(direction)
        if inspected_block_info is None:
            # Nothing to dig!
            print("Digging towards empty air!")
            return

        block_name = inspected_block_info[b"name"].decode("utf-8")
        if block_info.name_matches_regexes(block_name, block_info.do_not_mine):
            msg = f"Tried to mine blacklisted block: {block_name}"
            raise MinedBlacklistedBlockError(msg)

        # Actually dig the block
        try:
            lua_errors.run(dig_mapping[direction])
        except lua_errors.UnbreakableBlockError as e:
            e.direction = direction
            raise e

        # Mark all slots as unconfirmed, since we don't know where that material
        # moved to
        self.inventory.mark_all_slots_unconfirmed()

        # Since the block was successfully removed, remove it as a potential
        # obstacle in the map.
        with self.state as state:
            map = state.map.read()
            obstacle_position = math_utils.coordinate_in_turtle_direction(
                curr_pos=map.position,
                curr_angle=map.direction,
                direction=direction
            )
            map.remove_obstacle(obstacle_position)
            state.map.write(map)

        raise StepFinished

    def inspect_in_direction(self, direction: Direction) \
            -> Optional[Dict[bytes, bytes]]:
        inspect_mapping = {
            Direction.up: turtle.inspectUp,
            Direction.down: turtle.inspectDown,
            Direction.front: turtle.inspect
        }

        if direction not in inspect_mapping:
            raise ValueError(f"You can't inspect in the direction: {direction}")

        return lua_errors.run(inspect_mapping[direction])

    def suck_in_direction(self, direction: Direction, amount=None, refresh=True):
        suck_mapping = {
            Direction.up: turtle.suckUp,
            Direction.down: turtle.suckDown,
            Direction.front: turtle.suck
        }

        if direction not in suck_mapping:
            raise ValueError(f"You can't suck in the direction: {direction}")

        lua_errors.run(suck_mapping[direction], amount)

        # Mark all slots as unconfirmed, since we don't know where that material
        # moved to
        self.inventory.mark_all_slots_unconfirmed()

    def drop_in_direction(self, direction: Direction, amount=None):
        drop_mapping = {
            Direction.up: turtle.dropUp,
            Direction.down: turtle.dropDown,
            Direction.front: turtle.drop
        }

        if direction not in drop_mapping:
            raise ValueError(f"You can't drop in the direction: {direction}")

        lua_errors.run(drop_mapping[direction], amount)

        # Now that items have been potentially dropped, update the inventory:
        self.inventory.selected.refresh()

        raise StepFinished

    def place_in_direction(self, direction: Direction):
        place_mapping = {
            Direction.up: turtle.placeUp,
            Direction.down: turtle.placeDown,
            Direction.front: turtle.place
        }
        if direction not in place_mapping:
            raise ValueError(f"You can't place in the direction: {direction}")

        lua_errors.run(place_mapping[direction])

        # Track the change in inventory, since no errors occurred
        self.inventory.selected.refresh()
        raise StepFinished

    def turn_right(self):
        self.turn_degrees(90)

    def turn_left(self):
        self.turn_degrees(-90)

    def select(self, slot_id):
        lua_errors.run(turtle.select, slot_id)
        self.inventory.selected_id = slot_id

    def refuel(self, fuel_amount):
        lua_errors.run(turtle.refuel, fuel_amount)
        self.inventory.selected.refresh()
