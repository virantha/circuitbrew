# Building an inverter

## Subclass Module and define Ports
The first thing to do is define a new class that corresponds to the inverter and
define its ports.

Every class in CircuitBrew that emits a SPICE subcircuit must inherit from the
['Module'][circuitbrew.module] class.  To add single bit ports, you specify
class attributes that are instances of
['InputPort'][circuitbrew.ports.InputPort] and
['OutputPort'][circuitbrew.ports.OutputPort].

``` py linenums="1"
--8<--- "circuitbrew/examples/inverter/inverter_01.py"
```