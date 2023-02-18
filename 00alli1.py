import os
import time
import subprocess
import re

numberTasks = 128
min_time = 180
max_time = 300
num_cpus=1
sleep = 30
sleepCounter=8
#improve to check for more than only one
ficheroCSV= " . "
#maxConfiguration=77371252455336267181195263
maxConfiguration=128978157015543273035239205301883937138390460458037480988271657477215308241387905145121400363197555638348240965150666181367760634644210336242807367788803607643649092773194600627131718182721299085210994362356247168981452219910049252646092992863046014767953755101986815
model="uClibc_simple.uvl"


def count_file_by_extension(extension,n_cpu,n_tasks):
    json_file_regex="R_" + str(n_cpu) + "_[0-9]+-" + str(n_tasks) +"." + extension
    pattern = re.compile(json_file_regex)
    cont=0
    for roots,dirs, files in os.walk("."):
        for file in files:
            if pattern.match(file):
                cont+=1   
        break
    return cont


totalTime = 0
numberCSV = 10000
while (True):
    ########---------------------
    # 
    # Lanzamos las tareas
    #
    ########---------------------
    if (os.path.isfile("./R_" + str(num_cpus)+"_"+str(numberTasks)+"_joined_0.csv")):
            ficheroCSV = " ./R_" + str(num_cpus)+"_"+str(numberTasks)+"_joined_0.csv "

    cont = 0 
    for i in range(numberTasks):
            fS= "./OutputR_" + str(num_cpus)+"_" + str(i) + "-" + str(numberTasks) + ".err"
            comando= "/usr/bin/time -o " + fS  + " python ./../01main.py ./../fm_models/simples/" + model + " " + str(num_cpus) +" " + str(numberTasks) + " " + str(i) + ficheroCSV + str(min_time) + " " + str(max_time) + " &"
            #print(comando)
            os.system(comando) 
        
            cont+=1
            if (cont>sleepCounter):
                    cont=0
                    time.sleep(sleep)

    ########---------------------
    # 
    # Combinamos
    #
    ########---------------------
    #Wait into it finish
    while (count_file_by_extension("json",num_cpus,numberTasks) < numberTasks):
           time.sleep(10)

    numberCSV = count_file_by_extension("csv",num_cpus,numberTasks)
    if (numberCSV==0):
          break
    
    commando = "python ../processTimeLocal.py OutputR_" + str(num_cpus) + "_ " +  str(numberTasks)  


    proc = subprocess.Popen(commando, stdout=subprocess.PIPE, shell=True)
    (out, err) = proc.communicate()
    totalTime+=float(out)

    

    comando= "python ./../02processOutput.py " + str(num_cpus) +" " + str(numberTasks) + " " + str(maxConfiguration)
    #print(comando)
    os.system(comando) 
    
print("TOtal time is " + str(totalTime))

    
