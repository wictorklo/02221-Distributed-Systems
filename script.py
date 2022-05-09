from pyparsing import nullDebugAction
from drones import ADrone, BDrone
from network_interfaces import NetworkInterface, Message

def loadTransmit(self,transmit):
        self.data = json.loads(transmit)
        self.source = self.data["source"]
        self.destination = self.data["destination"]
        self.payload = self.data["payload"]


class Script:
    def __init__(self, script = None):
        if script == None:
            script = lambda m, a, b : m, a, b
        self.performScriptedAction = script

    def performScriptedAction(map, ADrones, BDrones):
        pass

def succeed1(map, a, b):
    a[0].networkInterface.sendMessage(Message('{"source": a[0].networkInterface.ID, "destination": b[0].networkInterface.ID, "payload":None}'))

transmissionSucceed = [Script(succeed1)]

def dropped1(map, a, b):
    a[0].networkInterface.sendMessage(Message('{"source": a[0].networkInterface.ID, "destination": b[0].networkInterface.ID, "payload":None}'))
    a[0].networkInterface.getOutgoing()

transmissionDropped = [Script(dropped1)]



class EmptyScript(Script):
    def __init__(self) -> None:
        pass
    def performScriptedAction(map, ADrones, BDrones):
        return (map, ADrones, BDrones, True)


if __name__ == "__main__":
    from simulator import emptyMap, setFire, printMap
    ADrones = [ADrone(NetworkInterface("DroneA"), 1, 1)]
    BDrones = [BDrone(NetworkInterface("DroneB"), 9, 9)]
    map = emptyMap(10, 10, False)
    map2, A, B, _ = transmissionSucceed[0].performScriptedAction(map, ADrones, BDrones)
    printMap(map2, A, B)
    