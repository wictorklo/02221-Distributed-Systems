class Action:
    def __init__(self, speed = 0, direction = 0):
        self.speed = speed
        self.direction = direction


class Drone:
    def __init__(self,networkInterface,xpos = 0, ypos = 0):
        self.networkInterface = networkInterface
        self.xpos = xpos
        self.ypos = ypos

    #method used by simulator
    #get drones current desired physical action
    def getAction(self):
        return Action()

    #give drone computing power
    #this can update action returned by getAction(), put and get messages in and from the network interface 
    def think(self):
        pass

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