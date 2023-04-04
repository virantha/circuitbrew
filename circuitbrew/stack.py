#from ports import Port, WithId
from helpers import WithId
from ports import *

class Stack(WithId):

    def __init__(self):
        super().__init__()
        self.top = None
        self.bot = None
        self.fets = []
        self.tmp_id = 0
        self.tmp_nodes = [] # Internal nodes only get added when adding
                            # series fets

    def __and__(self, other):
        if isinstance(other, Port):
            self.add_series_fet(other)
            return self
        elif isinstance(other, Stack):
            # Merge the two stacks
            other.bot._set(self.top)
            self.top = other.top
            self.fets += other.fets
            return self
        else:
            assert False

    def __or__(self, other):
        if isinstance(other, Port):
            self.add_parallel_fet(other)
            return self
        elif isinstance(other, Stack):
            # Merge the two stacks
            other.bot._set(self.bot)
            self.top._set = other.top
            self.fets += other.fets
            return self
        else:
            assert False

    def connect_power(self, powerport): 
        for fet in self.fets:
            fet.connect_power(powerport)


    # def add_series_nfet(self, gate_port):
    #     from fets import Nfet
    #     nfet = Nfet()
    #     nfet.g = gate_port
    #     self.add_series_fet(nfet)

    def _get_fet(self, gate_port):
        from fets import Pfet, Nfet
        if gate_port._negated:
            # Pfet
            fet_type = Pfet
        else:
            fet_type = Nfet
        fet = fet_type()
        fet.g = gate_port
        return fet

    def add_series_fet(self, gate_port):
        fet = self._get_fet(gate_port)
        self._connect_series_fet(fet)

    def _connect_series_fet(self, fet):
        self.fets.append(fet)
        if self.top:
            # a & b -> put 
            tmp_node = Port(f't{self.count}_{self.tmp_id}')
            self.tmp_id += 1
            self.tmp_nodes.append(tmp_node)
            tmp_node._set(fet.s)
            self.top._set(tmp_node)
            #fet.s = tmp_node 
            #self.top = tmp_node # Update earlier transistor top
            
            self.top = fet.d  # Update the new top
        else:
            self.top = fet.d
            self.bot = fet.s

    def add_parallel_fet(self, gate_port):
        fet = self._get_fet(gate_port)
        self._connect_parallel_fet(fet)

    def _connect_parallel_fet(self, fet):
        self.fets.append(fet)
        if self.top:
            fet.d._set(self.top)
            fet.s._set(self.bot)
        else:
            self.top = fet.d
            self.bot = fet.s
        