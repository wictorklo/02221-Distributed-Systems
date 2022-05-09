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

class NetworkInterface:
    def __init__(self,ID):
        self.ID = ID
        self.outGoing = deque()
        self.inComing = deque()
        self.inbox = deque()

    #method used by associated drone
    #sends a message to one or other drones
    #destination might be identity of one other drone, gps area, nearest type A drone, etc etc
    def sendMessage(self,message : 'Message'):
        self.outGoing.append(message.getTransmit())

    #method used by associated drone
    #returns a message meant for the drone:
    def getIncoming(self):
        if self.inComing:
            message = self.inComing.popleft()
            self.inbox.append(message)
            return message
        else:
            return None

    #method used by simulator 
    #gives interface message from network
    def receiveMessage(self,transmit):
        message = Message(transmit)
        if message.data["destination"] == self.ID:
            if message.data["mtype"] == "payload":
                self.inComing.append(message.data["payload"])
                #Send ACK
                ack = Message()
                ack.data = {
                    "source": self.ID,
                    "destination": message.data["source"],
                    "mtype": "ack",
                    "ttl": 5
                    }
                self.sendMessage(ack)
        elif message.data["ttl"] > 0: #bounce on if meant to someone else and not expired
            message.data["ttl"] -= 1
            self.sendMessage(message)

    #message used by simulator
    #gets message interface wants broadcasted
    def getOutgoing(self):
        if self.outGoing:
            return self.outGoing.popleft()
        else:
            return None