import numpy as np
import math

#add an offset in a given direction and of a given magnitude to input vector
#direction is 0 for north, pi/2 for east, pi for south and so on
def movePosition(x,y,size,dir):
    return (x + size * math.sin(dir),y + size * math.cos(dir))