from random import randint
from module import *
from ports import *
from globals import SupplyPort
from elements import Supply, VerilogClock, VerilogSrc, VerilogBucket
from fets import *
from measure import Freq, Power

class Inv(Module):
    inp = InputPort()
    out = OutputPort()

    p = SupplyPort()

    def build(self):
        p = self.p
        self.pup = Pfet()
        self.pup.g = self.inp
        self.pup.d = self.p.vdd
        self.pup.s = self.out
        self.pup.b = self.p.vdd

        input = self.inp
        self.ndn = Nfet(g=input, d=self.out, s=p.gnd, b=p.gnd)
        # self.ndn.g = self.inp
        #self.ndn.d = self.out
        #self.ndn.s = self.p.gnd
        #self.ndn.b = self.p.gnd
        self.finalize()

    async def sim(self):
        while True:
            val = await self.inp.recv()
            await self.out.send(1-val)
    

class Buf(Module):
    a = InputPort()
    b = OutputPort()
    p = SupplyPort()

    def build(self):
        self.inv1 = Inv('inv1', p=self.p)
        self.inv2 = Inv('inv2', p=self.p)
        self.inv1.inp = self.a
        _a = self.inv1.out
        self.inv2.inp = _a
        self.inv2.out = self.b
        self.finalize()

class Main(Module):

    def build(self):
        self.supply = Supply('vdd', self.sim_setup['voltage'], 
                             measure=True )
        self.p = self.supply.p
        p = self.supply.p

        self.buf = Buf('mybuf', p=p)
        buf_in = self.buf.a

        self.clk_gen = VerilogClock('clk', freq=750e3, enable=p.vdd)
        clk = self.clk_gen.clk

        self.clk_buc = VerilogClock('clk2', freq=750e3, offset='100p',enable=p.vdd)
        clk2 = self.clk_buc.clk

        self.src = VerilogSrc('src', [randint(0,1) for i in range(10)], 
                            d=buf_in, clk=clk, _reset=p.vdd)

        #self.src2 = VerilogSrc('src2', [randint(0,1) for i in range(10)])

        self.bucket = VerilogBucket(name='buc', clk=clk2, _reset=p.vdd, d=self.buf.b)
        self.msr_freq = Freq(node=self.buf.b, first_transition=4, second_transition=5)
        self.finalize()