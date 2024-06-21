#!/bin/bash
#SBATCH -J write-pdb
#SBATCH --array=0-15
#SBATCH -p free
#SBATCH -t 1:00:00
#SBATCH --nodes=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=6GB
#SBATCH --account dmobley_lab
#SBATCH --export ALL
#SBATCH --output slurm-%x.%A-%a.out 

date
hostname

source ~/.bashrc
conda activate yammbs

mkdir -p pdbs

A27_PDBS=(      \
    "36996514"    \
    "36996515"    \
    "36996516"    \
    "36996517"    \
    "36996518"    \
    "36996519"    \
    "36996520"    \
    "36996521"    \
    "36996522"    \
    "36961574"    \
    "36961575"    \
    "36961576"    \
    "36961577"    \
    "36961578"    \
    "36961579"    \
    "36961580"    \
)


QCARCHIVE_ID="${A27_PDBS[$SLURM_ARRAY_TASK_ID]}"

echo $QCARCHIVE_ID


for NAME in "qm" "openff_unconstrained-2.1.0" "openff_unconstrained-2.2.0-rc1" "openff_unconstrained-2.2.1-rc1" ; do
    echo $NAME

    python write-pdb.py             \
        --input         "../05_benchmark_forcefield/output"         \
        --name          "${NAME}"                                   \
        --qcarchive-id  "${QCARCHIVE_ID}"                          \
        --output        "pdbs"

done
