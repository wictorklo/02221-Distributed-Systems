from messages import *


class SingleStepNI:
    def __init__(self,
            ID : 'str', neighbours, sendPrimitive,
            defaultTimeout = 3, defaultRetries = 5):
        self.ID = ID
        self.neighbours = neighbours
        self.sendPrimitive = sendPrimitive
        self.timeouts = {}
        self.timeoutHandlers = {}
        self.retries = {}
        self.broadcastLog = set()
        self.defaultTimeout = defaultTimeout
        self.defaultRetries = defaultRetries

    def sendPayloadMessage(self, message : 'PayloadSSMessage'):
        pass

    def broadcast(self, message : 'BroadcastMessage'):
        pass

    def ping(self):
        pass

    def receiveMessage(self, message : 'SSMessage'):
        pass
