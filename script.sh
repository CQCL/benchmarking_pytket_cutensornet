#!/bin/bash
#SBATCH -N 1
#SBATCH -C gpu
#SBATCH -G 4
#SBATCH -q regular
#SBATCH -J bench_chall
#SBATCH -t 03:00:00
#SBATCH -A m4147

#run the application:
srun cat $1 | parallel python run.py {}
