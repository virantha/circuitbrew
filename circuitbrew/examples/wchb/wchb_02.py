from random import randint
from circuitbrew.module import Module
from circuitbrew.elements import Supply, ResetPulse
from circuitbrew.qdi import Wchb, VerilogBucketE1of2, VerilogSrcE1of2

class Main(Module):
    def build(self):
        self.supply = Supply('vdd', self.sim_setup['voltage'], 
                             measure=True )
        self.p = self.supply.p
        p = self.supply.p
        self._preset_pulse = ResetPulse('preset', p=p)
        self._sreset_pulse = ResetPulse('sreset', p=p)
        

        _pR = self._preset_pulse.node

        # Set up a chain of wchbs
        N = 4
        self.buf = [ Wchb(f'wchb_{i}', _pReset=_pR, p=p)
                        for i in range(N)
                    ]
        # Connect the wchbs
        for i in range(1,N):
            self.buf[i].l = self.buf[i-1].r

        _sR = self._sreset_pulse.node
        l = self.buf[0].l
        r = self.buf[N-1].r

        self.src = VerilogSrcE1of2(
            name = 'src', values=[randint(0,1) for i in range(10)],
            _pReset=_pR, _sReset= _sR)
        self.src.l = self.buf[0].l

        self.buc = VerilogBucketE1of2(
            name='buc',
            _pReset=_pR, _sReset=self._sreset_pulse.node, l=r)

        self.finalize()