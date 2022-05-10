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
        assert(len(sim.BDrones[0].networkInterface.log) == 0)
    
    def test_drop_retry(self):
        #D1 sends message to D2 which is dropped during transmission. Succeeds on retry.
        script = Script(retry)
        map = emptyMap(100,100)
        ADrones = [ADrone(NetworkInterface("D1"),map, 0, 0)]
        BDrones = [BDrone(NetworkInterface("D2"),map, 2, 2)]
        sim = Simulator(map,script,ADrones,BDrones)
        sim.performTurn()
        assert(len(sim.BDrones[0].networkInterface.log) == 1)

class TestMessageDelivered(ut.TestCase):
    def test_deliver_message(self):
        # D1 sends message to D2
        script = Script(succeed1)
        map = emptyMap(100,100)
        ADrones = [ADrone(NetworkInterface("D1"),map, 0, 0)]
        BDrones = [BDrone(NetworkInterface("D2"),map, 2, 2)]
        sim = Simulator(map,script,ADrones,BDrones)
        sim.performTurn()
        assert(len(sim.ADrones[0].networkInterface.log) > 0)

    def test_propagate_message(self):
        # D1 sends a message to D2 by propagating it through D3
        script = Script(succeed1)
        map = emptyMap(100,100)
        ADrones = [ADrone(NetworkInterface("D1"),map, 0, 0)]
        BDrones = [BDrone(NetworkInterface("D2"),map, 6, 6), BDrone(NetworkInterface("D3"),map, 3, 3)]
        sim = Simulator(map,script,ADrones,BDrones)
        sim.performTurn()
        assert(len(sim.ADrones[0].networkInterface.log) > 0)
    
    #TODO: Test that ACK is received and stops resends
    def test_deliver_ack_message(self):
        # D1 sends message to D2. D2 sends ack to D1
        script = Script(succeed1)
        map = emptyMap(100,100)
        ADrones = [ADrone(NetworkInterface("D1"),map, 0, 0)]
        BDrones = [BDrone(NetworkInterface("D2"),map, 2, 2)]
        sim = Simulator(map,script,ADrones,BDrones, transmissionsPerTurn=1)
        sim.performTurn()
        assert(len(sim.ADrones[0].networkInterface.log) == 1)
        assert("ack" in sim.ADrones[0].networkInterface.outGoing[0])
        # Still awaiting ack
        assert(1 in sim.BDrones[0].networkInterface.timeouts.keys()) 
        sim.performTurn()
        # Ack received, deleting message.
        assert(1 not in sim.BDrones[0].networkInterface.timeouts.keys())