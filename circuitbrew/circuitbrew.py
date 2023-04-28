import sys, logging
from pathlib import Path
import curio
from docopt import docopt
from mako.template import Template
from importlib import import_module
import importlib
import yaml

import os
from .walker import BuildPass, NetlistPass, SimPass
from .module import Module

from .version import __version__ 

import circuitbrew.tech as tech

logger = logging.getLogger(__name__)

class CircuitBrew:
    """
        The main class.  Performs the following functions:
        
        - Build netlist
        - Simulate and generate vectors
        - Output netlist
        
    """

    file_extension = { 'hspice': 'sp', 'verilog': 'v'}
    def __init__(self, docopt_string):
        self.flow = { 'build': 'Build netlist',
                      'sim'  : 'Simulate vectors',
                      'netlist': 'Output netlist',
                    }
        self.docopt_string = docopt_string

    def _get_techfile(self, process: str) -> tuple[dict, str]:
        """
            Read the tech file from process/tech.yml and the template spice file
            for the process.  
            
            Two locations are searched:

            1. *Built-in*: The package resource inside circuitbrew/tech/process/{process}
            2. *Locally supplied*: The local directory {process}
            
            Args:
                process: A string like 'n7' or 'sw130', or a local directory
            
            Returns:
                (techoptions, template_file):  A dict of the tech options and the contents of the template spice file
        """
        pth = importlib.resources.files(tech) / 'process' / process
        if not pth.exists():
            pth_local = Path(process)
            assert pth_local.exists(), f'Cannot find process {process} in {pth} or {pth_local}'
            pth = pth_local

        with open(pth / 'tech.yml') as f:
            techfile = f.read()
            techoptions = yaml.safe_load(techfile)
        
        template_filename = techoptions['template']

        with open(pth / template_filename) as f:
            template_file = f.read()

        return techoptions, template_file

    def netlist(self):
        tech_options, template_str = self._get_techfile(self.process)
        mytemplate = Template(template_str)

        circuit_lib = import_module(self.module)

        sim_setup = tech_options
        sim_setup['sim_type'] = self.netlist_type   # Add in whether CL option was hspice or verilog

        # Measure.sim_setup = sim_setup
        # Leaf.sim_setup = sim_setup
        # G.sim_setup = sim_setup
        Module.sim_setup = sim_setup
        #sim_setup['circuit'] = main.get_netlist('xmain')
        main = circuit_lib.Main()
        walker = BuildPass(main, 'xmain')
        walker.run()
        
        if 'sim' in self.flow:
            walker = SimPass(main, 'xmain')
            curio.run(walker.run_sim, with_monitor=True)

        walker = NetlistPass(main, 'xmain')
        walker.run()
        lines = []
        for module, contents in Module._modules.items():
            lines += contents
            lines += '\n'
        sim_setup['circuit'] = '\n'.join(lines)
        sim_setup['main_type_name'] = main.get_module_type_name()

        spice = mytemplate.render(**sim_setup)

        with open(os.path.join(sim_setup['output_dir'], 'top.'+self.file_extension[self.netlist_type]), 'w') as f:
            f.write(spice)
        return spice

    def get_options(self, argv):
        """
            Parse the command-line options and set the following object properties:

            :param argv: usually just sys.argv[1:]
            :returns: Nothing

            :ivar debug: Enable logging debug statements
            :ivar verbose: Enable verbose logging
            :ivar config: Dict of the config file

        """
        docstring = self.docopt_string 
        padding = max([len(x) for x in self.flow.keys()]) # Find max length of flow step names for padding with white space
        docstring = docstring % ('|'.join(self.flow), 
                              ','.join(self.flow.keys()),
                              '\n'.join(['    '+k+' '*(padding+4-len(k))+v for k,v  in self.flow.items()]))
        args = docopt(docstring, version=__version__)
        if args['--debug']:
            logging.basicConfig(level=logging.DEBUG, format='%(message)s')
        elif args['--verbose']:
            logging.basicConfig(level=logging.INFO, format='%(message)s')   

        # Load in default conf values from file if specified
        # if args['--conf']:
        #     with open(args['--conf']) as f:
        #         conf_args = yaml.load(f)
        # else:
        #     conf_args = {}
        # args = merge_args(conf_args, args)

        if args['all'] == 0:
            for f in list(self.flow):
                if args[f] == 0: del self.flow[f]
            logging.info("Doing flow steps: %s" % (','.join(self.flow.keys())))

        #self.parameters = ordered_load(args['PARAMFILE'])
        #self.run_dir = args['--rundir']

        self.process = args['TECH']
        self.module   = args['MODULE']
        self.netlist_type = args['NETLIST_TYPE']

        self.args = args # Just save this for posterity


    def go(self, argv):
        """

            #. Do something
            #. Do something else
        """
        # Preliminary option parse to get the --verbose and --debug flags parsed
        # for the load_plugins method.  We will reparse args again in the get_options to get
        # the full set of arguments
        if '--verbose' in argv or '-v' in argv:
            logging.basicConfig(level=logging.INFO, format='%(message)s')
        if '--debug' in argv or '-d' in argv:
            logging.basicConfig(level=logging.DEBUG, format='%(message)s')

        logger.info('Analyzing options...')
        self.get_options(argv)
        logger.info('Setting up run...')
        self.netlist()
