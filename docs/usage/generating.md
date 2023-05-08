
# Generating netlists

## CLI 
Use `cb_netlist` to generate a netlist from an example:

``` 
cb_netlist sw130 circuitbrew.examples.inv hspice all
```

If your have your own file in a subdirectory `mine/logic.py` in your current
working directory:

``` 
cb_netlist sw130 mine.logic hspice all
```

The general arguments are:

- `techfile`:  only Skywater 130 is publicly released, although it's trivial to
write your own
- `module`: Module that will be instanced 
- `output format`: Only `hspice` for now, although verilog is planned
- `flow steps`: Only `all` for now.

### Output
The output goes by default into `./output`.  In this directory you will see all the files
required for simulation:

```
output/
   top.sp
   hspice_clk.va
   template_0_hspice_src.va
   template_0_hspice_bucket.va
```
You can run `hspice top.sp` (or finesim or whatever your simulator of choice is).