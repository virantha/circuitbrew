# Building an inverter

## Subclass Module and define Ports
The first thing to do is define a new class that corresponds to the inverter and
define its ports.

Every class in CircuitBrew that emits a SPICE subcircuit must inherit from the
['Module'][circuitbrew.module] class.  To add single bit ports, you specify
class attributes that are instances of
['InputPort'][circuitbrew.ports.InputPort] and
['OutputPort'][circuitbrew.ports.OutputPort].

``` py linenums="1" title='inverter_01.py'
--8<--- "circuitbrew/examples/inverter/inverter_01.py"
```

## Add supply ports for power/ground
We typically always want to add in power and ground connections, so we'll add
a special port called a ['SupplyPort'][circuitbrew.compound_ports.SupplyPort] to 
the ports list:

``` py linenums="1" title='inverter_02.py'
--8<--- "circuitbrew/examples/inverter/inverter_02.py"
```

A SupplyPort is an example of a CompoundPort, and is defined as:

``` py
class SupplyPort(CompoundPort):
    vdd = Port()
    gnd = Port()
```
CompoundPorts are used when you want to pass around pre-defined collections of ports,
and the sub-ports can be accessed via standard Python dotted notation (e.g. `p.vdd`).

## Create the transistors inside the inverter
The next step is to instance whatever circuit elements we want to use inside the inverter.
We do this inside a instance method called `build` which is executed at netlist creation time.
Any circuit module or leaf cell that is attached to the Module as an instance
attribute (`self.*`) will be emitted in the final SPICE output. 

``` py linenums="1" title='inverter_03.py'
--8<--- "circuitbrew/examples/inverter/inverter_03.py"
```

1. We have two transistors instanced, a [Pfet][circuitbrew.fets.Pfet] and
[Nfet][circuitbrew.fets.Nfet].  In order to get them to emit, we need to attach them 
to instance attributes as `self.pup` and `self.ndn` (choose whatever names you wish)
2. We connect the gate, drain, source, and bulk to the appropriate
nodes. Note that all the ports are also available as instance attributes 
3. The widths and lengths are whatever the defaults are in the
(techfile)[usage/techfiles.md].
4. We can create local vars to simplify long expressions names, for example, with the vdd and gnd connections.  
5. It's also important to end every `build` method with the `self.finalize()` call.  An
error will be thrown if you forget this.

## Add a Main Module for generating a netlist
In order to netlist the inverter, we need to have special `Main` class defined.  CircuitBrew
uses this as the starting point for tracing the hierarchy for emitting a netlist:

``` py linenums="1" title='inverter_04.py'
--8<--- "circuitbrew/examples/inverter/inverter_04.py"
```

## Emitting the netlist
Assuming your Inverter file is inside `circuitbrew/examples/inverter/`, we can 
run the following to emit the spice netlist:

```
python cb_netlist.py sw130 circuitbrew.examples.inverter.inverter_04 hspice all
```

## Adding stimuli to exercise the inverter
We can add test fixtures like clock signals, pulses, vectors, etc to the circuit, 
in order to do transient simulations in HSPICE.  You can import a `Supply` module for the
voltage source from the [Elements][circuitbrew.elements] module, and also a Verilog-A based
clock generator for the data input:

``` py linenums="1" title='inverter_05.py'
--8<--- "circuitbrew/examples/inverter/inverter_05.py"
```

This will then emit the following spice:

``` spice
*
.option brief=1
.lib "/Users/virantha/dev/circuitbrew/skywater-pdk-libs-sky130_fd_pr/models/sky130.lib.spice" tt
.option brief=0
.option scale=1e-6
.temp 85
.param voltage=1.8
.option post

.subckt Main 
xclk p.vdd inv_in VerilogClock freq=300000.0 offset=0
xmyinv inv_in b_0 gnd p.vdd Inverter
xvdd gnd p.vdd Supply
.ends

.subckt Supply p.gnd p.vdd
Vvdd_vss p.gnd 0 0.0
Vvdd_vdd p.vdd 0 1.8
.ends

.hdl hspice_clk.va

.subckt Inverter a b p.gnd p.vdd
xmn0 b a p.gnd p.gnd sky130_fd_pr__nfet_01v8_lvt w=1.0 l=0.5
xmp0 p.vdd a b p.vdd sky130_fd_pr__pfet_01v8_lvt w=1.0 l=0.5
.ends

xmain Main

.tran 1p 10n
.end
```

## Next steps
Now that we've covered the basics on assembling and providing a basic stimuli to circuits, let's 
move on to move advanced test vector generation in the next example.
