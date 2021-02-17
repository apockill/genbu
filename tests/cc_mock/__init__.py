class FS:
    files = {}

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


class Turtle:
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

class OS:
    pass


turtle = Turtle()
os = OS()
fs = FS()
