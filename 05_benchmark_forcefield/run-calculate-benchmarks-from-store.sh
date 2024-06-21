#!/bin/bash
#SBATCH -J calculate-benchmarks-from-store 
#SBATCH -p free
#SBATCH -t 16:00:00
#SBATCH --nodes=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=6GB
#SBATCH --account dmobley_lab
#SBATCH --export ALL
#SBATCH --constraint=fastscratch
#SBATCH --output slurm-%x.%A.out 

date
hostname

source ~/.bashrc
conda activate yammbs

FF="openff_unconstrained-1.3.1"
FF="openff_unconstrained-2.0.0"
FF="openff_unconstrained-2.1.0"
FF="openff_unconstrained-2.2.0"
# FF="openff_unconstrained-2.2.1-rc1"

python calculate-benchmarks-from-store.py                                   \
    --store                         "${FF}.sqlite"                          \
    --name                          "${FF}"                                 \
    --forcefield                    "openff_unconstrained-2.2.1-rc1.offxml" \
    --output                        "output/${FF}"                          \
    --n-workers                     300                     \
    --worker-type                   "slurm"                 \
    --batch-size                    5                      \
    --memory                        16                      \
    --walltime                      480                     \
    --queue                         "free"                  \
    --conda-environment             "yammbs"

