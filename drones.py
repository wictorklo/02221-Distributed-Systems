class Action:
    def __init__(self, speed = 0, direction = 0):
        self.speed = speed
        self.direction = direction



class Drone:
    def __init__(self,networkInterface):
        self.networkInterface = networkInterface

    #method used by simulator
    #get drones current desired physical action
    def getAction(self):
        pass

    #give drone computing power
    #this can update action returned by getAction(), put and get messages in and from the network interface 
    def think(self):
        pass

    #give drone sensor data
    def giveSensorData(self,observation):
        self.__updateStateObservation(observation)

    #update current state based on observation
    def __updateStateObservation(self,observation):
        pass

    #update current state based on information in message
    def __updateStateMessage(self,message):
        pass

class ADrone(Drone):
    def __init__(self, networkInterface):
        super().__init__(networkInterface)
        self.type = "A"

class BDrone(Drone):
    def __init__(self, networkInterface):
        super().__init__(networkInterface)
        self.type = "B"