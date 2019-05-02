# Introduction

`kpp` is a Python3 package for solving k-partition problems by preprocessing and cut-and-branch techniques.
As well as providing routines for solving the classical k-partition problem, it also provides functionality for solving a two-level version of the k-partition problem.

Details of the decomposition and cut-and-branch algorithms used can be found in the following paper:

- [A two-level graph partitioning problem arising in mobile wireless communications](https://link.springer.com/article/10.1007%2Fs10589-017-9967-9)

In addition, details of the projected clique inequalities can be found here:

- [Projection results for the k-partition problem](https://doi.org/10.1016/j.disopt.2017.08.001)

# Usage

See example scripts in the example directory.

# Dependencies

- setuptools
- igraph
- gurobipy

# Installation

Download the repository and in the package root directory run the following command:

`sudo python3 setup.py install`

Or, if the user does not have superuser privileges:

`python3 setup.py install --user`


