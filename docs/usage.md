# Generating netlists

Use `cb_netlist.py` to generate a netlist from an example:

``` 
python cb_netlist.py sw130 circuitbrew.examples.inv hspice all
```

The general arguments are

- `techfile`:  only Skywater 130 is publicly released, although it's trivial to
write your own), module to instance, 
- `module`: Module that will be instanced 
- `output format`: Only `hspice` for now, although verilog is planned
- `flow steps`: Only `all` for now.

