#!/bin/bash
#SBATCH -J calculate-mm-vs-qm
#SBATCH --array=0-18
#SBATCH -p free
#SBATCH -t 1-00:00:00
#SBATCH --nodes=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=64GB
#SBATCH --account dmobley_lab
#SBATCH --export ALL
#SBATCH --output slurm-%x.%A-%a.out 

date
hostname

source ~/.bashrc
conda activate yammbs


PARAMETER_IDS=(
    "a3"    \
    "a4"    \
    "a5"    \
    "a6"    \
    "a7"    \
    "a8"    \
    "a9"    \
    "a41"   \
    "a41a"  \
    "a13"   \
    "a13a"  \
    "a14"   \
    "a16"   \
    "a17"   \
    "a27"   \
    "a31"   \
    "a32"   \
    "a18a"  \
    "a20"   \
    "a29"   \
    "a34"   \
    "a37"   \
)

PARAMETER_ID="${PARAMETER_IDS[${SLURM_ARRAY_TASK_ID}]}"

python calculate-mm-vs-qm.py                                                \
    --input                         output/                                 \
    --output                        "mm-vs-qm/${PARAMETER_ID}"              \
    --forcefield                    "openff_unconstrained-2.2.1-rc1.offxml" \
    --parameter-id                  "${PARAMETER_ID}"                       \
    --n-workers                     300                     \
    --worker-type                   "slurm"                 \
    --batch-size                    200                     \
    --memory                        6                       \
    --walltime                      480                     \
    --queue                         "free"                  \
    --conda-environment             "yammbs"

