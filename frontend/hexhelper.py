#!/usr/bin/python
import math
import sys


def get_corners(h):
    """
    Helper method for creating hex images; for given square size, returns the hexagonal points to crop the picture to.
    Finds corners of a regular hexagon inscribed in a square with a point at the midpoint of the top and bottom sides.
    :param h: side length of square
    :return: tuple of 6 tuples, each containing the x and y coordinates of a vertex of the hexagon, starting upper left and going clockwise
    """
    leftmost_x = (h / 4) * (2 - math.sqrt(3))
    rightmost_x = h - leftmost_x
    c1 = (leftmost_x, h / 4)
    c2 = (h / 2, 0)
    c3 = (rightmost_x, h / 4)
    c4 = (rightmost_x, h * 0.75)
    c5 = (h / 2, h)
    c6 = (leftmost_x, h * 0.75)
    return c1, c2, c3, c4, c5, c6


if len(sys.argv) != 2:
    print(f"Usage: {sys.argv[0]} <integer_size>")
    sys.exit(1)

try:
    square_size = int(sys.argv[1])
    cns = get_corners(square_size)
    print(f"corners: {cns}")
except ValueError:
    print("Error: The argument is not a valid integer")
