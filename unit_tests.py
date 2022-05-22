#general test of software componenents
import json
from typing import Set
import unittest as ut
from simulator import *
from script import EmptyScript
from network_interfaces import *
from util import *
import math

class TestUtil(ut.TestCase):
    def test_move_position(self):
        x1,y1 = movePosition(1,3,1,0)
        self.assertAlmostEqual(x1,1)
        self.assertAlmostEqual(y1,4)
        x1,y1 = movePosition(1,3,1,math.pi)
        self.assertAlmostEqual(x1,1)
        self.assertAlmostEqual(y1,2)
        x1,y1 = movePosition(1,3,1,math.pi / 2)
        self.assertAlmostEqual(x1,0)
        self.assertAlmostEqual(y1,3)
        x1,y1 = movePosition(1,3,1,3 * math.pi / 2)
        self.assertAlmostEqual(x1,2)
        self.assertAlmostEqual(y1,3)
    
    def test_path(self):
        graph = {
            1: [2, 3, 4],
            2: [1, 4, 5],
            3: [1, 7],
            4: [1, 2, 5, 6],
            5: [2, 4, 8],
            6: [4],
            7: [3, 8],
            8: [5, 7]
        }
        startID = 1
        endID = 8
        assert(route(startID, endID, graph) == [1, 2, 5, 8])
        assert(route(startID, 9, graph) == None)
        assert(route(1, 1, graph) == [])

class MockNetworkInterface:
    def __init__(self,ID,singleStepNI,routingTable):
        self.ID = ID
        self.ticks = 0
        self.incoming = []
        self.dynamicRoutingNI = MockDynamicRoutingNI(ID,singleStepNI,routingTable)
    
    def tick(self):
        self.ticks += 1

    def getIncoming(self):
        return None

    def getOutgoing(self):
        return None

class MockSingleStepNI:
    def __init__(self,ID,neighbours,sendPrimitive):
        self.ID = ID
        self.neighbours = neighbours
        self.sendPayloads = []
        self.broadcasts = []
        self.pings = 0
    
    def sendPayloadMessage(self,message):
        self.sendPayloads.append(message)

    def broadcast(self, message : 'BroadcastMessage'):
        self.broadcasts.append(message)

    def ping(self):
        self.pings += 1

class MockDynamicRoutingNI:
    def __init__(self,ID,singleStepNI,routingTable):
        self.ID = ID

    def newPosition(self,x,y):
        pass

class TestSimulator(ut.TestCase):
    def test_inialize_and_perform_turn(self):
        script = EmptyScript()
        map = emptyMap(100,100)
        ADrones = []
        BDrones = []
        sim = Simulator(map,script,ADrones,BDrones)
        sim.performTurn()
    
    def test_move_corner_to_corner(self):
        script = EmptyScript()
        tmap = emptyMap(10,10)
        ni1 = MockNetworkInterface(0,None,None)
        drone1 = ADrone(ni1,tmap,xpos = 0,ypos = 0)
        drone1.getAction = lambda : Action(1,7 * math.pi / 4)

        sim = Simulator(tmap,script,[drone1],[])

        for i in range(6):
            sim.performTurn()

        self.assertAlmostEqual(sim.ADrones[0].xpos,10,delta=0.0001)
        self.assertAlmostEqual(sim.ADrones[0].ypos,10,delta=0.0001)
        self.assertEqual(math.floor(sim.ADrones[0].xpos),9)
        self.assertEqual(math.floor(sim.ADrones[0].ypos),9)

    @ut.skip("non-determinism means it sometimes fails")
    def test_spread_fire(self):
        script = EmptyScript()
        tmap = emptyMap(10,10,flammable=True)
        setFire(tmap,0,0)
        sim = Simulator(tmap,script,[],[])

        for i in range(200):
            sim.performTurn()

        self.assertTrue(
            (not isFlammable(sim.map[9][9])) or  #the tile is either burnt out
            isOnFire(sim.map[9][9]))           #or on fire

    def test_exstinguish_fire(self):
        script = EmptyScript()
        tmap = emptyMap(10,10,flammable=True)
        setFire(tmap,0,0)
        ni1 = MockNetworkInterface(0,None,None)
        drone1 = ADrone(ni1,tmap,xpos = 1,ypos = 1)
        sim = Simulator(tmap,script,[drone1],[])

        for i in range(3):
            sim.performTurn()

        self.assertFalse(isOnFire(sim.map[0][0]))
        self.assertFalse(isOnFire(sim.map[0][1]))
        self.assertFalse(isOnFire(sim.map[1][0]))
        self.assertFalse(isOnFire(sim.map[1][1]))

    def test_transmit_message(self):
        script = EmptyScript()
        tmap = emptyMap(10,10,flammable=True)
        routingTable = {"1" : set(["2"]), "2" : set(["1"])}
        infoTable = {
            "1" : {"type" : "A", "xpos" : 0, "ypos" : 0, "timestamp" : 0},
            "2" : {"type" : "A", "xpos" : 1, "ypos" : 1, "timestamp" : 0},
            "3" : {"type" : "B", "xpos" : 4, "ypos" : 5, "timestamp" : 0}}
        ni1 = NetworkInterface("1", routingTable, infoTable)
        ni2 = NetworkInterface("2", routingTable, infoTable)
        drone1 = ADrone(ni1,tmap,xpos = 1,ypos = 1)
        drone2 = ADrone(ni2,tmap,xpos = 2,ypos = 2)
        drone2.think = lambda : None #turn off mechanism that consumes messages in drone2
        sim = Simulator(tmap,script,[drone2,drone1],[], transmissionsPerTurn=1)

        message = PayloadSSMessage()
        message.data["destination"] = "2"
        message.data["payload"] = "hello"
        drone1.networkInterface.sendMessage(message)

        sim.performTurn()

        payload = drone2.networkInterface.getIncoming()
        self.assertEqual(payload,"hello")
    
    def test_internal_state_change_observation(self):
        script = EmptyScript()
        tmap = emptyMap(10,10,flammable=True)
        ni1 = MockNetworkInterface(1,None,None)
        drone1 = BDrone(ni1,tmap,xpos = 1,ypos = 1)
        sim = Simulator(tmap,script,[],[drone1])

        setFire(sim.map,0,0)
        setFire(sim.map,0,1)
        setFire(sim.map,1,0)
        setFire(sim.map,1,1)
        sim.performTurn()

        self.assertTrue(
            isOnFire(drone1.map[0][0]) or
            isOnFire(drone1.map[0][1]) or
            isOnFire(drone1.map[1][0]) or
            isOnFire(drone1.map[1][1])
        )
    
    #@ut.skip("not updated to new interfaces")
    def test_internal_state_change_message(self):
        script = EmptyScript()
        tmap = emptyMap(50,50,flammable=True)
        routingTable = {"1" : set(["2"]), "2" : set(["1"])}
        infoTable = {
            "1" : {"type" : "A", "xpos" : 0, "ypos" : 0, "timestamp" : 0},
            "2" : {"type" : "A", "xpos" : 1, "ypos" : 1, "timestamp" : 0},
            "3" : {"type" : "B", "xpos" : 4, "ypos" : 5, "timestamp" : 0}}
        ni1 = NetworkInterface("1",routingTable, infoTable)
        ni2 = NetworkInterface("2",routingTable, infoTable)
        drone1 = BDrone(ni1,tmap,xpos = 49,ypos = 49)
        drone2 = BDrone(ni2,tmap,xpos = 46,ypos = 46)
        sim = Simulator(tmap,script,[],[drone1,drone2])

        observation = Observation()
        observation.tiles.append((3,0,0))
        observation.tiles.append((3,1,0))
        observation.tiles.append((3,0,1))
        observation.tiles.append((3,1,1))
        message = PayloadSSMessage()
        message.data = {
            'destination' : "1",
            'payload' : observation.getObservationPayload(),
            'type': 'payload',
            'protocol': 'SingleStep'
        }
        drone2.networkInterface.sendMessage(message)

        sim.performTurn()

        self.assertTrue(
            isOnFire(drone1.map[0][0]) and
            isOnFire(drone1.map[0][1]) and
            isOnFire(drone1.map[1][0]) and
            isOnFire(drone1.map[1][1])
        )
    
    def test_seeks_fire(self):
        script = EmptyScript()
        tmap = emptyMap(50,50,flammable=True)
        setFire(tmap,0,0)

        ni1 = MockNetworkInterface("1",None,None)
        drone1 = ADrone(ni1,tmap,xpos = 49,ypos = 49)

        self.assertAlmostEqual(drone1.getAction().direction,math.pi * 3 / 4)
        self.assertEqual(drone1.getAction().speed,1)


class TestNetworkInterface(ut.TestCase):
    def test_recieve_message(self):
        routingTable = {"1" : set(["2"]), "2" : set(["1"])}
        ni1 = NetworkInterface("1", routingTable, None)
        ni1.receiveMessage(json.dumps({
            "source" : 0,
            "destination" : "1",
            "type" : "payload",
            "seq" : 0,
            "payload" : "hello",
            "protocol":"SingleStep"
            }))
        self.assertEqual(ni1.getIncoming(),"hello")

class TestDynamicRouting(ut.TestCase):
    def test_recieves_and_acks_payload_message(self):
        routingTable = {"1" : set(["2"]), "2" : set(["1"])}
        infoTable = {
            "1" : {"type" : "A", "xpos" : 0, "ypos" : 0, "timestamp" : 0},
            "2" : {"type" : "A", "xpos" : 1, "ypos" : 1, "timestamp" : 0},
            "3" : {"type" : "B", "xpos" : 4, "ypos" : 5, "timestamp" : 0}}
        singleStepNI = MockSingleStepNI("1",set(),None)
        dynamicRoutingNI = DynamicRoutingNI("1",singleStepNI,routingTable,infoTable)
        payloadMessage = PayloadDRMessage()
        payloadMessage.data["source"] = "2"
        payloadMessage.data["destination"] = "1"
        payloadMessage.data["payload"] = "payload1"
        payloadMessage.data["seq"] = 1
        payloadMessage.data["timestamp"] = 0
        payloadMessage.data["route"] = {"2" : "1"}
        dynamicRoutingNI.receiveMessage(payloadMessage)
        self.assertIn("payload1",dynamicRoutingNI.incoming)

        self.assertEqual(2,len(singleStepNI.sendPayloads))
        m1 = singleStepNI.sendPayloads[0]
        m2 = singleStepNI.sendPayloads[1]
        p1 = Message(m1.data["payload"])
        p2 = Message(m2.data["payload"])
        if p1.data["type"] == "payloadAck":
            ackPay = p1
            ack = p2
        else:
            ackPay = p2
            ack = p1
        self.assertEqual("payloadAck",ackPay.data["type"])
        self.assertEqual("ack",ack.data["type"])
        
    
    def test_bounce_message(self):
        routingTable = {"1" : set(["2"]), "2" : set(["1","3"]), "3" : set(["2"])}
        infoTable = {
            "1" : {"type" : "A", "xpos" : 0, "ypos" : 0, "timestamp" : 0},
            "2" : {"type" : "A", "xpos" : 1, "ypos" : 1, "timestamp" : 0},
            "3" : {"type" : "B", "xpos" : 4, "ypos" : 5, "timestamp" : 0}}
        singleStepNI = MockSingleStepNI("2",set(),None)
        dynamicRoutingNI = DynamicRoutingNI("2",singleStepNI,routingTable,infoTable)
        payloadMessage = PayloadDRMessage()
        payloadMessage.data["source"] = "1"
        payloadMessage.data["destination"] = "3"
        payloadMessage.data["payload"] = "payload1"
        payloadMessage.data["type"] = "payload"
        payloadMessage.data["seq"] = 1
        payloadMessage.data["timestamp"] = 0
        payloadMessage.data["route"] = {"1" : "2", "2" : "3"}
        dynamicRoutingNI.receiveMessage(payloadMessage)

        self.assertEqual(2,len(singleStepNI.sendPayloads))
        m1 = singleStepNI.sendPayloads[0]
        m2 = singleStepNI.sendPayloads[1]
        p1 = Message(m1.data["payload"])
        p2 = Message(m2.data["payload"])
        if p1.data["type"] == "payload":
            pay = p1
            ack = p2
        else:
            pay = p2
            ack = p1
        print(p1.data)
        print(p2.data)
        self.assertEqual("payload",pay.data["type"])
        self.assertEqual("ack",ack.data["type"])

    def test_multiple_jumps(self):
        routingTable = {"1" : set(["2"]), "2" : set(["1","3"]), "3" : set(["2"])}
        infoTable = {
            "1" : {"type" : "A", "xpos" : 0, "ypos" : 0, "timestamp" : 0},
            "2" : {"type" : "A", "xpos" : 1, "ypos" : 1, "timestamp" : 0},
            "3" : {"type" : "B", "xpos" : 4, "ypos" : 5, "timestamp" : 0}}
        networkInterface1 = NetworkInterface("1",routingTable,infoTable)
        networkInterface2 = NetworkInterface("2",routingTable,infoTable)
        networkInterface3 = NetworkInterface("3",routingTable,infoTable)
        payloadMessage = PayloadDRMessage()
        payloadMessage.data["source"] = "1"
        payloadMessage.data["destination"] = "3"
        payloadMessage.data["payload"] = "payload1"
        payloadMessage.data["type"] = "payload"
        payloadMessage.data["seq"] = 1
        payloadMessage.data["timestamp"] = 0
        payloadMessage.data["route"] = {"1" : "2", "2" : "3"}
        payloadMessage.data["protocol"] = "DynamicRouting"
        networkInterface1.sendMessage(payloadMessage)
        while True:
            m = networkInterface1.getOutgoing()
            if not m:
                break
            networkInterface2.receiveMessage(m)
        while True:
            m = networkInterface2.getOutgoing()
            if not m:
                break
            networkInterface1.receiveMessage(m)
            networkInterface3.receiveMessage(m)
        self.assertEqual("payload1",networkInterface3.getIncoming())

    def test_correct_routing(self):
        routingTable = {"1" : set(["2"]), "2" : set(["1","3"]), "3" : set(["2"])}
        infoTable = {
            "1" : {"type" : "A", "xpos" : 0, "ypos" : 0, "timestamp" : 0},
            "2" : {"type" : "A", "xpos" : 1, "ypos" : 1, "timestamp" : 0},
            "3" : {"type" : "B", "xpos" : 4, "ypos" : 5, "timestamp" : 0}}
        networkInterface1 = NetworkInterface("1",routingTable,infoTable)
        networkInterface2 = NetworkInterface("2",routingTable,infoTable)
        networkInterface3 = NetworkInterface("3",routingTable,infoTable)
        payloadMessage = PayloadDRMessage()
        payloadMessage.data["source"] = "1"
        payloadMessage.data["destination"] = "3"
        payloadMessage.data["payload"] = "payload1"
        payloadMessage.data["type"] = "payload"
        payloadMessage.data["seq"] = 1
        payloadMessage.data["timestamp"] = 0
        payloadMessage.data["route"] = {"1" : "2", "2" : "3"}
        payloadMessage.data["protocol"] = "DynamicRouting"
        networkInterface1.sendMessage(payloadMessage)
        networkInterface1.getOutgoing()
        while True:
            networkInterface1.tick()
            m = networkInterface1.getOutgoing()
            if m:
                break
        ping = PingSSMessage(m)
        self.assertEqual("SingleStep",ping.data["protocol"])
        self.assertEqual("ping",ping.data["type"])
        networkInterface3.receiveMessage(m)

        m = networkInterface3.getOutgoing()
        pong = PongSSMessage(m)
        self.assertEqual("SingleStep",pong.data["protocol"])
        self.assertEqual("pong",pong.data["type"])

        networkInterface1.receiveMessage(m)
        count = 0
        while count < 3:
            networkInterface1.tick()
            m = networkInterface1.getOutgoing()
            if m:
                networkInterface3.receiveMessage(m)
                count += 1
                print(m)
        self.assertEqual(set(["3"]),networkInterface1.dynamicRoutingNI.routingTable["1"])
        self.assertEqual(set(["3"]),networkInterface3.dynamicRoutingNI.routingTable["1"])
        p = networkInterface3.getIncoming()
        self.assertEqual("payload1",p)

    def test_predicate_evaluation(self):
        routingTable = {"1" : set(["2"]), "2" : set(["1","3"]), "3" : set(["2"])}
        infoTable = {
            "1" : {"type" : "A", "xpos" : 0, "ypos" : 0, "timestamp" : 0},
            "2" : {"type" : "A", "xpos" : 1, "ypos" : 1, "timestamp" : 0},
            "3" : {"type" : "B", "xpos" : 4, "ypos" : 5, "timestamp" : 0}}
        networkInterface1 = NetworkInterface("1",routingTable,infoTable)
        drones = networkInterface1.dynamicRoutingNI.fulfillsPredicate(["typeA",["varDrone"]])
        self.assertEqual(set(["1","2"]),drones)

        drones = networkInterface1.dynamicRoutingNI.fulfillsPredicate(["less",["dist",["xpos",["varDrone"]],["ypos",["varDrone"]],["num",1],["num",0]],["num",1.3]])
        self.assertEqual(set(["1","2"]),drones)
        
    def test_predicast_reaches_destination(self):
        script = EmptyScript()
        tmap = emptyMap(50,50,flammable=True)
        routingTable = {"1" : set(["2"]), "2" : set(["1","3"]), "3" : set(["2","4"]), "4" : set(["3"])}
        infoTable = {
            "1" : {"type" : "B", "xpos" : 0, "ypos" : 0, "timestamp" : 0},
            "2" : {"type" : "B", "xpos" : 5, "ypos" : 5, "timestamp" : 0},
            "3" : {"type" : "B", "xpos" : 10, "ypos" : 10, "timestamp" : 0},
            "4" : {"type" : "A", "xpos" : 15, "ypos" : 15, "timestamp" : 0}}
        ni1 = NetworkInterface("1",routingTable, infoTable)
        ni2 = NetworkInterface("2",routingTable, infoTable)
        ni3 = NetworkInterface("3",routingTable, infoTable)
        ni4 = NetworkInterface("4",routingTable, infoTable)
        drone1 = BDrone(ni1,tmap,xpos = 0,ypos = 0)
        drone2 = BDrone(ni2,tmap,xpos = 5,ypos = 5)
        drone3 = BDrone(ni3,tmap,xpos = 10,ypos = 10)
        drone4 = ADrone(ni4,tmap,xpos = 15,ypos = 15)
        sim = Simulator(tmap,script,[drone4],[drone1,drone2,drone3],transmissionDistance=10,lineOfSight=2)
        predicate = [
            "and",
                ["typeA",["varDrone"]],
                ["less",
                    ["dist",["xpos",["varDrone"]],["ypos",["varDrone"]],["num",0],["num",15]],
                    ["num",20]]
        ]
        observation = Observation()
        observation.tiles.append((3,0,15))
        message = PredicastDRMessage()
        message.data["predicate"] = predicate
        message.data["payload"] = observation.getObservationPayload()
        drone1.networkInterface.sendMessage(message)

        sim.performTurn()
        sim.performTurn()
        sim.performTurn()

        self.assertLess(drone4.xpos,15)