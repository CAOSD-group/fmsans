import os
import argparse
import re
import numpy as np
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Process minimumtime')
    parser.add_argument('fixed_name', type=str, help='Name of the json files.')
    parser.add_argument('n_tasks', type=int, help='Number of task.')
    args = parser.parse_args()

    pattern = re.compile(args.fixed_name + "[0-9]+-"+str(args.n_tasks) + ".err")
    json_file_count = 0 
    arrayTime = []
    for roots,dirs, files in os.walk("."):
        for file in files:
            if pattern.match(file):
                file_new_job = open(file,"r")
                file_new_job
                lines = file_new_job.readlines()
                line=lines[0]
                div=re.split(r' +', line)
                
                arrayTime.append(float(div[3].replace(',','.'))+float(div[5].replace(',','.')))
                            
    print("Max value real")
    print(np.max(arrayTime))
    print("Average value real")
    print(np.average(arrayTime))
    print("Min value real")
    print(np.min(arrayTime))
    
