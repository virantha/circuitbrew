from .module import Leaf
from .ports import *

class Fet(Leaf):

    d = Port()
    g = InputPort()
    s = Port()
    b = Port()

    def get_instance_spice(self, scope):
        connected = ' '.join(self._get_instance_ports(scope))
        s = f'xm{self.inst_prefix}{self._id} {connected} {self.fet_type} {self.width_id}={self.w} l={self.l}'
        return s

class Nfet(Fet):

    inst_prefix = 'n'

    def post_init(self):
        self.fet_type = getattr(self, self.vt)

    def connect_power(self, p):
        p.gnd = self.b

class Pfet(Fet):

    inst_prefix = 'p'

    def post_init(self):
        self.fet_type = getattr(self, self.vt)

    def connect_power(self, p):
        p.vdd = self.b