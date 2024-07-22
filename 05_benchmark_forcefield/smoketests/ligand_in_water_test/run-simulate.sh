#!/bin/bash

#SBATCH -J simulate
#SBATCH -p standard
#SBATCH -t 1-00:00:00
#SBATCH --nodes=1
#SBATCH --cpus-per-task=1
#SBATCH --account dmobley_lab
#SBATCH --export ALL
#SBATCH --constraint=fastscratch
#SBATCH -o slurm-%J.out-%A


source ~/.bashrc
conda activate yammbs


# python simulate.py              \
#     --forcefield        ../../../openff_unconstrained-2.2.1-rc1.offxml  \
#     --input-geometry    ../geometries/36972425/qcaid_36972425.sdf       \
#     --output-directory  sulfamide


# python simulate.py              \
#     --forcefield        ../../../openff_unconstrained-2.2.1-rc1.offxml  \
#     --input-geometry    ../geometries/36973709/qcaid_36973709.sdf       \
#     --output-directory  sulfonamide


python simulate.py              \
    --forcefield        ../../../openff_unconstrained-2.2.1-rc1.offxml  \
    --input-geometry    32_conf1_initial.sdf       \
    --output-directory  ligand
