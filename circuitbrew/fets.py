from .module import Leaf
from .ports import *

class Fet(Leaf):

    d = Port()
    g = InputPort()
    s = Port()
    b = Port()


    def get_instance_spice(self, scope):
        #connected = ' '.join(terminal.get_instance_spice() for terminal in [self.d, self.g, self.s, self.b])
        connected = ' '.join(self._get_instance_ports(scope))
        self.nfins=2
        s = f'xm{self.inst_prefix}{self._id} {connected} {self.fet_type} nfin={self.nfins} l=0.008u'
        return s

class Nfet(Fet):

    fet_type = 'nch_svt_mac'
    inst_prefix = 'n'

    def connect_power(self, p):
        p.gnd = self.b

class Pfet(Fet):

    fet_type = 'pch_svt_mac'
    inst_prefix = 'p'

    def connect_power(self, p):
        p.vdd = self.b