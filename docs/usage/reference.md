# Reference

The examples in the previous section has some details on useful built-in
modules in CircuitBrew to help you build and generate stimuli for your circuit.
This page is a comprehensive list on the gates and environment modules provided,
with links to the API, if you need more information on how to use them or extend
them.

## Built-in circuit modules
|Module | Description|
|--------|------------|
|[circuitbrew.gates.Inv][]| Inverter|
|[circuitbrew.gates.NorN][]| N-input NOR|
|[circuitbrew.qdi.Celement2][]| 2-input c-element|
|[circuitbrew.qdi.Wchb][]| 1-bit 4-phase half buffer|

## Environent modules
These modules are useful for setting up a simulation environment to
generate input stimuli and output verification during a SPICE simulation.
Most of these are covered in the different examples.

|Module | Description|
|--------|------------|
|[circuitbrew.elements.VoltageSource][]| Voltage source (usually easier to use Supply)|
|[circuitbrew.elements.Supply][]| Vdd and GND sources|
|[circuitbrew.elements.ResetPulse][]| Step waveform useful for applying resets|
|[circuitbrew.elements.VerilogClock][]| Generate clocks using a Verilog-A instance|
|[circuitbrew.elements.VerilogSrc][]| 1-bit Verilog-A source for input vectors|
|[circuitbrew.elements.VerilogBucket][]| 1-bit Verilog-A sink/verification for output vectors|
|[circuitbrew.qdi.VerilogSrcE1of2][]| 1-bit dual-rail w/ enable Verilog-A source for input vectors|
|[circuitbrew.qdi.VerilogBucketE1of2][]| 1-bit dual-rail w/ enable Verilog-A sink/verification for output vectors|