from functools import partial
from typing import Tuple

import mock
import pytest
import numpy as np
from computercraft.errors import LuaException

from tests import cc_mock as cc
from fleet import (
    StatefulTurtle,
    Direction,
    StateNotAcquiredError,
    StepFinished,
    StateRecoveryError,
    lua_errors,
    MinedBlacklistedBlockError
)


@pytest.mark.parametrize(
    argnames=("fn_name", "args", "wo_statefile_err", "w_statefile_err"),
    argvalues=[
        # Simple turns
        ("up", (), StateNotAcquiredError, StepFinished),
        ("down", (), StateNotAcquiredError, StepFinished),
        ("turn_left", (), StateNotAcquiredError, StepFinished),
        ("turn_right", (), StateNotAcquiredError, StepFinished),
        ("forward", (), StateNotAcquiredError, StepFinished),
        ("backward", (), StateNotAcquiredError, StepFinished),
        # Digging mechanics
        ("dig_in_direction", (Direction.up,), StepFinished, StepFinished),
        ("dig_in_direction", (Direction.down,), StepFinished, StepFinished),
        ("dig_in_direction", (Direction.front,), StepFinished, StepFinished),
        ("dig_in_direction", (Direction.left,), ValueError, ValueError),
        ("dig_in_direction", (Direction.right,), ValueError, ValueError),
        ("dig_in_direction", (Direction.back,), ValueError, ValueError),
        # Turn by degrees API
        ("turn_degrees", (90,), StateNotAcquiredError, StepFinished),
        ("turn_degrees", (-90,), StateNotAcquiredError, StepFinished),
        ("turn_degrees", (0,), None, None),
        ("turn_degrees", (10,), ValueError, ValueError),
        # Use move_in_direction incorrectly
        ("move_in_direction", (Direction.left,), ValueError, ValueError),
        ("move_in_direction", (Direction.right,), ValueError, ValueError),
        # Move by sign forward/backwards API
        ("move_in_direction", (Direction.front,), StateNotAcquiredError,
         StepFinished),
        ("move_in_direction", (Direction.back,), StateNotAcquiredError,
         StepFinished),
        ("move_in_direction", (Direction.up,), StateNotAcquiredError,
         StepFinished),
        ("move_in_direction", (Direction.down,), StateNotAcquiredError,
         StepFinished),
    ]
)
def test_statefile_required(
        fn_name,
        args,
        wo_statefile_err,
        w_statefile_err):
    """Test that a statefile is required for certain operations"""

    st = StatefulTurtle()

    # Pretend this turtle is already "position verified" in every way
    st.direction_verified = True

    def test(expected_err):
        fn = partial(st.__getattribute__(fn_name), *args)
        if expected_err is None:
            fn()
        else:
            with pytest.raises(expected_err):
                fn()

    # Do test without statefile
    test(wo_statefile_err)

    # Do test with statefile
    with st.state:
        test(w_statefile_err)


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
        # Test not next to an adjacent block
        ((0, 2, 0), (0, 0, 0), None),
        ((0, -2, 0), (0, 0, 0), None),
        ((1, 1, 0), (0, 0, 0), None),
        # Test no GPS available
        ((0, 1, 0), None, StateRecoveryError),
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
            with pytest.raises(expected_error):
                StatefulTurtle()


@pytest.mark.parametrize(
    argnames=("is_bedrock_blocked", "is_blocked", "direction",
              "expected_error"),
    argvalues=[
        # Test "happy path"
        (False, True, Direction.up, StepFinished),
        (False, True, Direction.down, StepFinished),
        (False, True, Direction.front, StepFinished),
        # Test "happy path" but there was empty air to dig
        (False, False, Direction.up, None),
        (False, False, Direction.down, None),
        (False, False, Direction.front, None),
        # Test invalid input
        (False, True, Direction.left, ValueError),
        (False, True, Direction.right, ValueError),
        (False, True, Direction.back, ValueError),
        # Test blocked by bedrock
        (True, True, Direction.up, lua_errors.UnbreakableBlockError),
        (True, True, Direction.down, lua_errors.UnbreakableBlockError),
        (True, True, Direction.front, lua_errors.UnbreakableBlockError)
    ],

)
def test_dig_towards(is_bedrock_blocked: bool,
                     is_blocked: bool,
                     direction: Direction,
                     expected_error):
    """

    :param is_bedrock_blocked: If there's a block to dig, but it's unbreakable
    :param is_blocked: If there's a block to dig, but it's not unbreakable
    :param direction: The direciton to dig
    :param expected_error: The error, if any
    :return:
    """
    if is_bedrock_blocked:
        assert is_blocked

    turtle = StatefulTurtle()
    with mock.patch.object(cc.turtle, "dig") as dig_front, \
            mock.patch.object(cc.turtle, "digUp") as dig_up, \
            mock.patch.object(cc.turtle, "digDown") as dig_down, \
            mock.patch.object(cc.turtle, "inspect") as inspect_front, \
            mock.patch.object(cc.turtle, "inspectUp") as inspect_up, \
            mock.patch.object(cc.turtle, "inspectDown") as inspect_down:
        mapping = {
            Direction.front: (dig_front, inspect_front),
            Direction.up: (dig_up, inspect_up),
            Direction.down: (dig_down, inspect_down),
            Direction.left: (None, None),
            Direction.right: (None, None),
            Direction.back: (None, None)
        }
        dig, inspect = mapping[direction]

        if is_bedrock_blocked and dig is not None:
            msg = lua_errors.TO_LUA[lua_errors.UnbreakableBlockError]
            dig.side_effect = LuaException(msg)

        if inspect is not None:
            if is_bedrock_blocked or is_blocked:
                inspect.return_value = cc.MOCK_INSPECT_VAL
            else:
                inspect.return_value = None

        assert not dig_up.called
        assert not dig_down.called
        assert not dig_front.called
        assert not inspect_front.called
        assert not inspect_up.called
        assert not inspect_down.called

        if expected_error:
            with pytest.raises(expected_error):
                turtle.dig_in_direction(direction)
        else:
            turtle.dig_in_direction(direction)

        # Verify the correct direction was called (and nothing else!)
        for direction_key, dig_inspect in mapping.items():
            if dig_inspect == (None, None):
                continue

            dig, inspect = dig_inspect
            if direction_key is direction:
                if is_blocked:
                    # Dig should only be called if a non-air block was in that
                    # direction
                    assert dig.called
                else:
                    assert not dig.called
                assert inspect.called
            else:
                assert not dig.called
                assert not inspect.called


@pytest.mark.parametrize(
    argnames=("dig_fn", "block_name", "is_mineable", "turtle_inspect_fn"),
    argvalues=[
        # Test "happy path"
        (dig_fn, block_name, is_mineable, turtle_inspect_fn)
        for block_name, is_mineable in [
            ("computercraft:turtle", False),
            ("computercraft:thisshouldmatchregex", False),
            ("fake-mod:this-matches-nothing-in-the-blacklist", True),
            ("cool:chest", False),
            ("chest:oh-no-dont-mine-me", False),
        ]
        for dig_fn, turtle_inspect_fn in [
            ("dig_up", "inspectUp"),
            ("dig_down", "inspectDown"),
            ("dig_front", "inspect")
        ]
    ],

)
def test_dig_towards_blacklisted_block(dig_fn: str,
                                       turtle_inspect_fn,
                                       block_name: str,
                                       is_mineable: bool):
    turtle = StatefulTurtle()

    # Mirror the output of turtle.inspect()
    inspect_retval = {
        b"state": {b"facing": b"south", b"waterlogged": False},
        b"name": bytes(block_name, encoding="ascii"),
        b"tags": {}}
    expected_exception = StepFinished if is_mineable else MinedBlacklistedBlockError

    with mock.patch.object(cc.turtle, turtle_inspect_fn) as inspect_front:
        inspect_front.return_value = inspect_retval
        # TODO: Make a good exception for this
        with pytest.raises(expected_exception):
            turtle.__getattribute__(dig_fn)()


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
