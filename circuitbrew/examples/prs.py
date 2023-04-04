from random import randint
from module import *
from ports import *
from globals import SupplyPort
from elements import Supply, VerilogClock, VerilogSrc, VoltageSource
from fets import *

class Inv(Module):
    a = InputPort()
    b = OutputPort()

    p = SupplyPort()

    def build(self):
        self.pup = Pfet()
        self.ndn = Nfet()
        self.pup.g = self.a
        self.pup.d = self.p.vdd
        self.pup.s = self.b
        self.pup.b = self.p.vdd

        self.ndn.g = self.a
        self.ndn.d = self.b
        self.ndn.s = self.p.gnd
        self.ndn.b = self.p.gnd
        self.finalize()

    
class And(Module):
    a = InputPort()
    b = InputPort()
    c = OutputPort()

    p = SupplyPort()

    def build(self):
        pdn = self.a & self.b
        pup = ~self.a | ~self.b
        self.stack = self.make_stacks(output=self.c, pdn=pdn, pup=pup, power=self.p)
        self.finalize()


class Main(Module):
    a=InputPorts(width=2)
    b=OutputPort()
    p=SupplyPort()

    def build(self):
        self.supply = Supply('vdd', 0.8)
        self.supply.p = self.p

        self.inv = Inv('myinv')
        mya = self.a
        self.inv.p = self.p
        self.inv.a = self.a[0]
        self.inv.b = self.b

        N=10
        self.my_ands = []
        for i in range(N):
            my_and = And('myand')
            my_and.a = self.a[0]
            my_and.b = self.a[1]
            my_and.c = self.b
            my_and.p = self.p
            self.my_ands.append(my_and)
        
        self.clk_gen = VerilogClock('clk', freq=750e3)
        self.clk_gen.enable = self.p.vdd
        
        clk = self.clk_gen.clk
        self.src = VerilogSrc('src', [randint(0,1) for i in range(10)])
        self.src.clk = clk
        self.src.d = self.a[0]
        self.src._reset = self.p.vdd

        self.src2 = VerilogSrc('src2', [randint(0,1) for i in range(10)])
        self.src.clk = clk
        self.src.d = self.a[1]
        self.src._reset = self.p.vdd
        self.finalize()