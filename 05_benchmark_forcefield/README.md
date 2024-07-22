# Benchmarking the performance of the Sage 2.2.1 fit

## Environment
The python environment that can be used to run the benchmarking suite is included as `yammbs-env-input.yaml`. The full environment is included as `yammbs-env-full.yaml` 

## Downloading and caching the benchmark dataset
We benchmark using the dataset `OpenFF Industry Benchmark Season 1 v1.1`. For details on downloading this, please see [the Sage 2.2.0 repo.](https://github.com/openforcefield/sage-2.2.0/tree/main/05_benchmark_forcefield)
 

## Benchmarking the force fields
To generate the benchmarking data, use `run-benchmark.sh` which shows an example use of `benchmark.py`.  Please see [the Sage 2.2.0 repo.](https://github.com/openforcefield/sage-2.2.0/tree/main/05_benchmark_forcefield) for more details. The SQLite databases will be attached in a release as they are too large to add to the GitHub repo. Global benchmarks are saved in directories named after the force field. For example, `openff_unconstrained-2.0.0` contains the global benchmarks (dde, rmsd, tfd, icrmsd) for the Sage 2.0.0 force field.

The script `calculate-benchmarks-from-store.py` calculates benchmarks from optimized geometries in an existing SQLite store and stores them in the `output` directory as parquet tables. The script `run-calculate-benchmarks-from-store.sh` shows an example use.

## Analyzing the benchmarks

`calculate-mm-vs-qm.py` compares the MM and QM values of optimized geometries. Outputs are saved in `mm-vs-qm`. An example use is shown in `run-calculate-mm-vs-qm.sh`. 

The directory `process_bm` contains scripts to process and analyze the benchmarking data. 
The included script `plot_benchmarks.py` can be used to plot the results of the benchmarking run. Example usage is in `plot_benchmarks.sh`, which shows how to plot the ICRMSD, DDE, RMSD, TFD, as well as filtered versions of all of these for different subsets of the data, and how to exclude known problematic molecules ("outliers") from the plots.

## Canary/smoke tests

We have run a number of "smoke tests" to ensure the performance of Sage 2.2.1 on a few known problem cases. These are in the `smoketests` directory.

`geometries` contains Jupyter notebooks showing the minimization of three problem chemistries that were addressed in Sage 2.2.1: sulfonamides, sulfamides, and 3-membered rings with heteroatoms.

`hmr` contains the result of an HMR simulation, ensuring it does not return NaN energies.

`ligand_in_water_test` contains three outputs: `ligand`, `sulfamide`, and `sulfonamide`. The associated trajectories show that even in the presence of explicit solvent, these geometries which were problematic in Sage 2.0 and Sage 2.1 retain the correct structure with Sage 2.2.1.
