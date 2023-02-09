import os
numberTasks = 64
for i in range(numberTasks):
        comando= "time python ./../01main.py ./../fm_models/simples/GPL_simple.uvl 4 " + str(numberTasks) + " " + str(i) + " ./R_4_64_joined_0.csv 30 600 &"
        print(comando)
        os.system(comando) 
