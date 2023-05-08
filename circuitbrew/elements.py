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
    """ Any Module class that depends on a Verilog-A/Verilog code inside a template file
        can subclass this.  It will automatically copy the template file to the output directory.

        If you have a subclass that needs parameters (for example, a Source module might need
        to inject a series of different values into the templated verilog file, thereby creating a 
        different verilog file each time it's instanced), then you should use the 
        [circuitbrew.elements.VerilogParametrizedModel][] below.
        
    """

    def build(self):
        self.finalize()

    def _emit_src_file(self, src_filename: str, 
                             param_dict: dict = {}, 
                             out_filename: str = None) -> str:
        """ Call this at the end of your `get_spice` method.
            Need to fix this to not use deprecated pkg_resources.

            Args:
                src_filename: The template file (Mako)
                param_dict: The template variables to fill in 
                out_filename: 
                    If you want to use a different name for the output template file.
                    If you leave unspecified, then it will use the src_filename in the output directory

            Returns:
                out_filename (str): The output file
        """
        mytemplate = Template(pkg_resources.files(tech).joinpath(src_filename).read_text())

        srcfile = mytemplate.render(**param_dict, **self.sim_setup)

        if not out_filename: out_filename=src_filename
        self._write_file(out_filename, srcfile)
        return out_filename

    def _write_file(self, filename: str, contents: str):
        """ Write out the filename to the output directory in `sim_setup['output_dir']`.
            Optionally create that directory if it doesn't exist
        """
        output_dir = self.sim_setup['output_dir']
        
        if not os.path.isdir(output_dir):
            logger.info(f'Creating output directory {output_dir}')
            os.makedirs(output_dir)

        with open(os.path.join(output_dir, filename), 'w') as f:
            f.write(contents)


    def get_spice(self, param_dict={}):
        """ You usually don't need to override this method.  You can add whatever
            custom parameters to the param_dict in your subclass before calling its
            super().get_spice() method.

            The parametrized modules are a notable exception to this.
            See [circuitbrew.elements.VerilogParametrizedModule.get_spice][]
        """
        simtype = self.sim_setup['sim_type']
        src_filename = self.src_filename[simtype]
        param_dict |= { 'MODULE_NAME': self.get_module_type_name(),
                      }
        self._emit_src_file(src_filename, param_dict)

        l = [f'.hdl {src_filename}']
        return l

class VerilogClock(VerilogModule):
    """ Create a clock with the specified frequency and offset

        Args:
            name: Name of object
            freq: Frequency of clock in Hz
            offset: Start of clock waveform from 0n (ns)

        Other Args:
            enable (InputPort): active-high enable signal     
            clk (OutputPort): the output clock signal
    """
    enable = InputPort()
    clk    = OutputPort()

    def __init__(self, name: str, freq: float, offset: float=0, **kwargs):
        super().__init__(name=name, **kwargs)
        self.freq = freq
        self.offset = offset
        self.src_filename = {'hspice': 'hspice_clk.va'}

    def get_instance_spice(self, scope):
        s = super().get_instance_spice(scope)
        s = f'{s} freq={self.freq} offset={self.offset}'
        return s

class VerilogParametrizedModule(ParametrizedModule, VerilogModule): 

    """ For any verilog-a/verilog module that we need to uniquify the template
        file.
    """

    def get_spice(self, param_dict: dict={}) -> str:
        """ Specialized version to make sure we change the output filename for
            every instance of this class

        """
        simtype = self.sim_setup['sim_type']
        src_filename = self.src_filename[simtype]
        param_dict |= { 'MODULE_NAME': self.get_module_type_name(),
                      }
        output_filename = f'template_{self._id}_{src_filename}'

        self._emit_src_file(src_filename, param_dict, output_filename)

        l = [f'.hdl {output_filename}']
        return l

class VerilogSrc(VerilogParametrizedModule, SourceModule):
    """ A single-bit source module that takes a list of values and outputs
        them on every clock edge.

        Args:
            values: sequence of values to output

        Other Args:
            clk (InputPort): input clock signal
            _reset (InputPort): only starts outputting when deasserted
            d (OutputPort): output values
    
    """
    clk = InputPort()
    _reset = InputPort()
    d  = OutputPort()

    def __init__(self, name, values: list[int], **kwargs):
        super().__init__(name=name, **kwargs)
        self.values = values
        self.src_filename = {'hspice': 'hspice_src.va'}
    
    def get_spice(self):
        param_dict = {'values': self.values,
                      'nvalues': len(self.values), 
                     }
        return super().get_spice(param_dict=param_dict)

    async def sim(self):
        for val in self.values:
            await self.d.send(val)

class VerilogBucket(VerilogParametrizedModule):
    """ A single-bit bucket module that sinks values on every clk edge and checks them 
        against the expected values.  If the user didn't specify the
        expected values, then the sim model method will provide the
        values.

        Args:
            values: sequence of values to check against

        Other Args:
            clk (InputPort): input clock signal
            _reset (InputPort): only starts checking when deasserted
            d (InputPort): input values
    

        Attributes:
            values: the sequence of values to check against
    """
    clk = InputPort()
    _reset = InputPort()
    d  = InputPort()

    def __init__(self, name: str, values: list[int]=None, **kwargs):
        super().__init__(name=name, **kwargs)
        self.values = values
        self.src_filename = {'hspice': 'hspice_bucket.va'}
    
    def get_spice(self):
        param_dict = {'values': self.values,
                      'nvalues': len(self.values), 
                     }
        return super().get_spice(param_dict=param_dict)

    async def sim(self):
        """ If self.values already exists, then do nothing.

            Otherwise, receive values on d, and append them to self.values
        """
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
