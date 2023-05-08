from .compound_ports import SupplyPort, CompoundPort
from .ports import InputPort, OutputPort, InputPorts, OutputPorts
from .fets import Nfet, Pfet
from .module import Module, SourceModule, Param, Parameterize
from .elements import VerilogParametrizedModule

class Inv(Module):
    """ Parametrized (n/p sizing and vt choice) inverter

        Examples:
            A n/p = 2/3 standard-vt Inverter:

            >>> self.inv = Parameterize(Inv, n_strength=2, p_strength=3, vt='svt')()

            Connecting ports:

            >>> self.inv = Parameterize(Inv, n_strength=2, p_strength=3, vt='svt')(
                                inp=INPUT, out=OUTPUT, p=SUPPLY)

            Multiple instances:

            >>> Inv_x4 = Parameterize(Inv, n_strength=4, p_strength=4, vt='svt')
            >>> self.inverters = [Inv_x4() for i in range(2)] # Create two x4 inverters


        Args:

            inp (InputPort): Input node
            out (OutputPort): Output node
            p (SupplyPort): Power/gnd port

    """
    inp = InputPort()
    out = OutputPort()

    p = SupplyPort()

    n_strength : Param
    p_strength : Param
    vt         : Param

    def build(self):
        """ Two transistors """

        self.pup = Pfet(w=self.p_strength, vt=self.vt,
                        g=self.inp, d=self.p.vdd, s=self.out, b=self.p.vdd)
        self.ndn = Nfet(w=self.n_strength, vt=self.vt,
                        g=self.inp, d=self.p.gnd, s=self.out, b=self.p.gnd)

        self.finalize()

    async def sim(self):
        """ Sim method """
        while True:
            val = await self.inp.recv()
            await self.out.send(1-val)

Inv_x1 = Parameterize (Inv, p_strength=1, n_strength=1, vt='svt')
"""A x1 Inverter ready to instantiate"""

Inv_x2 = Parameterize (Inv, p_strength=2, n_strength=2, vt='svt')
"""A x2 Inverter ready to instantiate"""

class NorN(Module):
    """ Parametrized (number of inputs) NOR gate

        Examples:
            A two-input NOR

            >>> self.nor = Parameterize(NorN, N=2)()

            Connecting ports:

            >>> self.nor = Parameterize(NorN, N=2)(
                                a=INPUT, b=OUTPUT, p=SUPPLY)

        Args:

            a (InputPorts): Input nodes (parameterized)
            b (OutputPort): Output node
            p (SupplyPort): Power/gnd port

    
    """
    N: Param

    a = InputPorts(width=Param('N'))
    b = OutputPort()
    p = SupplyPort()

    def build(self):
        """ Transistor implementation """

        p = self.p
        N = self.N
        pdn = self.a[0]
        pup = ~self.a[0]

        for i in range(1,N):
             pdn |= self.a[i]
             pup &= ~self.a[i]

        self.nor = self.make_stacks(output=self.b, pdn=pdn, pup=pup, power=p)
        self.finalize()

    async def sim(self):
        """ Sim method """
        while True:
            a_vals = await self.a.recv()
            b_val = not any(a_vals)
            b_val = int(b_val) # Convert bool to 0 or 1
            await self.b.send(b_val)