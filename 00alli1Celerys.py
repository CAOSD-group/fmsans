import os
import re
import csv
import re 
from datetime import datetime
import random
from task import picasso
import time

numberDivisions = 512
numberJobs = 8
max_time = 60

#Maximun and minium max_time adaptative.
min_time_to_task=15
max_time_to_task=300

#improve to check for more than only one
#maxConfiguration=77371252455336267181195263
#uClib 
#maxConfiguration=128978157015543273035239205301883937138390460458037480988271657477215308241387905145121400363197555638348240965150666181367760634644210336242807367788803607643649092773194600627131718182721299085210994362356247168981452219910049252646092992863046014767953755101986815
#                  128978157015543273035239205301883937138390460458037480988271657477215308241387905145121400363197555638348240965150666181367760634644210336242807367788803607643649092773194600627131718182721299085210994362356247168981452219910049252646092992863046014767953755101986816
# Ghamizi maxConfiguration=1298074214633706907132624082305023
#axTLS  maxConfiguration= 748288838313422294120286634350736906063837462003711
#uCliux-distribution 
#maxConfiguration=188501787658138776526316391973679239907820382867140805681144220780050698265428977917842924316820804490882044531700026161400423140624345724347059987430217219443542346615871751089083876220596224387399635909565487009065232689887930358404389913798458461035797425091600762263250923357187307004059038598692050448905404415
#model="fm_models/originals/Operating_Systems/KConfig/uClinux-distribution.uvl"

#maxConfiguration = 2305843009213693952

#maxConfiguration=2199023255551
maxConfiguration=77371252455336267181195263

#model="fm_models/simples/MTGCard2020_simple.uvl"
model="./fm_models/simples/GPL_simple.uvl"
fileDivision="R_0_1_divisions.csv"
folder = "GPL"
#model="fm_models/simples/axTLS_simple.uvl"



#leemos el fochero

def write2file(cont, fileName,data):
    file_new_jobs = open(fileName, "w")
    for row in data:
        file_new_jobs.write(str(int(cont))+";"+str(int(row[0]))+";"+str(int(row[1]))+";"+str(int(row[2]))+";\n")
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



def new_divisions(n_divisions):
        uncomplete = 0
        divisions=[]
        now = datetime.now()
        date_time = now.strftime("%Y-%m-%d-%H-%M-%S")


        #First diviions, we need to take out the index
        divisionsGeneral=[]
        file="R_0_1_divisions.csv"
        
        with open(file, newline='') as csvfile:
                spamreader = csv.reader(csvfile, delimiter=';', quotechar='|')
                for row in spamreader:
                        uncomplete+=1
                        #
                        #min,current,max, dif
                        divisionsGeneral.append([int(row[1]),int(row[2]),int(row[3]),int(row[3])-int(row[2])])          
                csvfile.close()

        if os.path.getsize(file) == 0:
                os.remove(file)
        else:
                old_name = file
                new_name = str(date_time)+file
                os.rename(old_name, new_name)
                



        #Seconds the new divisions.

        csv_file_regex="R_1_[0-9]+-[0-9]+.csv"
        pattern = re.compile(csv_file_regex)

        for roots,dirs, files in os.walk("."):
                for file in files:
                        if pattern.match(file):
                                with open(file, newline='') as csvfile:
                                        
                                        spamreader = csv.reader(csvfile, delimiter=';', quotechar='|')
                                        for row in spamreader:
                                                uncomplete+=1
                                                #current, min, dif, max
                                                #min,current,max, dif
                                                divisions.append([int(row[0]),int(row[1]),int(row[2]),int(row[2])-int(row[1])])       
                                        csvfile.close()

                                if os.path.getsize(file) == 0:
                                        os.remove(file)
                                else:
                                        old_name = file
                                        new_name = str(date_time)+file
                                        os.rename(old_name, new_name)
                break

        #progress1 = [sum(i) for i in zip(*divisions)]
        #progress2 = [sum(i) for i in zip(*divisionsGeneral)]
        #print(str((progress1[2]+progress2[2])/maxConfiguration))
        #print(str(maxConfiguration-progress1[2]+progress2[2]))

        maxIter = n_divisions-len(divisionsGeneral)

        #Divisions general-> divsiones que no se han llegado aprobar
        #divisoins, diviiones nuevas que no se han completado.

        divisions.sort(key=lambda x: x[3],reverse=True)
        if (len(divisions)>0):
                while (len(divisions)<maxIter//2):
                        first=divisions.pop(0)
                        currentNun=first[0]
                        firstIntervalLower, firstIntervalUpper, secondIntervalLower, secondIntervalUpper = get_intervals(first[0],first[2])
                        
                        while(currentNun>firstIntervalUpper):
                                firstIntervalLower, firstIntervalUpper, secondIntervalLower, secondIntervalUpper = get_intervals(secondIntervalLower,secondIntervalUpper)

                        divisions.append([firstIntervalLower,currentNun,firstIntervalUpper,firstIntervalUpper-currentNun])
                        divisions.append([secondIntervalLower,secondIntervalLower,secondIntervalUpper,secondIntervalUpper-secondIntervalLower])


                print(" Divisions size: " + str(len(divisions)))

        divisions+=divisionsGeneral
        divisions.sort(key=lambda x: x[3],reverse=True)
        if (len(divisions)>0):
                while (len(divisions)<n_divisions):
                        first=divisions.pop(0)
                        currentNun=first[0]
                        firstIntervalLower, firstIntervalUpper, secondIntervalLower, secondIntervalUpper = get_intervals(first[0],first[2])
                        
                        while(currentNun>firstIntervalUpper):
                                firstIntervalLower, firstIntervalUpper, secondIntervalLower, secondIntervalUpper = get_intervals(secondIntervalLower,secondIntervalUpper)

                        divisions.append([firstIntervalLower,currentNun,firstIntervalUpper,firstIntervalUpper-currentNun])
                        divisions.append([secondIntervalLower,secondIntervalLower,secondIntervalUpper,secondIntervalUpper-secondIntervalLower])
                

                print(" Divisions size: " + str(len(divisions)))
                #Escribimos a ficheros
                now = datetime.now()
                date_time = now.strftime("%Y-%m-%d-%H-%M-%S")
                
                #The last take all
                file_name = "R_0_1_divisions.csv"
                if os.path.isfile("./"+file_name):
                        os.rename(file_name, str(date_time)+file_name)
                write2file(0,"./"+file_name,divisions)

                rename_json(date_time)
        else:
               uncomplete=0

        return uncomplete
    

def init_process(n_divisions,n_max):

        divisions=[]

        #min, current max,dif
        divisions.append([0,0,n_max,n_max])          

        while (len(divisions)<n_divisions):
                first=divisions.pop(0)
                currentNun=first[0]
                firstIntervalLower, firstIntervalUpper, secondIntervalLower, secondIntervalUpper = get_intervals(first[0],first[2])

                while(currentNun>firstIntervalUpper):
                        firstIntervalLower, firstIntervalUpper, secondIntervalLower, secondIntervalUpper = get_intervals(secondIntervalLower,secondIntervalUpper)

                divisions.append([firstIntervalLower,currentNun,firstIntervalUpper,firstIntervalUpper-currentNun])
                divisions.append([secondIntervalLower,secondIntervalLower,secondIntervalUpper,secondIntervalUpper-secondIntervalLower])
                divisions.sort(key=lambda x: x[3],reverse=True)


        random.shuffle(divisions)
        #Escribimos a ficheros
        now = datetime.now()
        date_time = now.strftime("%Y-%m-%d-%H-%M-%S")
    
        file_name = "R_0_1_divisions.csv"
        if os.path.isfile("./"+file_name):
                os.rename(file_name, str(date_time)+file_name)
        write2file(0,"./"+file_name,divisions)
   




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





def wait_slot(arrayResult,st,max_time,):
        salir = False
        pos = -1
        while(not salir):
                for i in range(numberJobs):
                        if (arrayResult[i].state=='SUCCESS'):
                                pos = i
                                salir = True
                                break
                        elif (arrayResult[i].state=='FAILURE'):
                                print("NFAllo tarea")
                                print(arrayResult[i])
                                pos = i
                                salir = True
                                break
                               
                if (max_time-(time.time()-st)) < min_time_to_task:
                                print("NO duration left, break and new divisions, inside waitslot")
                                salir=True
                                pos = -1
                                break
                #time.sleep(2)
        return pos

def wait_forAll(arrayResult):
        while(len(arrayResult)>0):
                for i in range(len(arrayResult)-1,-1,-1):
                        if (arrayResult[i].state=='SUCCESS'):
                                del arrayResult[i]
                                break
                        elif (arrayResult[i].state=='FAILURE'):
                                print("NFAllo tarea for all")
                                print(arrayResult[i])
                                del arrayResult[i]
                                break
                time.sleep(1)
                
               
      

arrayResult = []

print(os.getcwd()) 

#Arrancamos todos
finish = False

fileToSaveProgess = "./progress" + folder + ".txt"
fProgress = open(fileToSaveProgess, "w")




init_process(numberDivisions,maxConfiguration)
while (not finish):
        with open(fileDivision, 'r+') as file:
                lines = file.readlines()
                contJob = 0     
                st = time.time()
                if (len(arrayResult)>0):
                       print("ERROR array result mayor que cero")
                       print(arrayResult)
                #Launch to complete all the job
                for line in lines:
                        line_division = line.split(";")
                        #model,n_min,n_current,n_max,divisions_id,numberDivisions,max_time

                        arrayResult.append(picasso.delay(model,int(line_division[1]),int(line_division[2]),int(line_division[3]),int(line_division[0]),numberDivisions,max_time,folder))
                        contJob+=1
                        if contJob>=numberJobs:
                                break
                
                for l in range(contJob-1,-1,-1):
                        del lines[l]
                contJob=0
                for line in lines:
                        line_division = line.split(";")
                        if (max_time-(time.time()-st)) < min_time_to_task:
                                print("NO duration left, break and new divisions pre wait")
                                break
                        pos = wait_slot(arrayResult,st,max_time)
                        if (pos < 0):
                               break
                        arrayResult[pos] = picasso.delay(model,int(line_division[1]) ,int(line_division[2]),int(line_division[3]),int(line_division[0]),numberDivisions,max_time-(time.time()-st),folder)
                        #print(arrayResult[pos])
                        #print(max_time-(time.time()-st))
                        contJob+=1
                
                for l in range(contJob-1,-1,-1):
                        del lines[l]
                
                #wait for the last one
                wait_forAll(arrayResult)
                #Escribir a fichero los que queden.
                file.seek(0)  # Move the file pointer to the beginning
                file.truncate()
                file.writelines(lines)
                file.close()
                
        #Combinamos todo en el fichero fileDivision
        uncomplete = new_divisions(numberDivisions)
        finish = (uncomplete<=0)  
        percent = 100*uncomplete/numberJobs

        fProgress.write("Iteration " + str(max_time) + " s divisions " + str(numberDivisions) + " uncomplete " + str(percent))
        print("Iteration " + str(max_time) + " s divisions " + str(numberDivisions) + " uncomplete " + str(percent))
        #Self adapt
        if (percent > 200):
                numberDivisions= round(numberDivisions/2)
                if (numberDivisions<numberJobs):
                        numberDivisions = numberJobs
        elif(percent < 70):
                numberDivisions= round(numberDivisions*2)
               

        print("Next Iteration " + str(max_time) + " s divisions " + str(numberDivisions) + " uncomplete " + str(percent))
       
        

fProgress.close()

        

        #OPen and atach all divisions to a list
        
        
        
        

                
                

        