import numpy as np
import math

#add an offset in a given direction and of a given magnitude to input vector
#direction is 0 for north, pi/2 for west, pi for south and so on
def movePosition(x,y,size,dir):
    return (x - size * math.sin(dir),y + size * math.cos(dir))

#get direction of arrow pointing from first vector to second
#north if |v2-v1|=0
def calculateDirection(v1,v2):
    x = v2[0] - v1[0]
    y = v2[1] - v1[1]
    if x == 0 and y == 0:
        return 0

    s = 1 / math.sqrt(x * x + y * y)

    rad1 = math.acos(s * y)
    if x < 0:
        return rad1#add pi/2 to make 0 northwards
    else: #if y is negative, flip the cos that is found by acos
        return (2 * math.pi - rad1)

# Given a dict of (ID -> ID set) return ID list of shortest path from start to end
def route(startID, endID, routingTable):
    if startID == endID:
        return []
    queue = [startID]
    visited = []
    parents = {}
    while queue and not endID in parents.keys():
        cur = queue.pop(0)
        visited.append(cur)
        for n in routingTable[cur]:
            if not n in visited and not n in queue:
                parents[n] = cur
                if n == endID:
                    break
                queue.append(n)
    
    if not endID in parents.keys():
        return None
    node = endID
    path = [node]
    while not node == startID:
        parent = parents[node]
        path.append(parent)
        node = parent
    return path[::-1]

def distance(x1,y1,x2,y2):
    x = x2 - x1
    y = y2 - y1
    return math.sqrt(x * x + y * y)



    
