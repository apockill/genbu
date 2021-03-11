from typing import List

import numpy as np

from fleet import (
    routines,
    StateAttr,
    PromptStateAttr,
    lua_errors,
    NavigationTurtle,
    StepFinished
)


def parse_position(val: str):
    return np.array(list(map(int, val.split(" "))))


# quarry.py
class QuarryTurtle(NavigationTurtle):
    def __init__(self):
        super().__init__()
        with self.state:
            initial_loc = self.state.map.read().position
        self.state.fuel_loc = PromptStateAttr(
            self.state, "fuel_loc",
            parser=parse_position,
            default=initial_loc)

        with self.state:
            hx, hy, hz = self.state.fuel_loc.read()

        self.state.dump_loc = PromptStateAttr(
            self.state, "dump_loc",
            parser=parse_position,
            default=np.array([hx + 2, hy, hz]))
        self.state.mining_x1z1 = PromptStateAttr(
            self.state, "mining_x1z1",
            parser=parse_position,
            default=np.array((hx + 10, hz)))
        self.state.mining_x2z2 = PromptStateAttr(
            self.state, "mining_x2z2",
            parser=parse_position,
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

        columns_started = state.columns_started.read()
        columns_finished = state.columns_finished.read()
        next_column = self.get_next_column(
            x1z1=state.mining_x1z1.read(),
            x2z2=state.mining_x2z2.read(),
            finished_columns=columns_finished
        )

        if next_column is None:
            # If the robot is done, go home!
            self.move_toward(state.fuel_loc.read())
            return

        x, z = next_column

        if next_column not in columns_started:
            # Then move to the correct X/Z
            self.move_toward([x, state.dig_height.read(), z])
            started = columns_started
            started.append(next_column)
            state.columns_started.write(started)

        with state:
            curr_x, curr_y, curr_z = state.map.read().position

        # Okay! The column has been started, better dig down!
        def mark_column_finished():
            """Mark a column as finished"""
            columns_finished.append(next_column)
            state.columns_finished.write(columns_finished)
            raise StepFinished()

        if curr_y <= state.dig_depth.read():
            mark_column_finished()

        try:
            self.move_toward(
                to_pos=[x, curr_y - 1, z],
                destructive=True)
        except lua_errors.UnbreakableBlockError:
            mark_column_finished()

    def get_next_column(self, x1z1, x2z2, finished_columns):
        from_x, to_x = sorted([x1z1[0], x2z2[0]])
        from_z, to_z = sorted([x1z1[1], x2z2[1]])
        try:
            return next(
                ([x, z]
                 for x in range(from_x, to_x + 1)
                 for z in range(from_z, to_z + 1)
                 if [x, z] not in finished_columns))
        except StopIteration:
            return None


QuarryTurtle().run()
