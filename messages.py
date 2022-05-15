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


class SSMessage(Message):
    def autoComplete(self,DroneID,seq):
        if not 'source' in self.data:
            self.data['source'] = DroneID
        if not 'seq' in self.data:
            self.data['seq'] = seq
        if not 'protocol' in self.data:
            self.data['protocol'] = 'SingleStep'

class PingSSMessage(SSMessage):
    def autoComplete(self,DroneID,seq):
        super().autoComplete(DroneID, seq)
        self.data['type'] = 'ping'

class AckSSMessage(SSMessage):
    def autoComplete(self,DroneID,seq):
        super().autoComplete(DroneID, seq)
        self.data['type'] = 'ack'

class PayloadSSMessage(SSMessage):
    def autoComplete(self,DroneID,seq):
        super().autoComplete(DroneID, seq)
        self.data['type'] = 'payload'

class BroadcastMessage(Message):
    def autoComplete(self,DroneID,seq):
        if not 'source' in self.data:
            self.data['source'] = DroneID
        if not 'seq' in self.data:
            self.data['seq'] = seq
        if not 'protocol' in self.data:
            self.data['protocol'] = 'Broadcast'
        if not 'type' in self.data:
            self.data = 'payload'

class DRMessage(Message):
    def autoComplete(self,DroneID,seq,clock):
        if not 'source' in self.data:
            self.data['source'] = DroneID
        if not 'seq' in self.data:
            self.data['seq'] = seq
        if not 'protocol' in self.data:
            self.data['protocol'] = 'DynamicRouting'
        if not 'timestamp' in self.data:
            self.data['timestamp'] = clock

class PayloadDRMessage(DRMessage):
    def autoComplete(self,DroneID,seq,clock):
        super().autoComplete(DroneID,seq,clock)
        self.data['type'] = 'payload'

class AckDRMessage(DRMessage):
    def autoComplete(self,DroneID,clock):
        super().autoComplete(DroneID,None,clock)
        self.data['type'] = 'ack'

class CorrectionDRMessage(DRMessage):
    def autoComplete(self, DroneID, seq, clock):
        super().autoComplete(DroneID, seq, clock)
        self.data['type'] = 'correction'

class PerformCorrectionDRMessage(DRMessage):
    def autoComplete(self, DroneID, seq, clock):
        super().autoComplete(DroneID, seq, clock)
        self.data['type'] = 'performCorrection'