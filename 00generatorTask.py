import os
numberTasks = 4
min_time = 1200
max_time = 1400
#improve to check for more than only one
ficheroCSV= " . "
if (os.path.isfile("./R_4_64_joined_0.csv")):
         ficheroCSV = " ./R_4_64_joined_0.csv "
       
for i in range(numberTasks):
        comando= "time python ./../01main.py ./../fm_models/simples/GPL_simple.uvl 4 " + str(numberTasks) + " " + str(i) + ficheroCSV + str(min_time) + " " + str(max_time) + " &"
        print(comando)
        os.system(comando) 
