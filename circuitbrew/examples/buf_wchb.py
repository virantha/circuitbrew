from circuitbrew.qdi import Wchb, VerilogBucketE1of2, VerilogSrcE1of2
from circuitbrew.module import Module
from circuitbrew.elements import Supply, ResetPulse

class Main(Module):
    def build(self):
        self.supply = Supply('vdd', self.sim_setup['voltage'], 
                             measure=True )
        self.p = self.supply.p
        p = self.supply.p
        self._preset_pulse = ResetPulse('preset', p=p, slope=0.5)
        self._sreset_pulse = ResetPulse('sreset', p=p)
        

        _pR = self._preset_pulse.node

        self.buf = Wchb('wchb', _pReset=_pR, p=p)

        #_sR = self._sreset_pulse.node
        l = self.buf.l
        r = self.buf.r

        self.src = VerilogSrcE1of2(
            name = 'src', values=[0,1,0,1,1],
            _pReset=_pR, _sReset=self._sreset_pulse.node, l=l)

        self.buc = VerilogBucketE1of2(
            name='buc',
            _pReset=_pR, _sReset=self._sreset_pulse.node, l=r)

        self.finalize()