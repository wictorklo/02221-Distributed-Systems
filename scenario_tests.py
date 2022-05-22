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
        infoTable = {
            "1" : {"type" : "A", "xpos" : 0, "ypos" : 0, "timestamp" : 0},
            "2" : {"type" : "A", "xpos" : 1, "ypos" : 1, "timestamp" : 0},
            "3" : {"type" : "B", "xpos" : 4, "ypos" : 5, "timestamp" : 0}}
        map = emptyMap(10,10)
        ADrones = [ADrone(NetworkInterface("1", rt, infoTable),map, 0, 0)]
        BDrones = [BDrone(NetworkInterface("2", rt, infoTable),map, 2, 2)]
        sim = Simulator(map,script,ADrones,BDrones, transmissionsPerTurn=3)
        sim.performTurn()
        self.assertTrue(len(sim.BDrones[0].networkInterface.dynamicRoutingNI.payloadLog) == 0)
    
    def test_drop_retry(self):
        #D1 sends message to D2 which is dropped during transmission. Succeeds on retry.
        script = Script(dropped1)
        rt = {"1" : set(["2"]), "2" : set(["1"])}
        infoTable = {
            "1" : {"type" : "A", "xpos" : 0, "ypos" : 0, "timestamp" : 0},
            "2" : {"type" : "A", "xpos" : 1, "ypos" : 1, "timestamp" : 0},
            "3" : {"type" : "B", "xpos" : 4, "ypos" : 5, "timestamp" : 0}}
        map = emptyMap(10,10)
        ADrones = [ADrone(NetworkInterface("1", rt, infoTable),map, 0, 0)]
        BDrones = [BDrone(NetworkInterface("2", rt, infoTable),map, 2, 2)]
        sim = Simulator(map,script,ADrones,BDrones)
        sim.performTurn()
        self.assertTrue(len(sim.BDrones[0].networkInterface.dynamicRoutingNI.payloadLog) == 1)

class TestMessageDelivered(ut.TestCase):
    def test_deliver_message(self):
        # D1 sends message to D2
        rt = {"1" : set(["2"]), "2" : set(["1"])}
        infoTable = {
            "1" : {"type" : "A", "xpos" : 0, "ypos" : 0, "timestamp" : 0},
            "2" : {"type" : "A", "xpos" : 1, "ypos" : 1, "timestamp" : 0},
            "3" : {"type" : "B", "xpos" : 4, "ypos" : 5, "timestamp" : 0}}
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
        ADrones = [ADrone(NetworkInterface("1", rt, infoTable),map, 0, 0)]
        BDrones = [BDrone(NetworkInterface("2", rt, infoTable),map, 2, 2)]
        sim = Simulator(map,script,ADrones,BDrones)
        ADrones[0].networkInterface.sendMessage(message)
        sim.performTurn()
        self.assertTrue(len(sim.BDrones[0].networkInterface.dynamicRoutingNI.payloadLog) > 0)

    def test_propagate_message(self):
        # D1 sends a message to D2 by propagating it through D3
        script = EmptyScript()
        message = PayloadDRMessage()
        infoTable = {
            "1" : {"type" : "A", "xpos" : 0, "ypos" : 0, "timestamp" : 0},
            "2" : {"type" : "A", "xpos" : 1, "ypos" : 1, "timestamp" : 0},
            "3" : {"type" : "B", "xpos" : 4, "ypos" : 5, "timestamp" : 0}}
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
        ADrones = [ADrone(NetworkInterface("1", rt, infoTable),map, 0, 0)]
        BDrones = [BDrone(NetworkInterface("2", rt, infoTable),map, 6, 6), BDrone(NetworkInterface("3", rt, infoTable),map, 3, 3)]
        sim = Simulator(map,script,ADrones,BDrones)
        ADrones[0].networkInterface.sendMessage(message)
        sim.performTurn()
        self.assertEqual(len(sim.ADrones[0].networkInterface.dynamicRoutingNI.timeouts), 3)
        self.assertIn("infocast", sim.ADrones[0].networkInterface.dynamicRoutingNI.timeouts.keys())
    
    #TODO: Test that ACK is received and stops resends
    def test_deliver_ack_message(self):
        # D1 sends message to D2. D2 sends ack to D1
        rt = {"1" : set(["2"]), "2" : set(["1"])}
        infoTable = {
            "1" : {"type" : "A", "xpos" : 0, "ypos" : 0, "timestamp" : 0},
            "2" : {"type" : "A", "xpos" : 1, "ypos" : 1, "timestamp" : 0},
            "3" : {"type" : "B", "xpos" : 4, "ypos" : 5, "timestamp" : 0}}
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
        ADrones = [ADrone(NetworkInterface("1", rt, infoTable),map, 0, 0)]
        BDrones = [BDrone(NetworkInterface("2", rt, infoTable),map, 2, 2)]
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
        infoTable = {
            "1" : {"type" : "A", "xpos" : 0, "ypos" : 0, "timestamp" : 0},
            "2" : {"type" : "A", "xpos" : 1, "ypos" : 1, "timestamp" : 0},
            "3" : {"type" : "B", "xpos" : 4, "ypos" : 5, "timestamp" : 0},
            "4" : {"type" : "B", "xpos" : 4, "ypos" : 5, "timestamp" : 0}}
        map = emptyMap(10, 10)
        adrones = [
            ADrone(NetworkInterface("1", routingTable, infoTable),map, 0, 0),
            ADrone(NetworkInterface("2", routingTable, infoTable),map, 0, 3),
            ADrone(NetworkInterface("3", routingTable, infoTable),map, 0, 3.5),
            ADrone(NetworkInterface("4", routingTable, infoTable),map, 0, 6)
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
        infoTable = {
            "1" : {"type" : "A", "xpos" : 0, "ypos" : 0, "timestamp" : 0},
            "2" : {"type" : "A", "xpos" : 1, "ypos" : 1, "timestamp" : 0},
            "3" : {"type" : "B", "xpos" : 4, "ypos" : 5, "timestamp" : 0},
            "4" : {"type" : "B", "xpos" : 4, "ypos" : 5, "timestamp" : 0}}
        map = emptyMap(10, 10)
        adrones = [
            ADrone(NetworkInterface("1", routingTable, infoTable),map, 0, 0),
            ADrone(NetworkInterface("2", routingTable, infoTable),map, 0, 3),
            ADrone(NetworkInterface("3", routingTable, infoTable),map, 0, 3.5),
            ADrone(NetworkInterface("4", routingTable, infoTable),map, 0, 6)
        ]
        sim = Simulator(map, script, adrones, [], transmissionsPerTurn=10, transmissionDistance=5)

        adrones[0].networkInterface.singleStepNI.ping()
        sim.performTurn()
        assert(len(adrones[0].networkInterface.singleStepNI.neighbours) == 2)

    def test_stabilize_routing_joint_network(self):
        #We want to test that if drones have conflicting routing tables
        #but are not in a disjoint network, then after enough
        #ordinary communication the routing tables will be correct
        script = EmptyScript()
        tmap = emptyMap(50,50,flammable=True)
        #nonsensical routing info
        routingTable = {"1" : set(["4"]), "2" : set(["1"]), "3" : set(["1","4"]), "4" : set([])}
        #nonsensical info table
        infoTable = {
            "1" : {"type" : "B", "xpos" : 100, "ypos" : 3, "timestamp" : 0},
            "2" : {"type" : "B", "xpos" : 64, "ypos" : 51, "timestamp" : 0},
            "3" : {"type" : "B", "xpos" : 14, "ypos" : 20, "timestamp" : 0},
            "4" : {"type" : "A", "xpos" : 92, "ypos" : 43, "timestamp" : 0}}
        ni1 = NetworkInterface("1",routingTable, infoTable)
        ni2 = NetworkInterface("2",routingTable, infoTable)
        ni3 = NetworkInterface("3",routingTable, infoTable)
        ni4 = NetworkInterface("4",routingTable, infoTable)
        drone1 = BDrone(ni1,tmap,xpos = 0,ypos = 0)
        drone2 = BDrone(ni2,tmap,xpos = 5,ypos = 5)
        drone3 = BDrone(ni3,tmap,xpos = 10,ypos = 10)
        drone4 = ADrone(ni4,tmap,xpos = 15,ypos = 15)
        sim = Simulator(tmap,script,[drone4],[drone1,drone2,drone3],transmissionDistance=10,lineOfSight=2)

        for i in range(20):
            source = [drone1,drone2,drone3,drone4][i % 4]
            destination = ["1","2","3","4"][(i + (1 + i // 4)) % 4]
            message = PayloadDRMessage()
            message.data["payload"] = Observation().getObservationPayload()
            message.data["destination"] = destination
            source.networkInterface.sendMessage(message)

            sim.performTurn()

        sim.performTurn()
        sim.performTurn()
        self.assertEqual(
            drone1.networkInterface.dynamicRoutingNI.routingTable["1"],
            set(["2"]))
        self.assertEqual(
            drone3.networkInterface.dynamicRoutingNI.routingTable["1"],
            set(["2"]))
        self.assertEqual(
            drone4.networkInterface.dynamicRoutingNI.routingTable["2"],
            set(["1","3"]))
        self.assertEqual(
            drone1.networkInterface.dynamicRoutingNI.infoTable["1"]["xpos"],
            0)
        self.assertEqual(
            drone3.networkInterface.dynamicRoutingNI.infoTable["1"]["ypos"],
            0)
        self.assertEqual(
            drone4.networkInterface.dynamicRoutingNI.infoTable["2"]["xpos"],
            5)
            
    def test_stabilize_routing_disjoint_network(self):
        #we want to test that if two networks are joined, then they stabilize
        #after enough ordinary communication
        pass
