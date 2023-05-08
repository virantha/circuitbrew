from random import randint
from circuitbrew.module import Module, Parameterize
from circuitbrew.ports import InputPort
from circuitbrew.compound_ports import SupplyPort, E1of2InputPort, E1of2OutputPort
from circuitbrew.gates import NorN
from circuitbrew.gates import Inv_x1 as Inv

from circuitbrew.qdi import Celement2

class Wchb(Module):
    l = E1of2InputPort()
    r = E1of2OutputPort()
    _pReset = InputPort()
    p = SupplyPort()

    def build(self):

        self.c2_t = Celement2(i=[self.l.t, self.r.e], o = self.r.t, p=self.p)
        self.c2_f = Celement2(i=[self.l.f, self.r.e], o = self.r.f, p=self.p)
        self.inv_mypreset = Inv(inp=self._pReset, p=self.p)
        mypreset = self.inv_mypreset.out

        self.nor = Parameterize(NorN, N=3)(a=[self.r.t, self.r.f, mypreset], 
                                           b=self.l.e, p=self.p)
        self.finalize()

    async def sim(self):
        while True:
            val = await self.l.recv()
            await self.r.send(val)
