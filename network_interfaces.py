class NWInterface:
    def __init__(self):
        self.outGoing = []
        self.inComing = []

    #method used by associated drone
    #sends a message to one or other drones
    #destination might be identity of one other drone, gps area, nearest type A drone, etc etc
    def sendMessage(self,destination,payload):
        self.outGoing.append(self.__constructMessage(destination,payload))

    #method used by associated drone
    #returns a message meant for the drone:
    def getPayload(self):
        pass

    #method used by simulator 
    #gives interface message from network
    def receiveMessage(self,message):
        self.inComing.append(message)

    #message used by simulator
    #gets message interface wants broadcasted
    def getMessage(self):
        self.outGoing.pop(0)

    #construct new message 
    def __constructMessage(self,destination,payload):
        pass