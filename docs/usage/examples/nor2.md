# Building a 2-input NOR

This example will explain how to use [Ports][circuitbrew.ports.Ports] for
multi-bit data.

## Ports
You can use an [circuitbrew.ports.InputPorts][] to do a two-wide port for the
two-input NOR gate:

``` py
class Nor2(Module):
    a = InputPorts(width=2)
    b = OutputPort()
    p = SupplyPort()
```

Now, we can access each bit in `a` as a Python list (`self.a[0], self.a[1]`).

## Implementation using logic operators
When you want to implement a CMOS stack that's more than just an inverter,
it can quickly become tedious to write out all the transistors and their
connections manually.  

CircuitBrew allows you to use Python logical operators to quickly
construct transistor pull-up and pull-down networks with minimal text:

``` py
    def build(self):
        pdn = self.a[0] | self.a[1]
        pup = ~self.a[0]&~self.a[1]
        self.nor = self.make_stacks(output=self.b, pdn=pdn, pup=pup, power=self.p)
        self.finalize() 
```

Here, we define the pull-up and pull-down stacks following these rules:

- Use Python OR `|` and AND `&` operators on ports to build the logic.
- All pull-down stacks (nfets) must have non-negated ports in the logical expression
- All pull-up stacks (pfets) must have negated ports in the logical expression

Finally, call [circuitbrew.module.Module.make_stacks][] to construct the Fets and
return a list of the transistors.

