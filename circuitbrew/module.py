
import curio
import inspect
from collections import Counter
import logging

from ports import Port, InputPort
from symbols import SymbolTable
from stack import Stack

logger = logging.getLogger(__name__)
class Module:
    registry = {}  # All sub classes (class name -> class)
    module_counts = Counter()
    _modules = {}

    def __init__(self, name='', **kwargs):
        self.finalize_called = False

        n = Module.module_counts[self.__class__]
        self._id = n
        # Increment subclass count
        Module.module_counts.update([self.__class__])

        if name=='':
            name = f'{self.get_module_type_name()}_inst_{n}'
        self.name = name

        self._sym_table = SymbolTable(self)

        # Connect the supplied ports if any in kwargs
        for p_name, p in kwargs.items():
            if(my_port := self._sym_table.ports.get(p_name)):
                my_port._set(p)

        logger.debug('\n-------------------------------\n\n')
        logger.debug(f'Printing ports of {self.get_module_type_name()}:...')
        logger.debug('\n-------------------------------\n\n')
        logger.debug(self._sym_table.ports)
        for name, p in self._sym_table.ports.items():
            logger.debug (f'{p.count} ')

    def iter_flattened(self, myiter, filter=lambda x: x is not None):
        """Iterator to flatten arbitrary nested lists"""
        if isinstance(myiter, list):
            for subitem in myiter:
                yield from self.iter_flattened(subitem, filter)
        elif filter(myiter):
            yield myiter
        else:
            return 

    def get_spice(self):
        l = []

        port_list = []
        port_list = ' '.join([port.get_spice() for port in self._sym_table.ports.values()])
        l.append(f'.subckt {self.get_module_type_name()} {port_list}')
        # Now, go through all the leaf/module instances in namespace
        for inst_name, modules in self._sym_table.sub_instances.items():
            for module in self.iter_flattened(modules): 
                l.append(module.get_instance_spice(scope=self._sym_table))

        l.append(f'.ends')
        return l

    def get_instance_spice(self, scope):
        logger.debug(f'Getting instance spice for {self.name}:{self.get_module_type_name()}')
        s = f'x{self.name} {" ".join(self._get_instance_ports(scope))} {self.get_module_type_name()}'
        return s

    def _get_instance_ports(self, scope):
        connected = [port.get_instance_spice(scope) for port in self._sym_table.ports.values()] 
        return connected
   
    def dump_spice(self):
        s = self.get_spice()
        print(s)

    def is_module(self, name, obj):

        # recursively check if this object is a module
        # (lists or iterables of modules work)
        if isinstance(obj, list):
            is_list = True
            for subobj in obj:
                _, is_module = self.is_module(name, subobj)
                return is_list, is_module
            return is_list, True
        else:
            is_list = False
            return is_list, isinstance(obj, Module)

    def finalize(self):
        logger.debug(f'Finalizing construction of {self}')
        #previous_frame = inspect.currentframe().f_back
        previous_frame = inspect.currentframe().f_back
        #frame_info = stack_data.FrameInfo(previous_frame)
        #print(frame_info.variables)

        my_locals = previous_frame.f_locals
        logger.debug (my_locals)
        for name, obj in my_locals.items():
            logger.debug (name)
            if isinstance(obj, Port):
                self._sym_table.add_local(name, obj)
        del previous_frame
        logger.debug(f'Instance attributes:')
        logger.debug(self._sym_table.get_log_ports(self._sym_table.locals))

        logger.debug(f'Instance attributes:')
        logger.debug('---------')
        for attr in dir(self):
            obj = getattr(self, attr)
            is_list, is_module = self.is_module(attr, obj)
            if is_module:
                if is_list:
                    for inst in obj:
                        self._sym_table.add_sub_instance(inst.name, inst)
                else:
                    self._sym_table.add_sub_instance(attr, obj)
        logger.debug('---------')
        # Set a flag so we can error out if the user forgot to call self.finalize()
        self.finalize_called = True
        
    def __str__(self):
        return self.name

    def get_module_type_name(self):
        return self.__class__.__name__

    def __init_subclass__(cls, **kwargs):
        cls.registry[str(cls)] = cls
        #cls.template = kwargs
        super().__init_subclass__(**kwargs)
         
    def make_stacks(self, output, pdn, pup, power):
        # Connect the output node
        assert isinstance(pdn, Stack), f'Pulldown {pdn} is not a stack'
        assert isinstance(pup, Stack), f'Pullup {pup} is not a stack'
        pdn.top._set(pup.bot)

        self._connect_all_to(pdn.bot, power.gnd)
        self._connect_all_to(pup.top, power.vdd)

        self._connect_all_to(pup.bot, output)
        self._connect_all_to(pdn.top, output)

        fets = []
        fets += self._connect_stack(pdn, power)
        fets += self._connect_stack(pup, power)

        return fets
        
    def _connect_all_to(self, port, connection):
        port._set(connection)
        for node in port.connections:
            node._set(connection)

    def _connect_stack(self, stack, power): # returns list of fets
        fet_list = []
        stack.connect_power(power)
        fet_list = stack.fets

        # What do we do about tmp nodes?
        # Add them to locals in sym_table
        for tmp_node in stack.tmp_nodes:
            self._sym_table.add_local(tmp_node.name, tmp_node)

        return fet_list

    async def sim(self): 
        # No sim method was defined in this module,
        # So, we need to propagate all values on input to their fanouts
        port_pids = []
        for port in self._sym_table.ports.values():
            pid = await curio.spawn(port.sim())
            port_pids.append(pid)

        # Wait until this module sim is terminated
        try:
            while True:
                await curio.sleep(1)
        except curio.CancelledError:
            # Cancel all ports
            for port_pid in port_pids:
                logger.info(f'Cancelling port {port_pid}')
                await port_pid.cancel()
            raise
        

class Leaf(Module):
    def build(self):
        # No submodules instanced in a leaf
        logger.debug(f'Finalized leaf {self.name}')
        self.finalize()

    def finalize(self): 
        self.finalize_called = True

class ParametrizedModule():
    def get_module_type_name(self):
        return f'{self.__class__.__name__}_{self._id}'

class SourceModule: # Just to keep track of when to stop a simulation
    pass