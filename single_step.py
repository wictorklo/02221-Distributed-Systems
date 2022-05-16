from numpy import broadcast
from messages import *
from collections import deque

class SingleStepNI:
    def __init__(self,
            ID : 'str', neighbours, sendPrimitive):
        self.ID = ID
        self.neighbours = neighbours
        self.sendPrimitive = sendPrimitive
        self.incoming = deque()
        self.broadcastLog = set()
        self.seq = 1

    def sendPayloadMessage(self, message : 'PayloadSSMessage'):
        self.__sendMessage(message)

    def broadcast(self, message : 'BroadcastMessage'):
        self.__sendMessage(message)

    def ping(self):
        self.neighbours = set()
        message = PingSSMessage()
        self.__sendMessage(message)

    def receiveMessage(self, message : 'SSMessage'):
        if not message.data["source"] in self.neighbours:
            self.neighbours.add(message.data["source"])
        if message.data["type"] == "ping":
            message = PongSSMessage()
            self.__sendMessage(message)
        if message.data["type"] == "payload" and message.data["destination"] == self.ID:
            self.incoming.append(message.data["payload"])
        if (message.data["type"] == "broadcast" and 
                not (message.data["source"],message.data["seq"]) in self.broadcastLog):
            self.broadcastLog.add((message.data["source"],message.data["seq"]))
            self.incoming.append(message.data["payload"])
            self.__sendMessage(message)
        

    def __sendMessage(self, message : 'SSMessage'):
        message.autoComplete(self.ID,self.seq)
        if message.data["source"] == self.ID and message.data["seq"] == self.seq:
            self.seq += 1
        self.sendPrimitive(message.getTransmit())