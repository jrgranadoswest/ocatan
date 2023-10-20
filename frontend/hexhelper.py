#!/usr/bin/python
# Takes single integer argument, representing side length of square with 
# regular hexagon inside, with two vertices at the top and bottom midpoints of 
# the square
# Returns the coordinates of the 6 hexagon vertices, starting upper left and 
# going clockwise
import math
import sys

def get_corners(h):
    leftmost_x = (h/4)*(2-math.sqrt(3))
    rightmost_x = h-leftmost_x
    c1 = (leftmost_x, h/4)
    c2 = (h/2, 0)
    c3 = (rightmost_x, h/4)
    c4 = (rightmost_x, h*0.75)
    c5 = (h/2, h)
    c6 = (leftmost_x, h*0.75)
    return (c1, c2, c3, c4, c5, c6)

if len(sys.argv) != 2:
    print(f"Usage: {sys.argv[0]} <integer_size>")
    sys.exit(1)

try:
    square_size = int(sys.argv[1])
    cns = get_corners(square_size)
    print(f"corners: {cns}")
except ValueError:
    print("Error: The argument is not a valid integer")
