#test protocols with scenarios designed to highlight weaknesses
import unittest as ut
from simulator import *
from script import *
from util import *
from script import succeed1, dropped1

class TestMessageDropped(ut.TestCase):
    def test_drop_message(self):
        #D1 sends message to D2 which is dropped during transmission
        script = Script(dropped1)
        rt = {"1" : set(["2"]), "2" : set(["1"])}
        map = emptyMap(10,10)
        ADrones = [ADrone(NetworkInterface("1", rt, None),map, 0, 0)]
        BDrones = [BDrone(NetworkInterface("2", rt, None),map, 2, 2)]
        sim = Simulator(map,script,ADrones,BDrones, transmissionsPerTurn=3)
        sim.performTurn()
        self.assertTrue(len(sim.BDrones[0].networkInterface.dynamicRoutingNI.payloadLog) == 0)
    
    def test_drop_retry(self):
        #D1 sends message to D2 which is dropped during transmission. Succeeds on retry.
        script = Script(dropped1)
        rt = {"1" : set(["2"]), "2" : set(["1"])}
        map = emptyMap(10,10)
        ADrones = [ADrone(NetworkInterface("1", rt, None),map, 0, 0)]
        BDrones = [BDrone(NetworkInterface("2", rt, None),map, 2, 2)]
        sim = Simulator(map,script,ADrones,BDrones)
        sim.performTurn()
        self.assertTrue(len(sim.BDrones[0].networkInterface.dynamicRoutingNI.payloadLog) == 1)

class TestMessageDelivered(ut.TestCase):
    def test_deliver_message(self):
        # D1 sends message to D2
        rt = {"1" : set(["2"]), "2" : set(["1"])}
        script = EmptyScript()
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
        map = emptyMap(100,100)
        ADrones = [ADrone(NetworkInterface("1", rt, None),map, 0, 0)]
        BDrones = [BDrone(NetworkInterface("2", rt, None),map, 2, 2)]
        sim = Simulator(map,script,ADrones,BDrones)
        ADrones[0].networkInterface.sendMessage(message)
        sim.performTurn()
        self.assertTrue(len(sim.BDrones[0].networkInterface.dynamicRoutingNI.payloadLog) > 0)

    def test_propagate_message(self):
        # D1 sends a message to D2 by propagating it through D3
        script = EmptyScript()
        message = PayloadDRMessage()
        message.data = {
            "source" : "1",
            "destination" : "2",
            "type" : "payload",
            "seq" : 0,
            "payload" : json.dumps({"type":"None"}),
            "protocol":"DynamicRouting",
            "route" : {"1" : "3", "3" : "2"},
            "timestamp" : 0
        }
        map = emptyMap(10,10)
        rt = {"1" : set(["3"]), "2" : set(["3"]), "3" : set(["1", "2"])}
        ADrones = [ADrone(NetworkInterface("1", rt, None),map, 0, 0)]
        BDrones = [BDrone(NetworkInterface("2", rt, None),map, 6, 6), BDrone(NetworkInterface("3", rt, None),map, 3, 3)]
        sim = Simulator(map,script,ADrones,BDrones)
        ADrones[0].networkInterface.sendMessage(message)
        sim.performTurn()
        self.assertTrue(len(sim.ADrones[0].networkInterface.dynamicRoutingNI.timeouts) == 1)
        self.assertTrue("infocast" in sim.ADrones[0].networkInterface.dynamicRoutingNI.timeouts.keys())
    
    #TODO: Test that ACK is received and stops resends
    def test_deliver_ack_message(self):
        # D1 sends message to D2. D2 sends ack to D1
        rt = {"1" : set(["2"]), "2" : set(["1"])}
        script = EmptyScript()
        message = PayloadDRMessage()
        message.data = {
            "source" : "2",
            "destination" : "1",
            "type" : "payload",
            "seq" : 0,
            "payload" : json.dumps({"type":"None"}),
            "protocol":"DynamicRouting",
            "route" : {"2" : "1"},
            "timestamp" : 0
        }
        map = emptyMap(100,100)
        ADrones = [ADrone(NetworkInterface("1", rt, None),map, 0, 0)]
        BDrones = [BDrone(NetworkInterface("2", rt, None),map, 2, 2)]
        sim = Simulator(map,script,ADrones,BDrones, transmissionsPerTurn=1)
        BDrones[0].networkInterface.sendMessage(message)
        sim.performTurn()
        self.assertTrue(len(sim.ADrones[0].networkInterface.dynamicRoutingNI.payloadLog) == 1)
        self.assertTrue(any("ack" in m for m in sim.ADrones[0].networkInterface.outgoing))
        # Still awaiting ack
        self.assertTrue(0 in sim.BDrones[0].networkInterface.dynamicRoutingNI.timeouts.keys()) 
        sim.performTurn()
        # Ack received, deleting message.
        self.assertTrue(0 not in sim.BDrones[0].networkInterface.dynamicRoutingNI.timeouts.keys())

class TestChallenges(ut.TestCase):
    def test_no_duplicate_diamond(self):
        script = EmptyScript()
        routingTable = {
            "1" : set(["2", "3"]),
            "2" : set(["1", "3", "4"]),
            "3" : set(["1", "2", "4"]),
            "4" : set(["2", "3"])
        }
        map = emptyMap(10, 10)
        adrones = [
            ADrone(NetworkInterface("1", routingTable, None),map, 0, 0),
            ADrone(NetworkInterface("2", routingTable, None),map, 0, 3),
            ADrone(NetworkInterface("3", routingTable, None),map, 0, 3.5),
            ADrone(NetworkInterface("4", routingTable, None),map, 0, 6)
        ]
        sim = Simulator(map, script, adrones, [], transmissionsPerTurn=10,transmissionDistance=4)

        message = PayloadDRMessage()
        message.data = {
            "destination" : "4",
            "type" : "payload",
            "seq" : 0,
            "payload" : json.dumps({"type":"None"}),
            "protocol":"DynamicRouting",
            "timestamp" : 0
        }

        adrones[0].networkInterface.sendMessage(message)
        sim.performTurn()
        sim.performTurn()
        self.assertEqual(len(adrones[3].networkInterface.dynamicRoutingNI.payloadLog),1)

class TestRouting(ut.TestCase):
    def test_ping_neighbours(self):
        script = EmptyScript()
        routingTable = {
            "1" : set(["2", "3"]),
            "2" : set(["1", "3", "4"]),
            "3" : set(["1", "2", "4"]),
            "4" : set(["2", "3"])
        }
        map = emptyMap(10, 10)
        adrones = [
            ADrone(NetworkInterface("1", routingTable, None),map, 0, 0),
            ADrone(NetworkInterface("2", routingTable, None),map, 0, 3),
            ADrone(NetworkInterface("3", routingTable, None),map, 0, 3.5),
            ADrone(NetworkInterface("4", routingTable, None),map, 0, 6)
        ]
        sim = Simulator(map, script, adrones, [], transmissionsPerTurn=10, transmissionDistance=5)

        adrones[0].networkInterface.singleStepNI.ping()
        sim.performTurn()
        assert(len(adrones[0].networkInterface.singleStepNI.neighbours) == 2)

    def test_stabilize_routing_joint_network(self):
        #We want to test that if drones have conflicting routing tables
        #but are not in a disjoint network, then after enough
        #ordinary communication the routing tables will be correct
        pass

    def test_stabilize_routing_disjoint_network(self):
        #we want to test that if two networks are joined, then they stabilize
        #after enough ordinary communication
        pass