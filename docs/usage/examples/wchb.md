# QDI Buffer - A More complicated example

## Introduction
In this example we will generate an asynchronous circuit built using pipelined 
4-phase handshake circuits that are quasi-delay-insensitive (QDI).

### Communication protocol
In our example, two buffers communicating a 1-bit data value using a 4-phase handshake
will use a bundle of three wires consisting of:

- two data rails (a true and false rail) 
- an acknowledge (or enable) wire

``` mermaid
flowchart LR
BUF1-- t --> BUF2
BUF1-- f --> BUF2
BUF2-- e --> BUF1
```

We will use return-to-zero signaling on the data wires. So, for example,
to send a value of `1` from BUF1 to BUF2, we would do the following:

``` mermaid
sequenceDiagram
    participant BUF1
    Note right of BUF1: Reset with t,f low and e high
    BUF1 ->> BUF2: Raise t wire
    BUF2 -->> BUF1: Lower e wire
    BUF1 ->> BUF2: Lower t wire
    BUF2 -->> BUF1: Raise e wire
    Note right of BUF1: Back at initial state with t,f low and e high
```
### Circuit implementation of a Buffer
We will use a simple implementation of a weak-conditioned-half-buffer(WCHB)
handshake circuit to implement BUF1, shown in the schematic below.  The circle
with a 'C' represents a [Muller Consensus or
C-element](https://en.wikipedia.org/wiki/C-element) which is a dynamic gate that
sets its output value to the input value when both inputs are the same.  

![wchb](wchb.png)

## Building blocks
First, let's take a look at how we build the individual gates in the WCHB 
schematic.

### Parametrized Inverter
Although we saw a simple [inverter](inverter.md) previously, this
time we're going to show you how to build a parametrized inverter based on its
sizes and vt choices.  

This inverter is built in to the standard [gates][circuitbrew.gates]
library, but let's take a look at the implementation:

``` py linenums="1" title='wchb_inverter.py'
--8<--- "circuitbrew/examples/wchb/wchb_inverter_01.py"
```

Adding parameters to a Module is done in the following way:

- Add each parameter as a type annotation ([Param][circuitbrew.module.Param])
- Use the parameters as a regular Python attribute in your `build` method

When you want to use the parametrized Module, you call `Parametrize` on the 
Module you want with the parameter values, which will return a new Module (class)
that you can then instance.  If you don't want to keep around the parametrized
class for more instances, you could also simply do:

``` py
    self.inv = Parameterize(Inv, p_strength=3, n_strength=3, vt='svt')()

```

### Parametrized NOR
Now let's take a look at a different use for parameters: Specifying the width of
a port. 

We've already seen how to do a [2-input NOR](nor2.md), but
what if we want to build a generic N-input NOR?  Well, we need to first declare
N as a Param.  But how do we pass this into the InputPorts as the width, since it
hasn't been defined yet?  The way we do this is by using [Param][circuitbrew.module.Param]
as a placeholder function with the name of the parameter:

``` py linenums="1" title='wchb_nor2_01.py'
--8<--- "circuitbrew/examples/wchb/wchb_nor2_01.py"
```

Once [Parameterize][circuitbrew.module.Parameterize] is called with the actual value for `N`,
it will resolve itself when `a` is accessed for the first time.  The rest of the implementation
of NorN just needs to use `self.N` in an appropriate way to build the circuit like so:


``` py linenums="1" title='wchb_nor2_02.py'
--8<--- "circuitbrew/examples/wchb/wchb_nor2_02.py"
```

Here, you can see how we used the `|` and `&` operators in a loop to construct the
CMOS stacks.

The resulting SPICE looks like 

```spice
.subckt Main 
xNorN_N_3_size_2_inst_0 a_0 a_1 a_2 b_3 p_4 p_5 NorN_N_3_size_2
.ends


.subckt NorN_N_3_size_2 a[0] a[1] a[2] b p.gnd p.vdd
xmn0 b a[1] p.gnd p.gnd sky130_fd_pr__nfet_01v8_lvt w=2 l=0.5
xmn1 b a[0] p.gnd p.gnd sky130_fd_pr__nfet_01v8_lvt w=2 l=0.5
xmn2 b a[2] p.gnd p.gnd sky130_fd_pr__nfet_01v8_lvt w=2 l=0.5
xmp0 d_0 a[0] b p.vdd sky130_fd_pr__pfet_01v8_lvt w=2 l=0.5
xmp1 d_1 a[1] d_0 p.vdd sky130_fd_pr__pfet_01v8_lvt w=2 l=0.5
xmp2 p.vdd a[2] d_1 p.vdd sky130_fd_pr__pfet_01v8_lvt w=2 l=0.5
.ends
```

Notice that the parameterized Nor sub-circuit has its parameter values
inserted into the name.  If another Nor is parameterized (say with N=4),
then it will have a different sub-circuit definition with `N_4` in the name.

### C-element
The c-element will be a state-holding gate, with the pull-up and pull-down
both just having the two terms in series.  We will use combinational
feedback to maintain the output when the inputs disagree in value.


``` py linenums="1" title='wchb_c2_01.py' 
--8<--- "circuitbrew/examples/wchb/wchb_c2_01.py"
```

## Putting it all together

### Assembling the WCHB
Let's construct the full WCHB circuit, with all of these building blocks.


???+ note "wchb_01.py"

    ``` py
    --8<--- "circuitbrew/examples/wchb/wchb_01.py"
    ```

We have added a reset signal to the schematic, just to make sure this circuit resets 
to a known state in the handshake.
The simulation method is quite straightforward, since it's just a pipelined buffer.

### Buffer chain
For the SPICE simulation, we're going to build a parameterized chain of buffers.
We will also use `src` and `bucket` modules that can drive `e1of2` ports.

``` mermaid
graph LR
    src --> buf_0;
    buf_0 --> buf_1;
    buf_1 --> buf_2;
    buf_2 --> buf_3;
    buf_3 --> bucket;

```

???+ note "wchb_02.py"

    ``` py
    --8<--- "circuitbrew/examples/wchb/wchb_02.py"
    ```

It becomes quite simple to build complex SPICE structures in CircuitBrew with Python's
powerful syntax; here, we're instantiating a chain of buffers in a `for` loop and
connecting them in a generic way.

The generated SPICE file is shown below:

??? note "wchb_02.sp"

    ``` spice
    *
    .option brief=1
    .lib "/Users/virantha/dev/circuitbrew/skywater-pdk-libs-sky130_fd_pr/models/sky130.lib.spice" tt
    .option brief=0
    .option scale=1e-6
    *---------------------------------------
    .temp 85
    .param voltage=1.8
    .option post

    .subckt Main 
    Vpwlpreset _pR p.gnd PWL (0n 0 4n 0 4.5n 1.8)
    Vpwlsreset _sR p.gnd PWL (0n 0 4n 0 4.5n 1.8)
    xbuc _pR _sR r.t r.f r.e VerilogBucketE1of2_0
    xwchb_0 _pR l.t l.f l.e p.vdd p.gnd r_0 r_1 r_2 Wchb
    xwchb_1 _pR r_0 r_1 r_2 p.vdd p.gnd r_3 r_4 r_5 Wchb
    xwchb_2 _pR r_3 r_4 r_5 p.vdd p.gnd r_6 r_7 r_8 Wchb
    xwchb_3 _pR r_6 r_7 r_8 p.vdd p.gnd r.t r.f r.e Wchb
    xsrc _pR _sR l.t l.f l.e VerilogSrcE1of2_0
    xvdd p.vdd p.gnd Supply
    .ends


    .subckt Supply p.vdd p.gnd
    .measure TRAN supplycurrent0 avg i(Vvdd_vdd)  
    .measure TRAN supplypower0 PARAM='-supplycurrent0*1.8'
    .measure TRAN supplypower_direct0 AVG P(Vvdd_vdd)  
    Vvdd_vss p.gnd 0 0.0
    Vvdd_vdd p.vdd 0 1.8
    .ends

    .subckt Wchb _pReset l.t l.f l.e p.vdd p.gnd r.t r.f r.e
    xCelement2_inst_1 l.f r.e r.f p.vdd p.gnd Celement2
    xCelement2_inst_0 l.t r.e r.t p.vdd p.gnd Celement2
    xInv_p_strength_1_n_strength_1_vt_svt_inst_0 _pReset mypreset p.vdd p.gnd Inv_p_strength_1_n_strength_1_vt_svt
    xNor3_inst_0 r.t r.f mypreset l.e p.vdd p.gnd Nor3
    .ends

    .subckt Celement2 i[0] i[1] o p.vdd p.gnd
    xmn0 t228_0 i[0] p.gnd p.gnd sky130_fd_pr__nfet_01v8_lvt w=1.0 l=0.5
    xmn1 _o i[1] t228_0 p.gnd sky130_fd_pr__nfet_01v8_lvt w=1.0 l=0.5
    xmp0 d_0 i[0] _o p.vdd sky130_fd_pr__pfet_01v8_lvt w=1.0 l=0.5
    xmp1 p.vdd i[1] d_0 p.vdd sky130_fd_pr__pfet_01v8_lvt w=1.0 l=0.5
    xmn2 t255_0 i[1] p.gnd p.gnd sky130_fd_pr__nfet_01v8_lvt w=1.0 l=0.5
    xmn3 d_1 i[0] p.gnd p.gnd sky130_fd_pr__nfet_01v8_lvt w=1.0 l=0.5
    xmn4 _o o t255_0 p.gnd sky130_fd_pr__nfet_01v8_lvt w=1.0 l=0.5
    xmp2 d_2 o _o p.vdd sky130_fd_pr__pfet_01v8_lvt w=1.0 l=0.5
    xmp3 d_3 i[0] d_2 p.vdd sky130_fd_pr__pfet_01v8_lvt w=1.0 l=0.5
    xmp4 p.vdd i[1] s_4 p.vdd sky130_fd_pr__pfet_01v8_lvt w=1.0 l=0.5
    xInv_p_strength_1_n_strength_1_vt_svt_inst_1 _o o p.vdd p.gnd Inv_p_strength_1_n_strength_1_vt_svt
    .ends

    .subckt Inv_p_strength_1_n_strength_1_vt_svt inp out p.vdd p.gnd
    xmn0 p.gnd inp out p.gnd sky130_fd_pr__nfet_01v8_lvt w=1 l=0.5
    xmp0 p.vdd inp out p.vdd sky130_fd_pr__pfet_01v8_lvt w=1 l=0.5
    .ends

    .subckt Nor3 a[0] a[1] a[2] b p.vdd p.gnd
    xmn0 b a[1] p.gnd p.gnd sky130_fd_pr__nfet_01v8_lvt w=1.0 l=0.5
    xmn1 b a[0] p.gnd p.gnd sky130_fd_pr__nfet_01v8_lvt w=1.0 l=0.5
    xmn2 b a[2] p.gnd p.gnd sky130_fd_pr__nfet_01v8_lvt w=1.0 l=0.5
    xmp0 d_0 a[0] b p.vdd sky130_fd_pr__pfet_01v8_lvt w=1.0 l=0.5
    xmp1 d_1 a[1] d_0 p.vdd sky130_fd_pr__pfet_01v8_lvt w=1.0 l=0.5
    xmp2 p.vdd a[2] d_1 p.vdd sky130_fd_pr__pfet_01v8_lvt w=1.0 l=0.5
    .ends

    .hdl template_0_hspice_src_1of2.va
    .hdl template_0_hspice_bucket_1of2.va

    xmain Main

    .tran 1p 10n

    .end
    ```

The waveforms from the resulting simulation are shown below, with the `l.t` and `l.f` input
rails and the shifted versions `r.t` and `r.f` at the end of the chain of buffers.
![SPICE](wchb_chain.png)