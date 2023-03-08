import os
import argparse
import multiprocessing
import csv
import re 
import re 
from datetime import datetime
import decimal
import decimal
import math
import random


def write2file(cont, fileName,data):
    file_new_jobs = open(fileName, "w")
    for row in data:
        file_new_jobs.write(str(int(cont))+";"+str(int(row[0]))+";"+str(int(row[1]))+";"+str(int(row[3]))+";\n")
        cont+=1
    file_new_jobs.close()

def rename_json(date_time):
    json_file_regex="R_1_[0-9]+-[0-9]+.json" 
    pattern = re.compile(json_file_regex)
    for roots,dirs, files in os.walk("."):
        for file in files:
            if pattern.match(file):
                old_name = file
                new_name = str(date_time)+file
                os.rename(old_name, new_name)     
        break

def get_intervals(n_min,n_max) -> tuple[int, int, int,int]:
    
    and_min_max = bin(n_min^n_max)
    and_min_max=and_min_max[2:]
    s_min=bin(n_min)[2:]
    s_max=bin(n_max)[2:]
    n_bits_total = n_max.bit_length()
    index = and_min_max.find('1') + n_bits_total - (n_min^n_max).bit_length()
    and_min_max=s_min[0:index]
    


    firstIntervalLower = n_min
    firstIntervalUpper = "0b" + and_min_max + "01" + bin(2**(n_bits_total-index-2)-1)[2:]
    secondIntervalLower = "0b" + and_min_max + "10" + format(0, f'0{n_bits_total-index-2}b')
    firstIntervalUpper = int(firstIntervalUpper,2)
    secondIntervalLower = int(secondIntervalLower,2)
    secondIntervalUpper = n_max


    return (firstIntervalLower, firstIntervalUpper, secondIntervalLower,secondIntervalUpper)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Convert an FM in (.uvl) with only simple constraints (requires and excludes) to an FMSans (.json).')
    parser.add_argument('n_divisions', type=int,  default=-1, help='Number of divisions.')
    parser.add_argument('n_files', type=int,  default=-1, help='Number of files to divide.')
    parser.add_argument('n_max', type=int,  default=-1, help='Maximum number of configuraiton.')
    args = parser.parse_args()

  

    #OPen and atach all divisions to a list
   
    
    
    
    divisions=[]
    now = datetime.now()
    date_time = now.strftime("%Y-%m-%d-%H-%M-%S")


    #First diviions, we need to take out the index
    divisionsGeneral=[]
    csv_file_regex="R_[0-9]+_[0-9]+_divisions.csv"
    pattern = re.compile(csv_file_regex)
   
    for roots,dirs, files in os.walk("."):
        for file in files:
            if pattern.match(file):
                with open(file, newline='') as csvfile:
                    spamreader = csv.reader(csvfile, delimiter=';', quotechar='|')
                    for row in spamreader:
                        #id, current, min, max
                        #current min,max
                        divisionsGeneral.append([int(row[1]),int(row[2]),int(row[3])-int(row[2]),int(row[3])])          
                    csvfile.close()

                if os.path.getsize(file) == 0:
                    os.remove(file)
                else:
                    old_name = file
                    new_name = str(date_time)+file
                    os.rename(old_name, new_name)

        break



    #Seconds the new divisions.

    csv_file_regex="R_1_[0-9]+-[0-9]+.csv"
    pattern = re.compile(csv_file_regex)

    for roots,dirs, files in os.walk("."):
        for file in files:
            if pattern.match(file):
                with open(file, newline='') as csvfile:
                    spamreader = csv.reader(csvfile, delimiter=';', quotechar='|')
                    for row in spamreader:
                        #current, min, dif, max
                        #current min,max
                        divisions.append([int(row[0]),int(row[1]),int(row[2])-int(row[0]),int(row[2])])          
                    csvfile.close()

                if os.path.getsize(file) == 0:
                    os.remove(file)
                else:
                    old_name = file
                    new_name = str(date_time)+file
                    os.rename(old_name, new_name)

        break

    progress1 = [sum(i) for i in zip(*divisions)]
    progress2 = [sum(i) for i in zip(*divisionsGeneral)]
    print(str((progress1[2]+progress2[2])/args.n_max))
    print(str(args.n_max-progress1[2]+progress2[2]))

    maxIter = args.n_divisions-len(divisionsGeneral)
    
    while (len(divisions)<maxIter//2):
        first=divisions.pop(0)
        currentNun=first[0]
        firstIntervalLower, firstIntervalUpper, secondIntervalLower, secondIntervalUpper = get_intervals(first[1],first[3])
        
        while(currentNun>firstIntervalUpper):
            firstIntervalLower, firstIntervalUpper, secondIntervalLower, secondIntervalUpper = get_intervals(secondIntervalLower,secondIntervalUpper)

        divisions.append([currentNun,firstIntervalLower,firstIntervalUpper-currentNun,firstIntervalUpper])
        divisions.append([secondIntervalLower,secondIntervalLower,secondIntervalUpper-secondIntervalLower,secondIntervalUpper])
        divisions.sort(key=lambda x: x[2],reverse=True)

    divisions+=divisionsGeneral
    while (len(divisions)<args.n_divisions):
        first=divisions.pop(0)
        currentNun=first[0]
        firstIntervalLower, firstIntervalUpper, secondIntervalLower, secondIntervalUpper = get_intervals(first[1],first[3])
        
        while(currentNun>firstIntervalUpper):
            firstIntervalLower, firstIntervalUpper, secondIntervalLower, secondIntervalUpper = get_intervals(secondIntervalLower,secondIntervalUpper)

        divisions.append([currentNun,firstIntervalLower,firstIntervalUpper-currentNun,firstIntervalUpper])
        divisions.append([secondIntervalLower,secondIntervalLower,secondIntervalUpper-secondIntervalLower,secondIntervalUpper])
        divisions.sort(key=lambda x: x[2],reverse=True)
   
    random.shuffle(divisions)

    print(" Divisions size: " + str(len(divisions)))
    #Escribimos a ficheros
    now = datetime.now()
    date_time = now.strftime("%Y-%m-%d-%H-%M-%S")
    cont = 0
    division_size = len(divisions)//args.n_files
    while (cont < args.n_files-1 ):
        file_name = "R_" + str(cont) + "_" + str(args.n_files) +"_divisions.csv"
        if os.path.isfile("./"+file_name):
            os.rename(file_name, str(date_time)+file_name)
        write2file(cont*division_size,"./"+file_name,divisions[cont*division_size:(cont+1)*division_size])
        cont+=1
    #The last take all
    file_name = "R_" + str(cont) + "_" + str(args.n_files) +"_divisions.csv"
    if os.path.isfile("./"+file_name):
        os.rename(file_name, str(date_time)+file_name)
    write2file(cont*division_size,"./"+file_name,divisions[cont*division_size:len(divisions)])

    rename_json(date_time)
    
   
