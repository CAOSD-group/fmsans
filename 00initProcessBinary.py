import os
import argparse
import math
import sys
import random
from datetime import datetime

sys.set_int_max_str_digits(10000)


def write2file(cont, fileName,data):
    file_new_jobs = open(fileName, "w")
    for row in data:
        file_new_jobs.write(str(int(cont))+";"+str(int(row[0]))+";"+str(int(row[1]))+";"+str(int(row[3]))+";\n")
        cont+=1
    file_new_jobs.close()

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
    parser.add_argument('n_files', type=int,  default=-1, help='Number of files to create.')
    parser.add_argument('n_max', type=int,  default=-1, help='Maximum configurations')
    args = parser.parse_args()

    if (args.n_divisions%args.n_files >0):
        print("Dede ser divisible el numero de tareqs y el numero de ficheros")
        exit(-1)

    #OPen and atach all divisions to a list
   
    
    divisions=[]
   
    num_bits_pre = int(math.log2(args.n_divisions))
    num_bits_post = int(math.log2(args.n_max)-num_bits_pre)



             
    i = 1
    lowerBound = 0
    while (i<args.n_divisions):
        binary_string = bin(i)[2:].zfill(num_bits_pre)
        binary_string = "0b"+binary_string.ljust(num_bits_pre+num_bits_post, '0')
        upperBound = int(binary_string,2)
        #,current, min, dif, max
        divisions.append([lowerBound,lowerBound,upperBound-lowerBound,upperBound]) 
        lowerBound=upperBound+1  
        i+=1

    print("Now, shuffle")
    random.shuffle(divisions)
    #Escribimos a ficheros
    now = datetime.now()
    date_time = now.strftime("%Y-%m-%d-%H-%M-%S")
    cont = 0
    division_size = args.n_divisions//args.n_files
    while (cont < args.n_files ):
        file_name = "R_" + str(cont) + "_" + str(args.n_files) +"_divisions.csv"
        if os.path.isfile("./"+file_name):
            os.rename(file_name, str(date_time)+file_name)
        if (cont == args.n_files-1):
            write2file(cont*division_size,"./"+file_name,divisions[cont*division_size:])
        else:
            write2file(cont*division_size,"./"+file_name,divisions[cont*division_size:(cont+1)*division_size])
        cont+=1
   
