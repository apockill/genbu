import random

import pytest

from tests.cc_mock import monkeypatch_cc_import
from tests import cc_mock as cc


@pytest.fixture(autouse=True)
def each_test_setup_teardown():
    random.seed("3")

    # Clear turtles "filesystem"
    cc.FS.files = {}

    yield
