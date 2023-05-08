import logging

from .symbols import SymbolTable
from .ports import Port

logger = logging.getLogger(__name__)

class CompoundPort(Port):
    """ Aggregate different ports into one structure (like a struct) by subclassing this.

        Examples:
            Combining data/clk into one Port instance.

            ``` py
            class DataClk(CompoundPort):
                din = InputPort()
                dout = OutputPort()
                clk = InputPort()
            ```

        Attributes:
            sym_table (SymbolTable): Hold all the mappings
    """

    def __init__(self, name=""):
        """In general, no extra args except the name if needed
        """
        super().__init__(name)
        self.sym_table = SymbolTable(self)

    def _insert_into_instance(self, instance):
        """ Used for the descriptor protocol for attribute access to the sub ports.

            Returns:

                CompoundPort: Either the lookup if it exists, or the newly created self
        """
        
        # Need to create a new CompoundPort object and create new Sub port objects to go along with it
        if (compound_port:= instance.__dict__.get(self.name)):
            return compound_port
        else:
            compound_port = type(self)(name=self.name)
            for sub_port_name, sub_port in compound_port.sym_table.get_ports().items():
                #compound_port.__dict__[sub_port_name] = type(sub_port)(name=f'{self.name}.{sub_port_name}')
                compound_port.__dict__[sub_port_name] = type(sub_port)(name=f'{sub_port_name}')
            instance.__dict__[self.name] = compound_port
            return compound_port

    def __get__(self, instance, cls):
        port = self._insert_into_instance(instance)
        return port

    def __set__(self, instance, value):
        # This gets called when we try to assign one compound port to another
        # We need to make sure the fields match up
        #assert isinstance(value, type(self)), f'Trying to connect two compound ports of types {type(value)} and {type(self)}'
        port = self._insert_into_instance(instance)

        # Create a new CompoundPort object (not a descriptor) to store it into the instance
        # if the instance does not already have it
        for port_name, subport in port.sym_table.get_ports().items():
            val = getattr(value, port_name)
            subport._set(val)

    def _set(self, value):
        assert isinstance(value, CompoundPort), f'Trying to set {self} to non-compound port type {type(value)}'
        for port_name, subport in self.sym_table.get_ports().items():
            subport._set(getattr(value, port_name))


    def __set_name__(self, cls, name):
        super().__set_name__(cls, name)
            
    def __repr__(self):
        # Get all the subports
        port_dict = self.sym_table.get_ports()
        l = [f'{n}:{p}' for n,p in port_dict.items() ]

        return ' '.join(l)

    def get_spice(self):
        # Need to get all the sub ports
        ports = self.sym_table.get_ports() 
        ports_spice = [port.get_spice() for port in ports.values()]
        #s = ' '.join([ port.get_spice() for port in ports.values()])
        s = ' '.join([f'{self.name}.{port}' for port in ports_spice])
        return s

    def get_instance_spice(self, scope):
        # Need to get all the sub ports
        # TODO: Do we need to maintain the hierarchy name for the sub-ports?
        ports = self.sym_table.get_ports() 
        s = ' '.join([ port.get_instance_spice(scope) for port in ports.values()])
        return s

    def __eq__(self, other):
        if not isinstance(other, CompoundPort):
            return False
        myports = self.sym_table.get_ports()
        other_ports = set(other.sym_table.get_ports().values())


        for port_name, port in myports.items():
            if port not in other_ports:
                return False
        return True

    def __hash__(self):
        return hash(map(hash, self.sym_table.get_ports()))

    def __iter__(self):
        myports = self.sym_table.get_ports()
        for portname, port in myports.items():
            yield from port

    def get_flattened(self, parent_scope_name=None):
        port_dict = {}
        for portname, port in self.sym_table.get_ports().items():
            subport_dict = port.get_flattened(parent_scope_name=self.name)
            port_dict = port_dict | subport_dict
        return port_dict
        
    def iter_flattened(self):
        for port in self.sym_table.get_ports().values():
            yield from port.iter_flattened()

    def is_flat(self): 
        return False
            

class SupplyPort(CompoundPort):
    """Use this for passing around the vdd and gnd global ports

        Attributes:
            vdd (Port): + terminal
            gnd (Port): - terminal    
    """
    vdd = Port()
    gnd = Port()


class E1of2(CompoundPort):
    """ A dual rail port with enable.

        For simulation, we will do a quick hack to make sure
        that we don't need to handle the data wires and enable individually.  The
        async queues already give us all the back-pressure behavior we need.  We
        will send the data value on the true rail only, and ignore the f and e
        rails.

        Attributes:
            t (Port): True rail
            f (Port): False rail
            e (Port): Enable (active low acknowledge)
    """
    t = Port()
    f = Port()
    e = Port()

# ----------------------------------------------------------------
# Simulation related methods for E1of2
# ----------------------------------------------------------------
    async def send(self, val):
        """ Just use the true rail for sending valuese for modelling
        """
        await self.t.send(val)

    async def recv(self):
        """ Just use the true rail for sending valuese for modelling
        """
        val = await self.t.recv()
        logger.info(f'channel {self} received {val}')
        return val

class E1of2InputPort(E1of2):
    """Input Dual-rail port
    """
    pass

class E1of2OutputPort(E1of2):
    """Output Dual-rail port
    """
    pass