#general test of software componenents
import unittest as ut
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
        