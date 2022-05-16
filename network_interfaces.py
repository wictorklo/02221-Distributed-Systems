from collections import deque
import json
from messages import *
from dynamic_routing import DynamicRoutingNI
from single_step import SingleStepNI

class NetworkInterface:
    def __init__(self, 
            ID : 'str', routingTable,
            defaultTimeoutOrigin = 100, defaultTimeoutRouting = 20,
            defaultRetriesOrigin = 5, defaultRetriesRouting = 3,
            defaultPingTimeout = 6):
        self.seq = 0
        self.ID = ID
        self.outgoing : 'deque[str]'= deque()
        self.incoming = deque()

        sendPrimitive = lambda transmit : self.outgoing.append(transmit)
        self.singleStepNI = SingleStepNI(
            self.ID, routingTable[self.ID], sendPrimitive
        )
        self.dynamicRoutingNI = DynamicRoutingNI(
            ID, self.singleStepNI, routingTable,
            defaultTimeoutOrigin = defaultTimeoutOrigin, 
            defaultTimeoutRouting = defaultTimeoutRouting,
            defaultRetriesOrigin = defaultRetriesOrigin, 
            defaultRetriesRouting = defaultRetriesRouting,
            defaultPingTimeout = defaultPingTimeout
        )
        
    def tick(self):
        self.dynamicRoutingNI.tick()
        while self.dynamicRoutingNI.incoming or self.singleStepNI.incoming:
            if self.dynamicRoutingNI.incoming:
                self.incoming.append(self.dynamicRoutingNI.incoming.popleft())
            if self.singleStepNI.incoming:
                self.incoming.append(self.singleStepNI.incoming.popleft())

    #method used by associated drone
    #sends a message to one or more other drones
    def sendMessage(self, message : 'Message'):
        if not "protocol" in message.data:
            return "NoProtocol"
        if message.data["protocol"] == "DynamicRouting":
            pass
    
    #method used by associated drone
    #returns a message meant for the drone:
    def getIncoming(self):
        if self.inComing:
            message = self.inComing.popleft()
            return message
        else:
            return None

    #method used by simulator 
    #gives interface message from network
    def receiveMessage(self,transmit):
        pass

    #message used by simulator
    #gets message interface wants broadcasted
    def getOutgoing(self):
        if self.outGoing:
            return self.outGoing.popleft()
        else:
            return None