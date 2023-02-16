import os
import argparse
import multiprocessing
import csv
import re 
from datetime import datetime
import decimal

def rename_json(date_time,n_processes,n_tasks):
    json_file_regex="R_" + str(n_processes) + "_[0-9]+-" + str(n_tasks) +".json" 
    pattern = re.compile(json_file_regex)
    for roots,dirs, files in os.walk("."):
        for file in files:
            if pattern.match(file):
                old_name = file
                new_name = str(date_time)+file
                os.rename(old_name, new_name)     
        break

def rename_ouput(date_time,n_processes,n_tasks):
    json_file_regex="OutputR_" + str(n_processes) + "_[0-9]+-" + str(n_tasks) +".err" 
    pattern = re.compile(json_file_regex)
    for roots,dirs, files in os.walk("."):
        for file in files:
            if pattern.match(file):
                old_name = file
                new_name = str(date_time)+file
                os.rename(old_name, new_name)     
        break

def write2file(ini, end, fileName,data):
    file_new_jobs = open(fileName, "w")
    cont = 0
    for row in data:
        file_new_jobs.write(str(int(cont))+";"+str(int(row[0]))+";"+str(int(row[1]))+";"+"\n")
        cont+=1
    file_new_jobs.close()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Convert an FM in (.uvl) with only simple constraints (requires and excludes) to an FMSans (.json).')
    parser.add_argument('n_cores', type=int, default=multiprocessing.cpu_count(), help='Number of cores (processes) to execute (power of 2) (default = CPU count).')
    parser.add_argument('n_tasks', type=int,  default=-1, help='Number of tasks.')
    parser.add_argument('n_max', type=int,  default=-1, help='Maximum configurations')
    args = parser.parse_args()

    #OPen and atach all divisions to a list
   
    csv_file_regex="R_" + str(args.n_cores) + "_[0-9]+-" + str(args.n_tasks) +".csv"
    
    divisions=[]
    pattern = re.compile(csv_file_regex)
    now = datetime.now()
    date_time = now.strftime("%Y-%m-%d-%H-%M-%S")
    rename_json(date_time,args.n_cores,args.n_tasks)
    rename_ouput(date_time,args.n_cores,args.n_tasks)
    for roots,dirs, files in os.walk("."):
        for file in files:
            if pattern.match(file):
                with open(file, newline='') as csvfile:
                    spamreader = csv.reader(csvfile, delimiter=';', quotechar='|')
                    for row in spamreader:
                        divisions.append([int(row[0]),int(row[1]),int(row[1])-int(row[0])])          
                    csvfile.close()
                #rename file
                old_name = file
                new_name = str(date_time)+file
                os.rename(old_name, new_name)

        break

    divisions.sort(key=lambda x: x[2],reverse=True)
    divisionCopy=divisions.copy()
    cont = 0
    sumConfigToDo=0
    while (cont<len(divisions)):
        sumConfigToDo+=divisions[cont][2]
        cont+=1
    progression = decimal.Decimal(sumConfigToDo/args.n_max)
    print("To complete " + str(progression))


    while (len(divisionCopy)<args.n_tasks):
        first=divisionCopy.pop(0)
        middle = round((first[1]-first[0])//2+first[0])
        divisionCopy.append([first[0], middle, middle-first[0]])
        divisionCopy.append([middle+1, first[1], first[1]-(middle+1)])
        divisionCopy.sort(key=lambda x: x[2],reverse=True)

   
    if (len(divisionCopy)>args.n_tasks):
        #Dividir en dos tareas
        a=1
        cont = 0
        numberFiles = 1
        while (cont < len(divisionCopy)):
            file_name = "R_" + str(args.n_cores) + "_" + str(args.n_tasks) +"_joined_"+ str(numberFiles) +".csv"
            if os.path.isfile("./"+file_name):
                os.rename("./"+file_name, str(date_time)+file_name)
            write2file(cont,args.n_tasks*numberFiles-1,file_name,divisionCopy);
            cont += args.n_tasks
            numberFiles +=1
    elif (len(divisionCopy)==args.n_tasks):
        #Escribir a fichero
        file_name = "R_" + str(args.n_cores) + "_" + str(args.n_tasks) +"_joined_0.csv"
        if os.path.isfile("./"+file_name):
            os.rename(file_name, str(date_time)+file_name)
        write2file(0,args.n_tasks-1,"./"+file_name,divisionCopy);
    else:
        print("Error al dividir, salen " + str(len(divisionCopy) + "divisiones"))
