
# Generating netlists

## CLI 
Use `cb_netlist.py` to generate a netlist from an example:

``` 
python cb_netlist.py sw130 circuitbrew.examples.inv hspice all
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