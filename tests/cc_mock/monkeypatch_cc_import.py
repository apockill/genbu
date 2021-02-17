import sys

# Do an import hack to set the cc library to be the mock library
import tests.cc_mock

sys.modules["cc"] = tests.cc_mock
