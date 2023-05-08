import sys, inspect, logging
from collections.abc import MutableSequence
from .helpers import WithId
from curio import Queue

logger = logging.getLogger(__name__)

class Port(WithId):
    """The basic port class used to build up arrays of ports
       Ports, and Compound ports.

       Simulation abilities
       --------------------
       Has a built in queue to model transferring data from the sender
       to the receiver.  The recv, send, and sim async functions implement
       the actual data transfer.
    """

    def __init__(self, name="", count=None):
        super().__init__()
        self.connections = set()
        self._q = Queue()   
        self.name = name

        if count:
            self.count = count
        logger.debug(f'__init__ ({name}): id = {self.count}')

    # ----------------------------------------------------------------
    # Simulation related methods
    # ----------------------------------------------------------------
    async def recv(self):
        """Receive a value on the internal Curio queue

           :return: received value
        """
        q = self._q
        tok = await q.get()
        #await q.task_done()
        logger.info(f'Received {tok} on port {self.name}')
        return tok

    async def send(self, val):
        # Copy to all listeners in the q
        for receiver in self.connections:
            queue = receiver._q
            logger.info(f'Sending {val} on {self} to receiver {receiver.name}')
            await queue.put(val)

    async def sim(self):
        while True:
            val = await self.recv()
            await self.send(val)

    # ----------------------------------------------------------------
    # Transistor stack creation using bit-wise operators
    #   e.g. port_a & port_b yields a series n-fet stack 
    # ----------------------------------------------------------------
    def __invert__(self):
        logger.debug(f'NEGATING port {self}')
        from .stack import Stack
        stack=Stack()
        stack.add_parallel_fet(self, negated=True)
        return stack


    def __and__(self, other):
        from .stack import Stack
        logger.debug(f'ANDing ports {self} with {other}')
        if isinstance(other, Stack):
            other.add_series_fet(self)
            return other
        else:
            logger.debug(f'Got {self.name} & {other.name}')
            stack = Stack()
            stack.add_series_fet(self)
            stack.add_series_fet(other)
            return stack
        
    def __or__(self, other):
        from .stack import Stack
        from .fets import Nfet
        logger.debug(f'ORing ports {self} with {other}')
        if isinstance(other, Stack):
            other.add_parallel_fet(self)
            return other
        else:
            logger.debug(f'Got {self.name} & {other.name}')
            stack = Stack()
            stack.add_parallel_fet(other)
            stack.add_parallel_fet(self)
            return stack

    # ----------------------------------------------------------------
    # Decorator protocol to allow these to be used in Module classes
    # as instance variables ("block ports") 
    # ----------------------------------------------------------------
    def __set_name__(self, cls, name):
        logger.debug(f'{self.__class__}: setting name to {name} for port id {self.count}')
        self.name = name

    def __get__(self, instance, cls):
        return self._get_or_create_port(instance)

    def __set__(self, instance, value):
        # Create a new Port object (not a descriptor) to store it into the instance
        # if the instance does not already have it
        port = self._get_or_create_port(instance)
        port._set(value)

    def _get_or_create_port(self, instance):
        if (port := instance.__dict__.get(self.name)):
            return port
        else:
            port = type(self)(name=self.name, count=self.count)
            instance.__dict__[self.name] = port
            return port

    def _set(self, value):
        assert isinstance(value, Port), f'Trying to set {self} to non-port type {type(value)}'
        self.connections.add(value)
        value.connections.add(self)

    def __str__(self):
        s = f'{self.name}:{self.__class__.__name__}({hex(id(self))})'
        if len(self.connections) > 0:
            connects = []
            for p in self.connections:
                p_str = f'{p.name}:{p.__class__.__name__}({hex(id(p))})'
                connects.append(p_str)

            #connects = ','.join([f'{p.name}:{str(p)}' for p in self.connections if id(p)!=id(self) ])
            connects = ','.join(connects)
            return f'{s} -> [{connects}]'
        else:
            return s

    def get_spice(self):
        """When building the subckt definition's port list, just return the name of this
           port.
        """
        return self.name

    def get_instance_spice(self, scope: "SymbolTable"):
        """When a module is instanced, then we need to find the proper
           argument name to pass in to the port.  This is done using the scope, 
           to translate this port object into the scoped variable name.
        """
        #assert len(self.connections) > 0, f'{self} is not connected!'
        if (port_tuple := scope.get_symbol_from_scope(self)):
            port_name, port = port_tuple
            return port_name
        else:
            # TODO: Convert this to an assert in production code
            return 'UNC'

    def __iter__(self):
        yield self

    def get_flattened(self, parent_scope_name=None):
        if not parent_scope_name:
            return {self.name: self}
        else:
            return {f'{parent_scope_name}.{self.name}': self}

    def iter_flattened(self):
        yield self

    def is_flat(self):
        return True

class InputPort(Port): 
    """Single bit Input Port
    """
    pass

class OutputPort(Port): 
    """Single bit Output Port
    """
    pass


class Ports(MutableSequence, WithId):
    port_type = Port
    def __init__(self, **kwargs):
        super().__init__()
        self.ports = None
        if (count := kwargs.get('count')):
            self.count = count
        if 'items' in kwargs:
            items = kwargs['items']
            self.width = len(items) 
            self.ports = items
            if 'name' in kwargs:
                self.name = kwargs['name']
        elif 'name' in kwargs:
            assert 'width' in kwargs, f'{type(self)} construction must specify width using (width=..)'
            self.width = kwargs['width']
            self.name = kwargs['name']
            # Enough info to instantiate this object
            self.ports = [self.port_type(name=f'{self.name}[{i}]') for i in range(self.width)]

        else:
            # Decorator only
            assert 'width' in kwargs, f'{type(self)} construction must specify width using (width=..)'
            self.width = kwargs['width']

    def __set_name__(self, cls, name):
        logger.debug(f'got name {name} for ')
        self.name = name
        #if not self.ports:  # In case we manually supplied the list of ports already in the constructore (items=...)
            #self.ports = [self.port_type(name=f'{self.name}[{i}]') for i in range(self.width)]

    def _insert_into_instance(self, instance):
        if (ports := instance.__dict__.get(self.name)):
            return ports
        else:
            # Check if there was parameter for the width.  If so, it will be a deferred callable that should
            # resolve at this point (because the instance has been instantiatied).
            if callable(self.width): self.width = self.width(instance)
            ports = instance.__dict__[self.name] = type(self)(name=self.name, width=self.width, count=self.count)
            return ports

    def _set(self, value):
        assert isinstance(value, list), f'Trying to set {self} to non-list type {type(value)}'
        for p,v in zip(self.ports, value):
            assert isinstance(v, Port), f'Trying to set {self} to non-port type {type(value)}'
            p._set(v)

    def __get__(self, instance, cls):
        ports = self._insert_into_instance(instance)
        assert ports
        return ports

    def __set__(self, instance, value):
        assert len(value) == self.width
        ports = self._insert_into_instance(instance)

        for port, val in zip(ports, value):
            port._set(val)

    def __getitem__(self, index):
        if isinstance(index, slice):
            elements = self.ports[index]
            return type(self)(name=self.name, items=elements)
        else:
            return self.ports[index]
            #return type(self)(key=f'{self.key}[{index}]', width=1, items=[self.ports[index]])
    
    def __len__(self): 
        return self.width

    def __setitem__(self, index, val):
        logger.debug(f'Inside __setitem__ with {val} and index {index}')
        # Just need to set the connection
        if isinstance(index, slice):
            for port, v in zip(self.ports[index], val):
                port._set(v)
                logger.debug(f'\tSetting connection {port} to {v}')
        else:
            self.ports[index]._set(val)

    def __delitem__(self, index):
        raise Exception

    def insert(self, index, val):
        raise Exception

    def get_spice(self):
        s = ' '.join([ port.get_spice() for port in self.ports])
        return s

    def get_instance_spice(self, scope):
        """scope is a symbol table of the module that is trying to instance
           this in its body
        """
        s = ' '.join([ port.get_instance_spice(scope) for port in self.ports])
        return s

    def get_flattened(self, parent_scope_name=None):
        port_dict = {}
        for port in self.ports:
            if parent_scope_name: 
                prefix= f'{parent_scope_name}.'
            else:
                prefix = ''
            port_dict[f'{prefix}{port.name}'] = port
        return port_dict

    def iter_flattened(self):
        yield from self.ports
        # for port in self.ports:
        #     yield from port.iter_flattened()

    def is_flat(self):
        return False

    async def recv(self):
        """ Receive a list of values on each port

            Returns:
                received value
        """
        vals = []
        for p in self.ports:
            vals.append(await p.recv())
        logger.info(f'Received {vals} on port {self.name}')
        return vals

    async def send(self, val: list):
        """ Send list of values on list of ports
        """
        # Copy to all listeners in the q
        for p, v in zip(self.ports, val):
            # Copy v to every connection in p
            await p.send(v)

class InputPorts(Ports):
    """Sequence (array) of InputPort
    """
    port_type = InputPort


class OutputPorts(Ports):
    """Sequence (array) of OutputPort
    """
    port_type = OutputPort


