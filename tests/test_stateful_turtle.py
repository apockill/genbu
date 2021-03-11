from functools import partial
from typing import Tuple

import mock
import pytest
import numpy as np
from computercraft.errors import LuaException

import fleet.stateful_turtle
from tests import cc_mock as cc
from fleet import (
    StatefulTurtle,
    Direction,
    StateNotAcquiredError,
    StepFinished,
    StateRecoveryError,
    lua_errors
)


def test_statefile_required():
    """Test that a statefile is required for certain operations"""

    st = StatefulTurtle()

    # Pretend this turtle is already "position verified" in every way
    st.direction_verified = True

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
        (partial(st.dig_towards, Direction.left), ValueError),
        (partial(st.dig_towards, Direction.right), ValueError),
        (partial(st.dig_towards, Direction.back), ValueError),
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
        # Test not next to an adjacent block (these yield OSErrors because
        # pytest raises OSError when input() is called)
        ((0, 2, 0), (0, 0, 0), OSError),
        ((0, -2, 0), (0, 0, 0), OSError),
        ((1, 1, 0), (0, 0, 0), OSError),
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


@pytest.mark.parametrize(
    argnames=("is_bedrock_blocked", "direction", "expected_error"),
    argvalues=[
        # Test "happy path"
        (False, Direction.up, StepFinished),
        (False, Direction.down, StepFinished),
        (False, Direction.front, StepFinished),
        # Test invalid input
        (False, Direction.left, ValueError),
        (False, Direction.right, ValueError),
        (False, Direction.back, ValueError),
        # Test blocked by bedrock
        (True, Direction.up, lua_errors.UnbreakableBlockError),
        (True, Direction.down, lua_errors.UnbreakableBlockError),
        (True, Direction.front, lua_errors.UnbreakableBlockError)
    ],

)
def test_dig_towards(is_bedrock_blocked: bool,
                     direction: Direction,
                     expected_error):
    turtle = StatefulTurtle()
    with mock.patch.object(cc.turtle, "dig") as dig_front, \
            mock.patch.object(cc.turtle, "digUp") as dig_up, \
            mock.patch.object(cc.turtle, "digDown") as dig_down:
        mapping = {
            Direction.front: dig_front,
            Direction.up: dig_up,
            Direction.down: dig_down
        }
        if is_bedrock_blocked:
            msg = lua_errors.TO_LUA[lua_errors.UnbreakableBlockError]
            mapping[direction].side_effect = LuaException(msg)

        assert not dig_up.called
        assert not dig_down.called
        assert not dig_front.called

        with pytest.raises(expected_error):
            turtle.dig_towards(direction)

        # Verify the correct direction was called
        for key, val in mapping.items():
            if key is direction:
                assert val.called
            else:
                assert not val.called


@pytest.mark.parametrize(
    argnames=("mv_direction", "is_blocked", "from_pos", "to_gps_pos",
              "pre_move_dir", "post_move_dir"),
    argvalues=[
        # Happy path, where expected matches what was discovered
        ("forward", False, (1, 1, 1), (2, 1, 1), 0, 0),
        ("backward", False, (-1, -1, -1), (0, -1, -1), 180, 180),
        ("backward", False, (1, 2, 3), (1, 2, 2), 90, 90),
        # Test the state direction was overwritten if it was incorrect
        # We do a bunch of test cases here mostly just to make sure the angle
        # calculations work, and that the forward/backwards calculation is also
        # done correctly
        ("forward", False, (1, 2, 3), (2, 2, 3), 90, 0),
        ("backward", False, (0, 0, 0), (1, 0, 0), 90, 180),
        ("forward", False, (0, 0, 0), (0, 0, 1), 180, 90),
        ("backward", False, (0, 0, 0), (0, 0, 1), 90, 270),
        ("forward", False, (0, 0, 0), (0, 0, -1), 90, 270),
        ("backward", False, (0, 0, 0), (0, 0, -1), 270, 90),
        ("forward", False, (0, 0, 0), (-1, 0, 0), 90, 180),
        ("backward", False, (0, 0, 0), (-1, 0, 0), 90, 0),
        ###### Test forward-position finding routine
        # In this case the robot moves backwards instead of forward, because
        # forward was blocked
        ("forward", True, (0, 0, 0), (-1, 0, 0), 0, 0),
    ]
)
def test_dir_uncorrupted_on_move_forward_or_backward(
        mv_direction: str,
        is_blocked: bool,
        from_pos: Tuple[int, int, int],
        to_gps_pos: Tuple[int, int, int],
        pre_move_dir: int,
        post_move_dir: int
):
    """
    If the turtle moves forward and finds the direction it had recorded was
    correct, everything works fine and direction is verified
    """

    with mock.patch.object(cc.gps, "locate") as gps_locate:
        gps_locate.return_value = from_pos

        # Create an initial statefile to set the pre_move_dir
        state = StatefulTurtle().state
        with state:
            map = state.map.read()
            print("MAP", map)
            map.direction = pre_move_dir
            state.map.write(map)
        del state

        # Create the turtle again, to verify everything loaded from the state
        # file as expected
        gps_locate.return_value = from_pos
        turtle = StatefulTurtle()
        with turtle.state:
            map = turtle.state.map.read()
        assert map.direction == pre_move_dir
        assert (map.position == from_pos).all()

    with turtle.state:
        # The direction should not be initially verified
        assert not turtle.direction_verified

        expected_err = lua_errors.TurtleBlockedError if is_blocked else StepFinished
        with mock.patch.object(cc.gps, "locate") as gps_locate, \
                mock.patch.object(cc.turtle, "forward") as turtle_forward, \
                mock.patch.object(cc.turtle, "back") as turtle_backward:
            if is_blocked:
                # If the turtle is blocked, we expect a LuaException
                # when the turtle tries to move forward
                msg = lua_errors.TO_LUA[expected_err]
                turtle_forward.side_effect = LuaException(msg)
                turtle_backward.side_effect = LuaException(msg)
            gps_locate.return_value = to_gps_pos
            with pytest.raises(expected_err):
                turtle.__getattribute__(mv_direction)()

        assert turtle.state.map.read().direction == post_move_dir
        if not is_blocked:
            assert turtle.direction_verified
        else:
            # Do some simple check here to verify the other code path was taken
            # here. This code path will be better checked in another test
            # dedicated to this
            raise NotImplementedError()
