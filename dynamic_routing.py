from single_step import SingleStepNI
from messages import *
from collections import deque
import util

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
        for ID in self.routingTable:
            if ID != self.ID:
                self.lastCorrections[ID] = 0

    def tick(self):
        for seq in list(self.timeouts.keys()):
            self.timeouts[seq] -= 1
            if self.timeouts[seq] <= 0:
                self.timeoutHandlers[seq]()
        if not self.routingTable[self.ID] == self.singleStepNI.neighbours:
            self.__correctRouting()


    #just used in first step
    def sendPayloadMessage(self,message : 'PayloadDRMessage'):
        message.autoComplete(self.ID,self.seq,self.clock)
        message.data["timestamp"] = self.clock
        seq = message.data['seq']
        if seq == self.seq:
            self.seq += 1

        if not seq in self.timeouts:
            self.timeouts[seq] = self.defaultTimeoutOrigin
            self.timeoutHandlers[seq] = (lambda : self.sendPayloadMessage(message))
            self.timeoutStarts[seq] = self.clock
        if not seq in self.retries:
            self.retries[seq] = self.defaultRetriesOrigin
        if self.retries[seq] <= 0:
            del self.timeouts[seq]
            del self.timeoutStarts[seq]
            del self.timeoutHandlers[seq]
            del self.retries[seq]
            return

        self.__sendMessage(message)

    def receiveMessage(self, message : 'DRMessage'):
        self.clock += 1
        #we treat no destination as broadcasts
        if 'destination' in message.data and message.data['destination'] != self.ID:
            self.__bounceMessage(message)
        elif message.data['type'] == 'payload':
            self.__receivePayloadMessage(message)
        elif message.data['type'] == 'payloadAck':
            self.__receivePayloadAckMessage(message)
        elif message.data['type'] == "ack":
            self.__receiveAckMessage(message)
            return #acks don't expect acks
        elif message.data['type'] == 'correction':
            self.__receiveCorrection(message)
            return #correction messages don't expect acks
        elif message.data['type'] == 'performCorrection':
            self.__correctRouting()
            return #performCorrection messages don't expect acks
        
        #we misuse the source field to store the source of the message we are acking
        #this scheme could lead to problems if we are excpecting acks from multiple nodes for the same message
        destination = self.__prevStep(message)
        if not destination:
            raise Exception("no previous node")
        ack = AckDRMessage()
        ack.data["seq"] = message.data["seq"]
        ack.data["source"] = message.data["source"]
        ack.data["destination"] = destination
        ack.data["ackedType"] = message.data["type"]
        ack.autoComplete(self.ID,self.seq,self.clock)
        
        ssMessage = PayloadSSMessage()
        ssMessage.data["payload"] = ack.getTransmit()
        ssMessage.data["destination"] = destination
        self.singleStepNI.sendPayloadMessage(ssMessage)

    def __multicast(self,message : 'Message',destinations):
        for destination in destinations:
            route = util.route(self.ID,destination,self.routingTable)
            if not route:
                return "NoRoute"
            ssMessage = PayloadSSMessage()
            ssMessage.data["payload"] = message.getTransmit()
            ssMessage.data["destination"] = route[1]
            self.singleStepNI.sendPayloadMessage(ssMessage)

    #used in intermediate steps
    #we assume message contains necessary info
    def __sendMessage(self,message : 'PayloadDRMessage'):
        self.clock += 1
        #autocomplete
        message.autoComplete(self.ID,self.seq,self.clock)
        if message.data["source"] == self.ID and message.data["seq"] == self.seq:
            self.seq += 1

        seq = (message.data["source"],message.data["seq"],message.data["type"])

        #handle timeouts
        if seq in self.timeouts and self.timeoutStarts[seq] > self.lastCorrections[self.ID]:
            self.__correctRouting()
            self.timeouts[seq] = self.defaultTimeoutRouting
            return "Correcting"
        if not seq in self.timeouts:
            self.timeoutStarts[seq] = self.clock
            self.timeouts[seq] = self.defaultTimeoutRouting
            self.timeoutHandlers[seq] = (lambda : self.__sendMessage(message))
        
        #handle retries
        if not seq in self.retries:
            self.retries[seq] = self.defaultRetriesRouting
        if self.retries[seq] <= 0:
            del self.timeouts[seq]
            del self.timeoutHandlers[seq]
            del self.retries[seq]
            del self.timeoutStarts[seq]
            return "RetriesExhausted"
        self.retries[seq] -= 1

        #add route if missing or outdated
        if not "route" in message.data or self.timeoutStarts[seq] < self.lastCorrections[self.ID]:
            if not self.__findRoute(message):
                return "NoRoute"

        
        #send through SS layer
        nextStepID = message.data["route"][self.ID]
        ssMessage = PayloadSSMessage()
        ssMessage.data["payload"] = message.getTransmit()
        ssMessage.data["destination"] = nextStepID
        self.singleStepNI.sendPayloadMessage(ssMessage)
        return "Success"

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
        ack = PayloadAckDRMessage()
        #we missuse source field for original source to avoid duplicate seqs
        ack.data['source'] = source
        ack.data['destination'] = source
        ack.data['seq'] = seq
        self.__sendMessage(ack)
        if (seq,source) in self.payloadLog: 
            return #already received
        self.payloadLog.add((seq,source))
        self.incoming.append(message.data['payload'])

    def __receivePayloadAckMessage(self, message : 'PayloadAckDRMessage'):
        seq = message.data['seq']
        if seq in self.timeouts:
            del self.timeouts[seq]
            del self.timeoutHandlers[seq]
            del self.retries[seq]
            del self.timeoutStarts[seq]
    
    def __receiveAckMessage(self, message : 'AckDRMessage'):
        seq = (message.data['source'],message.data['seq'],message.data['ackedType'])
        if seq in self.timeouts:
            del self.timeouts[seq]
            del self.timeoutHandlers[seq]
            del self.retries[seq]
            del self.timeoutStarts[seq]

    def __receiveCorrection(self, message : 'CorrectionDRMessage'):
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
                ssMessage = PayloadSSMessage()
                ssMessage.data["payload"] = performCorrection.getTransmit()
                ssMessage.data["destination"] = ID
                self.singleStepNI.sendPayloadMessage(ssMessage)

    def __findRoute(self, message : 'DRMessage'):
        route = util.route(self.ID, message.data["destination"], self.routingTable)
        routeMap = {}
        for i in range(1,len(route)):
            routeMap[route[i-1]] = route[i]
        message.data["route"] = routeMap
        return route

    def __prevStep(self, message : 'DRMessage'):
        route = message.data["route"]
        for prev in route:
            nxt = route[prev]
            if nxt == self.ID:
                return prev
        return None

#TODO: 
#expand routing tables with drone type and coordinates + timestamps
#requirements for automatic ping (unexpected neighbour)
#requirements for automatic general info table correction
#tests