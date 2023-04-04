from random import randint
from module import *
from ports import *
from globals import SupplyPort
from elements import Supply, VerilogClock, VerilogSrc, VerilogBucket
from fets import *


class Inv(Module):
    inp = InputPort()
    out = OutputPort()

    p = SupplyPort()

    def build(self):

        self.pup = Pfet()
        self.ndn = Nfet()
        self.pup.g = self.inp
        self.pup.d = self.p.vdd
        self.pup.s = self.out
        self.pup.b = self.p.vdd

        self.ndn.g = self.inp
        self.ndn.d = self.out
        self.ndn.s = self.p.gnd
        self.ndn.b = self.p.gnd
        
        #pdn = self.inp & self.inp
        #pup = ~self.inp & ~self.inp
        #self.stack = self.make_stacks(output=self.out, pdn=pdn, pup=pup, power=self.p)

        self.finalize()

    
    

class Main(Module):

    p = SupplyPort()

    def build(self):
        self.supply = Supply('vdd', self.sim_setup['voltage'], p=self.p)
        self.myinv = Inv(p=self.p)

        self.finalize()