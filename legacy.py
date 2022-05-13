#this file contains previous versions of the system, for testing improvements and tolerance to new scenarios
#should be kept up to date with regards to the simulator, but not scripts
from collections import deque
import json

class Message:
    def __init__(self,transmit = None):
        if transmit:
            self.loadTransmit(transmit)
        else:
            self.data = {}

    def loadTransmit(self,transmit):
        self.data = json.loads(transmit)

    def getTransmit(self):
        return json.dumps(self.data)

class FloodMessage(Message):
    def autoComplete(self,DroneID,ttl,seq):
        if not 'source' in self.data:
            self.data['source'] = DroneID
        if not 'ttl' in self.data:
            self.data['ttl'] = ttl
        if not 'seq' in self.data:
            self.data['seq'] = seq

class PayloadFloodMessage(FloodMessage):
    def autoComplete(self,DroneID,ttl,seq):
        super().autoComplete(DroneID,ttl,seq)
        self.data['type'] = 'payload'

class AckFloodMessage(FloodMessage):
    def autoComplete(self,DroneID,ttl,seq):
        super().autoComplete(DroneID,ttl,seq)
        self.data['type'] = 'ack'

class BufferMessage:
    # Types
    # 1 - Sent message, awaiting acknowledgement
    def __init__(self, ID, type, message : 'Message', timeRemaining, retries):
        self.ID = ID
        self.type = type
        self.message = message
        self.message.data["seq"] = self.ID
        self.timeRemaining = timeRemaining
        self.retries = retries
    
    def decay(self):
        self.timeRemaining -= 1
        resend = self.timeRemaining <= 0
        return resend and self.retries >= 1 

class NetworkInterface:
    def __init__(self, ID, defaultTTL = 5, defaultTimeout = 20, defaultRetries = 3):
        self.seq = 0
        self.ID = ID
        self.outGoing : 'deque[Message]'= deque()
        self.inComing = deque()
        self.log  : 'deque[Message]' = deque()
        self.timeouts : 'dict[int,BufferMessage]' = {} # seq -> BufferMessage
        self.defaultTTL = defaultTTL
        self.defaultTimout = defaultTimeout
        self.defaultRetries = defaultRetries

    def tick(self):
        expired = []
        for key in self.timeouts:
            bm = self.timeouts[key]
            if bm.decay():
                #Resend message with lower retry
                self.sendMessage(bm.message)
            if bm.retries <= 0:
                expired.append(bm.ID)
        for e in expired:
            del self.timeouts[e]


    #method used by associated drone
    #sends a message to one or other drones
    #destination might be identity of one other drone, gps area, nearest type A drone, etc etc
    def sendMessage(self, message : 'FloodMessage', timeout = None, retries = None):
        message.autoComplete(self.ID,self.defaultTTL,self.seq)
        if message.data['seq'] == self.seq:
            self.seq += 1

        self.outGoing.append(message.getTransmit())

        if message.data['seq'] in self.timeouts:
            self.timeouts[message.data['seq']].retries -= 1

        elif message.data["type"] == "payload":
            if timeout == None:
                timeout = self.defaultTimout
            if retries == None:
                retries = self.defaultRetries
            bufferedMessage = BufferMessage(message.data['seq'], "1", message, timeout, retries)
            self.timeouts[message.data['seq']] = bufferedMessage

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
        message = Message(transmit)
        if message.data["destination"] == self.ID:
            if message.data["type"] == "payload":
                self.__sendAck(message)
                if (not any(l.data["seq"] == message.data["seq"] and l.data["source"] == message.data["source"] for l in self.log)):
                    self.log.append(message)
                    self.inComing.append(message.data["payload"])
            elif message.data["type"] == "ack":
                if message.data["seq"] in self.timeouts:
                    del self.timeouts[message.data["seq"]]

        elif "ttl" in message.data and message.data["ttl"] > 0: #bounce on if meant to someone else and not expired
            message = FloodMessage(transmit) #reload as flood message
            message.data["ttl"] -= 1
            self.sendMessage(message)

    #message used by simulator
    #gets message interface wants broadcasted
    def getOutgoing(self):
        if self.outGoing:
            return self.outGoing.popleft()
        else:
            return None

    def __sendAck(self,message : 'Message'):
        ack = AckFloodMessage()
        ack.data = {
            "destination": message.data["source"],
            "seq" : message.data["seq"]
            }
        self.sendMessage(ack)
