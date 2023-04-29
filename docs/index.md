# Welcome to CircuitBrew

CircuitBrew provides a framework for building SPICE-based circuits and generating test vectors 
for arbitrarily complex transistor-based circuits directly in Python.  

* Free and open-source software: ASL2 license
* Blog: http://virantha.com/category/projects/circuitbrew
* Documentation: http://virantha.github.io/circuitbrew
* Source: https://github.com/virantha/circuitbrew

Some notable features of CircuitBrew over a schematic capture tool or a Domain
Specific Language based circuit design tool:  

1. **Built-in test vector generation**: With most other tools, I end up needing
to build a behavioral model in a high-level language like Python to
generate test vectors.  CircuitBrew provides the hooks to build the model inline with the
circuit description, and uses a built-in event simulator to generate expected vectors.

2. **Simplicity**: Schematic capture for complex digital circuit *design* can be
tedious. And learning/re-learning a circuit design DSL creates a lot of
overhead, especially when you want to jump in quickly and prototype a custom circuit. Here, 
subckts are just Python classes, and ports are just init args; all the power of Python is
available to assemble complex digital circuits at the transistor level.

3. **Ease of maintenance**: Extending a circuit design DSL, as SPICE models
evolve and become more complex, becomes incredibly time-consuming, especially
when the original tool authors have moved on from the code base.  Everything
here is built on standard Python features, and should be easily extensible.

The examples below show SPICE files emitted for the open-source SkyWater 130nm PDK, to avoid 
revealing any proprietary data, but I generally use this in my own work for advanced 7nm
and smaller-node foundries.

## Installation

``` sh

    $ pip install circuitbrew

```
## Usage
Please see the [usage guide](usage/). 

## Disclaimer

The software is distributed on an "AS IS" BASIS, WITHOUT
WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.

## Simple example
Here's a simple inverter implemented directly in Python:

### Inverter in Python
``` py
class Inv(Module):
    inp = InputPort()
    out = OutputPort()

    p = SupplyPort()

    def build(self):
        vdd, gnd = self.p.vdd, self.p.gnd
        self.pup = Pfet(g=self.inp, d=vdd, s=self.out, b=vdd)
        self.ndn = Nfet(g=self.inp, d=self.out, s=gnd, b=gnd)
        self.finalize()

class Main(Module):

    def build(self):
        self.inv = Inv('myinv')
        self.finalize()
```

### SPICE for a simple inverter
CircuitBrew directly emits SPICE from this:

``` spice 
.subckt Main 
xmyinv inp_0 out_1 p_2 p_3 Inv
.ends

.subckt Inv inp out p.gnd p.vdd
xmn0 out inp p.gnd p.gnd sky130_fd_pr__nfet_01v8_lvt w=1.0 l=0.5
xmp0 p.vdd inp out p.vdd sky130_fd_pr__pfet_01v8_lvt w=1.0 l=0.5
.ends

xmain Main
```

## More complex example with test vector generation
Here's a more complex example that generates a simulation harness with test vector
generation and digital checking of outputs.  We generate random values that get
fed into the inverter, and verify them on the output in the SPICE sim.  CircuitBrew
contains custom Verilog-A modules that can handle driving and checking values digitally
inside an analog hspice simulation.

### Python for simulation/verification of an Inverter
``` py
class Inv(Module):
    inp = InputPort()
    out = OutputPort()

    p = SupplyPort()

    def build(self):
        vdd, gnd = self.p.vdd, self.p.gnd
        self.pup = Pfet(g=self.inp, d=vdd, s=self.out, b=vdd)
        self.ndn = Nfet(g=self.inp, d=self.out, s=gnd, b=gnd)
        self.finalize()

    async def sim(self):
        while True:
            val = await self.inp.recv()
            await self.out.send(1-val)
    
class Main(Module):

    def build(self):
        self.supply = Supply('vdd', self.sim_setup['voltage'], )
        p = self.supply.p
        vdd, gnd = p.vdd, p.gnd
        self.inv = Inv('myinv', p=p)

        self.clk_gen = VerilogClock('clk', freq=750e3, enable=vdd)
        src_clk = self.clk_gen.clk

        self.clk_buc = VerilogClock('clk2', freq=750e3, offset='100p', enable=vdd)
        sample_clk = self.clk_buc.clk

        self.src = VerilogSrc('src', [randint(0,1) for i in range(10)], 
                             d=self.inv.inp, clk=src_clk, _reset=vdd)

        self.bucket = VerilogBucket(name='buc', clk=sample_clk, _reset=vdd, d=self.inv.out)
        self.finalize()
```

### Generated SPICE with test bench

``` spice
.subckt Main 
xbuc sample_clk p.vdd d_0 VerilogBucket_0
xclk2 p.vdd sample_clk VerilogClock freq=750000.0 offset=100p
xclk p.vdd src_clk VerilogClock freq=750000.0 offset=0
xmyinv inp_1 d_0 gnd p.vdd Inv
xsrc src_clk p.vdd inp_1 VerilogSrc_0
xvdd gnd p.vdd Supply
.ends

.subckt Supply p.gnd p.vdd
Vvdd_vss p.gnd 0 0.0
Vvdd_vdd p.vdd 0 1.8
.ends

.subckt Inv inp out p.gnd p.vdd
xmn0 out inp p.gnd p.gnd sky130_fd_pr__nfet_01v8_lvt w=1.0 l=0.5
xmp0 p.vdd inp out p.vdd sky130_fd_pr__pfet_01v8_lvt w=1.0 l=0.5
.ends

.hdl hspice_clk.va
.hdl template_0_hspice_src.va
.hdl template_0_hspice_bucket.va

xmain Main
```
For full documentation visit [mkdocs.org](https://www.mkdocs.org).



