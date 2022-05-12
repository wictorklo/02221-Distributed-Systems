import numpy as np
from math import floor
import json

tiletype = np.dtype("u1")

#State is a tile-grid of 1byte numbers. 
#First index is horizontal position and second vertical
#[0][0] is bottom left corner
def emptyMap(xsize,ysize,flammable = False):
    if flammable:
        return np.full((xsize,ysize),1,dtype=tiletype)
    else:
        return np.zeros((xsize,ysize),dtype=tiletype)


#meaning of bits in byte-map:
#1st bit - on for flammable material
#2nd bit - on if area on fire
#... Something that obstructs view? Obstructs communication?

#speed must be at least sqrt(2), otherwise you could just end up in same tile

def isFlammable(tile):
    return (tile & 1)
def isOnFire(tile):
    return (tile & 2) >> 1

def setFlammable(tmap,x,y):
    tmap[x][y] |= 1
def setFire(tmap,x,y):
    tmap[x][y] |= 2

def unsetFlammable(tmap,x,y):
    tmap[x][y] &= ~1
def unsetFire(tmap,x,y):
    tmap[x][y] &= ~2

#TODO: make better printer
def printMap(tilemap,adrones,bdrones): 
    print(np.flipud(np.transpose(tilemap)))
    print("--------DRONES---------")
    for x in range(tilemap.shape[0]):
        for y in range(tilemap.shape[1]):
            if any([floor(d.xpos) == x and floor(d.ypos) == y for d in adrones]):
                print("A", end="")
            elif any([floor(d.xpos) == x and floor(d.ypos) == y for d in bdrones]):
                print("B", end="")
            else:
                print("0", end="")
        print("\n", end="")
    print("--------ADRONES--------")
    for drone in adrones:
        print("x: " + str(drone.xpos) + ", y: " + str(drone.ypos))
    print("--------BDRONES--------")
    for drone in bdrones:
        print("x: " + str(drone.xpos) + ", y: " + str(drone.ypos))


class Action:
    def __init__(self, speed = 0, direction = 0) -> None:
        self.speed = speed
        self.direction = direction

class Observation:
    def __init__(self,observationPayload = None):
        if observationPayload:
            self.loadObservationPayload(observationPayload)
        else:
            self.tiles = []
            self.drones = []

    def loadObservationPayload(self,observationPayload):
        data = json.loads(observationPayload)
        self.tiles = data["tiles"]
        self.drones = data["drones"]

    def getObservationPayload(self):
        observation = {"type" : "observation", "tiles" : self.tiles, "drones" : self.drones}
        return json.dumps(observation)