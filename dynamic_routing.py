from network_interfaces import Message,FloodMessage,AckFloodMessage,PayloadFloodMessage,SingleStepMessage

class DRMessage(Message):
    def autoComplete(self,DroneID,seq):
        if not 'source' in self.data:
            self.data['source'] = DroneID
        if not 'seq' in self.data:
            self.data['seq'] = seq

class PayloadDRMessage(DRMessage):
    def autoComplete(self,DroneID,seq):
        super().autoComplete(DroneID,seq)
        self.data['type'] = 'payload'

class CorrectionDRMessage(DRMessage):
    def autoComplete(self, DroneID, seq):
        super().autoComplete(DroneID, seq)
        self.data['type'] = 'correction'

class PerformCorrectionDRMessage(DRMessage):
    def autoComplete(self, DroneID, seq):
        super().autoComplete(DroneID, seq)
        self.data['type'] = 'performCorrection'

class DynamicRoutingNI:
    def __init__(self,
            ID,singleStepNI,routingTable,
            defaultTimeoutOrigin = 100, defaultTimeoutRouting = 20,
            defaultRetriesOrigin = 5, defaultRetriesRouting = 3,
            defaultPingTimeout = 6):
        self.ID = ID
        self.singleStepNI = singleStepNI
        self.timeouts = {}
        self.timeoutHandlers = {}
        self.retries = {}
        self.timeoutStarts = {}
        self.routingTable = routingTable
        self.defaultTimeoutOrigin = defaultTimeoutOrigin
        self.defaultTimeoutRouting = defaultTimeoutRouting
        self.defaultRetriesOrigin = defaultRetriesOrigin
        self.defaultRetriesRouting = defaultRetriesRouting
        self.defaultPingTimeout = defaultPingTimeout
        self.seq = 1
        self.clock = 0
        self.lastCorrection = self.clock


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

        self.retries[seq] -= 1
        self.__sendPayloadMessage(plmessage)

    #used in intermediate steps
    #we assume message contains necessary info
    def __sendPayloadMessage(self,message : 'Message'):
        self.clock += 1
        seq = (message.data["source"],message.data["seq"])
        if seq in self.timeouts and self.timeoutStarts[seq] > self.lastCorrection:
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
            return
        
        self.retries[seq] -= 1
        nextStepID = self.__findPath(message.data["destination"])[0]
        ssMessage = SingleStepMessage()
        ssMessage.data["payload"] = message.getTransmit()
        ssMessage.data["destination"] = nextStepID
        self.singleStepNI.sendMessage(ssMessage)


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
        self.lastCorrection = self.clock

        if self.routingTable[self.ID] != self.singleStepNI.neighbours:
            #correct neighbours
            self.routingTable[self.ID] = self.singleStepNI.neighbours

            #broadcast new neighbours
            correction = CorrectionDRMessage()
            correction.data["neighbours"] = self.routingTable[self.ID]
            correction.autoComplete(self.ID,self.seq)
            self.seq += 1

            bcMessage = BroadcastMessage()
            bcMessage.data["payload"] = correction.getTransmit()

            self.singleStepNI.broadcast(bcMessage)

            #tell neighbours to correct
            for ID in self.routingTable[self.ID]:
                performCorrection = PerformCorrectionDRMessage()
                performCorrection.data["destination"] = ID
                performCorrection.autoComplete()
                self.singleStepNI.sendMessage(performCorrection)

#TODO: origin recieves payload
#router successfully routes
#expand routing tables with drone type and coordinates + timestamps
#requirements for automatic ping (unexpected neighbour)
#requirements for automatic general info table correction
#implement broadcast
#recieve routing info broadcast
#recieve order to ping message
#tests
#cooperation between single step and dynamic routing 