import argparse
import random


from task import picasso
import time



#Maximun and minium max_time adaptative.
min_time_to_task=15

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


#model="fm_models/simples/MTGCard2020_simple.uvl"
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



def new_divisions(n_divisions,divisions):
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
       

        return divisions
    

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
        return divisions




def wait_slot(arrayResult,st,max_time,dicJson: dict[str, int],arrayCSV):
        salir = False
        pos = -1
        while(not salir):
                for i in range(numberJobs):
                        if (arrayResult[i].state=='SUCCESS'):
                                pos = i
                                salir = True
                                dict, min, current, max = arrayResult[i].get()
                                dicJson.update(dict)
                                if (current < max):
                                        arrayCSV.append([min, current, max, max-current])
                                
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

def wait_forAll(arrayResult,dicJson: dict[str, int],arrayCSV):
        while(len(arrayResult)>0):
                for i in range(len(arrayResult)-1,-1,-1):
                        if (arrayResult[i].state=='SUCCESS'):
                                dict, min, current, max = arrayResult[i].get()
                                dicJson.update(dict)
                                if (current < max):
                                        arrayCSV.append([min, current, max, max-current])
                                del arrayResult[i]
                                break
                        elif (arrayResult[i].state=='FAILURE'):
                                print("NFAllo tarea for all")
                                print(arrayResult[i])
                                del arrayResult[i]
                                break
                time.sleep(1)
                
               
if __name__ == '__main__':
        parser = argparse.ArgumentParser(description='Convert an FM in (.uvl) with only simple constraints (requires and excludes) to an FMSans (.json).')
        parser.add_argument('numberDivisions', type=int, help='Initial Number of Divisions to split the input space.')
        parser.add_argument('numberJobs', type=int, default=1, help='Number of cores (processes) to execute (power of 2) (default = CPU count).')
        parser.add_argument('max_time_iteration', type=int,  default=-1, help='Maximum time per iteration.')
        parser.add_argument('max_time_total', type=int,  default=-1, help='Maximum time in total.')
        parser.add_argument('maxConfiguration', type=int, default=-1, help='Number of maximum configuration.')
        parser.add_argument('model_name', type=str,  default=-1, help='Name of the model to test.')
        parser.add_argument('json_file', type=str, default=-1, help='jSon file to keep de transformation')
        args = parser.parse_args()

        numberDivisions = args.numberDivisions
        numberJobs = args.numberJobs
        max_time = args.max_time_iteration
        maxConfiguration= args.maxConfiguration
        model_name= args.model_name
        json_file= args.json_file

        # numberJobs = 8
        # max_time = 30
        # maxConfiguration=77371252455336267181195263
        # model_name="./fm_models/simples/GPL_simple.uvl"
        # json_file="./GPL_simple.json"

        arrayResult = []


        #Arrancamos todos
        finish = False

        fileToSaveProgess = "./progress.txt"
        fProgress = open(fileToSaveProgess, "w")





        divisions = init_process(numberDivisions,maxConfiguration)
        initTime = time.time()
        while ((not finish) and (time.time()-initTime<args.max_time_total)):
                contJob = 0     
                st = time.time()
                #Launch to complete all the job
                print("Start to launch")
                for line_division in divisions:
                        
                        #model,n_min,n_current,n_max,divisions_id,numberDivisions,max_time

                        arrayResult.append(picasso.delay(model_name,line_division[0],line_division[1],line_division[2],contJob,numberDivisions,max_time))
                        contJob+=1
                        if contJob>=numberJobs:
                                break
                
                for l in range(contJob-1,-1,-1):
                        del divisions[l]
                contJob=0

                dictJSON = {}
                arrayCSV = []
                for line_division in divisions:
                
                        if (max_time-(time.time()-st)) < min_time_to_task:
                                print("NO duration left, break and new divisions pre wait")
                                break
                        pos = wait_slot(arrayResult,st,max_time,dictJSON,arrayCSV)
                        if (pos < 0):
                                break
                        arrayResult[pos] = picasso.delay(model_name,line_division[0] ,line_division[1],line_division[2],contJob,numberDivisions,max_time-(time.time()-st))
                        #print(arrayResult[pos])
                        #print(max_time-(time.time()-st))
                        contJob+=1
                
                for l in range(contJob-1,-1,-1):
                        del divisions[l]
                
                #wait for the last one
                print("Wait for all")
                wait_forAll(arrayResult,dictJSON,arrayCSV)
                print("Merge and relaunch")
                for line_division in divisions:
                        arrayCSV.append([line_division[0] ,line_division[1],line_division[2],line_division[2]-line_division[1]])
                        
                #Combinamos todo en el fichero 
                percent = 100*len(arrayCSV)/numberJobs
                divisions = new_divisions(numberDivisions,arrayCSV)
                finish = (len(divisions)==0)  
                

                fProgress.write("Iteration " + str(max_time) + " s divisions " + str(numberDivisions) + " uncomplete " + str(percent))
                print("Iteration " + str(max_time) + " s divisions " + str(numberDivisions) + " uncomplete " + str(percent))
                #Self adapt
                if (percent < 100):
                        numberDivisions= round(numberDivisions*2)
                

                print("Next Iteration " + str(max_time) + " s divisions " + str(numberDivisions) + " uncomplete " + str(percent*numberJobs/100))
                jsonNewtransforms = open(json_file, "a")
                if (not finish and (time.time()-initTime<args.max_time_total)):
                        for key, value in dictJSON.items():
                                jsonNewtransforms.write(f'"{key}": {value},\n')
                else:
                        cont = 0
                        for i, (key, value) in enumerate(dictJSON.items()):
                                if i == len(dictJSON) - 1:
                                        jsonNewtransforms.write(f'"{key}": {value}\n')
                                else:
                                        jsonNewtransforms.write(f'"{key}": {value},\n')
                        
                jsonNewtransforms.close()
        jsonNewtransforms = open(json_file, "a")
        jsonNewtransforms.write("\t\t}\n}")
        jsonNewtransforms.close()


                

        fProgress.close()

                

                #OPen and atach all divisions to a list
                
                
                
                

                        
                        

                