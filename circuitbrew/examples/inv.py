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
        # self.stack = self.make_stacks(output = self.out,
        #                               pdn = self.inp,
        #                               pup = self.inp,
        #                               power=self.p
        #                               )
        self.finalize()

    async def sim(self):
        while True:
            val = await self.inp.recv()
            await self.out.send(1-val)
    

class Main(Module):

    def build(self):
        self.supply = Supply('vdd', self.sim_setup['voltage'], )
        p = self.supply.p

        self.inv = Inv('myinv', p=p)
        inv_in = self.inv.inp
        #inv_out = self.inv.out

        self.clk_gen = VerilogClock('clk', freq=750e3, enable=p.vdd)
        clk = self.clk_gen.clk

        self.clk_buc = VerilogClock('clk2', freq=750e3, offset='100p',enable=self.supply.p.vdd)
        clk2 = self.clk_buc.clk

        self.src = VerilogSrc('src', [randint(0,1) for i in range(10)], 
                             d=inv_in, clk=clk, _reset=self.supply.p.vdd)

        #self.src2 = VerilogSrc('src2', [randint(0,1) for i in range(10)])

        self.bucket = VerilogBucket(name='buc', clk=clk2, _reset=self.supply.p.vdd, d=self.inv.out)
        self.finalize()