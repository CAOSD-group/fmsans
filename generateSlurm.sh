#!/usr/bin/env bash
# Leave only one comment symbol on selected options
# Those with two commets will be ignored:
# The name to show in queue lists for this job:


#SBATCH -J ${fm_model}

# Number of desired cpus (can be in any node):
#SBATCH --ntasks=1

# Number of desired cpus (all in same node):
#SBATCH --cpus-per-task=${n_cores}

# Amount of RAM needed for this job:
#SBATCH --mem=2gb

# The time the job will be running:
#SBATCH --time=20:00:00

# To use GPUs you have to request them:
##SBATCH --gres=gpu:1

# If you need nodes with special features leave only one # in the desired SBATCH constraint line. cal is selected by default:
# * to request any machine without GPU - DEFAULT
##SBATCH --constraint=cal
# * to request only the machines with 128 cores and 1800GB of usable RAM
##SBATCH --constraint=bigmem
# * to request only the machines with 128 cores and 450GB of usable RAM (
##SBATCH --constraint=sr
# * to request only the machines with 52 cores and 187GB of usable RAM (
#SBATCH --constraint=sd

# Set output and error files
#SBATCH --error=${fm_model}.${n_min}.${n_max}.%A_%a.err
#SBATCH --output=${fm_model}.${n_min}.${n_max}.%A_%a.out

# Leave one comment in following line to make an array job. Then N jobs will be launched. In each one SLURM_ARRAY_TASK_ID will take one value from 1 to 100
#SBATCH --array=0-${n_task}%32

# the program to execute with its parameters:
source $HOME/fm_solver/envpypy/bin/activate
time python $HOME/fm_solver/01main.py $HOME/fm_models/simples/${fm_model}.uvl ${n_cores} ${n_task} ${SLURM_ARRAY_TASK_ID} ${n_min} ${n_max}
deactivate