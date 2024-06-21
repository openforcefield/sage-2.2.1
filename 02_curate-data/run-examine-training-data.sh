#!/bin/bash
#SBATCH -J examine-training-data
#SBATCH -p free
#SBATCH -t 1-00:00:00
#SBATCH --nodes=1
#SBATCH --cpus-per-task=1
#SBATCH --account dmobley_lab
#SBATCH --export ALL
#SBATCH --constraint=fastscratch
#SBATCH --output slurm-%x.%A.out

date

source ~/.bashrc
conda activate yammbs    

python examine-training-data.py                         \
        --n-workers                     200                     \
        --worker-type                   "slurm"                 \
        --batch-size                    100                     \
        --memory                        8                       \
        --walltime                      480                     \
        --queue                         "free"                  \
        --conda-environment             "yammbs"                \
    --data-set      "output/optimization-training-set.json"                             \
    --data-set      "output/torsion-training-set.json"                                  \
    --forcefield    ../01_generate-forcefield/output/initial-force-field_nor4.offxml    \
    --output        "analysis/dataset-labels"

date