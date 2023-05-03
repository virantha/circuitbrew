from circuitbrew.module import Module
from circuitbrew.ports import InputPort, OutputPort
from circuitbrew.compound_ports import SupplyPort

class Inverter(Module):
    a = InputPort()
    b = OutputPort()
    p = SupplyPort()

