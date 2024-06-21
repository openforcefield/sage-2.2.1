#!/bin/bash
#SBATCH -J plot-mm-vs-qm
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

for param in "a3" "a4" "a5" "a6" "a7" "a8" "a9" "a41" "a41" "a13" "a13a" "a14" "a16" "a17" "a27" "a31" "a32"; do
    echo $param

    python plot-mm-vs-qm.py           \
        --input         "../05_benchmark_forcefield/mm-vs-qm"   \
        --output        "images/mm-vs-qm/${param}.png"          \
        --outlier-ids   "problem_ids/all_r7_outliers.txt"       \
        --outlier-ids   "problem_ids/sx4_outliers.txt"          \
        --parameter-id  $param

    python plot-mm-vs-qm-scatter.py             \
        --input         "../05_benchmark_forcefield/mm-vs-qm/${param}"   \
        --output        "images/mm-vs-qm/${param}-scatter.png"          \
        --outlier-ids   "problem_ids/all_r7_outliers.txt"               \
        --outlier-ids   "problem_ids/sx4_outliers.txt"                  \

done
