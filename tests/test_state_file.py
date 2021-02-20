import pytest

from fleet import StateNotAcquiredError, StateFile, StateAttr, Map


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


def test_adding_attr_commits_to_filesystem():
    """Test adding a StateAttr adds it to the dict"""
    state = StateFile()
    with state:
        assert state.dict == {}

    state.map = StateAttr(state_file=state,
                          key_name="map",
                          default=Map(position=(0, 0, 0), direction=90))
    SERIALIZED_MAP = state.map.default.to_dict()

    with state:
        assert state.dict == {"map": SERIALIZED_MAP}


def test_changing_defaults_doesnt_autocommit_to_file():
    """Ensure that changing the defaults doesn't change the value written in
    the file"""
    state = StateFile()
    state.coolkey = StateAttr(state_file=state,
                              key_name="cool_key",
                              default=3)
    with pytest.raises(StateNotAcquiredError):
        state.coolkey.read()

    with state:
        assert state.coolkey.read() == 3

    # Now create a new statefile with a DIFFERENT default, and make sure that
    # didn't get written to the file
    state = StateFile()
    state.coolkey = StateAttr(state_file=state,
                              key_name="cool_key",
                              default=420)
    with state:
        assert state.coolkey.read() == 3
