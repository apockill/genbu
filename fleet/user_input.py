from typing import Callable, List

import numpy as np


def parse_ndarray(n_elements=None) -> Callable[[str], np.ndarray]:
    """Parse a position, in the form of "# # # ..."
    """

    def parser(val: str) -> np.array:
        return np.array(parse_number_list(n_elements=n_elements)(val=val))

    return parser


def parse_number_list(n_elements=None) -> Callable[[str], List[int]]:
    def parser(val: str):
        position = list(map(int, val.split(" ")))
        if n_elements is not None:
            assert len(position) == n_elements, \
                f"The position must be {n_elements} elements!"
        return position

    return parser
