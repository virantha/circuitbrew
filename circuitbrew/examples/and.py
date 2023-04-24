from random import randint

from circuitbrew.module import *
from circuitbrew.ports import *
from circuitbrew.globals import SupplyPort
from circuitbrew.fets import *
from circuitbrew.elements import VerilogBucket, VerilogClock, VerilogSrc, Supply

class Nand(Module):
    a = InputPorts(width=2)
    b = OutputPort()
    p = SupplyPort()

    def build(self):
        
        self.stack = self.make_stacks(
            output = self.b,
            pdn    = self.a[0] & self.a[1],
            pup    = ~self.a[0] | ~self.a[1],
            power  = self.p
        )

        self.finalize()

    async def sim(self):
        while True:
            val_a = await self.a[0].recv()
            val_b = await self.a[1].recv()
            await self.b.send(1-(val_a & val_b))
    
class Main(Module):

    def build(self):
        self.supply = Supply('vdd', self.sim_setup['voltage'], )
        p = self.supply.p


        self.clk = VerilogClock(name = 'clk', freq=750000, enable=p.vdd)
        self.sample_clk = VerilogClock(name = 'sclk', freq=750000, offset='100p', enable=p.vdd)
        clk = self.clk.clk
        sample_clk = self.sample_clk.clk

        self.src = [VerilogSrc(name   = f'src_a{src_i}', 
                               values = [randint(0,1) for i in range(10)],
                               #d      = a[src_i],
                               clk    = clk,
                               _reset = p.vdd,
                              )
                        for src_i in range(2)]
        self.nand = Nand('mynand', p=p)
        self.nand.a[0] = self.src[0].d
        self.nand.a[1] = self.src[1].d

        b= self.nand.b
        self.buc = VerilogBucket(name = f'buc',
                                 clk = sample_clk,
                                 _reset = p.vdd,
                                 d = b)
        
        self.finalize()