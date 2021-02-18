import pytest

from fleet import StateNotAcquiredError, StateFile, StateAttr


def test_basic_usage():
    def get_statefile():
        state = StateFile()
        state.my_attr = StateAttr(state, "my_attr", default=4)
        return state

    state = get_statefile()

    # Verify you can't read or write without first acquiring a statefile
    with pytest.raises(StateNotAcquiredError):
        state.my_attr.write(3)
    with pytest.raises(StateNotAcquiredError):
        state.my_attr.read()

    # Verify nothing changed
    with state:
        assert state.my_attr.read() == 4

    # Try writing
    with state:
        state.my_attr.write(3)
        assert state.my_attr.read() == 3

    # Validate it was committed to a file
    state_2 = get_statefile()
    with pytest.raises(StateNotAcquiredError):
        state_2.my_attr.read()

    with state_2:
        assert state_2.my_attr.read() == 3


def test_reading_uncommitted_attribute():
    state = StateFile()

    # Write the statefile to the system
    with state:
        pass

    # Add an attribute
    state.my_attr = StateAttr(state, "cool_key", default=16)
    with state:
        assert state.my_attr.read() == 16
        assert state.dict == {}
