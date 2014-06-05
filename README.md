
Turbine is a Dataflow graph generator. 
It can generate SDFGs, CSDFGs and PCGs with initilization phases. All the graphs can be saved in the SDF3 XML format (a particular notation is considered for threshold and initilization phases).

Features
=======

 * Generate SDFG/CSDFG/PCG up to 10,000 actors (~10m for SDFG, ~2h for CSDFG/PCG).
 * Normalize/denormalize dataflow graph.
 * Compute initial marking.
 * Compute symbolic execution of dataflow graphs.
 * Generate .sdf3 xml files (see SDF3 generator)
 * Generate .tur files (10 times smaller than sdf3 files and easy to write by hand)

Installation
=======

Requirements
-------

 * networkx-1.8.1
 * python-glpk-0.4.43

 On Fedora 17+, you can install networkx by using `yum install networkx -y`.
python-glpk can be found here http://www.dcc.fc.up.pt/~jpp/code/python-glpk/.

Usage
=======

How to generate a dataflow using Python
-------

```
import turbine
graph = generate(taskCount)
write_sdf3_file(graph)

```

Then a SDF3 XML file `sortie.sdf3` will be created in current directory.
To change the filename, you can use  `write_sdf3_file(graph, fileName = "fileName")`.

How to see the generated linear program used to compute the inital marking
--------

```
generate(taskCount, writePL = True)
```

A `preload.pl` file will be created in current directory.

