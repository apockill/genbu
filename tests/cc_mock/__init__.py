from copy import deepcopy


class FS:
    def __init__(self):
        self.files = {}

    class ReadHandler:
        def __init__(self, filename):
            self._filename = filename

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            pass

        def readAll(self):
            return fs.files[self._filename]

    class WriteHandler:
        def __init__(self, filename):
            self._filename = filename

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            pass

        def write(self, to_write):
            assert isinstance(to_write, str)
            fs.files[self._filename] = to_write

    def exists(self, file):
        assert isinstance(file, str)

    def open(self, file, mode):
        assert mode in ["w", "r"]
        assert isinstance(file, str)
        if mode == "w":
            return self.WriteHandler(file)
        else:
            return self.ReadHandler(file)


MOCK_INSPECT_VAL = {
    b"state": {b"facing": b"south", b"waterlogged": False},
    b"name": b"boring-mod:boring-block",
    b"tags": {}}


class Turtle:
    __boring_inspect_val = deepcopy(MOCK_INSPECT_VAL)
    """The value for inspect*() functions. Those functions are to be 
    mocked if any tests are to be done on them. 
    """

    def digUp(self):
        pass

    def digDown(self):
        pass

    def dig(self):
        pass

    def up(self):
        pass

    def down(self):
        pass

    def turnLeft(self):
        pass

    def turnRight(self):
        pass

    def forward(self):
        pass

    def back(self):
        pass

    def inspect(self):
        return self.__boring_inspect_val

    def inspectUp(self):
        return self.__boring_inspect_val

    def inspectDown(self):
        return self.__boring_inspect_val


class OS:
    def getComputerID(self):
        return 0


class GPS:
    def locate(self):
        return (0, 0, 0)


turtle = Turtle()
os = OS()
fs = FS()
gps = GPS()
