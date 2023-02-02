import os
import argparse
import re
import numpy as np
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Convert an FM in (.uvl) with only simple constraints (requires and excludes) to an FMSans (.json).')
    parser.add_argument('model_name', type=str, help='Name of the json files.')
    parser.add_argument('job_id', type=int, default=0, help='ID of the job in the supercomputer')
    args = parser.parse_args()

    pattern = re.compile(args.model_name + "." + str(args.job_id) + "_[0-9]+.err")
    json_file_count = 0 
    arrayTime = []
    for roots,dirs, files in os.walk("."):
        for file in files:
            if pattern.match(file):
                file_new_job = open(file,"r")
                file_new_job
                Lines = file_new_job.readlines()
                count = 0
                # Strips the newline character
                for line in Lines:
                    if (len(line)>0 and line[0]=='r'):
                        time = 0
                        line = line.split('\t')[1]
                        line = line.split('h')
                        if (len(line)>1):
                            time += int(line[0])*3600
                            line = line[1]
                        else:
                            line = line[0]
                        line = line.split('m')
                        if (len(line)>1):
                            time += int(line[0])*60
                            line = line[1]
                        else:
                            line = line[0]
                        line = line.split('s')
                        time += float(line[0].replace(",","."))
                        arrayTime.append(time)
                            
    print("Max value real")
    print(np.max(arrayTime))
    print("Average value real")
    print(np.average(arrayTime))
    print("Min value real")
    print(np.min(arrayTime))
    
