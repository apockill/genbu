from functools import partial

import pytest

from fleet import StatefulTurtle, Direction, StateNotAcquiredError, StepFinished


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
        (partial(st.move_in_direction, -1), StateNotAcquiredError, StepFinished),
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
