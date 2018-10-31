
Turbine is a Dataflow graph generator. For any question or bug report please contact youen.lesparre@lip6.fr.
It can generate SDFGs, CSDFGs and PCGs with initilization phases. All the graphs can be saved in the SDF3 XML format (a particular notation is considered for threshold and initilization phases).

Features
=======

 * Generate live SDFG/CSDFG/PCG up to 10,000 actors in ~20s.
 * Normalize/denormalize dataflow graph.
 * Compute initial marking (under period constraint and with linear or mixed interger programming).
 * Compute symbolic execution of dataflow graphs.
 * Compute period.
 * Generate .sdf3 xml files (see SDF3 generator)
 * Generate .tur files (10 times smaller than sdf3 files and easy to write by hand)

Installation
=======

Requirements
-------

 * networkx-1.11
 * swiglpk (python-glpk-0.4.43 still work but is obsolete)
 * GLPK in any version schould work, also, v4.58 work great (GLPK 4.47 or 4.48 if running with python-glpk).

With Fedora 17+, you can install networkx by using `yum install networkx -y`.
Instructions to install swiglpk can be found here https://pypi.python.org/pypi/swiglpk.
GLPK is available at http://ftp.gnu.org/gnu/glpk/.

To test if the installation is ok run basic_test.py located on the root of turbine.
Please, report any trouble at youen.lesparre@lip6.fr .

Update note for Fedora 28, the two following command can help to prepare the system for Turbine:

 * yum install python2-networkx.noarch glpk python2-pydot
 * pip install swiglpk

Usage
=======


How to run Turbine
-------

There is no installation step, to use Turbine you just have to specify it in the PYTHONPATH environnement variable.
As an example, to run the `examples/compute_initial_marking.py` script, in the root directory of turbine :
```
$ PYTHONPATH=`pwd`  ./Turbine/examples/compute_initial_marking.py
#################generated graph#################
###### Setup the SDF generation #####
###### Generate dataflow ############
name: SDF_of_test
task count: 10 arc count: 30
tot initial marking: 0
###### Compute the initial marking ##
name: SDF_of_test
task count: 10 arc count: 30
tot initial marking: 6714
....
```


How to generate a dataflow using Python
-------

```
import turbine

param= param.parameters.Parameters()

dataflow = generate(param)
write_sdf3_file(dataflow, filename = "fileName.sdf3")

```

Then a SDF3 XML file `filename.sdf3` will be created in current directory.

How to see the generated linear program used to compute the inital marking
--------

```
param= param.parameters.Parameters()
param.set_lp_filename(test.lp)

generate(param)
```

Several examples are avalaible in 'turbine/examples'.

