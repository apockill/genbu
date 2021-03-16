from typing import List
from functools import partial

import numpy as np

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
        # TODO: add support for tree_width
        self.state.tree_width = PromptStateAttr(
            self.state, "tree_width",
            parser=int,
            default=1)

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

    def step(self, state: StateFile):
        routines.maybe_refuel(self, state.fuel_loc.read())

        # TODO: ensure inventory

        # Priority 0: Make sure trees are planted in the first place
        self.plant_trees(state)

        # Priority 1: Make sure
        # tree_nodes = self.scan_for_nodes(state)
        # self.travel_along_node(state)

    def travel_along_node(self, state):
        """Travel along any known tree nodes"""
        tree_nodes: List[List[int]] = state.tree_nodes.read()
        curr_pos = state.map.read().position

        if not len(tree_nodes):
            return

        distance = partial(math_utils.turtle_distance, curr_pos)
        tree_nodes.sort(key=distance)
        next_node = tree_nodes[0]

        safe_to_dig = distance(next_node) <= self.NODE_MIN_DISTANCE_TO_DIG
        self.move_toward(to_pos=next_node, destructive=safe_to_dig)

    def plant_trees(self, state):
        """Ensure that all trees are planted"""
        tree_locations = self.get_tree_planting_locations(state)
        placed_dirt = state.placed_dirt.read()
        for tree_location in tree_locations:
            self.plant_tree(state, tree_location)

    def plant_tree(self, state, dirt_location):
        placed_dirt_locations = state.placed_dirt.read()
        placed_sapling_locations = state.placed_saplings.read()

        # First place the dirt, if necessary
        if dirt_location not in placed_dirt_locations:
            self.move_toward(dirt_location)
            try:
                self.select(self.DIRT_SLOT)
                self.place_in_direction(Direction.down)
            except lua_errors.BlockNotPlaceableError:
                placed_dirt_locations.append(dirt_location)
                with state:
                    state.placed_dirt.write(placed_dirt_locations)

        # Then, place the sapling, if necessary
        sapling_location = [dirt_location[0],
                            dirt_location[1] + 1,
                            dirt_location[2]]
        if sapling_location not in placed_sapling_locations:
            self.move_toward(sapling_location)
            try:
                self.select(self.SAPLING_SLOT)
                self.place_in_direction(Direction.down)
            except lua_errors.BlockNotPlaceableError:
                placed_sapling_locations.append(sapling_location)
                with state:
                    state.placed_saplings.write(placed_sapling_locations)

    def get_tree_planting_locations(self, state):
        """Generates a list of locations where trees should be planted"""
        x1z1 = state.farm_x1z1.read()
        x2z2 = state.farm_x2z2.read()
        spacing = state.space_between_trees.read() + 1
        tree_width = state.tree_width.read()
        height = state.farm_height.read()

        from_x, to_x = sorted([x1z1[0], x2z2[0]])
        from_z, to_z = sorted([x1z1[1], x2z2[1]])

        return (
            [x + offset_x, height, z + offset_z]
            for x in
            range(from_x + spacing, to_x + 1 - spacing,
                  spacing + tree_width - 1)
            for z in
            range(from_z + spacing, to_z + 1 - spacing,
                  spacing + tree_width - 1)
            for offset_x in range(0, tree_width)
            for offset_z in range(0, tree_width)
        )

    def scan_for_nodes(self, state):
        map = state.map.read()
        tree_nodes = state.tree_nodes.read()

        # Get rid of any nodes that match the current position
        if map.position.tolist() in tree_nodes:
            tree_nodes.remove(map.position.tolist())

        scan_directions = [
            Direction.front,
            Direction.up,
            Direction.down,
        ]

        for direction in scan_directions:
            block = self.inspect_in_direction(direction)
            block_position = math_utils.coordinate_in_turtle_direction(
                curr_pos=map.position,
                curr_angle=map.direction,
                direction=direction).tolist()

            if block_position in tree_nodes:
                continue
            elif block is None and block_position in tree_nodes:
                index = tree_nodes.index(block_position)
                tree_nodes.remove(index)
                continue
            elif block is None:
                continue

            matches_regex = block_info.name_matches_regexes(
                block_name=block[b"name"],
                regex_list=self.TREE_REGEXES)

            if matches_regex:
                tree_nodes.append(block_position)
                neighbors = math_utils.get_coordinate_neighbors(block_position)
                for neighbor in neighbors:
                    tree_nodes.append(neighbor.tolist())

        state.tree_nodes.write(tree_nodes)
        return tree_nodes


TreeFarmBot().run()
