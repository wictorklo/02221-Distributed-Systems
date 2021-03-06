from pyparsing import nullDebugAction
from drones import ADrone, BDrone
#from legacy import NetworkInterface, Message, PayloadFloodMessage
import json
from network_interfaces import *


class Script:
    def __init__(self, script = None):
        if script == None:
            script = lambda m, a, b : (m, a, b)
        self.performScriptedAction = script

    def performScriptedAction(map, ADrones, BDrones):
        pass

def succeed1(map, a, b : 'list[BDrone]'):
    message = PayloadDRMessage()
    message.data = {
        "source" : "1",
        "destination" : "2",
        "type" : "payload",
        "seq" : 0,
        "payload" : json.dumps({"type":"None"}),
        "protocol":"DynamicRouting",
        "route" : {"1" : "2", "2" : "2"},
        "timestamp" : 0
    }
    b[0].networkInterface.sendMessage(message)
    return map, a, b, True

transmissionSucceed = [Script(succeed1)]

def dropped1(map, a, b):
    message = PayloadDRMessage()
    message.data = {
        "source" : "1",
        "destination" : "2",
        "type" : "payload",
        "seq" : 0,
        "payload" : json.dumps({"type":"None"}),
        "protocol":"DynamicRouting",
        "route" : {"1" : "2", "2" : "2"},
        "timestamp" : 0
    }
    a[0].networkInterface.sendMessage(message)
    a[0].networkInterface.getOutgoing()
    return map, a, b, True

transmissionDropped = [Script(dropped1)]



class EmptyScript(Script):
    def __init__(self) -> None:
        pass
    def performScriptedAction(self, map, ADrones, BDrones):
        return (map, ADrones, BDrones, True)


if __name__ == "__main__":
    from simulator import emptyMap, setFire, printMap
    ADrones = [ADrone(NetworkInterface("DroneA"), 1, 1)]
    BDrones = [BDrone(NetworkInterface("DroneB"), 9, 9)]
    map = emptyMap(10, 10, False)
    map2, A, B, _ = transmissionSucceed[0].performScriptedAction(map, ADrones, BDrones)
    printMap(map2, A, B)
