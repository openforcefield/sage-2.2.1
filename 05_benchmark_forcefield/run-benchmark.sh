#!/bin/bash
#SBATCH -J benchmark-2.2.1-quarter-k
#SBATCH -p standard
#SBATCH -t 2-00:00:00
#SBATCH --nodes=1
#SBATCH --cpus-per-task=16
#SBATCH --mem=32gb
#SBATCH --account dmobley_lab
#SBATCH --export ALL
#SBATCH --constraint=fastscratch
#SBATCH -o %J.out

date
hostname

source ~/.bashrc
conda activate yammbs

savedir="openff_unconstrained-2.2.1-a27-quarter-k"
mkdir $savedir

python -c "from openff.toolkit.utils import *; assert OpenEyeToolkitWrapper().is_available"

python -u  benchmark.py -f "${savedir}.offxml" -d "datasets/OpenFF-Industry-Benchmark-Season-1-v1.1-filtered-charge-coverage-cache.json" -s "${savedir}.sqlite" -o $savedir --procs 16

date
