import sys, inspect, logging
from collections.abc import MutableSequence
from helpers import WithId
from curio import Queue

logger = logging.getLogger(__name__)

class Port(WithId):

    def __init__(self, name="", count=None):
        super().__init__()
        self.connections = set()
        self._q = Queue()   # The input side of this port
        self.name = name
        if count:
            self.count = count
        logger.debug(f'__init__ ({name}): id = {self.count}')
        self._negated = None

    # ----------------------------------------------------------------
    # Simulation related methods
    # ----------------------------------------------------------------
    async def recv(self):
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
        #assert not self._negated, 'Can only negate a port once'
        self._negated = True
        return self

    def __and__(self, other):
        from stack import Stack
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
        from stack import Stack
        from fets import Nfet
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
        return self.name

    def get_instance_spice(self, scope):
        #assert len(self.connections) > 0, f'{self} is not connected!'
        #if (port_tuple := scope.get_port_from_scope(self)):
        if (port_tuple := scope.get_symbol_from_scope(self)):
            port_name, port = port_tuple
            return port_name
        else:
            return 'UNC'

    def __iter__(self):
        yield self

    def get_flattened(self, parent_scope_name=None):
        if not parent_scope_name:
            return {self.name: self}
        else:
            return {f'{parent_scope_name}.{self.name}': self}

    def is_flat(self):
        return True


class Wire(Port):
    pass

class InputPort(Port): pass

class OutputPort(Port): pass



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

    def is_flat(self):
        return False

class InputPorts(Ports):
    port_type = InputPort

class OutputPorts(Ports):
    port_type = OutputPort

class BiggerModule:
    a = InputPorts(width=5)
    b = OutputPorts(width=4)

class Wires(Ports):
    port_type = Wire

    def __init__(self, **kwargs):
        assert 'name' in kwargs, f'Wire array {self} must specify name using Wires(name=..., width=...)'
        super().__init__(**kwargs)
        self.__set_name__(None, kwargs['name'])

        
if __name__=='__main__':
    m = SimpleModule()
    print(m.p)
    global_gnd = Wire('GND')
    global_vdd = Wire('VDD')
    a = SupplyPort()
    a.vdd = global_vdd
    a.gnd = global_gnd

    #m.p.gnd = global_gnd
    m.p = a
    print(m.p)


    
    m = BiggerModule()
    print(m.a)
    m.a[0] = m.b[2]
    wires = Wires(name='w',width=8)
    print(wires)
    print('connections:')
    print(m.a[0].connections)
    m.a[1:3] = wires[0:2]
    print(m.a[2].connections)
    sys.exit(0)

    m = Module()
    f = Wire(key='f', width=5)
    print(m.a)
    print(m.b)
    print(m.a[0].connections)
    m.a[0] = f[0]
    print(m.a[0])

    print(m.a[0].connections)
    g = Wire(key='g', width=4)
    m.b = g
    print(m.b)
    print(m.b[0].connections)
    m.b[1] = m.a[2]
    print(m.b[1].connections)


