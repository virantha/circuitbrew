import logging
from curio import spawn

from .module import Module, Leaf, SourceModule
from .helpers import LogBlock
logger = logging.getLogger(__name__)

class Walker: 
    def __init__(self, target, target_name):
        assert isinstance(target, Module), f'{target}:{target_name} is not a Module'
        self.target = target
        self.target_name = target_name

    def iter_flattened(self, myiter, filter=lambda x: x is not None):
        """Iterator to flatten arbitrary nested lists"""
        if isinstance(myiter, list):
            for subitem in myiter:
                yield from self.iter_flattened(subitem, filter)
        elif filter(myiter):
            yield myiter
        else:
            return 


class BuildPass(Walker):

    def run(self):
        LogBlock(f'Build pass {self.target}')
        self.target.build()
        assert self.target.finalize_called, f'{self.target} build method does not havea self.finalize() call at the end'
        # Now, look at all the modules attached as attributes in the target module
        # and walk those recursively
        for varname, var in vars(self.target).items():
            for i, module in enumerate(self.iter_flattened(var, lambda x: isinstance(x,Module))):
                walker = BuildPass(module, f'{self.target_name}.{varname}{i}')
                walker.run()
        LogBlock(f'Build pass {self.target}')

        
class NetlistPass(Walker):

    def run(self):
        cls_name = self.target.get_module_type_name()
        LogBlock(f'Netlist pass {cls_name}')
        if cls_name not in Module._modules and not isinstance(self.target, Leaf):
            # Call the fast symbol table lookup constructor
            self.target._sym_table._setup_connections_lookup()
            Module._modules[cls_name] = self.target.get_spice()
            logger.debug(f'Got spice for {cls_name}')
            logger.debug(Module._modules[cls_name])
            logger.debug(self.target._sym_table.ports)
        else:  
            pass
        # Now, look at all the modules attached as attributes in the target module
        # and walk those recursively
        for varname, var in vars(self.target).items():
            for i, module in enumerate(self.iter_flattened(var, lambda x: isinstance(x,Module))):
                logger.debug(f'Walking {i}:{module}')
                walker = NetlistPass(module, f'{self.target_name}.{varname}{i}')
                walker.run()
        LogBlock(f'Netlist pass {cls_name}')

class SimPass(Walker):

    async def run_sim(self):
        processes = await self.run()
        for proc in self.iter_flattened(processes, lambda x: isinstance(x,SourceModule)):
            logger.info(f'Joining on {proc}')
            await proc._pid.join()
        
        for proc in self.iter_flattened(processes, lambda x: not isinstance(x,SourceModule)):
            logger.info(f'Cancelling {proc}')
            await proc._pid.cancel() 

    async def run(self):
        sim_modules = []  # Keep track off all the sim jobs we launched (module)
        logger.info(f'Running sim of {self.target.name}')
        LogBlock(f'Sim pass {self.target.name}')
        pid = await spawn(self.target.sim())
        self.target._pid = pid
        sim_modules.append(self.target)

        # Now, look at all the modules attached as attributes in the target module
        # and walk those recursively, if there's no sim method defined in the target class
        has_sim_method = 'sim' in vars(self.target.__class__)
        if not has_sim_method:
            # We need to simulate all the sub instances recursively
            for varname, var in vars(self.target).items():
                for i, module in enumerate(self.iter_flattened(var, 
                                                    lambda x: isinstance(x,Module) and not 
                                                            isinstance(x, Leaf))):
                    logger.debug(f'Siming {i}:{module}')
                    walker = SimPass(module, f'{self.target_name}.{varname}{i}')
                    sim_submodules = await walker.run()
                    sim_modules.append(sim_submodules)
        LogBlock(f'Sim pass {self.target.name}')
        return sim_modules