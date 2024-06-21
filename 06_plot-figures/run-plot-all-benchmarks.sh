#!/bin/bash
#SBATCH -J plot-benchmarks
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

python plot-all-benchmarks.py           \
    --input         "../05_benchmark_forcefield/output"     \
    --output        "output/all"                            \
    --images        "images/all"                            \
    --outlier-ids   "problem_ids/all_r7_outliers.txt"       \
    --outlier-ids   "problem_ids/sx4_outliers.txt"          \



for param in "a16" "a17" "a27" "a35" "sx4" "sulfamide" "sulfonamide" "r3" "r4" "r5" "r5S" "r4O" "r4N" "r3C" "r3het" "r4C" ; do
    echo $param

    mkdir -p "output/${param}"
    mkdir -p "images/${param}"

    python plot-all-benchmarks.py           \
        --input         "../05_benchmark_forcefield/output"     \
        --output        "output/${param}"                       \
        --images        "images/${param}"                       \
        --outlier-ids   "problem_ids/all_r7_outliers.txt"       \
        --outlier-ids   "problem_ids/sx4_outliers.txt"          \
        --chemical-group    $param

done