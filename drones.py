import json
from math import floor
from network_interfaces import *
from environment import *
import copy
import math
import random as rnd

from util import calculateDirection


class Drone:
    def __init__(self, networkInterface : 'NetworkInterface', initialMap, xpos = 0, ypos = 0):
        self.networkInterface = networkInterface
        self.ID = networkInterface.ID
        self.map = copy.deepcopy(initialMap)
        self.otherDrones = [] #map from droneid to (type,x,y)
        self.xpos = xpos
        self.ypos = ypos

    #method used by simulator
    #get drones current desired physical action
    def getAction(self):
        return Action()

    #give drone computing power
    #this can update action returned by getAction(), put and get messages in and from the network interface 
    def think(self):
        self.networkInterface.tick()
        self.networkInterface.dynamicRoutingNI.newPosition(self.xpos,self.ypos)
        while True:
            payload = self.networkInterface.getIncoming()
            if not payload:
                break
            
            data = json.loads(payload)
            if data["type"] == "observation":
                print("")
                print("got got")
                observation = Observation(payload) 
                self.__updateStateObservation(observation)

    #give drone sensor data
    def giveSensorData(self,observation):
        self.__updateStateObservation(observation)

    def getPosition(self):
        return (self.xpos,self.ypos)

    #update current state based on observation
    def __updateStateObservation(self,observation : 'Observation'):
        for tilestate, x, y in observation.tiles:
            self.map[x][y] = tilestate
        for droneID, droneType, x, y in observation.drones:
            self.otherDrones[droneID] = (droneType,x,y)
        

class ADrone(Drone):
    def __init__(self, networkInterface,initialMap,xpos = 0, ypos = 0):
        super().__init__(networkInterface,initialMap,xpos,ypos)
        self.type = "A"

    def getAction(self):
        #bfs for closest fire
        considered = set()
        frontier = deque()
        considered.add((floor(self.xpos),floor(self.ypos)))
        frontier.append((floor(self.xpos),floor(self.ypos)))
        while frontier:
            x, y = frontier.popleft()
            if isOnFire(self.map[x][y]):
                break

            for xd, yd in [(-1,0),(0,-1),(1,0),(0,1)]:
                x1, y1 = (x + xd, y + yd)
                if (not (x1, y1) in considered and
                        x1 >= 0 and x1 < self.map.shape[0] and 
                        y1 >= 0 and y1 < self.map.shape[1]):
                    considered.add((x1,y1))
                    frontier.append((x1,y1))
        else:
            return Action()
        return Action(speed = 1, direction = calculateDirection(self.getPosition(),(x,y)))

class BDrone(Drone):
    def __init__(self, networkInterface, initialMap, xpos = 0, ypos = 0, drunkWalk = False):
        super().__init__(networkInterface,initialMap,xpos,ypos)
        self.type = "B"
        self.drunkWalk = drunkWalk

    def getAction(self):
        if self.drunkWalk:
            return Action(speed = 1, direction = rnd.random() * 2 * math.pi)
        else:
            return Action()

    def giveSensorData(self, observation):
        super().giveSensorData(observation)
        #TODO send info about fire to close type A drones