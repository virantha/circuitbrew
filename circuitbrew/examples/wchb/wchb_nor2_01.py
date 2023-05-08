
class NorN(Module):
    N: Param

    a = InputPorts(width=Param('N'))
    b = OutputPort()
    p = SupplyPort()