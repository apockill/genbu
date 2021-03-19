from functools import lru_cache
from typing import List, Optional

import numpy as np

from fleet import (
    routines,
    StateAttr,
    PromptStateAttr,
    lua_errors,
    NavigationTurtle,
    StepFinished,
    math_utils,
    user_input
)


# quarry.py
class QuarryTurtle(NavigationTurtle):
    def __init__(self):
        super().__init__()
        with self.state:
            initial_loc = self.state.map.read().position
        self.state.fuel_loc = PromptStateAttr(
            self.state, "fuel_loc",
            parser=user_input.parse_ndarray(3),
            default=initial_loc)

        with self.state:
            hx, hy, hz = self.state.fuel_loc.read()

        self.state.dump_loc = PromptStateAttr(
            self.state, "dump_loc",
            parser=user_input.parse_ndarray(3),
            default=np.array([hx + 2, hy, hz]))
        self.state.mining_x1z1 = PromptStateAttr(
            self.state, "mining_x1z1",
            parser=user_input.parse_ndarray(2),
            default=np.array((hx + 10, hz)))
        self.state.mining_x2z2 = PromptStateAttr(
            self.state, "mining_x2z2",
            parser=user_input.parse_ndarray(2),
            default=np.array((hx + 110, hz + 100)))
        self.state.dig_height = PromptStateAttr(
            self.state, "dig_height",
            parser=int,
            default=int(hy))
        self.state.dig_depth = PromptStateAttr(
            self.state, "dig_depth",
            parser=int,
            default=-1)
        self.state.columns_finished = StateAttr(
            self.state, "columns_finished",
            default=[])
        self.state.columns_started = StateAttr(
            self.state, "columns_started",
            default=[])
        """This will hold a list of [x, z] areas of columns that have already 
        been dug all the way down."""

        # Clean up any broken state (columns that were started but not finished
        with self.state as state:
            started = state.columns_started.read()
            finished = state.columns_finished.read()
            started = [c for c in started if c in finished]
            state.columns_started.write(started)

    def step(self, state):
        routines.maybe_refuel(self, state.fuel_loc.read())
        routines.dump_if_full(self, state.dump_loc.read(), range(2, 16 + 1))

        fuel_loc = state.fuel_loc.read()
        columns_started = state.columns_started.read()
        columns_finished = state.columns_finished.read()
        mining_x1z1 = state.mining_x1z1.read()
        mining_x2z2 = state.mining_x2z2.read()
        dig_height = state.dig_height.read()
        dig_depth = state.dig_depth.read()
        curr_pos = state.map.read().position

        next_column = self.get_next_column(
            x1z1=tuple(mining_x1z1.tolist()),
            x2z2=tuple(mining_x2z2.tolist()),
            home_pos=tuple(fuel_loc.tolist()),
            finished_columns=tuple(tuple(c) for c in columns_finished)
        )

        if next_column is None:
            # If the robot is done, go home!
            self.move_toward(state.fuel_loc.read())
            return

        x, z = next_column

        within_dig_volume = math_utils.within_bounding_points(
            point=curr_pos,
            bp1=(mining_x1z1[0], dig_depth, mining_x1z1[1]),
            bp2=(mining_x2z2[0], dig_height, mining_x2z2[1])
        )

        if (next_column not in columns_started
                or not within_dig_volume):
            # The turtle will move to the start of the next column if it
            # a) is above the height of the dig volume (ie, if it grabs fuel
            #    or dumps its items)
            # b) it simply hasn't started the next column
            column_start_pos = np.array((x, dig_height, z))

            self.move_toward(column_start_pos,
                             destructive=within_dig_volume)
            started = columns_started
            started.append(next_column)
            state.columns_started.write(started)

        # Okay! The column has been started, better dig down!
        def mark_column_finished():
            """Mark a column as finished"""
            columns_finished.append(next_column)
            state.columns_finished.write(columns_finished)
            raise StepFinished()

        if curr_pos[1] <= dig_depth:
            mark_column_finished()

        try:
            self.move_toward(
                to_pos=[x, curr_pos[1] - 1, z],
                destructive=within_dig_volume)
        except lua_errors.UnbreakableBlockError:
            mark_column_finished()

    @staticmethod
    @lru_cache
    def get_next_column(home_pos, x1z1, x2z2, finished_columns) \
            -> Optional[List[int]]:
        """Return the next column. They are sorted by distance from home"""
        from_x, to_x = sorted([x1z1[0], x2z2[0]])
        from_z, to_z = sorted([x1z1[1], x2z2[1]])

        columns = [(x, z)
                   for x in range(from_x, to_x + 1)
                   for z in range(from_z, to_z + 1)
                   if (x, z) not in finished_columns]
        if not len(columns):
            return None

        hx, _, hz = home_pos
        columns.sort(
            key=lambda c: (hx - c[0]) ** 2 + (hz - c[1]) ** 2)
        return list(columns[0])


QuarryTurtle().run()
