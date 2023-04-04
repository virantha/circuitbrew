import inspect, logging
from ports import Port, Ports 
from collections.abc import MutableSequence

logger = logging.getLogger(__name__)
class Symbol:
    def __init__(self, name, port, hierarchy=None):
        self.name = name
        self.port = port
        self.hierarchy = hierarchy

    def get_hierarchical_name(self, separator='.'):
        if self.hierarchy:
            parent_name = self.hierarchiy.get_hiearchical_name(separator)
            return f'{parent_name}{separator}{self.name}'
        else:
            return f'{self.name}'

    def __repr__(self):
        return f'Symbol({self.name}, {self.port}, {self.hierarchy})'

class SymbolTable:
    
    def __init__(self, instance):
        self.instance = instance
        
        # Keep track of the local vars (typically not Ports) with:
        # 1. Forward map (name to obj)
        # 2. Reverse map (obj to name)
        self.locals = {}
        self.locals_obj_to_name = {}

        self.sub_instances = {} # Dict mapping instance name to instance object 
                                # instantiated in this module
        self.sub_instance_ports = {}
        self.ports = self.get_ports()
        
        self.params = {} # If this module needs to be parametrized

        self.tmp_id = 0  # Counter to keep track of new temp variables we create in locals


    def get_ports(self):
        """Utility method to get all the ports attached to this instance, in the
           same order they were listed in the class definition.

           We need to use the count attribute to sort the ports to get this ordered
           list.
        """
        # [ (name, obj), ...]
        unsorted_tuple_list = inspect.getmembers(self.instance, 
                                                lambda attr: 
                                                    isinstance(attr, Ports) or isinstance(attr, Port))

        sorted_tuple_list = sorted(unsorted_tuple_list, key=lambda p: p[1].count)
        return dict(sorted_tuple_list)

    def add_local(self, local_name, local_obj):
        # Called by finalize
        # Let's keep the reverse mapping too
        # Add all the flattened ports too
        all_ports = local_obj.get_flattened(local_name)

        
        if len(all_ports) > 1:  # Don't add in single ports (Otherwise we end up with things like clk.clk)
            for pname, p in all_ports.items():
                #sym = Symbol(pname, p)
                sym = p
                self.locals[pname] = sym
                self.locals_obj_to_name[sym] = pname

        #sym = Symbol(local_name, local_obj)
        sym = local_obj
        self.locals[local_name] = sym
        self.locals_obj_to_name[sym] = local_name
        return


    def add_sub_instance(self, inst_name, inst):

        self.sub_instances[inst_name] = inst
        
        # Add all the ports of the sub
        # Complication here because instt could be a list
        #self.sub_instance_ports[inst_name] = [i._sym_table.ports for i in self.iter_flattened(inst)]
        self.sub_instance_ports[inst_name] = inst._sym_table.get_ports()


    """
        In the below, at the Main module, myinv does not have its supply ports connected
        So, they should be labeled as unconnected.  
        Instead, because they are connecdted inside the Inv module, it uses those connections
        (the shortest available).

        Instead, what we need to do is:
            When instancing a submodule inside a module,
            Each port for the submodule needs to be matched to something in scope at that module
            And only from those matches should we pick the shortest one.

        .subckt Main a b
        xmyinv a s d s Inv
        .ends                               


.subckt Inv a b p.vdd p.gnd
xmn0 b a p.gnd UNC nch_svt_mac nfin=2 l=0.008u
xmp0 p.vdd a b UNC pch_svt_mac nfin=2 l=0.008u
.ends
 
    """
    # Just build a graph

    def get_symbol_from_scope(self, port):
        """We're given a port to find in the current context (symbol table) and return
           it's name if it exists:

                - Search the locals (variables defined in the build)
                - Search the module's ports
                - Search any the ports of any submodules instanced in this module:
                        self.inv = Inv(a, b)  # self.inv.in and self.inv.out can be used in this context
        """

        # Do I need a graph here to check connectivity?
        # - probably not because everything should be only 1 away


        # Check the instance ports first; this name should always take priority
        if (sym := self.get_connected_symbol(port, self.ports)):
            logger.debug(f'\t\tFound instance port {sym}')
            return sym.name, sym.port
        elif (sym := self.get_connected_symbol(port, self.locals)):
            logger.debug(f'\t\tFound local port {sym}')
            return sym.name, sym.port
        else:
            # More complicated case to search in sub_instance ports in this module
            sym = self.get_connected_symbol(port, self.sub_instance_ports)
            if (sym):
                # Need to create a temp var here to access the sub port
                # because I'm not sure verilog allows a "inst.port" reference
                tmp_var = Port(f'{sym.name}_{self.tmp_id}')
                tmp_var._set(sym.port)
                for conn in sym.port.connections:
                    tmp_var._set(conn)
                self.add_local(tmp_var.name, tmp_var)
                logger.debug(f'\t\tCreated new local {tmp_var.name}={tmp_var} for {port.name}, {port}')
                self.tmp_id+=1
                return tmp_var.name, tmp_var
                #return sym.name, sym.port
            else:
                return None




    def get_connected_symbol(self, port, lookup_dict):
        """ Problem here is that a port may have multiple names(aliases) assorted with it
            Symbol(a, port_a), Symbol(local_a, port_a) are two aliases to the same port "port_a"

            We can't use sets for this.

            They  

            Need to convert this to handle the sub_instance_ports provided as a 
        """

        # Need to make a set of port and its connections, then find intersection with p and its connections
        logger.debug(f'Getting connected symbol for {port}')
        port_aliases = set([port]) | port.connections
        for p_name, p in lookup_dict.items():
            logger.debug(f'Searching {p_name}={p}')
            if isinstance(p, dict):
                # Collection of sub_instance ports
                logger.debug('found dict')
                for sub_port_name, sub_port in p.items():
                    if port == sub_port or sub_port in port.connections:
                        return Symbol(f'{sub_port_name}', sub_port, hierarchy=p_name)
            elif p.is_flat():
                p_aliases = set([p]) | p.connections
                common_port = port_aliases & p_aliases
                if len(common_port) > 0:
                    return Symbol(p_name, p)
                else:
                    continue
            elif not p.is_flat():
                # Check all the flattened ports
                #sub_ports = p.get_flattened(p_name)
                sub_ports = p.get_flattened()
                sub_port_match = self.get_connected_symbol(port, sub_ports)
                if sub_port_match:
                    return sub_port_match
            else:
                # No match
                # Check the connected ports of each 
                continue
        return None


    def get_log_ports(self, port_dict, indent=0, msg=None):
        lines = []
        tabs = '\t'*indent
        
        if msg:
            lines.append(f'{tabs}{msg} in scope:')
        else:
            dict_name = list(self.__dict__.keys())[ list(self.__dict__.values()).index(port_dict)]
            lines.append(f'{tabs}{dict_name} in scope:')
        found = False
        for port_name, port in port_dict.items():
            found = True
            lines.append(f'{tabs}\t{port_name} = {port}')
        if not found:
            lines.append(f'{tabs}\tNone')

        return '\n'.join(lines)