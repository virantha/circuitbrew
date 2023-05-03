from circuitbrew.module import Module
from circuitbrew.ports import InputPort, OutputPort

class Inverter(Module):
    a = InputPort()
    b = OutputPort()

