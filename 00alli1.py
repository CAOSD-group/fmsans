import os
import time
import subprocess
import re

numberTasks = 65536
numberJobs = 8
max_time = 3600
sleep = 1
sleepCounter=8
#improve to check for more than only one
ficheroCSV= " . "
maxConfiguration=77371252455336267181195263
#uClib maxConfiguration=128978157015543273035239205301883937138390460458037480988271657477215308241387905145121400363197555638348240965150666181367760634644210336242807367788803607643649092773194600627131718182721299085210994362356247168981452219910049252646092992863046014767953755101986815
# Ghamizi maxConfiguration=1298074214633706907132624082305023
#axTLS  maxConfiguration= 748288838313422294120286634350736906063837462003711
#uCliux-distribution 
#maxConfiguration=188501787658138776526316391973679239907820382867140805681144220780050698265428977917842924316820804490882044531700026161400423140624345724347059987430217219443542346615871751089083876220596224387399635909565487009065232689887930358404389913798458461035797425091600762263250923357187307004059038598692050448905404415
#model="fm_models/originals/Operating_Systems/KConfig/uClinux-distribution.uvl"


#model="fm_models/simples/uClibc_simple.uvl"
model="fm_models/simples/GPL_simple.uvl"


cont = 0 
for i in range(numberJobs):
        fS= "./OutputR_1_" + str(i) + "-" + str(numberTasks) + ".err"
        divisionFile = "./R_" + str(i) + "_" + str(numberJobs) + "_divisions.csv"
        comando= "/usr/bin/time -o " + fS  + " python ./../picassofiles01main.py ./../" + model + " " + divisionFile + " " + str(numberTasks) + " " + str(i) + " " + str(max_time) + " &"

        #comando= "/usr/bin/time -o " + fS  + " -f \"%U %S\" python ./../picasso01main.py ./../" + model + "  " + str(numberTasks) + " " + str(i) + ficheroCSV + str(min_time) + " " + str(max_time) + " &"
        #print(comando)
        os.system(comando) 
    
        cont+=1
        if (cont>sleepCounter):
                cont=0
                time.sleep(sleep)

   