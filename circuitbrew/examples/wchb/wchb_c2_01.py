from circuitbrew.compound_ports import SupplyPort
from circuitbrew.ports import InputPorts, OutputPort
from circuitbrew.module import Module, Parameterize, Param

from .wchb_inverter_01 import Inv

class Celement2(Module):
    i = InputPorts(width=2)
    o = OutputPort()
    p = SupplyPort()

    def build(self):
        p = self.p
        # Let's constnnruct this using combination feedback
        pdn = self.i[0] & self.i[1]
        pup = ~self.i[0] & ~self.i[1]

        self.inv = Parameterize(Inv, n_strength=2, p_strength=2, vt='lvt')(out = self.o, p = p)
        _o = self.inv.inp

        cf_pdn = self.o & (self.i[0] | self.i[1])
        cf_pup = ~self.o & (~self.i[0] | ~self.i[1])

        self.celem = self.make_stacks(output=_o, pdn=pdn, pup=pup, power=p)
        self.cf    = self.make_stacks(output=_o, pdn=cf_pdn, pup=cf_pup, power=p)

        self.finalize()


class Main(Module):
    def build(self):
        self.c2 = Celement2()
        self.finalize()