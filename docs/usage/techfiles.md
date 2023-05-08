
# Techfile Files
Techfiles are typically found in `circuitbrew/tech/process`.  Each process node should be a subdirectory here, with two files
like the following for Skywater:

```
    circuitbrew/
        tech/
            process/
                sw130/
                    sw130.sp
                    tech.yml
```

The `sw130.sp` file is the main SPICE template that's written using Mako.  The process parameters are specified in
`tech.yml`:

```yaml
tech: sw130
voltage: 1.8
temp: 85
output_dir: 'output'
template: 'sw130.sp'

Fet:
  auto:
    l: 0.5    # Length
    w:  1.0   # Default width
    vt: lvt   # Default vt 
    width_id: w  # Name in spice xtor model for width/nfin/etc
  Pfet:
    auto:
      # Define xtor models for different VTs
      lvt: sky130_fd_pr__pfet_01v8_lvt
  Nfet:
    auto:
      # Define xtor models for different VTs
      lvt: sky130_fd_pr__nfet_01v8_lvt

```
This tech file is loaded at start up and stored in every `Module` instance as a dict: 
`self.sim_setup`. In addition, everything is accessible inside your SPICE template
file, so if you wanted to add a configuration setting/value pair into your SPICE
file, you could just add it to the top-level of the `tech.yml` file.  Then, 
write it into your `sw130.sp` file with Jinja syntax (e.g. `${new_option}`)

The keys that are named after Module names are meant to provide a way to get 
configuration settings to specific classes.
Anything that is under the `auto` key is automatically set as a member attributes for
the matching class's objects.  For example, every `Fet` module object
automatically has the `l`, `w`, `vt`, and `width_id` member attributes set.
These can also be overridden via keyword args to the constructor.

So, doing the following will create a Fet with width 2.0 while keeping the length as 0.5:
``` py
    ...
    self.mynfet = Nfet(w=3)
```

Make sure you **follow the class hierarchy** in the `tech.yaml` file if you want the
attributes to apply properly.