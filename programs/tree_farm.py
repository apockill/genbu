from typing import List
from functools import partial
from time import time
from functools import lru_cache

import numpy as np
from cc import os

from fleet import (
    NavigationTurtle,
    StateFile,
    StateAttr,
    math_utils,
    block_info,
    Direction,
    routines,
    user_input,
    PromptStateAttr,
    StepFinished,
    lua_errors
)


class TreeFarmBot(NavigationTurtle):
    NODE_MIN_DISTANCE_TO_DIG = 1
    """The distance from which the turtle is allowed to dig near a node"""
    TREE_REGEXES = [
        ".*spruce.*",
        ".*log.*",
        ".*planks.*"
    ]

    DIRT_SLOT = 2
    SAPLING_SLOT = 3

    def __init__(self):
        super().__init__()
        with self.state:
            initial_loc = self.state.map.read().position

        # Get user input
        self.state.fuel_loc = PromptStateAttr(
            self.state, "fuel_loc",
            parser=user_input.parse_ndarray(3),
            default=initial_loc)
        self.state.sapling_loc = PromptStateAttr(
            self.state, "sapling_loc",
            parser=user_input.parse_ndarray(3),
            default=initial_loc)
        self.state.dirt_loc = PromptStateAttr(
            self.state, "dirt_loc",
            parser=user_input.parse_ndarray(3),
            default=initial_loc)
        self.state.dump_loc = PromptStateAttr(
            self.state, "dump_loc",
            parser=user_input.parse_ndarray(3),
            default=initial_loc)

        self.state.farm_x1z1 = PromptStateAttr(
            self.state, "farm_x1z1",
            parser=user_input.parse_ndarray(2),
            default=np.array([initial_loc[0] - 10, initial_loc[2] - 10]))
        self.state.farm_x2z2 = PromptStateAttr(
            self.state, "farm_x2z2",
            parser=user_input.parse_ndarray(2),
            default=np.array([initial_loc[0] + 10, initial_loc[2] + 10]))
        self.state.farm_height = PromptStateAttr(
            self.state, "farm_height",
            parser=int,
            default=int(initial_loc[1]))
        self.state.space_between_trees = PromptStateAttr(
            self.state, "space_between_trees",
            parser=int,
            default=2)
        self.state.tree_width = PromptStateAttr(
            self.state, "tree_width",
            parser=int,
            default=1)
        self.state.check_every_n_seconds = PromptStateAttr(
            self.state, "check_every_n_seconds",
            parser=int,
            default=60 * 5)

        # Create other state
        self.state.placed_dirt = StateAttr(
            self.state, "placed_dirt",
            default=[])
        self.state.placed_saplings = StateAttr(
            self.state, "placed_saplings",
            default=[])
        self.state.tree_nodes = StateAttr(
            self.state, "tree_nodes",
            default=[])
        self.state.confirmed_not_tree = StateAttr(
            self.state, "confirmed_not_tree",
            default=[])
        self.state.last_checkup = StateAttr(
            self.state, "last_checkup",
            default=time())

    @property
    def destructive(self):
        """If True, the turtle is safe to dig!"""
        pos = self.state.map.read().position
        within_y_bounds = self.state.farm_height.read() - 1 <= pos[1]
        within_farm_bounds = math_utils.within_bounding_points(
            point=(pos[0], pos[2]),
            bp1=self.state.farm_x1z1.read(),
            bp2=self.state.farm_x2z2.read()
        )
        return within_y_bounds and within_farm_bounds

    def step(self, state: StateFile):
        fuel_loc = state.fuel_loc.read()
        dump_loc = state.dump_loc.read()
        last_checkup_time = state.last_checkup.read()
        check_every_n_seconds = state.check_every_n_seconds.read()

        # ALWAYS scan for tree nodes!
        self.scan_for_nodes(state)

        # Basic maintenance
        routines.maybe_refuel(self, fuel_loc)
        routines.dump_if_full(self, dump_loc, range(4, 17))

        # Resupply on dirt or saplings as necessary
        self.maybe_resupply(state)

        # Priority 0: Make sure any tree chopping tasks are finished
        self.chop_trees(state)

        # Priority 1: Make sure trees are planted in the first place
        self.plant_trees(state)

        # Priority 2: Wait for trees to grow
        if time() - last_checkup_time < check_every_n_seconds:
            self.move_toward(fuel_loc, destructive=self.destructive)
            print("Waiting...")
            os.sleep(30)
            raise StepFinished
        else:
            print("Writing tree nodes!")
            state.tree_nodes.write(self.get_tree_corners(height_offset=4))
            state.placed_dirt.write([])
            state.placed_saplings.write([])
            state.confirmed_not_tree.write([])
            state.last_checkup.write(time())

    def maybe_resupply(self, state):
        """This will resupply if the turtle is running out of materials"""
        dirt_slot = self.inventory.slot(self.DIRT_SLOT)
        sapling_slot = self.inventory.slot(self.SAPLING_SLOT)
        # raise ValueError(f"yeet {dirt_slot.count} {sapling_slot.count}")
        if dirt_slot.count <= 1:
            self.move_toward(state.dirt_loc.read(),
                             destructive=self.destructive)
            self.suck_in_direction(Direction.down, end_step=False)
            dirt_slot.refresh()

        if sapling_slot.count <= 1:
            self.move_toward(state.sapling_loc.read(),
                             destructive=self.destructive)
            self.suck_in_direction(Direction.down, end_step=False)
            sapling_slot.refresh()

    def chop_trees(self, state):
        tree_nodes: List[List[int]] = state.tree_nodes.read()
        if len(tree_nodes) == 0:
            # If theres no tree cutting tasks to be done
            return

        curr_pos = state.map.read().position
        distance = partial(math_utils.turtle_distance, curr_pos)
        tree_nodes.sort(key=distance)
        next_node = tree_nodes[0]
        self.move_toward(to_pos=next_node, destructive=self.destructive)
        raise StepFinished

    def plant_trees(self, state):
        """Ensure that all trees are planted"""
        placed_dirt_locations = state.placed_dirt.read()
        placed_sapling_locations = state.placed_saplings.read()

        for tree_location in self.tree_planting_locations:
            self.plant_tree(
                state=state,
                dirt_location=tree_location,
                placed_dirt_locations=placed_dirt_locations,
                placed_sapling_locations=placed_sapling_locations)

    def plant_tree(self, state, dirt_location, placed_dirt_locations,
                   placed_sapling_locations):

        # First place the dirt, if necessary
        self.maybe_place_item(
            state=state,
            slot=self.DIRT_SLOT,
            item_location=dirt_location,
            placed_locations=placed_dirt_locations,
            state_var=state.placed_dirt)

        # Then, place the sapling, if necessary
        sapling_location = [dirt_location[0],
                            dirt_location[1] + 1,
                            dirt_location[2]]
        self.maybe_place_item(
            state=state,
            slot=self.SAPLING_SLOT,
            item_location=sapling_location,
            placed_locations=placed_sapling_locations,
            state_var=state.placed_saplings)

    def maybe_place_item(self, state: StateFile,
                         slot: int,
                         item_location: List[int],
                         placed_locations: List[List[int]],
                         state_var):

        if item_location not in placed_locations:
            self.move_toward(item_location, destructive=self.destructive)
            self.select(slot)
            try:
                self.dig_in_direction(Direction.down, end_step=False)
            except lua_errors.NoItemToDigError:
                pass

            self.place_in_direction(Direction.down, end_step=False)
            placed_locations.append(item_location)
            with state:
                state_var.write(placed_locations)

    @lru_cache
    def get_tree_corners(self, height_offset=0) -> List[List[int]]:
        """Return the corner of each tree planting location
        :param height_offset: Adds an offset to the height. This is useful so
        when the robot goes scanning tree nodes, it starts at a slightly higher
        height
        """
        x1z1 = self.state.farm_x1z1.read()
        x2z2 = self.state.farm_x2z2.read()
        spacing = self.state.space_between_trees.read() + 1
        tree_width = self.state.tree_width.read()
        height = self.state.farm_height.read()

        from_x, to_x = sorted([x1z1[0], x2z2[0]])
        from_z, to_z = sorted([x1z1[1], x2z2[1]])

        return list(
            [x, height + height_offset, z]
            for x in range(from_x + spacing, to_x + 1 - spacing,
                           spacing + tree_width - 1)
            for z in range(from_z + spacing, to_z + 1 - spacing,
                           spacing + tree_width - 1)
        )

    @property
    @lru_cache
    def tree_planting_locations(self):
        """Generates a list of locations where trees should be planted"""
        tree_width = self.state.tree_width.read()

        return list(
            [x + offset_x, h, z + offset_z]
            for x, h, z in self.get_tree_corners()
            for offset_x in range(0, tree_width)
            for offset_z in range(0, tree_width)
        )

    def scan_for_nodes(self, state):
        map = state.map.read()
        tree_nodes = state.tree_nodes.read()
        confirmed_not_tree = state.confirmed_not_tree.read()

        # Get rid of any nodes that match the current position
        if map.position.tolist() in tree_nodes:
            tree_nodes.remove(map.position.tolist())

        scan_directions = [
            Direction.front,
            Direction.up,
            Direction.down,
        ]

        for direction in scan_directions:
            block_position = math_utils.coordinate_in_turtle_direction(
                curr_pos=map.position,
                curr_angle=map.direction,
                direction=direction).tolist()
            if block_position in confirmed_not_tree:
                continue

            within_farm_bounds = math_utils.within_bounding_points(
                point=(block_position[0], block_position[2]),
                bp1=self.state.farm_x1z1.read(),
                bp2=self.state.farm_x2z2.read()
            )
            if not within_farm_bounds:
                # Don't scan wood that's not within the farm bounds!
                continue
            if block_position in tree_nodes:
                # This block is already known to be a tree! No need to waste
                # time running inspect()
                continue
            block = self.inspect_in_direction(direction)

            if block is None:
                # This block is air, and isn't known to be a tree
                confirmed_not_tree.append(block_position)
                continue

            matches_regex = block_info.name_matches_regexes(
                block_name=block[b"name"],
                regex_list=self.TREE_REGEXES)

            if matches_regex:
                tree_nodes.append(block_position)
                # TODO: Am I sure we don't necessarily want to add the neighbors?
                # neighbors = math_utils.get_coordinate_neighbors(block_position)
                # for neighbor in neighbors:
                #     tree_nodes.append(neighbor.tolist())
        with state:
            state.tree_nodes.write(tree_nodes)
            state.confirmed_not_tree.write(confirmed_not_tree)
        return tree_nodes


TreeFarmBot().run()
