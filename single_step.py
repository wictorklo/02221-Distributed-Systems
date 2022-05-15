from messages import *
from collections import deque()

class SingleStepNI:
    def __init__(self,
            ID : 'str', neighbours, sendPrimitive):
        self.ID = ID
        self.neighbours = neighbours
        self.sendPrimitive = sendPrimitive
        self.incoming = deque()
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

    def __sendMessage(self, message : 'SSMessage'):
        message.autoComplete(self.ID,)