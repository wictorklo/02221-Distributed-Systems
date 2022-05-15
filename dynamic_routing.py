from single_step import SingleStepNI
from messages import *
from collections import deque

class DynamicRoutingNI:
    def __init__(self,
            ID : 'str', singleStepNI : 'SingleStepNI', routingTable,
            defaultTimeoutOrigin = 100, defaultTimeoutRouting = 20,
            defaultRetriesOrigin = 5, defaultRetriesRouting = 3,
            defaultPingTimeout = 6):
        self.ID = ID
        self.singleStepNI = singleStepNI
        self.timeouts = {}
        self.timeoutHandlers = {}
        self.retries = {}
        self.timeoutStarts = {}
        self.payloadLog = set()
        self.incoming = deque()
        self.routingTable = routingTable
        self.defaultTimeoutOrigin = defaultTimeoutOrigin
        self.defaultTimeoutRouting = defaultTimeoutRouting
        self.defaultRetriesOrigin = defaultRetriesOrigin
        self.defaultRetriesRouting = defaultRetriesRouting
        self.defaultPingTimeout = defaultPingTimeout
        self.seq = 1
        self.clock = 0
        self.lastCorrections = {self.ID : self.clock}


    #just used in first step
    def sendPayloadMessage(self,message : 'Message'):
        plmessage = PayloadDRMessage()
        plmessage.data = message.data
        plmessage.autoComplete(self.ID,self.seq)
        seq = plmessage.data['seq']
        if seq == self.seq:
            self.seq += 1
        if not seq in self.timeouts:
            self.timeouts[seq] = self.defaultTimeoutOrigin
            self.timeoutHandlers[seq] = (lambda : self.sendPayloadMessage(plmessage))
        if not seq in self.retries:
            self.retries[seq] = self.defaultRetriesOrigin
        if self.retries[seq] <= 0:
            del self.timeouts[seq]
            del self.timeoutHandlers[seq]
            del self.retries[seq]
            return

        self.__sendPayloadMessage(plmessage)

    def receiveMessage(self, message : 'DRMessage'):
        self.clock += 1
        if message.data['destination'] != self.ID:
            self.__bounceMessage(message)
        if message.data['type'] == 'payload':
            self.__receivePayloadMessage(message)
        if message.data['type'] == 'ack':
            self.__receiveAckMessage(message)
        if message.data['type'] == 'correction':
            self.__recieveCorrection(message)
        if message.data['type'] == 'performCorrection':
            self.__correctRouting()

    #used in intermediate steps
    #we assume message contains necessary info
    def __sendMessage(self,message : 'DRMessage'):
        self.clock += 1
        message.autoComplete(self.ID,self.seq,self.clock)
        if message.data["source"] == self.ID and message.data["seq"] == self.seq:
            self.seq += 1
        nextStepID = message.data["route"][self.ID]
        ssMessage = PayloadSSMessage()
        ssMessage.data["payload"] = message.getTransmit()
        ssMessage.data["destination"] = nextStepID
        self.singleStepNI.sendPayloadMessage(ssMessage)
        return "Success"

    def __sendPayloadMessage(self,message : 'PayloadDRMessage'):
        seq = (message.data["source"],message.data["seq"])
        if seq in self.timeouts and self.timeoutStarts[seq] > self.lastCorrections[self.ID]:
            self.__correctRouting()
            self.timeouts[seq] = self.defaultTimeoutRouting
            return
        if not seq in self.timeouts:
            self.timeouts[seq] = self.defaultTimeoutRouting
            self.timeoutHandlers[seq] = (lambda : self.__sendPayloadMessage(message))
        if not seq in self.retries:
            self.retries[seq] = self.defaultRetriesRouting
        if self.retries[seq] <= 0:
            del self.timeouts[seq]
            del self.timeoutHandlers[seq]
            del self.retries[seq]
            del self.timeoutStarts[seq]
            return "RetriesExhausted"
        
        self.retries[seq] -= 1
        if self.__findRoute(message):
            return self.__sendMessage(message)
        else:
            return "NoRoute"


    def __sendAckMessage(self,ack : 'AckDRMessage'):
        if self.__findRoute(ack):
            return self.__sendMessage(ack)
        else:
            return "NoRoute"

    def __bounceMessage(self, message : 'DRMessage'):
        #if bounce is not possible
        if not message.data["route"][self.ID] in self.routingTable[self.ID]:
            #send correction back to source
            correction = CorrectionDRMessage()
            correction.data["neighbours"] = list(self.routingTable[self.ID])
            correction.data["destination"] = message.data["source"]
            self.__sendMessage(correction)

            #find actual path
            if not self.__findRoute(message):
                return "NoRoute"
        return self.__sendMessage(message)

    def __receivePayloadMessage(self, message : 'PayloadDRMessage'):
        seq = message.data['seq']
        source = message.data['source']
        ack = AckDRMessage()
        ack.data['destination'] = source
        ack.data['seq'] = seq
        self.__sendAckMessage(ack)
        if (seq,source) in self.payloadLog: 
            return #already received
        self.payloadLog.add((seq,source))
        self.incoming.append(message.data['payload'])

    def __receiveAckMessage(self, message : 'AckDRMessage'):
        seq = message.data['seq']
        if seq in self.timeouts:
            del self.timeouts[seq]
            del self.timeoutHandlers[seq]
            del self.retries[seq]
            del self.timeoutStarts[seq]

    def __recieveCorrection(self, message : 'CorrectionDRMessage'):
        if not message.data["timestamp"] > self.lastCorrections[message.data["source"]]:
            return #ignore floating corpse
        self.lastCorrections[message.data["source"]] = message.data["timestamp"]
        self.routingTable[message.data["source"]] = set(message.data["neighbours"])

    def __correctRouting(self):
        self.clock += 1
        if not "correction" in self.timeouts:
            self.singleStepNI.ping()
            self.timeouts["correction"] = self.defaultPingTimeout
            self.timeoutHandlers["correction"] = self.__correctionTimeout

    def __correctionTimeout(self):
        self.clock += 1
        del self.timeouts["correction"]
        del self.timeoutHandlers["correction"]
        self.lastCorrections[self.ID] = self.clock

        if self.routingTable[self.ID] != self.singleStepNI.neighbours:
            #correct neighbours
            self.routingTable[self.ID] = self.singleStepNI.neighbours

            #broadcast new neighbours
            correction = CorrectionDRMessage()
            correction.data["neighbours"] = list(self.routingTable[self.ID])
            correction.data["timestamp"] = self.clock 
            correction.autoComplete(self.ID,self.seq,self.clock)

            self.clock += 1
            self.seq += 1
            bcMessage = BroadcastMessage()
            bcMessage.data["payload"] = correction.getTransmit()

            self.singleStepNI.broadcast(bcMessage)

            #tell neighbours to correct
            for ID in self.routingTable[self.ID]:
                performCorrection = PerformCorrectionDRMessage()
                performCorrection.data["destination"] = ID
                performCorrection.autoComplete(self.ID,self.seq,self.clock)
                self.seq += 1
                self.clock += 1
                self.singleStepNI.sendPayloadMessage(performCorrection)

#TODO: 
#router successfully routes
#expand routing tables with drone type and coordinates + timestamps
#requirements for automatic ping (unexpected neighbour)
#requirements for automatic general info table correction
#implement broadcast
#tests
#cooperation between single step and dynamic routing 