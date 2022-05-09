import json
from network_interfaces import *
from environment import emptyMap

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
        observation = {"tiles" : self.tiles, "drones" : self.drones}
        return json.dumps(observation)

class Drone:
    def __init__(self, networkInterface : 'NetworkInterface', initialMap, xpos = 0, ypos = 0):
        self.networkInterface = networkInterface
        self.ID = networkInterface.ID
        self.map = initialMap
        self.xpos = xpos
        self.ypos = ypos

    #method used by simulator
    #get drones current desired physical action
    def getAction(self):
        return Action()

    #give drone computing power
    #this can update action returned by getAction(), put and get messages in and from the network interface 
    def think(self):
        while True:
            m = self.networkInterface.getIncoming()
            if not m:
                break

            

    #give drone sensor data
    def giveSensorData(self,observation):
        self.__updateStateObservation(observation)

    def getPosition(self):
        return (self.xpos,self.ypos)

    #update current state based on observation
    def __updateStateObservation(self,observation):
        pass

    #update current state based on information in message
    def __updateStateMessage(self,message):
        pass

class ADrone(Drone):
    def __init__(self, networkInterface,xpos = 0, ypos = 0):
        super().__init__(networkInterface,xpos,ypos)
        self.type = "A"

class BDrone(Drone):
    def __init__(self, networkInterface,xpos = 0, ypos = 0):
        super().__init__(networkInterface,xpos,ypos)
        self.type = "B"