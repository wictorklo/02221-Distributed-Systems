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

class BufferMessage:
    # Types
    # 1 - Sent message, awaiting acknowledgement
    def __init__(self, ID, type, message, timeRemaining = 0, retries = 0):
        self.ID = ID
        self.type = type
        self.message = message
        self.timeRemaining = timeRemaining
        self.retries = retries
    
    def decay(self):
        self.timeRemaining -= 1
        resend = self.timeRemaining <= 0
        if resend:
            self.retries -= 1
        return resend and self.retries >= 0 

class NetworkInterface:
    def __init__(self,ID):
        self.seq = 0
        self.ID = ID
        self.outGoing = deque()
        self.inComing = deque()
        self.log = deque()
        self.timeouts = {} # seq -> BufferMessage

        self.timeoutHandlers = {
            "1": lambda bm : self.sendMessage(bm.message, bm.retries-1, bm.ID) # 1 - No ack received. Retry.
        }

    def tick(self):
        expired = []
        for key in self.timeouts:
            bm = self.timeouts[key]
            if bm.decay():
                #Resend message with lower retry
                self.timeoutHandlers[bm.type](bm)
            expired.append(bm.ID)
        for e in expired:
            del self.timeouts[e]


    #method used by associated drone
    #sends a message to one or other drones
    #destination might be identity of one other drone, gps area, nearest type A drone, etc etc
    def sendMessage(self, message : 'Message', retries = 2, seq = None):
        if seq == None:
            self.seq += 1
            seq = self.seq
        if retries <= -1:
            pass
        self.outGoing.append(message.getTransmit())
        bufferedMessage = BufferMessage(seq, "1", message, 10, retries-1)
        self.timeouts[seq] = bufferedMessage

    #method used by associated drone
    #returns a message meant for the drone:
    def getIncoming(self):
        if self.inComing:
            message = self.inComing.popleft()
            self.log.append(message)
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