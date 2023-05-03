from circuitbrew.module import Module
from circuitbrew.ports import InputPort, OutputPort
from circuitbrew.compound_ports import SupplyPort
from circuitbrew.fets import Nfet, Pfet

class Inverter(Module):
    a = InputPort()
    b = OutputPort()
    p = SupplyPort()

    def build(self):
        vdd, gnd = self.p.vdd, self.p.gnd
        self.pup = Pfet(g=self.a, d=vdd, s=self.b, b=vdd)
        self.ndn = Nfet(g=self.a, d=self.b, s=gnd, b=gnd)
        self.finalize()

class Main(Module):

    def build(self):
        self.inv = Inverter('myinv')
        self.finalize()