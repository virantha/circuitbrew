from random import randint
from circuitbrew.module import *
from circuitbrew.ports import *
from circuitbrew.globals import SupplyPort
from circuitbrew.elements import Supply, VerilogClock, VerilogSrc, VerilogBucket
from circuitbrew.fets import *

class Inv(Module):
    inp = InputPort()
    out = OutputPort()

    p = SupplyPort()

    def build(self):
        vdd, gnd = self.p.vdd, self.p.gnd
        self.pup = Pfet(g=self.inp, d=vdd, s=self.out, b=vdd)
        self.ndn = Nfet(g=self.inp, d=self.out, s=gnd, b=gnd)
        self.finalize()

    async def sim(self):
        while True:
            val = await self.inp.recv()
            await self.out.send(1-val)
    

class Main(Module):

    def build(self):
        self.supply = Supply('vdd', self.sim_setup['voltage'], )
        p = self.supply.p
        vdd, gnd = p.vdd, p.gnd
        self.inv = Inv('myinv', p=p)

        self.clk_gen = VerilogClock('clk', freq=750e3, enable=vdd)
        src_clk = self.clk_gen.clk

        self.clk_buc = VerilogClock('clk2', freq=750e3, offset='100p', enable=vdd)
        sample_clk = self.clk_buc.clk

        self.src = VerilogSrc('src', [randint(0,1) for i in range(10)], 
                             d=self.inv.inp, clk=src_clk, _reset=vdd)

        self.bucket = VerilogBucket(name='buc', clk=sample_clk, _reset=vdd, d=self.inv.out)
        self.finalize()