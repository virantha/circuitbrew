import os
import logging
import curio
from .measure import Power
from .ports import *
from .compound_ports import SupplyPort
from .module import Leaf, Module, ParametrizedModule, SourceModule

# The template files
from mako.template import Template
import importlib.resources as pkg_resources
import circuitbrew.tech as tech

logger = logging.getLogger(__name__)

class VoltageSource(Leaf):
    """ Emits a voltage source with ref to global '0'.  If you're trying to define
        the system global voltage supply, then I recommend using
        instead [circuitbrew.elements.Supply][] which instantiates this module
        and gives you access to vdd and gnd
        as a [circuitbrew.compound_ports.SupplyPort][]


        Args:
            name: Name for the voltage source subcircuit instance
            voltage: Voltage level ('1.8V', '750mV', etc)
            measure: Whether to measure power or not (not implemented)

        Other Args:
            node (Port): The node to apply the voltage to
        
    """
    node = Port()

    def __init__(self, name: str, voltage: str, measure: bool =False, **kwargs):
        super().__init__(name=name, **kwargs)
        self.voltage = voltage
        self.measure = measure

    def get_instance_spice(self, scope):
        """
        """
        connected = ' '.join(self._get_instance_ports(scope))
        s = []
        s.append(f'V{self.name} {connected} 0 {self.voltage}')
        return '\n'.join(s)

class Supply(Module):
    """ Instantiate the full supply for vdd and gnd as a sub-circuit.

        Examples:

            >>> self.vdd_supply = Supply(name='vdd', voltage=self.sim_setup['voltage'])
                p = self.vdd_supply.p
                vdd = p.vdd
                gnd = p.gnd

        Args:
            name: Name for the voltage source subcircuit instance
            voltage: Voltage level ('1.8V', '750mV', etc)
            measure: Whether to measure power or not
            
        Other Args:
            p (SupplyPort, Optional): The port to connect to
        
    """
    p = SupplyPort()

    def __init__(self, name, voltage, measure=True, **kwargs):
        super().__init__(name=name, **kwargs)
        self.voltage = voltage
        self.measure = measure

    def build(self):
        self.vsupply =  VoltageSource(f'{self.name}_vdd', self.voltage)
        self.p.vdd = self.vsupply.node
        self.vgnd =  VoltageSource(f'{self.name}_vss', 0.0)
        self.p.gnd = self.vgnd.node

        if self.measure:
            self.msr_power = Power(voltage_source=self.vsupply)

        self.finalize()

class ResetPulse(Leaf):
    """ Create a single step waveform (useful for Reset signals)

        Examples:

            >>> self.rst = ResetPulse(name='rst', node=myport, p=p) 

            This will use the settings in tech.yml for timing of step.
            
            >>> self.rst = ResetPulse(name='rst', slope=0.5, deassert_time=4)

            Move step to 5n and complete step after 0.5n

        Args:
            name: Name for the voltage source subcircuit instance
            
        Other Args:
            slope (float): 0-100% time in ns
            deassert_time (float): When to create the step

        Attributes:
            node (Port): Where the reset pulse is connected 
            p    (SupplyPort):  
    """
    node = Port()
    p = SupplyPort()

    def __init__(self, name, **kwargs):
        super().__init__(name=name, **kwargs)
    
    def get_instance_spice(self, scope):
        node_str = self.node.get_instance_spice(scope)
        gnd_str = self.p.gnd.get_instance_spice(scope)
        s = []
        rsttime = self.deassert_time
        s.append(f'Vpwl{self.name} {node_str} {gnd_str} PWL (0n 0 {rsttime}n 0 {rsttime+self.slope}n {self.sim_setup["voltage"]})')
        return 'n'.join(s)

class VerilogModule(Module):

    def build(self):
        self.finalize()

    def _emit_src_file(self, src_filename, param_dict={}, out_filename=None):
        mytemplate = Template(pkg_resources.files(tech).joinpath(src_filename).read_text())

        srcfile = mytemplate.render(**param_dict, **self.sim_setup)

        if not out_filename: out_filename=src_filename
        self._write_file(out_filename, srcfile)
        return src_filename

    def _write_file(self, filename, contents):
        output_dir = self.sim_setup['output_dir']
        
        if not os.path.isdir(output_dir):
            logger.info(f'Creating output directory {output_dir}')
            os.makedirs(output_dir)

        with open(os.path.join(output_dir, filename), 'w') as f:
            f.write(contents)


    def get_spice(self):
        simtype = self.sim_setup['sim_type']
        src_filename = self.src_filename[simtype]
        param_dict = { 'MODULE_NAME': self.get_module_type_name(),
                     }
        self._emit_src_file(src_filename, param_dict)

        l = [f'.hdl {src_filename}']
        return l

class VerilogClock(VerilogModule):
    enable = InputPort()
    clk    = OutputPort()

    def __init__(self, name, freq, offset=0, **kwargs):
        """offset is a time delta to the first edge of the clock"""
        super().__init__(name=name, **kwargs)
        self.freq = freq
        self.offset = offset
        self.src_filename = {'hspice': 'hspice_clk.va'}

    def get_instance_spice(self, scope):
        s = super().get_instance_spice(scope)
        s = f'{s} freq={self.freq} offset={self.offset}'
        return s

class VerilogParametrizedModule(ParametrizedModule, VerilogModule): pass

class VerilogSrc(VerilogParametrizedModule, SourceModule):
    clk = InputPort()
    _reset = InputPort()
    d  = OutputPort()

    def __init__(self, name, values, **kwargs):
        super().__init__(name=name, **kwargs)
        self.values = values
        self.src_filename = {'hspice': 'hspice_src.va'}
    
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
            await self.d.send(val)

class VerilogBucket(VerilogParametrizedModule):
    clk = InputPort()
    _reset = InputPort()
    d  = InputPort()

    def __init__(self, name, values=None, **kwargs):
        super().__init__(name=name, **kwargs)
        self.values = values
        self.src_filename = {'hspice': 'hspice_bucket.va'}
    
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
            # No need to simulate if user already supplied the expected values
            return
        try:
            logger.info(f'Bucket {self} waiting')
            vals = []
            while True:
                val = await self.d.recv()
                logger.info(f'Bucket {self} received {val}')
                vals.append(val)
        except curio.CancelledError:
            pass # Time to end because the simulation is done and we were cancelled
        finally:
            self.values = vals
