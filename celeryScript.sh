#!/usr/bin/env bash
# Leave only one comment symbol on selected options
# Those with two commets will be ignored:
# The name to show in queue lists for this job:
#SBATCH -J fm_GPL

# Number of desired cpus (can be in any node):
#SBATCH --ntasks=1

# Number of desired cpus (all in same node):
#SBATCH --cpus-per-task=8

# Amount of RAM needed for this job:
#SBATCH --mem=2gb

# The time the job will be running:
#SBATCH --time=00:30:00

# To use GPUs you have to request them:
##SBATCH --gres=gpu:1

# If you need nodes with special features leave only one # in the desired SBATCH constraint line. cal is selected by default:
# * to request any machine without GPU - DEFAULT
#SBATCH --constraint=cal
# * to request only the machines with 128 cores and 1800GB of usable RAM
##SBATCH --constraint=bigmem
# * to request only the machines with 128 cores and 450GB of usable RAM (
##SBATCH --constraint=sr
# * to request only the machines with 52 cores and 187GB of usable RAM (
##SBATCH --constraint=sd

# Set output and error files
#SBATCH --error=GPL.%A_%a.err
#SBATCH --output=GOK.%A_%a.out

# Leave one comment in following line to make an array job. Then N jobs will be launched. In each one SLURM_ARRAY_TASK_ID will take one value from 1 to 100
#SBATCH --array=0-16

# the program to execute with its parameters:
source $HOME/venv/bin/activate
srun celery -A task worker -n celery@node${SLURM_ARRAY_TASK_ID} --concurrency=8
deactivate