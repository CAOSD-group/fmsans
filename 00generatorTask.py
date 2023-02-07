import os
for i in range(128):
    print("time python 01main.py ./fm_models/simples/Krieter2020o_simple.uvl 4 128 " + str(i) + " -1 -1")
    os.system("time python 01main.py ./fm_models/simples/Krieter2020o_simple.uvl 4 128 " + str(i) + " -1 -1 &") 
