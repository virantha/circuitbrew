from .module import Leaf
from .ports import *
from .compound_ports import SupplyPort

class Fet(Leaf):
    """ Transistor cell

            d: Drain
            g: Gate
            s: Source
            b: Bulk
            w (Optional[str]): width
            l (Optional[str]): length
            
    """
    d = Port()
    g = InputPort()
    s = Port()
    b = Port()

    def get_instance_spice(self, scope):
        connected = ' '.join(self._get_instance_ports(scope))
        s = f'xm{self.inst_prefix}{self._id} {connected} {self.fet_type} {self.width_id}={self.w} l={self.l}'
        return s

class Nfet(Fet):
    """Nfet
    """

    inst_prefix = 'n'

    def post_init(self):
        self.fet_type = getattr(self, self.vt)

    def connect_power(self, p: SupplyPort):
        """ Called when creating stacks (production rules) to make sure
            the bulk is connected to gnd.
        """
        p.gnd = self.b

class Pfet(Fet):
    """Pfet

    """

    inst_prefix = 'p'

    def post_init(self):
        self.fet_type = getattr(self, self.vt)

    def connect_power(self, p:SupplyPort):
        """ Called when creating stacks (production rules) to make sure
            the bulk is connected to vdd.
        """
        p.vdd = self.b