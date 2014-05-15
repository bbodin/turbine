
Turbine is a Dataflow graph generator. 
It can generate SDFs, CSDFs and PCGs with initilization phases. All the graphs can be saved in the SDF3 XML format (a particular notation is considered for threshold and initilization phases).

Features
=======

TBA

Installation
=======

Requirements
-------

 * networkx-1.8.1
 * python-glpk-0.4.43

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

