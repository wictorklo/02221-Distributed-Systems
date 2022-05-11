from math import floor
import numpy as np
import random as rnd
from drones import *
from script import *
from util import *
from environment import *

class Simulator:
    def __init__(self,
            initialState, script : 'Script',
            ADrones : 'list[ADrone]', BDrones : 'list[BDrone]',
            spreadChance = 0.3, burnoutChance = 0.04, ASpeed = 3, BSpeed = 3, lineOfSight = 4, 
            transmissionDistance = 4, transmissionsPerTurn = 100):

        self.map = initialState 

        self.ADrones = ADrones
        self.BDrones = BDrones
        self.droneMap : 'dict[int,Drone]' = {}
        for drone in ADrones + BDrones:
            self.droneMap[drone.ID] = drone

        self.script = script
        self.turns = 0
        self.spreadChance = spreadChance
        self.burnoutChance = burnoutChance
        self.ASpeed = ASpeed
        self.BSpeed = BSpeed
        self.lineOfSight = lineOfSight 
        self.transmissionDistance = transmissionDistance
        self.transmissionsPerTurn = transmissionsPerTurn

    def performTurn(self):
        shouldContinue = self.__performScriptedAction()
        if not shouldContinue:
            return

        self.__exstinguishFire()
        self.__spreadFire()
        self.__moveDrones()
        self.__droneObservations()
        self.__thinkAndSendMessages()
        self.turns += 1

    def __performScriptedAction(self):
        self.map, self.ADrones, self.BDrones, shouldContinue = self.script.performScriptedAction(self.map, self.ADrones, self.BDrones)
        return shouldContinue 

    def __exstinguishFire(self):
        for drone in self.ADrones: 
            for xd, yd in np.ndindex((3,3)):
                x = drone.xpos + xd - 1
                y = drone.ypos + yd - 1
                if (x >= 0 and x < self.map.shape[0] and
                        y >= 0 and y < self.map.shape[1]):
                    x = floor(x)
                    y = floor(y)
                    unsetFire(self.map,x,y)

    def __spreadFire(self):
        spreadmap = np.zeros(self.map.shape,dtype=tiletype)
        for x, y in np.ndindex(self.map.shape): 
            if isOnFire(self.map[x,y]): #if tile is on fire
                if rnd.random() <= self.burnoutChance:
                    unsetFire(self.map,x,y)
                    unsetFlammable(self.map,x,y)
                    continue
                for xd, yd in np.ndindex((3,3)): #for all neighbours
                    x1 = x + xd - 1 #subtract 1 to consider range [-1,0,1]
                    y1 = y + yd - 1
                    if (x1 >= 0 and x1 < self.map.shape[0] and #if neighbour is on map
                            y1 >= 0 and y1 < self.map.shape[1] and 
                            isFlammable(self.map[x1][y1]) and #and neighbour is flammable
                            rnd.random() <= self.spreadChance): #and the fire spreads according to dice
                        setFire(spreadmap,x1,y1) #then put neighbour on fire
        self.map = np.bitwise_or(self.map,spreadmap)
                

    def __moveDrones(self):
        drones : 'list[Drone]' = self.ADrones + self.BDrones
        for drone in drones:
            maxSpeed = (self.ASpeed if drone.type == "A" else self.BSpeed)
            action = drone.getAction()
            x, y = movePosition(drone.xpos,drone.ypos,action.speed * maxSpeed,action.direction)
            x = min(max(0,x),self.map.shape[0] - 0.00001)
            y = min(max(0,y),self.map.shape[1] - 0.00001)
            drone.xpos = x
            drone.ypos = y
            
    def __droneObservations(self):
        drones : 'list[Drone]' = self.ADrones + self.BDrones
        for drone in drones:
            observation = Observation()
            for xd, yd in np.ndindex(2 * self.lineOfSight + 1, 2 * self.lineOfSight + 1):
                x = floor(drone.xpos - self.lineOfSight + xd)
                y = floor(drone.ypos - self.lineOfSight + yd)
                if (x >= 0 and x < self.map.shape[0] and 
                        y >= 0 and y < self.map.shape[1]):
                    observation.tiles.append((self.map[x][y],x,y))
            drone.giveSensorData(observation)

    def __thinkAndSendMessages(self):
        transmissionMap : 'dict[int,set[int]]' = {}
        drones : 'list[Drone]' = self.ADrones + self.BDrones
        for drone in drones:
            transmissionMap[drone.ID] = set()

        for i in range(len(drones)):
            for j in range(i + 1,len(drones)):
                if (abs(drones[i].xpos - drones[j].xpos) <= self.transmissionDistance and
                        abs(drones[i].ypos - drones[j].ypos) <= self.transmissionDistance):
                    transmissionMap[drones[i].ID].add(drones[j].ID)
                    transmissionMap[drones[j].ID].add(drones[i].ID)

        for i in range(self.transmissionsPerTurn):
            for drone in drones:
                drone.think()
                transmit = drone.networkInterface.getOutgoing()
                if transmit:
                    for ID in transmissionMap[drone.ID]:
                        self.droneMap[ID].networkInterface.receiveMessage(transmit)
        