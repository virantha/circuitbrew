import curio
import inspect
import sys
from collections import Counter
import logging

from .ports import Port, InputPort
from .symbols import SymbolTable
from .stack import Stack

logger = logging.getLogger(__name__)
class Module:
    registry = {}  # All sub classes (class name -> class)
    module_counts = Counter()
    _modules = {}

    def __init__(self, name='', **kwargs):
        self.finalize_called = False

        self.fet_count = Counter()
        n = self._update_count()

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

        self.get_sim_setup(**kwargs)

        self.post_init()

    def _update_count(self):

        n = Module.module_counts[self.__class__]
        self._id = n
        # Increment subclass count
        Module.module_counts.update([self.__class__])
        return n


    def post_init(self): pass

    def get_sim_setup(self, **kw: dict):
        """Called at the end of __init__ to take any settings
           from the tech file and apply them automatically as member variables
           to this object.

           If any of these settings have been overridden by the user via the
           kwargs, then apply those instead
           
           Args:
                kw: any options you want to override during module/leaf instancing
           Returns:
                None
        """
        # Get any settings from the sim_setup dict, mapped by class name
        setup_dict = self.sim_setup

        # Reverse MRO so we apply defaults from base class -> sub classes
        base_classes = reversed(inspect.getmro(self.__class__))

        def _get_auto_dict(d):
            # At each dict level, we search for each base class name
            for bc in base_classes:
                bc_name = bc.__name__
                bc_dict = d.get(bc_name, {})
                if bc_dict:
                    # base class name is found, so check if there are any auto settings
                    auto = bc_dict.get('auto', {})
                    for k,v in auto.items():
                        # Check if user overrode with kwargs
                        if k in kw:
                            setattr(self, k, kw[k])
                        else:
                            setattr(self, k, v)
                    # Recurse
                    _get_auto_dict(bc_dict)
        _get_auto_dict(setup_dict)

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
         
    def make_stacks(self, output, pdn: Stack, pup: Stack, 
                    power: 'SupplyPort', width=None) -> list['Fet']:
        """ Given two stacks (constructed manually or via logical operators on
            Ports), construct the CMOS gate based on the pullup and pulldown
            networks, and return a list of Fets.
        """
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

        if width:
            for fet in fets:
                fet.w = width
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
    """ A Leaf cell has no instances attached to it. 

        It will emit its own spice (for example a transistor), or emit an 
        measurement command.
    """
     
    def build(self):
        """ Finalize this without adding any instances
        """
        logger.debug(f'Finalized leaf {self.name}')
        self.finalize()

    def finalize(self): 
        """Override the Module's finalize class because we don't
           want to capture any local variables, for example
        """
        self.finalize_called = True

class ParametrizedModule():
    def get_module_type_name(self):
        return f'{self.__class__.__name__}_{self._id}'

class SourceModule: # Just to keep track of when to stop a simulation
    pass


def Param(name):
    """Returns a new function that returns the instance variable "name" of 
       the specified instance
    """
    def lookup(self):
        v = getattr(self, name)
        return v
    return lookup

def Parameterize(cls, **kwargs):
    """Given Parameterize(cls, N=3, P=4), 
        it will return a new subclass of cls that has an __init__
        that sets instance vars N and P

        e.g Parameterize(cls, N=3, P=4) is effectively returning the following:

            Class subcls_N_3_P_4(cls):
                def __init__(self, *args, **kwargs):
                    self.N = 3
                    self.P = 4
                    cls.__init__(self, *args, **kwargs)

    """
    # Check to make sure every param in kwargs was defined as
    # a class annotation of type Param. 
    params = []
    cls_annotations = cls.__annotations__
    for name, val in kwargs.items():
        assert name in cls_annotations,\
                f'{name} is not defined as a parameter type annotation in {cls}'
        assert cls_annotations[name] is Param, \
                f'Annotation for {name} must be of type Param in {cls} to use as a parameter'
        params.append(f'{name}_{val}')
    params_to_str = '_'.join(params)

    #params_to_str = '_'.join([f'{name}_{val}' for name, val in kwargs.items()])

    def init_fn(self, *a, **kw):
        for name, val in kwargs.items():
            setattr(self, name, val)
        cls.__init__(self, *a, **kw)

    #print (cls.__annotations__)
    #sys.exit(0)
    parameterized_class = type(f'{cls.__name__}_{params_to_str}', (cls,), 
                              { '__init__': init_fn })

    return parameterized_class