#!/bin/bash
#SBATCH -J plot-parameter-changes
#SBATCH -p free
#SBATCH -t 1:00:00
#SBATCH --nodes=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=6GB
#SBATCH --account dmobley_lab
#SBATCH --export ALL
#SBATCH --output slurm-%x.%A.out 

date
hostname

source ~/.bashrc
conda activate yammbs

mkdir -p images/mm-vs-qm

python plot-parameter-changes.py            \
    --original      ../openff_unconstrained-2.2.0.offxml        \
    --new           ../openff_unconstrained-2.2.1-rc1.offxml    \
    --images        images/parameter-changes
