from functools import partial

import mock
import pytest
import numpy as np

from tests import cc_mock as cc
from fleet import (
    StatefulTurtle,
    Direction,
    StateNotAcquiredError,
    StepFinished,
    StateRecoveryError
)


def test_statefile_required():
    """Test that a statefile is required for certain operations"""

    st = StatefulTurtle()

    # A list of tuples in the form of
    # (function, error expected w/o state file, error expected with state file)
    movement_fns = [
        # Simple turns
        (st.up, StateNotAcquiredError, StepFinished),
        (st.down, StateNotAcquiredError, StepFinished),
        (st.turn_left, StateNotAcquiredError, StepFinished),
        (st.turn_right, StateNotAcquiredError, StepFinished),
        (st.forward, StateNotAcquiredError, StepFinished),
        (st.backward, StateNotAcquiredError, StepFinished),
        # Digging mechanics
        (partial(st.dig_towards, Direction.up), StepFinished, StepFinished),
        (partial(st.dig_towards, Direction.down), StepFinished, StepFinished),
        (partial(st.dig_towards, Direction.front), StepFinished, StepFinished),
        (partial(st.dig_towards, Direction.left), NotImplementedError),
        (partial(st.dig_towards, Direction.right), NotImplementedError),
        (partial(st.dig_towards, Direction.back), NotImplementedError),
        # Turn by degrees API
        (partial(st.turn_degrees, 90), StateNotAcquiredError, StepFinished),
        (partial(st.turn_degrees, -90), StateNotAcquiredError, StepFinished),
        (partial(st.turn_degrees, 0), None),
        (partial(st.turn_degrees, 10), ValueError),
        # Move by sign vertically API
        (partial(st.move_vertically, 1), StateNotAcquiredError, StepFinished),
        (partial(st.move_vertically, -1), StateNotAcquiredError, StepFinished),
        (partial(st.move_vertically, 0), ValueError),
        (partial(st.move_vertically, 25), ValueError),
        # Move by sign forward/backwards API
        (partial(st.move_in_direction, 1), StateNotAcquiredError, StepFinished),
        (partial(st.move_in_direction, -1), StateNotAcquiredError,
         StepFinished),
        (partial(st.move_in_direction, 55), ValueError),
        (partial(st.move_in_direction, 0), ValueError),
    ]
    for fn, *error in movement_fns:
        if len(error) == 1:
            without_statefile_err = error[0]
            with_statefile_err = error[0]
        else:
            without_statefile_err, with_statefile_err = error

        def test(expected_err):
            if expected_err is None:
                fn()
            else:
                with pytest.raises(expected_err):
                    fn()

        # Do test without statefile
        test(without_statefile_err)

        # Do test with statefile
        with st.state:
            test(with_statefile_err)


@pytest.mark.parametrize(
    argnames=("state_pos", "gps_pos", "expected_error"),
    argvalues=([
        # Test state matches GPS (happy path)
        ((0, 1, 0), (0, 1, 0), None),
        # Test state _almost_ matches GPS, to within an adjacent block
        ((0, 1, 0), (0, 0, 0), None),
        ((0, 1, 0), (-1, 1, 0), None),
        ((0, 1, 0), (1, 1, 0), None),
        ((0, 1, 0), (0, 1, -1), None),
        # Test no GPS available
        ((0, 1, 0), None, StateRecoveryError),
        # Test not next to an adjacent block
        ((0, 2, 0), (0, 0, 0), StateRecoveryError),
        ((0, -2, 0), (0, 0, 0), StateRecoveryError),
        ((1, 1, 0), (0, 0, 0), StateRecoveryError),
    ])
)
def test_gps_recovery(state_pos,
                      gps_pos,
                      expected_error):
    """Test the turtle can recovery GPS correctly"""
    # Initialize the state file with default attributes
    state = StatefulTurtle().state

    # Modify the statefile with a new position
    with state:
        map = state.map.read()
        map.position = np.array(state_pos)
        state.map.write(map)

    # Try initializing the turtle with the new (incorrect) states
    with mock.patch.object(cc.gps, "locate") as locate_fn:
        locate_fn.return_value = gps_pos
        if expected_error is None:
            turtle = StatefulTurtle()
        else:
            with pytest.raises(StateRecoveryError):
                StatefulTurtle()