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
import circuitbrew.circuitbrew as cb
import sys

if __name__=='__main__':
    print(__doc__)
    script = cb.CircuitBrew(__doc__)
    script.go(sys.argv[1:])

