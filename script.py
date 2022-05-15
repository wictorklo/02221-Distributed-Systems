from pyparsing import nullDebugAction
from drones import ADrone, BDrone
from legacy import NetworkInterface, Message, PayloadFloodMessage
import json


class Script:
    def __init__(self, script = None):
        if script == None:
            script = lambda m, a, b : (m, a, b)
        self.performScriptedAction = script

    def performScriptedAction(map, ADrones, BDrones):
        pass

def succeed1(map, a, b : 'list[BDrone]'):
    message = PayloadFloodMessage()
    message.data = {
        "source" : b[0].networkInterface.ID,
        "destination" : a[0].networkInterface.ID,
        "type": "payload",
        "ttl" : 5,
        "payload" : json.dumps({"type" : "observation","tiles" : [], "drones" : []})
    }
    b[0].networkInterface.sendMessage(message,timeout=10,retries=2)
    return map, a, b, True

transmissionSucceed = [Script(succeed1)]

def dropped1(map, a, b):
    message = PayloadFloodMessage()
    message.data = {
        "destination" : b[0].networkInterface.ID,
        "type": "payload",
        "ttl" : 5,
        "payload" : json.dumps({"type" : "observation","tiles" : [], "drones" : []})
    }
    a[0].networkInterface.sendMessage(message,retries = 0)
    a[0].networkInterface.getOutgoing()
    return map, a, b, True

def retry(map, a, b):
    message = PayloadFloodMessage()
    message.data = {
        "source" : a[0].networkInterface.ID,
        "destination" : b[0].networkInterface.ID,
        "type": "payload",
        "ttl" : 5,
        "payload" : json.dumps({"type" : "observation","tiles" : [], "drones" : []}),
        "seq" : 1
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
