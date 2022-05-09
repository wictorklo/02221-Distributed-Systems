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
        map = emptyMap(100,100)
        ADrones = [ADrone(NetworkInterface("D1"),map, 0, 0)]
        BDrones = [BDrone(NetworkInterface("D2"),map, 2, 2)]
        sim = Simulator(map,script,ADrones,BDrones)
        sim.performTurn()
        assert(sim.BDrones[0].networkInterface.getOutgoing() == None)

class TestMessageDelivered(ut.TestCase):
    def test_Deliver_message(self):
        # D1 sends message to D2
        script = Script(succeed1)
        map = emptyMap(100,100)
        ADrones = [ADrone(NetworkInterface("D1"),map, 0, 0)]
        BDrones = [BDrone(NetworkInterface("D2"),map, 2, 2)]
        sim = Simulator(map,script,ADrones,BDrones)
        sim.performTurn()
        assert(sim.BDrones[0].networkInterface.getIncoming() != None)

    def test_propagate_message(self):
        # D1 sends a message to D2 by propagating it through D3
        script = Script(succeed1)
        map = emptyMap(100,100)
        ADrones = [ADrone(NetworkInterface("D1"),map, 0, 0)]
        BDrones = [BDrone(NetworkInterface("D2"),map, 6, 6), BDrone(NetworkInterface("D3"),map, 3, 3)]
        sim = Simulator(map,script,ADrones,BDrones)
        sim.performTurn()
        assert(sim.BDrones[0].networkInterface.getIncoming() != None)
