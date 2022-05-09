#general test of software componenents
import json
import unittest as ut
from network_interfaces import NetworkInterface
from simulator import *
from script import *
from util import *
import math

class TestUil(ut.TestCase):
    def test_move_position(self):
        x1,y1 = movePosition(1,3,1,0)
        self.assertAlmostEqual(x1,1)
        self.assertAlmostEqual(y1,4)
        x1,y1 = movePosition(1,3,1,math.pi)
        self.assertAlmostEqual(x1,1)
        self.assertAlmostEqual(y1,2)
        x1,y1 = movePosition(1,3,1,math.pi / 2)
        self.assertAlmostEqual(x1,2)
        self.assertAlmostEqual(y1,3)
        x1,y1 = movePosition(1,3,1,3 * math.pi / 2)
        self.assertAlmostEqual(x1,0)
        self.assertAlmostEqual(y1,3)

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
        ni1 = NetworkInterface(0)
        drone1 = ADrone(ni1,tmap,xpos = 0,ypos = 0)
        drone1.getAction = lambda : Action(1,math.pi / 4)

        sim = Simulator(tmap,script,[drone1],[])

        for i in range(6):
            sim.performTurn()

        self.assertAlmostEqual(sim.ADrones[0].xpos,10,delta=0.0001)
        self.assertAlmostEqual(sim.ADrones[0].ypos,10,delta=0.0001)
        self.assertEqual(math.floor(sim.ADrones[0].xpos),9)
        self.assertEqual(math.floor(sim.ADrones[0].ypos),9)

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
        ni1 = NetworkInterface(0)
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
        ni1 = NetworkInterface(1)
        ni2 = NetworkInterface(2)
        drone1 = ADrone(ni1,tmap,xpos = 1,ypos = 1)
        drone2 = ADrone(ni2,tmap,xpos = 2,ypos = 2)
        drone2.think = lambda : None #turn off mechanism that consumes messages in drone2
        sim = Simulator(tmap,script,[drone1,drone2],[])

        message = Message()
        message.data = {
            "destination" : 2,
            "source" : 1,
            "ttl" : 1,
            "payload" : "hello"
            }
        drone1.networkInterface.sendMessage(message)

        sim.performTurn()

        payload = drone2.networkInterface.getIncoming()
        self.assertEqual(payload,"hello")


class TestNetworkInterface(ut.TestCase):
    def test_recieve_message(self):
        ni1 = NetworkInterface(1)
        ni1.receiveMessage(json.dumps({
            "destination" : 1,
            "source" : 0,
            "ttl" : 1,
            "payload" : "hello"
            }))
        self.assertEqual(ni1.getIncoming(),"hello")

    def test_bounce_message(self):
        ni1 = NetworkInterface(1)
        message = Message()
        message.data = {
            "destination" : 2,
            "source" : 0,
            "ttl" : 1,
            "payload" : "hello"}
        ni1.receiveMessage(message.getTransmit())
        message.data["ttl"] -= 1
        self.assertEqual(Message(ni1.getOutgoing()).data,message.data)
