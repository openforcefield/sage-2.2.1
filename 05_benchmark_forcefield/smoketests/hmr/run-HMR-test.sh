#!/bin/bash

#SBATCH -J hmr
#SBATCH -p standard
#SBATCH -t 16:00:00
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

python HMR-test.py -ff ../../../openff-2.2.1-rc1.offxml > hmr_test.log

