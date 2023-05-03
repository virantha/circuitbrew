from random import randint
from circuitbrew.module import Module
from circuitbrew.ports import InputPort, OutputPort
from circuitbrew.compound_ports import SupplyPort
from circuitbrew.fets import Nfet, Pfet

class Inv(Module):
    inp = InputPort()
    out = OutputPort()

    p = SupplyPort()

    def build(self):
        vdd, gnd = self.p.vdd, self.p.gnd
        self.pup = Pfet(g=self.inp, d=vdd, s=self.out, b=vdd)
        self.ndn = Nfet(g=self.inp, d=self.out, s=gnd, b=gnd)
        self.finalize()

class Main(Module):

    def build(self):
        self.inv = Inv('myinv')
        self.finalize()