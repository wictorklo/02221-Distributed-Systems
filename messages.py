import json

class Message:
    def __init__(self,transmit = None,protocol = None,type = None):
        self.data = {}
        self.data["protocol"] = protocol
        self.data["type"] = type
        if transmit:
            self.loadTransmit(transmit)

    def loadTransmit(self,transmit):
        self.data = json.loads(transmit)

    def getTransmit(self):
        return json.dumps(self.data)


class SSMessage(Message):
    def __init__(self, transmit = None, type = None):
        super().__init__(transmit,"SingleStep", type)

    def autoComplete(self,DroneID,seq):
        if not 'source' in self.data:
            self.data['source'] = DroneID
        if not 'seq' in self.data:
            self.data['seq'] = seq
            

class PingSSMessage(SSMessage):
    def __init__(self, transmit=None):
        super().__init__(transmit,"ping")

class PongSSMessage(SSMessage):
    def __init__(self, transmit=None):
        super().__init__(transmit,"pong")

class PayloadSSMessage(SSMessage):
    def __init__(self, transmit=None):
        super().__init__(transmit,"payload")

class BroadcastMessage(SSMessage):
    def __init__(self, transmit=None):
        super().__init__(transmit,"broadcast")

class DRMessage(Message):
    def __init__(self, transmit = None, type = None):
        super().__init__( transmit,"DynamicRouting",type)

    def autoComplete(self,DroneID,seq,clock):
        if not 'source' in self.data:
            self.data['source'] = DroneID
        if not 'seq' in self.data:
            self.data['seq'] = seq
        if not 'timestamp' in self.data:
            self.data['timestamp'] = clock

class PayloadDRMessage(DRMessage):
    def __init__(self, transmit=None):
        super().__init__(transmit,"payload")

class PredicastDRMessage(DRMessage):
    def __init__(self, transmit=None):
        super().__init__(transmit,"predicast")

class PayloadAckDRMessage(DRMessage):
    def __init__(self, transmit=None):
        super().__init__(transmit,"payloadAck")

class AckDRMessage(DRMessage):
    def __init__(self, transmit=None):
        super().__init__(transmit,"ack")

class CorrectionDRMessage(DRMessage):
    def __init__(self, transmit=None):
        super().__init__(transmit,"correction")

class InfoDRMessage(DRMessage):
    def __init__(self, transmit=None):
        super().__init__(transmit,"info")

class PerformCorrectionDRMessage(DRMessage):
    def __init__(self, transmit=None):
        super().__init__(transmit,"performCorrection")
