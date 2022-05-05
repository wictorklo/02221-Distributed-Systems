import numpy as np
import random as rnd
from drones import *
from util import *

tiletype = np.dtype("u1")

def emptyMap(xsize,ysize):
    return np.zeros((xsize,ysize),dtype=tiletype)

#State is a tile-grid of 1byte numbers. 
#First index is horizontal position and second vertical
#[0][0] is bottom left corner

#meaning of bits in byte-map:
#1st bit - on for flammable material
#2nd bit - on if area on fire
#... Something that obstructs view? Obstructs communication?

def isFlammable(tile):
    return (tile & 1)
def isOnFire(tile):
    return (tile & 2) >> 1

class Simulator:
    def __init__(self,
            initialState,script,
            ADrones,BDrones,
            spreadChance = 0.5,ASpeed = 3,BSpeed = 3):
        self.map = initialState 
        self.ADrones = ADrones
        self.BDrones = BDrones
        self.script = script
        self.turns = 0
        self.spreadChance = spreadChance
        self.ASpeed = ASpeed
        self.BSpeed = BSpeed

    def performTurn(self):
        shouldContinue = self.__performScriptedAction()
        if not shouldContinue:
            return

        self.__exstinguishFire()
        self.__spreadFire()
        self.__moveDrones()
        self.__sendMessages()
        self.turns += 1

    def __performScriptedAction(self):
        pass

    def __exstinguishFire(self):
        for drone in self.ADrones: #This nesting fucking sucks, change later
            for xd in [-1,0,1]:
                x = drone.xpos + xd
                if x >= 0 and x < self.map.shape[0]:
                    for yd in [-1,0,1]:
                        y = drone.ypos + yd
                        if y >= 0 and y < self.map.shape[1]:
                            self.map[x][y] &= ~2

    def __spreadFire(self):
        for x, y in np.ndindex(self.map.shape): 
            if self.map[x,y] & 2:
                for xd in [-1,0,1]:
                    x1 = x + xd
                    if x1 >= 0 and x1 < self.map.shape[0]:
                        for yd in [-1,0,1]:
                            y1 = y + yd
                            if y1 >= 0 and y1 < self.map.shape[1] and rnd.random() <= self.spreadChance:
                                self.map[x1][y1] |= 2
                

    def __moveDrones(self):
        for drone in self.ADrones + self.BDrones:
            maxSpeed = self.ASpeed if drone.type == "A" else self.BSpeed
            action = drone.getAction()
            x, y = movePosition(drone.xpos,drone.ypos,action.speed * maxSpeed,action.direction)
            x, y = round(x), round(y)
            x = min(max(0,x),self.map.shape[0])
            y = min(max(0,y),self.map.shape[1])
            drone.xpos = x
            drone.ypos = y
            

    def __sendMessages(self):
        pass