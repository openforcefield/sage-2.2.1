# Sage 2.2.1

This repository contains files and progress in re-fitting OpenFF 2.2.1,
a patch update to [OpenFF 2.2.0](https://github.com/openforcefield/sage-2.2.0).

The goals of this update were to:

    * re-fit with linear angles set to 180°
    * re-fit Improper torsions as well


Most files in this force field were originally copied from the
[OpenFF 2.2.0](https://github.com/openforcefield/sage-2.2.0)
repository, and then updated or modified.

## Fitting pipeline
The code that was used to produce the fit is all included here, and should be reproducible. The fit is performed in several steps, with instructions for how to run each step in the `README` file in each directory:

1. `01_generate-forcefield`: Generate an initial "template" force field, which contains the desired SMIRKs patterns for all bond/angle terms, the desired SMIRKs patterns and initial values for all torsion terms, and the desired final value for all other parameters such as electrostatics.

**This was modified to re-set all linear angles to 180°.**

2. `02_curate-data`: Download and filter/curate the optimized geometry and torsion drive datasets to use for the fit. Determine which parameters to optimize based on dataset coverage.

**The files in this directory were *not* modified. Some scripts were
added for inspecting the training set.**

3. `03_generate-initial-ff`: Generate initial values for the bond and angle terms of the force field using the Modified Seminario Method.

**Files in this directory were modified to avoid re-setting values
for linear angles.**

4. `04_fit-forcefield`: Fit the force field bonds, angles, and proper torsions to the data using ForceBalance.

**All files in this directory were re-generated for the new fit.**

5. `05_benchmark_forcefield`: Benchmark the force field.

**Files in this directory were somewhat modified for updated analysis.**

6. `06_plot-figures`: plot figures analyzing the new force field.

This is a new directory that plots the benchmark results in the
benchmarking directory.


## Python environment

Where possible, shell scripts (`*.sh`) have been provided
showing which environments were used to run Python scripts,
as well as example inputs and outputs. Two environments
were used throughout this force field:

* [yammbs](05_benchmark_forcefield/yammbs-env-full.yaml)
* [fb_196_ic_0318](04_fit-forcefield/nor4/fb-fit/full-env.yaml)

Environments can be re-created using the provided files:

```
mamba env create -f yammbs-env-full.yaml
```

If using a different platform, a less detailed environment
may need to be created instead. Smaller specification files
can be found in the 2.2.0 repo.


## Changes

The following angles below had their equilibrium values set to 180 degrees.

| Parameter | SMIRKS                    | MSM value (°) |
|-----------|---------------------------|---------------|
| a16       | `[*:1]~[#6X2:2]~[*:3]`    | 178           |
| a17       | `[*:1]~[#7X2:2]~[*:3]`    | 176           |
| a27       | `[*:1]~[#7X2:2]~[#7X1:3]` | 176           |
| a35*      | `[*:1]=[#16X2:2]=[*:3]`   | 180           |

### Global benchmarks

The global benchmarks (ddEs, RMSDs, and TFDS) look very similar
to 2.2.0:

![ddE histogram](06_plot-figures/images/all/dde.png)
![ddE CFD](06_plot-figures/images/all/abs_dde.png)
![RMSDs](06_plot-figures/images/all/aa_rmsds.png)
![TFDs](06_plot-figures/images/all/tfds.png)
