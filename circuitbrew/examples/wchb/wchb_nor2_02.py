from circuitbrew.compound_ports import SupplyPort
from circuitbrew.ports import InputPorts, OutputPort
from circuitbrew.module import Module, Parameterize, Param

class NorN(Module):
    N: Param
    size: Param

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

        self.nor = self.make_stacks(output=self.b, 
                                    pdn=pdn, pup=pup, power=p,
                                    width=self.size)
        self.finalize()

class Main(Module):
    def build(self):
        Nor3 = Parameterize(NorN, N=3, size=2)
        self.nor3 = Nor3()
        self.finalize()