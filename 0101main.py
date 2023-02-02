import os
import argparse
import multiprocessing
import csv

def callBatch(fm,n_cores,n_task,min_id,max_id):

    a='''#!/usr/bin/env bash
# Leave only one comment symbol on selected options
# Those with two commets will be ignored:
# The name to show in queue lists for this job:

#SBATCH -J ''' + fm + '''

# Number of desired cpus (can be in any node):
#SBATCH --ntasks=1

# Number of desired cpus (all in same node):
#SBATCH --cpus-per-task='''+str(n_cores) + '''

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
##SBATCH --constraint=srs
# * to request only the machines with 52 cores and 187GB of usable RAM (
#SBATCH --constraint=sd

# Set output and error files
#SBATCH --error='''+fm+"."+str(min_id)+"."+str(max_id)+'''.%A_%a.err
#SBATCH --output='''+fm+"."+str(min_id)+"."+str(max_id)+'''.%A_%a.out

# Leave one comment in following line to make an array job. Then N jobs will be launched. In each one SLURM_ARRAY_TASK_ID will take one value from 1 to 100
#SBATCH --array=0-'''+str(n_task)+'''%32

# the program to execute with its parameters:
module load python/3.9.13
source $HOME/fm_solver/envpypy/bin/activate
time python $HOME/fm_solver/01main.py $HOME/fm_models/simples/'''+fm+".uvl "+str(n_cores) + " " + str(n_task) + " ${SLURM_ARRAY_TASK_ID} " + str(min_id) + " " + str(max_id) + '''
deactivate"'''
    text_file = open("script_" + fm + "_" + str(n_cores) + "_" + str(n_task) + "_" + str(min_id) + "_" + str(max_id)+".sh", "w")
 
#write string to file
    text_file.write(a)
 
#close file
    text_file.close()


 
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Convert an FM in (.uvl) with only simple constraints (requires and excludes) to an FMSans (.json).')
    parser.add_argument('feature_model', type=str, help='Input feature model in UVL format.')
    parser.add_argument('division_file', type=str, help='Input division in CSV format.')
    parser.add_argument('n_cores', type=int, default=multiprocessing.cpu_count(), help='Number of cores (processes) to execute (power of 2) (default = CPU count).')
    parser.add_argument('n_task', type=int, default=multiprocessing.cpu_count(), help='Number of cores (processes) to execute (power of 2) (default = CPU count).')
    args = parser.parse_args()


    with open(args.division_file, newline='') as csvfile:
        spamreader = csv.reader(csvfile, delimiter=';', quotechar='|')
        for row in spamreader:
            callBatch(args.feature_model,args.n_cores,args.n_task,row[0],row[1])
        csvfile.close()
    os.rename(args.division_file,args.division_file+"_generated")

    


