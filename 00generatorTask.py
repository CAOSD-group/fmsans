import os
import time
numberTasks = 2
min_time = 120
max_time = 240
num_cpus=1
sleep = 10
sleepCounter=1
#improve to check for more than only one
ficheroCSV= " . "

if (os.path.isfile("./R_" + str(num_cpus)+"_"+str(numberTasks)+"_joined_0.csv")):
         ficheroCSV = " ./R_" + str(num_cpus)+"_"+str(numberTasks)+"_joined_0.csv "

cont = 0 
for i in range(numberTasks):
        fS= "./OutputR_" + str(num_cpus)+"_" + str(i) + "-" + str(numberTasks) + ".err"
        comando= "/usr/bin/time -o " + fS  + " python ./../01main.py ./../fm_models/simples/uClibc_simple.uvl " + str(num_cpus) +" " + str(numberTasks) + " " + str(i) + ficheroCSV + str(min_time) + " " + str(max_time) + " &"
        print(comando)
        os.system(comando) 
       
        cont+=1
        if (cont>sleepCounter):
                cont=0
                time.sleep(sleep)
