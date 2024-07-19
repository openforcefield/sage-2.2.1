#!/bin/bash
#SBATCH -J sage_220_nor4_msm-half-k
#SBATCH -p standard
#SBATCH -t 1-00:00:00
#SBATCH --nodes=1
#SBATCH --cpus-per-task=1
#SBATCH --account dmobley_lab
#SBATCH --export ALL
#SBATCH --constraint=fastscratch
#SBATCH -o run-%J.out

date
hostname

source ~/.bashrc
conda activate fb_196_ic_0318    

# python create-msm-ff.py                                                                                     \
#     --initial-force-field       "../01_generate-forcefield/output/initial-force-field_nor4.offxml"          \
#     --frozen-angle-file         "../01_generate-forcefield/linear-angles.json"                              \
#     --optimization-dataset      "../02_curate-data/output/optimization-training-set.json"                   \
#     --working-directory         "working-directory"                                                         \
#     --output                    "output/initial-force-field-msm_nor4.offxml"


# python create-msm-ff-a27-half-k.py                                                                                     \
#     --initial-force-field       "../01_generate-forcefield/output/initial-force-field_nor4.offxml"          \
#     --frozen-angle-file         "../01_generate-forcefield/linear-angles.json"                              \
#     --optimization-dataset      "../02_curate-data/output/optimization-training-set.json"                   \
#     --working-directory         "working-directory-half-k"                                                         \
#     --output                    "output/initial-force-field-msm_nor4-half-k-a27.offxml"

python create-msm-ff-a27-quarter-k.py                                                                                     \
    --initial-force-field       "../01_generate-forcefield/output/initial-force-field_nor4.offxml"          \
    --frozen-angle-file         "../01_generate-forcefield/linear-angles.json"                              \
    --optimization-dataset      "../02_curate-data/output/optimization-training-set.json"                   \
    --working-directory         "working-directory-quarter-k"                                                         \
    --output                    "output/initial-force-field-msm_nor4-a27-quarter-k.offxml"

date
