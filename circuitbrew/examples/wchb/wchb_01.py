from random import randint
from circuitbrew.module import Module
from circuitbrew.ports import InputPort, OutputPort
from circuitbrew.compound_ports import SupplyPort
from circuitbrew.fets import Nfet, Pfet
from circuitbrew.elements import Supply, VerilogClock, VerilogSrc, VerilogBucket

class Inverter(Module):
    a = InputPort()
    b = OutputPort()
    p = SupplyPort()

    def build(self):
        vdd, gnd = self.p.vdd, self.p.gnd
        self.pup = Pfet(g=self.a, d=vdd, s=self.b, b=vdd)
        self.ndn = Nfet(g=self.a, d=self.b, s=gnd, b=gnd)
        self.finalize()

    async def sim(self):
        while True:
            val = await self.a.recv()
            await self.b.send(1-val)

class Main(Module):

    def build(self):
        # Voltage supply
        self.supply = Supply(name='vdd', voltage=self.sim_setup['voltage'])
        p = self.supply.p
        vdd, gnd = p.vdd, p.gnd
        
        # Change the clock to drive the VerilogSrc instead of the Inverter
        self.clk_gen = VerilogClock('clk', freq=300e3, enable=vdd)

        # Sequence of input test vectors on output node 'd'
        vals = [randint(0,1) for i in range(10)]
        self.src = VerilogSrc('src', values=vals,
                              clk=self.clk_gen.clk, _reset=vdd)
        inv_in = self.src.d
        self.inv = Inverter('myinv', a=inv_in, p=p)
        
        # A sampling clock for checking expected output of the inverter
        self.clk_buc = VerilogClock('clk_buc', freq=300e3, offset='100p', enable=vdd)

        self.bucket = VerilogBucket(name='buc', # values=expected, no longer needed 
                                    clk=self.clk_buc.clk, _reset=vdd, d=self.inv.b)
        self.finalize()