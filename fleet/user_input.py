from typing import Callable, Tuple

import numpy as np


def parse_position(n_elements=None) -> Callable[[str], np.ndarray]:
    """Parse a position, in the form of "# # # ..."
    """

    def parser(val: str) -> np.array:
        position = list(map(int, val.split(" ")))
        assert len(position) == n_elements, \
            f"The position must be {n_elements} elements!"
        return np.array(position)

    return parser
