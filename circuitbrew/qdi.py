import curio, logging
from .compound_ports import SupplyPort, E1of2InputPort, E1of2OutputPort
from .ports import InputPorts, InputPort, OutputPort, OutputPorts 
from .fets import *
from .module import Module, SourceModule
from .elements import VerilogParametrizedModule

logger = logging.getLogger(__name__)


class Nor2(Module):
    a = InputPorts(width=2)
    b = OutputPort()
    p = SupplyPort()

    def build(self):
        p = self.p
        pdn = self.a[0] | self.a[1]
        pup = ~self.a[0]&~self.a[1]
        self.nor = self.make_stacks(output=self.b, pdn=pdn, pup=pup, power=p)
        self.finalize()

    async def sim(self):
        while True:
            val = []
            for i in range(2):
                val.append(await self.a[i].recv())
            if sum(val) > 0:
                await self.out.send(0)
            else:
                await self.out.send(1)

class Nor3(Module):
    a = InputPorts(width=3)
    b = OutputPort()
    p = SupplyPort()

    def build(self):
        p = self.p
        pdn = self.a[0] | self.a[1] | self.a[2]
        pup = ~self.a[0]&~self.a[1]&~self.a[2]
        self.nor = self.make_stacks(output=self.b, pdn=pdn, pup=pup, power=p)
        self.finalize()

    async def sim(self):
        while True:
            val = []
            for i in range(3):
                val.append(await self.a[i].recv())
            if sum(val) > 0:
                await self.out.send(0)
            else:
                await self.out.send(1)

class Celement2(Module):
    i = InputPorts(width=2)
    o = OutputPort()
    p = SupplyPort()

    def build(self):
        p = self.p
        # Let's constnnruct this using combination feedback
        pdn = self.i[0] & self.i[1]
        pup = ~self.i[0] & ~self.i[1]

        self.inv = Inv(out = self.o, p = p)
        _o = self.inv.inp

        cf_pdn = self.o & (self.i[0] | self.i[1])
        cf_pup = ~self.o & (~self.i[0] | ~self.i[1])

        self.celem = self.make_stacks(output=_o, pdn=pdn, pup=pup, power=p)
        self.cf    = self.make_stacks(output=_o, pdn=cf_pdn, pup=cf_pup, power=p)

        self.finalize()

    async def sim(self):
        self.current_val = 0
        while True:
            #val = await self.i[0].recv()
            val = []
            for i in range(2):
                val.append(await self.i[i].recv())
            if val[0] == val[1]:
                self.current_val = val[0]
            await self.out.send(self.current_val)

class Wchb(Module):
    l = E1of2InputPort()
    r = E1of2OutputPort()
    _pReset = InputPort()
    p = SupplyPort()

    def build(self):

        self.c2_t = Celement2(i=[self.l.t, self.r.e], o = self.r.t, p=self.p)
        self.c2_f = Celement2(i=[self.l.f, self.r.e], o = self.r.f, p=self.p)
        self.inv_mypreset = Inv(inp=self._pReset, p=self.p)
        mypreset = self.inv_mypreset.out

        self.nor = Nor3(a=[self.r.t, self.r.f, mypreset], b=self.l.e, p=self.p)

        self.finalize()

    async def sim(self):
        while True:
            logger.debug(f'{self} Waiting to receive')
            val = await self.l.recv()
            logger.debug(f'{self} received {val}')
            await self.r.send(val)
            logger.debug(f'{self} sent {val}')


class VerilogSrcE1of2(VerilogParametrizedModule, SourceModule):
    _pReset = InputPort()
    _sReset = InputPort()
    l = E1of2OutputPort()


    def __init__(self, name, values, **kwargs):
        super().__init__(name=name, **kwargs)
        self.values = values
        self.src_filename = {'hspice': 'hspice_src_1of2.va'}
    
    def get_spice(self):
        simtype = self.sim_setup['sim_type']
        src_filename = self.src_filename[simtype]
        param_dict = {'values': self.values,
                      'nvalues': len(self.values), 
                      'MODULE_NAME': self.get_module_type_name(),
                     }
        output_filename = f'template_{self._id}_{src_filename}'

        self._emit_src_file(src_filename, param_dict, output_filename)

        l = [f'.hdl {output_filename}']
        return l

    async def sim(self):
        for val in self.values:
            await self.l.send(val)

class VerilogBucketE1of2(VerilogParametrizedModule):
    _pReset = InputPort()
    _sReset = InputPort()
    l = E1of2InputPort()


    def __init__(self, name, values=None, **kwargs):
        super().__init__(name=name, **kwargs)
        self.values = values
        self.src_filename = {'hspice': 'hspice_bucket_1of2.va'}

    def get_spice(self):
        simtype = self.sim_setup['sim_type']
        src_filename = self.src_filename[simtype]
        param_dict = {'values': self.values,
                      'nvalues': len(self.values), 
                      'MODULE_NAME': self.get_module_type_name(),
                     }
        output_filename = f'template_{self._id}_{src_filename}'

        self._emit_src_file(src_filename, param_dict, output_filename)

        l = [f'.hdl {output_filename}']
        return l


    async def sim(self):
        if self.values:
            return # No need to sim as user supplied values

        try:
            logger.info(f'Bucket_1of2 {self} waiting')
            vals = []
            while True:
                val = await self.l.recv()
                logger.info(f'Bucket_1of2 {self} received {val}')
                vals.append(val)
        except curio.CancelledError:
            pass # Time to end because the simulation is done and we were cancelled
        finally:
            # Save the check values for writing to a file
            self.values = vals
