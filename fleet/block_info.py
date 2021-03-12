"""This module will be used to keep track of different types of blocks that
are useful for things.

Each list of a list of regex matches for block names
"""

do_not_mine = [
    r"computercraft:.*",
    # Never ever ever mine anything with the word 'chest' in it!
    r".*chest.*"
]
"""This is a list of items a turtle should never mine, under any circumstance.
"""
