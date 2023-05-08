# Usage guide

Circuits designed in CircuitBrew are written as standard Python classes 
using the following rules:

## Netlisting
1. Inherit from [Module][circuitbrew.module.Module] [^1].
1. Every [Port][circuitbrew.module.Module] must be defined as a class attribute.
1. Every Module must have a `def build(self)` method.
1. Every sub-instance to be emitted as part of your Module must be assigned as an instance attribute on 
the Module using `self`.
1. Every `build` method needs a `self.finalize()` statement at the end.

Other than that, you can use bog-standard Python to construct your instances/connectivity.
  
## Modeling
1. Implement an `async def sim(self):` method
2. `Recv` from the input [ports][circuitbrew.ports], transform the inputs, and
`send` on the output [ports][circuitbrew.ports]

All of these concepts are covered in-depth in the [examples](examples)
[^1]: Inherit from [Leaf][circuitbrew.module.Leaf] if you're going to emit raw spice without any sub-modules

