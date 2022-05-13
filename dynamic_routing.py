from network_interfaces import Message,FloodMessage,AckFloodMessage,PayloadFloodMessage

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

class DynamicRoutingNI:
    def __init__(self,
            ID,singleStepNI,routingTable,
            defaultTimeoutOrigin = 100, defaultTimeoutRouting = 20,
            defaultRetriesOrigin = 5, defaultRetriesRouting = 3):
        self.ID = ID
        self.singleStepNI = singleStepNI
        self.originTimeouts = {}
        self.routeTimeouts = {}
        self.originTimeoutHandlers = {}
        self.routeTimeoutHandlers = {}
        self.originRetries = {}
        self.routingTable = routingTable
        self.defaultTimeoutOrigin = defaultTimeoutOrigin
        self.defaultTimeoutRouting = defaultTimeoutRouting
        self.defaultRetriesOrigin = defaultRetriesOrigin
        self.defaultRetriesRouting = defaultRetriesRouting
        self.seq = 1

    #just used in first step
    def sendPayloadMessage(self,message : 'Message'):
        plmessage = PayloadDRMessage()
        plmessage.data = message.data
        plmessage.autoComplete(self.ID,self.seq)
        seq = plmessage.data['seq']
        if seq == self.seq:
            self.seq += 1
        if not seq in self.originTimeouts[plmessage]:
            self.originTimeouts[seq] = self.defaultTimeoutOrigin
            self.originTimeoutHandlers[seq] = (lambda : self.sendPayloadMessage(plmessage))
        if not plmessage.data['seq'] in self.originRetries:
            self.originRetries[plmessage.data['seq']] = self.defaultRetriesOrigin
        if self.originRetries[plmessage.data['seq']] >= 1:
            self.__sendPayloadMessage(plmessage)
            self.originRetries[plmessage.data['seq']] -= 1
        else:
            del self.originTimeouts[seq]
            del self.originTimeoutHandlers[seq]
            del self.originRetries[seq]

    #used in both original and intermediate steps
    def __sendPayloadMessage(self,message : 'Message'):
        nextStepID = self.__findPath(message.data["destination"])
        ssMessage = SingleStepMessage()
        ssMessage.data["payload"] = message
        ssMessage.data["destination"] = nextStepID
        successful = self.singleStepNI.sendMessage(ssMessage)
        if not successful:
            pass