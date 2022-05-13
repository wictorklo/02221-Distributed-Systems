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

class SingleStepMessage(FloodMessage):
    def autoComplete(self,DroneID,ttl,seq):
        super().autoComplete(DroneID, 1, seq)

class PingMessage(SingleStepMessage):
    def autoComplete(self,DroneID,ttl,seq):
        super().autoComplete(DroneID, ttl, seq)
        self.data['type'] = 'ping'

class AckPingMessage(SingleStepMessage):
    def autoComplete(self,DroneID,ttl,seq):
        super().autoComplete(DroneID, ttl, seq)
        self.data['type'] = 'ack'


class BufferMessage:
    # Types
    # 1 - Sent message, awaiting acknowledgement
    # 2 - Sent ping, awaiting response
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
        self.defaultTimeout = defaultTimeout
        self.defaultRetries = defaultRetries
        #TEMPORARY - REPLACE WITH ROUTING TABLE LATER
        self.neighbours = set()

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
                timeout = self.defaultTimeout
            if retries == None:
                retries = self.defaultRetries
            bufferedMessage = BufferMessage(message.data['seq'], "1", message, timeout, retries)
            self.timeouts[message.data['seq']] = bufferedMessage
        
        elif message.data["type"] == "ping":
            self.neighbours = set()
            if timeout == None:
                timeout = self.defaultTimeout
            if retries == None:
                retries = self.defaultRetries
            bufferedMessage = BufferMessage(message.data['seq'], "2", message, timeout, retries)
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
        if message.data["type"] == "ping" and not message.data["source"] == self.ID:
                self.__sendAck(message)
        elif message.data["destination"] == self.ID:
            if message.data["type"] == "payload":
                self.__sendAck(message)
                if (not any(l.data["seq"] == message.data["seq"] and l.data["source"] == message.data["source"] for l in self.log)):
                    self.log.append(message)
                    self.inComing.append(message.data["payload"])
            elif message.data["type"] == "ack":
                if message.data["seq"] in self.timeouts:
                    if self.timeouts[message.data["seq"]].type == "2":
                        self.neighbours.add(message.data["source"])
                    else:
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
        ack = Message()
        match message.data["type"]:
            case "payload":
                ack = AckFloodMessage()
            case "ping":
                ack = AckPingMessage()
        ack.data = {
            "destination": message.data["source"],
            "seq" : message.data["seq"]
        }
        self.sendMessage(ack)
