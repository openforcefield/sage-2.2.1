#!/bin/bash
#SBATCH -J fit-2.2.1 
#SBATCH -p standard
#SBATCH -t 144:00:00
#SBATCH --nodes=1
#SBATCH --cpus-per-task=1
#SBATCH --ntasks=1
#SBATCH --mem=10000mb
#SBATCH --account dmobley_lab
#SBATCH --export ALL
#SBATCH --mail-user=lilyw7@uci.edu
#SBATCH --constraint=fastscratch
#SBATCH -o master-%A.out
#SBATCH -e master-%A.err

conda_env=fb_196_ic_0318

compressed_env=/dfs9/dmobley-lab/$USER/envs/packed/$conda_env.tar.gz

TMPDIR=/tmp/$USER/$SLURM_JOB_ID


rm -rf $TMPDIR
mkdir -p $TMPDIR
cd $TMPDIR

source $HOME/.bashrc

cp $compressed_env .
mkdir -p $conda_env
tar xzf $compressed_env -C $conda_env
conda activate $conda_env

echo $CONDA_PREFIX > $SLURM_SUBMIT_DIR/env.path

scp -C  $SLURM_SUBMIT_DIR/optimize.in     $TMPDIR
scp -C  $SLURM_SUBMIT_DIR/targets.tar.gz  $TMPDIR
scp -Cr $SLURM_SUBMIT_DIR/forcefield      $TMPDIR

tar -xzf targets.tar.gz

datadir=$(pwd)
echo $(hostname) > $SLURM_SUBMIT_DIR/host

export OMP_NUM_THREADS=1
export MKL_NUM_THREADS=1

# in case of ownership issues messing with disk quota
newgrp dmobley_lab_share
mkdir -p result/optimize
touch result/optimize/force-field.offxml

if ForceBalance.py optimize.in ; then
   newgrp dmobley_lab_share
   echo "-- Force field done --"
   # cat result/optimize/force-field.offxml > "${SLURM_SUBMIT_DIR}/result/optimize/force-field.offxml"
   echo "-- -- -- -- -- -- -- --"
   tar -czf optimize.tmp.tar.gz optimize.tmp
   rsync  -azIi -rv --exclude="optimize.tmp" --exclude="optimize.bak" \
	  --exclude="fb*" \
	  --chown=lilyw7:dmobley_lab_share  \
	  --exclude="targets*" $TMPDIR/* $SLURM_SUBMIT_DIR > copy.log
   rm -rf $TMPDIR
fi

echo "All done"
