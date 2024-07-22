# Plotting figures

In this directory we plot the results of benchmarks comparing optimized MM geometries to QM.

Problematic QM data points are identified in `problem_ids/`. Please see the [Sage 2.2.0 repo](https://github.com/openforcefield/sage-2.2.0/tree/main/05_benchmark_forcefield) for more details on how these IDs were obtained.

To plot global benchmarks, we use `plot-all-benchmarks.py` -- an example use is shown in `run-plot-all-benchmarks.sh`. Images are saved in the `images/` directory.

The plot MM vs QM figures, we use `plot-mm-vs-qm.py` (for aggregated box plots) or `plot-mm-vs-qm-scatter.py`  (for scatter plots comparing MM and QM). Example uses are shown in `run-plot-mm-vs-qm.sh`.

To plot parameter changes between 2.2.0 and 2.2.1, we use `plot-parameter-changes.py` as shown in `run-plot-parameter-changes.sh`.

Finally, to investigate structures of molecules, we write molecules out to PDB using `write-pdb.py` and `run-write-pdb.sh`. These are written out to the `pdbs/` directory.
