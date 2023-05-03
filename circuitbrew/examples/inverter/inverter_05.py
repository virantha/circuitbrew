from circuitbrew.module import Module
from circuitbrew.ports import InputPort, OutputPort
from circuitbrew.compound_ports import SupplyPort
from circuitbrew.fets import Nfet, Pfet
from circuitbrew.elements import Supply, VerilogClock

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
        # Voltage supply
        self.supply = Supply(name='vdd', voltage=self.sim_setup['voltage'])
        p = self.supply.p
        vdd, gnd = p.vdd, p.gnd
        
        # Create a clock signal to act as input to inverter
        self.clk_gen = VerilogClock('clk', freq=300e3, enable=vdd)
        inv_in = self.clk_gen.clk

        self.inv = Inverter('myinv', a=inv_in, p=p)
        
        self.finalize()