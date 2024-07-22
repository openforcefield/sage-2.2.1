# Sage 2.2.1

This repository contains files and progress in re-fitting OpenFF 2.2.1,
a patch update to [OpenFF 2.2.0](https://github.com/openforcefield/sage-2.2.0).

**Note: this force field is still in progress, and many files (*especially READMEs*!)
were copied across from the 2.2.0 repository that require modification.
Use with caution!**

The goals of this update were to:

* re-fit with linear angles set to 180°
* re-fit Improper torsions as well


Most files in this force field were originally copied from the
[OpenFF 2.2.0](https://github.com/openforcefield/sage-2.2.0)
repository, and then updated or modified.

<!-- vscode-markdown-toc -->
* 1. [Fitting pipeline](#Fittingpipeline)
* 2. [Python environment](#Pythonenvironment)
* 3. [Changes](#Changes)
	* 3.1. [Global benchmarks](#Globalbenchmarks)
	* 3.2. [Sulfamide angles remain similar to 2.2.0](#Sulfamideanglesremainsimilarto2.2.0)
	* 3.3. [3-membered ring angle parameters remain similar to 2.2.0](#memberedringangleparametersremainsimilarto2.2.0)
	* 3.4. [Linear angles stay linear.](#Linearanglesstaylinear.)
* 4. [Parameter changes](#Parameterchanges)
	* 4.1. [Bond, improper, and proper torsion parameters don't change much](#Bondimproperandpropertorsionparametersdontchangemuch)
	* 4.2. [Several angle parameters change substantially](#Severalangleparameterschangesubstantially)

<!-- vscode-markdown-toc-config
	numbering=true
	autoSave=true
	/vscode-markdown-toc-config -->
<!-- /vscode-markdown-toc -->

##  1. <a name='Fittingpipeline'></a>Fitting pipeline
The code that was used to produce the fit is all included here, and should be reproducible. The fit is performed in several steps, with instructions for how to run each step in the `README` file in each directory:

### `01_generate-forcefield`: Generate an initial "template" force field, which contains the desired SMIRKs patterns for all bond/angle terms, the desired SMIRKs patterns and initial values for all torsion terms, and the desired final value for all other parameters such as electrostatics.

This was modified to re-set all linear angles to 180°

### `02_curate-data`: Download and filter/curate the optimized geometry and torsion drive datasets to use for the fit. Determine which parameters to optimize based on dataset coverage.

The files in this directory were *not* modified. Some scripts were
added for inspecting the training set.

### `03_generate-initial-ff`: Generate initial values for the bond and angle terms of the force field using the Modified Seminario Method.

Files in this directory were modified to avoid re-setting values
for linear angles.

### `04_fit-forcefield`: Fit the force field bonds, angles, and proper torsions to the data using ForceBalance.

All files in this directory were re-generated for the new fit.
This directory contains the results of several fitting experiments.
The `nor4` directory contains the fit that resulted in 2.2.1-rc1.

### `05_benchmark_forcefield`: Benchmark the force field.

Files in this directory were somewhat modified for updated analysis.

### `06_plot-figures`: plot figures analyzing the new force field.

This is a new directory that plots the benchmark results in the
benchmarking directory.


##  2. <a name='Pythonenvironment'></a>Python environment

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


##  3. <a name='Changes'></a>Changes

The following angles below had their equilibrium values set to 180 degrees.

| Parameter | SMIRKS                    | MSM value (°) |
|-----------|---------------------------|---------------|
| a16       | `[*:1]~[#6X2:2]~[*:3]`    | 178           |
| a17       | `[*:1]~[#7X2:2]~[*:3]`    | 176           |
| a27       | `[*:1]~[#7X2:2]~[#7X1:3]` | 176           |
| a35*      | `[*:1]=[#16X2:2]=[*:3]`   | 180           |

###  3.1. <a name='Globalbenchmarks'></a>Global benchmarks

The global benchmarks (ddEs, RMSDs, and TFDS) look very similar
to 2.2.0:

![ddE histogram](06_plot-figures/images/all/dde.png)
![ddE CFD](06_plot-figures/images/all/abs_dde.png)
![RMSDs](06_plot-figures/images/all/aa_rmsds.png)
![TFDs](06_plot-figures/images/all/tfds.png)

###  3.2. <a name='Sulfamideanglesremainsimilarto2.2.0'></a>Sulfamide angles remain similar to 2.2.0

Sulfamide angles improve relative to 2.1.0, and remain similar to 2.2.0.

![a31](06_plot-figures/images/mm-vs-qm/a31.png)
![a32](06_plot-figures/images/mm-vs-qm/a32.png)
![sulfamide-ligand](05_benchmark_forcefield/smoketests/geometries/36972425/combination.png)

###  3.3. <a name='memberedringangleparametersremainsimilarto2.2.0'></a>3-membered ring angle parameters remain similar to 2.2.0

They broadly improve from 2.1.0, except the a4 parameter.

![a3](06_plot-figures/images/mm-vs-qm/a3.png)
![a4](06_plot-figures/images/mm-vs-qm/a4.png)
![a5](06_plot-figures/images/mm-vs-qm/a5.png)
![a6](06_plot-figures/images/mm-vs-qm/a6.png)

![epoxide-ligand](05_benchmark_forcefield/smoketests/geometries/37008138/combination.png)

The a4 parameter outliers largely concern three unique molecules.

###  3.4. <a name='Linearanglesstaylinear.'></a>Linear angles stay linear.

a35 was not covered in either the testing or training data so
is not presented here.

![a16](06_plot-figures/images/mm-vs-qm/a16.png)
![a17](06_plot-figures/images/mm-vs-qm/a17.png)
![a27](06_plot-figures/images/mm-vs-qm/a27.png)

The apparent worse performance for a27 is due to QM angles less
than 175 degrees. All data points are various conformers of
2 unique molecules.

![a27 scatter](06_plot-figures/images/mm-vs-qm/a27-scatter.png)

##  4. <a name='Parameterchanges'></a>Parameter changes

###  4.1. <a name='Bondimproperandpropertorsionparametersdontchangemuch'></a>Bond, improper, and proper torsion parameters don't change much

Parameter change plots can be seen in the
[parameter-changes](06_plot-figures/images/parameter-changes/)
directory. The scale of the y-axis for bonds,
propers, and improper torsion parameters don't change much.


###  4.2. <a name='Severalangleparameterschangesubstantially'></a>Several angle parameters change substantially

However, several angle parameters do change substantially.

![angles k](06_plot-figures/images/parameter-changes/Angles_k.png)
![angles angle](06_plot-figures/images/parameter-changes/Angles_angle.png)

Below a table of equilibrium angles:

| Parameter | SMIRKS                                        | MSM | 2.2.0 | 2.2.1-rc1 |
|-----------|-----------------------------------------------|-----|-------|-----------|
| a18a      | `[*:1]@-[r!r6;#7X4,#7X3,#7X2-1:2]@-[*:3]`     | 95  | 94    | 95        |
| a20       | `[*:1]~[#7X3$(*~[#6X3,#6X2,#7X2+0]):2]~[*:3]` | 120 | 122   | 120       |
| a29       | `[#6X3,#7:1]~;@[#8;r:2]~;@[#6X3,#7:3]`        | 110 | 121   | 109       |
| a34       | `[*:1]~[#16X2,#16X3+1:2]~[*:3]`               | 98  | 100   | 98        |
| a37       | `[#6X3:1]-[#16X2:2]-[#6X3:3]`                 | 91  | 102   | 91        |

These differences appear largely to have improved the fit to QM angles.

![a29](06_plot-figures/images/mm-vs-qm/a29.png)
![a37](06_plot-figures/images/mm-vs-qm/a37.png)
![a34](06_plot-figures/images/mm-vs-qm/a34.png)
![a20](06_plot-figures/images/mm-vs-qm/a20.png)
