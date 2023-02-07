import os
import argparse
import multiprocessing
import csv
import time

def callBatch(n_task,min_id,max_id):
    for i in range(256):  
        print("python 01main.py ./fm_models/simples/Krieter2020o_simple.uvl 4 128 " + str(i) + " " + str(min_id) + " " + str(max_id) + "  &")
        #os.system("python 01main.py ./fm_models/simples/Krieter2020o_simple.uvl 4 128 " + str(i) + " " + str(min_id) + " " + str(max_id) + "  &") 


 
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Convert an FM in (.uvl) with only simple constraints (requires and excludes) to an FMSans (.json).')
    parser.add_argument('division_file', type=str, help='Input division in CSV format.')
    parser.add_argument('n_task', type=int, default=multiprocessing.cpu_count(), help='Number of cores (processes) to execute (power of 2) (default = CPU count).')
    args = parser.parse_args()

    toGenerate = []
    toSave=[]
    with open(args.division_file, newline='') as csvfile:
            spamreader = csv.reader(csvfile, delimiter=';', quotechar='|')
            first = True
            for row in spamreader:
                if first:
                     callBatch(args.n_task,row[0],row[1])
                     toSave = row
                     first = False
                else:
                     toGenerate.append(row)                
            csvfile.close()

    if (len(toSave)>0):
         with open(args.division_file+"_generated", mode='a') as save_file:
            saveF_writer = csv.writer(save_file, delimiter=';', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            saveF_writer.writerow(toSave)
    if (len(toGenerate)>0):
         with open(args.division_file, mode='w') as save_file:
            saveF_writer = csv.writer(save_file, delimiter=';', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            for row in toGenerate:
                 saveF_writer.writerow(row)
    

    


