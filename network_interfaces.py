from collections import deque
import json

from messages import *
from dynamic_routing import DynamicRoutingNI
from single_step import SingleStepNI

class NetworkInterface:
    def __init__(self, 
            ID : 'str', routingTable, infoTable,
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
            ID, self.singleStepNI, routingTable, infoTable,
            defaultTimeoutOrigin = defaultTimeoutOrigin, 
            defaultTimeoutRouting = defaultTimeoutRouting,
            defaultRetriesOrigin = defaultRetriesOrigin, 
            defaultRetriesRouting = defaultRetriesRouting,
            defaultPingTimeout = defaultPingTimeout
        )
        
    def tick(self):
        self.dynamicRoutingNI.tick()
        self.__stabilizeIncoming()

    #method used by associated drone
    #sends a message to one or more other drones
    def sendMessage(self, message : 'Message'):
        if not "protocol" in message.data:
            return "NoProtocol"
        if message.data["protocol"] == "DynamicRouting":
            return self.dynamicRoutingNI.sendPayloadMessage(message)
        elif message.data["protocol"] == "SingleStep":
            return self.singleStepNI.sendPayloadMessage(message)
    
    #method used by associated drone
    #returns a message meant for the drone:
    def getIncoming(self):
        if self.incoming:
            message = self.incoming.popleft()
            return message
        else:
            return None

    #method used by simulator 
    #gives interface message from network
    def receiveMessage(self,transmit):
        message = Message(transmit)
        if not "protocol" in message.data or message.data["protocol"] != "SingleStep":
            return
        ssMessage = SSMessage(transmit)
        self.singleStepNI.receiveMessage(ssMessage)
        self.__stabilizeIncoming()

    #message used by simulator
    #gets message interface wants broadcasted
    def getOutgoing(self):
        if self.outgoing:
            return self.outgoing.popleft()
        else:
            return None

    def __stabilizeIncoming(self):
        while self.dynamicRoutingNI.incoming or self.singleStepNI.incoming:
            if self.dynamicRoutingNI.incoming:
                transmit = self.dynamicRoutingNI.incoming.popleft()
                self.__tryReceiveMessage(transmit)
            if self.singleStepNI.incoming:
                transmit = self.singleStepNI.incoming.popleft()
                self.__tryReceiveMessage(transmit)
    
    def __tryReceiveMessage(self,transmit):
        try:
            jsn = json.loads(transmit)
        except json.JSONDecodeError:
            self.incoming.append(transmit)
            return
        if not type(jsn) is dict or "protocol" not in jsn:
            self.incoming.append(transmit)
            return
        message = Message(transmit)
        if message.data["protocol"] == "SingleStep":
            ssMessage = SSMessage(transmit)
            self.singleStepNI.receiveMessage(ssMessage)
        elif message.data["protocol"] == "DynamicRouting":
            drMessage = DRMessage(transmit)
            self.dynamicRoutingNI.receiveMessage(drMessage)