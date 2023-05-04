from .compound_ports import SupplyPort, CompoundPort
from .ports import InputPort, OutputPort, InputPorts, OutputPorts
from .fets import Nfet, Pfet
from .module import Module, SourceModule
from .elements import VerilogParametrizedModule

class Inv(Module):
    inp = InputPort()
    out = OutputPort()

    p = SupplyPort()

    def build(self):

        self.pup = Pfet(g=self.inp, d=self.p.vdd, s=self.out, b=self.p.vdd)
        self.ndn = Nfet(g=self.inp, d=self.p.gnd, s=self.out, b=self.p.gnd)

        self.finalize()

    async def sim(self):
        while True:
            val = await self.inp.recv()
            await self.out.send(1-val)

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