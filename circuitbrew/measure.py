from module import Leaf
from ports import *

class Measure(Leaf):
    node = Port()


class Freq(Measure):

    def __init__(self, name='', first_transition=2, second_transition=3, **kwargs):
        self.first_transition = first_transition
        self.second_transition = second_transition
        super().__init__(name=name, **kwargs)

    def get_instance_spice(self, scope):
        node_name = ' '.join(self._get_instance_ports(scope))
        msr = []
        vdd = float(self.sim_setup['voltage'])
        cross_vdd = vdd/2
        msr.append(f'.measure TRAN cycletime{self._id} trig v({node_name}) val={cross_vdd} TD=1ns RISE={self.first_transition} \
                   \n+ TARG v({node_name}) val={cross_vdd} RISE={self.second_transition}')
        msr.append(f".measure TRAN freq{self._id} PARAM='1/cycletime{self._id}' ")
        return '\n'.join(msr)

class Power(Measure):

    def __init__(self, name='', voltage_source=None,start_time=None, end_time=None, **kwargs):
        super().__init__(name=name, **kwargs)
        self.start_time = start_time
        self.end_time = end_time
        self.voltage_source = voltage_source

    def get_instance_spice(self, scope):
        assert self.voltage_source, f'Must specify a voltage source in {self}'
        node_name = f'V{self.voltage_source.name}'
        msr = []
        start_str = f'from={self.start_time}' if self.start_time else ''
        end_str   = f'to={self.end_time}' if self.end_time else ''
        msr.append(f'.measure TRAN supplycurrent{self._id} avg i({node_name}) {start_str} {end_str}')
        msr.append(f".measure TRAN supplypower{self._id} PARAM='-supplycurrent{self._id}*{self.sim_setup['voltage']}'")
        msr.append(f".measure TRAN supplypower_direct{self._id} AVG P({node_name}) {start_str} {end_str}")
        return '\n'.join(msr)
