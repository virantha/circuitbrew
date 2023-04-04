from module import Leaf
from ports import *

class Measure(Leaf):
    node = Port()


class Freq(Measure):

    def get_instance_spice(self, scope):
        node_name = ' '.join(self._get_instance_ports(scope))
        msr = []
        msr.append(f'.measure TRAN cycletime{self._id} trig v({node_name}) val=0.4 TD=1ns RISE=2 TARG v({node_name}) val=0.4 RISE=3')
        msr.append(f".measure TRAN freq{self._id} PARAM='1/cycletime{self._id}' ")
        return '\n'.join(msr)
