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
    async def sim(self):
        while True:
            val = await self.inp.recv()
            await self.out.send(1-val)

class Nand(Module):
    a = InputPorts(width=2)
    #a = InputPort()
    #b = InputPort()
    out = OutputPort()
    p = SupplyPort()

    def build(self):
        
        self.stack = self.make_stacks(
            output = self.out,
            pdn = self.a[0] & self.a[1],
            pup = ~self.a[0] | ~self.a[1],
            # pdn    = self.a & self.b,
            # pup    = ~self.a | ~self.b,
            power  = self.p
        )

        self.finalize()
    
    
    async def sim(self):
        while True:
            val_a = await self.a[0].recv()
            val_b = await self.a[1].recv()
            await self.out.send(1-(val_a & val_b))

class Main(Module):


    def build(self):
        self.supply = Supply('vdd', self.sim_setup['voltage'])
        p = self.supply.p
        self.clk_gen = VerilogClock('clk', freq=750e3, enable=p.vdd)
        self.clk_buc = VerilogClock('clk2', freq=750e3, offset='100p',enable=self.supply.p.vdd)

        clk = self.clk_gen.clk
        clk2 = self.clk_buc.clk


        self.myinv = Inv(p=p)
        self.myinv2 = Inv(p=p)
        out = [self.myinv.out, self.myinv2.out]
        inp = [self.myinv.inp, self.myinv2.inp]
        
        self.nand = Nand(a=out, p=p)
        self.src = [
                VerilogSrc(f'src{i}', [randint(0,1) for j in range(10)], 
                            d=inp[i], clk=clk, _reset=p.vdd)
                for i in range(2)
        ]

        # self.src0 = VerilogSrc('src0', [randint(0,1) for i in range(10)], 
        #                      d=inp[0], clk=clk, _reset=p.vdd)
        # self.src1 = VerilogSrc('src1', [randint(0,1) for i in range(10)], 
        #                      d=inp[1], clk=clk, _reset=p.vdd)

        self.bucket = VerilogBucket(name='buc', clk=clk2, _reset=self.supply.p.vdd, d=self.nand.out)
        #self.bucket = VerilogBucket(name='buc', clk=clk2, _reset=self.supply.p.vdd, d=out[0])
        #self.bucket2 = VerilogBucket(name='buc2', clk=clk2, _reset=self.supply.p.vdd, d=out[1])

        self.finalize()