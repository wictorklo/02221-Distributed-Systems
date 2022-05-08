#general test of software componenents
import unittest as ut
from network_interfaces import NWInterface
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
        ni1 = NWInterface()
        drone1 = ADrone(ni1,xpos = 0,ypos = 0)
        drone1.getAction = lambda : Action(1,math.pi / 4)

        script = EmptyScript()
        tmap = emptyMap(10,10)
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


