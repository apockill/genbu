import random
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from tests.cc_mock import monkeypatch_cc_import
from tests import cc_mock as cc
from fleet import state


@pytest.fixture(autouse=True)
def each_test_setup_teardown():
    random.seed("3")

    # Clear turtles "filesystem"
    cc.fs.files = {}

    # Set the statefile writing location
    old_statefile_directory = state.STATE_DIR
    with TemporaryDirectory() as temp_state_dir:
        state.STATE_DIR = Path(temp_state_dir)
        yield

    state.STATE_DIR = old_statefile_directory
