import os
import argparse
import multiprocessing
import csv

def callBatch(fm,n_cores,n_task,min_id,max_id):
    
    s="sbatch generateSlurm.sh --export=fm_model="+fm+",n_cores="+str(n_cores)+",n_task="+str(n_task)+",n_min="+str(min_id)+",n_max=" + str(max_id)
    print(s+"\n")
    os.system(s)


 
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
            print(', '.join(row))


