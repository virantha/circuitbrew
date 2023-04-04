"""
Generate a spice netlist from a Python representation

Usage:
    netlist.py [options] TECH MODULE NETLIST_TYPE all
    netlist.py [options] TECH MODULE NETLIST_TYPE (%s)...

    netlist.py -h

Arguments:
    TECH     Tech file to use
    MODULE   Module to netlist
    NETLIST_TYPE   Type of netlist to output
    all      Run all steps in the flow (%s)
%s

Options:
    -h --help                 show this message
    -v --verbose              show more information
    -d --debug                show even more information              

"""
import sys, logging
import mako, curio
from docopt import docopt
from mako.template import Template
from mako.lookup import TemplateLookup
from importlib import import_module
import os
from walker import BuildPass, NetlistPass, SimPass
from module import Module

from version import __version__ 

logger = logging.getLogger(__name__)

class CircuitBrew:
    """
        The main class.  Performs the following functions:
        
        - Build netlist
        - Simulate and generate vectors
        - Output netlist
        
    """

    file_extension = { 'hspice': 'sp', 'verilog': 'v'}
    def __init__(self):
        self.flow = { 'build': 'Build netlist',
                      'sim'  : 'Simulate vectors',
                      'netlist': 'Output netlist',
                    }

    def netlist(self):
        mylookup = TemplateLookup(directories=['tech'])
        mytemplate = mylookup.get_template(self.techfile)

        circuit_lib = import_module(self.module)

        main = circuit_lib.Main()
        sim_setup = {'voltage': '0.75',
                    'temp': "105",
                    'output_dir': 'output',
                    'sim_type': self.netlist_type,
        }
        # Measure.sim_setup = sim_setup
        # Leaf.sim_setup = sim_setup
        # G.sim_setup = sim_setup
        Module.sim_setup = sim_setup
        #sim_setup['circuit'] = main.get_netlist('xmain')
        walker = BuildPass(main, 'xmain')
        walker.run()
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

    def get_options(self, argv):
        """
            Parse the command-line options and set the following object properties:

            :param argv: usually just sys.argv[1:]
            :returns: Nothing

            :ivar debug: Enable logging debug statements
            :ivar verbose: Enable verbose logging
            :ivar config: Dict of the config file

        """
        docstring = __doc__ 
        padding = max([len(x) for x in self.flow.keys()]) # Find max length of flow step names for padding with white space
        docstring = __doc__ % ('|'.join(self.flow), 
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

        self.techfile = args['TECH']
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

def main():
    script = CircuitBrew()
    script.go(sys.argv[1:])

if __name__=='__main__':
    main()