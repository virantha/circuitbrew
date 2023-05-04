from random import randint
from circuitbrew.module import *
from circuitbrew.ports import *
from circuitbrew.compound_ports import SupplyPort
from circuitbrew.elements import Supply, VerilogClock, VerilogSrc, VerilogBucket
from circuitbrew.fets import *


class NorN(Module):
    N: Param

    a = InputPorts(width=Param('N'))
    b = OutputPort()
    p = SupplyPort()

    def build(self):
        p = self.p
        N = self.N
        pdn = self.a[0]
        pup = ~self.a[0]

        for i in range(1,N):
             pdn |= self.a[i]
             pup &= ~self.a[i]

        self.nor = self.make_stacks(output=self.b, pdn=pdn, pup=pup, power=p)
        self.finalize()


class Main(Module):

    def build(self):
        self.supply = Supply('vdd', self.sim_setup['voltage'], )
        p = self.supply.p

        self.nor3 = Parameterize(NorN, N=4)(p=p)
        #self.inv = Inv('myinv', p=p)
        #inv_in = self.inv.inp
        #inv_out = self.inv.out

        # self.clk_gen = VerilogClock('clk', freq=750e3, enable=p.vdd)
        # clk = self.clk_gen.clk

        # self.clk_buc = VerilogClock('clk2', freq=750e3, offset='100p',enable=self.supply.p.vdd)
        # clk2 = self.clk_buc.clk

        # self.src = VerilogSrc('src', [randint(0,1) for i in range(10)], 
        #                      d=inv_in, clk=clk, _reset=self.supply.p.vdd)

        #self.src2 = VerilogSrc('src2', [randint(0,1) for i in range(10)])

        #self.bucket = VerilogBucket(name='buc', clk=clk2, _reset=self.supply.p.vdd, d=self.inv.out)
        self.finalize()