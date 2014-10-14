
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
 * glpk 4.47 or 4.48 (constraint from python-glpk)

With Fedora 17+, you can install networkx by using `yum install networkx -y`.
Instructions to install python-glpk can be found here http://en.wikibooks.org/wiki/GLPK/Python.
glpk is available at http://ftp.gnu.org/gnu/glpk/.

Special note for python-glpk with Fedora
-------

With fedora there is no `pyversions` tool (required by `python-glpk`). You can fix it by adding the folowing line in the swig `Makefile` :

```
`pkg-config --cflags --libs python2`
```


Usage
=======

How to generate a dataflow using Python
-------

```
import turbine

param= param.parameters.Parameters()
param.setNbTask(100)

graph = generate(param)
write_sdf3_file(graph, fileName = "fileName.sdf3")

```

Then a SDF3 XML file `fileName.sdf3` will be created in current directory.

How to see the generated linear program used to compute the inital marking
--------

```
param= param.parameters.Parameters()
param.setNbTask(100)
param.setLPFileName(test.lp)

generate(param)
```

A `test.pl` file will be created in current directory.

Several examples are avalaible in 'turbine/examples'.

