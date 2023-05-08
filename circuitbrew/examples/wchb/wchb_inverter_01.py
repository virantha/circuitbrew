from circuitbrew.compound_ports import SupplyPort
from circuitbrew.ports import InputPort, OutputPort
from circuitbrew.fets import Nfet, Pfet
from circuitbrew.module import Module, Parameterize, Param

class Inv(Module):
    inp = InputPort()
    out = OutputPort()

    p = SupplyPort()

    n_strength : Param
    p_strength : Param
    vt         : Param

    def build(self):

        self.pup = Pfet(w=self.p_strength, vt=self.vt,
                        g=self.inp, d=self.p.vdd, s=self.out, b=self.p.vdd)
        self.ndn = Nfet(w=self.n_strength, vt=self.vt,
                        g=self.inp, d=self.p.gnd, s=self.out, b=self.p.gnd)

        self.finalize()

    async def sim(self):
        while True:
            val = await self.inp.recv()
            await self.out.send(1-val)

class Main(Module):
    def build(self):
        Inv_x3 = Parameterize(Inv, p_strength=3, n_strength=3, vt='svt')
        self.inv = Inv_x3()
        self.finalize()