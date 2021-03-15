"""This module will be used to keep track of different types of blocks that
are useful for things.

Each list of a list of regex matches for block names
"""
from typing import List, Union
import re

do_not_mine = [
    r"computercraft:.*",
    # Never ever ever mine anything with the word 'chest' in it!
    r".*chest.*"
]
"""This is a list of items a turtle should never mine, under any circumstance.
"""


def name_matches_regexes(block_name: Union[bytes, str], regex_list: List[str]):
    combined_regex = '(?:% s)' % '|'.join(regex_list)
    if isinstance(block_name, bytes):
        block_name = str(block_name, encoding="utf-8")
    return re.match(combined_regex, block_name)
