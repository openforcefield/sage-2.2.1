# Fit force field

This is the directory where the FF fit happens. The directory contains a few files and directories. As most of these were copied from the [Sage 2.2.0](https://github.com/openforcefield/sage-2.2.0/tree/main/04_fit-forcefield) repo, please see that repo for more detail on the files.

This directory contains the results of a number of experiments:

- nor4: this is analogous to `nor4` in Sage 2.2.0 and is the fit that resulted in 2.2.1-rc1. 
- a27-half-k: this is the same fit as `nor4` (with the same targets, priors, etc.) but the starting force field has the force constant of a27 set to *half* the MSM value.
- a27-quarter-k: this is the same fit as `nor4` (with the same targets, priors, etc.) but the starting force field has the force constant of a27 set to *a quarter* of the MSM value.

