import pandas as pd
from scipy.stats import mannwhitneyu
import csv
import numpy as np



#Montamos el df con los csvs
#models=[,]
models=['MobileMedia2','Pizza','FQAs','Truck','ApoGames','MTG', 'JHipster','BerkeleyDb','Graph','Oh2019','GPL']
csv_files = ['Normal.csv', 'Removed.csv', 'Random.csv','Genetic.csv']


# Read each CSV file into a DataFrame and append to the list
result=[]
for model in models:
    dfs = []
    path="evaluation/heuristics/"+model+"/"+model+"_heuristics_"
    for file in csv_files:
        df = pd.read_csv(path+file)
        dfs.append(df[['Analyzed', 'Time(s)']])

    # Concatenate all DataFrames in the list
    df = pd.concat(dfs, axis=1)
    df.columns=['NormalT','NormalA','RemovedT','RemovedA','RandomT','RandomA','GeneticT','GeneticA']
    to_compare = {0: 'A',1:'T'}
    variable = {0:'Removed',1:'Random',2:'Genetic'}

    
    currentLen = len(result)
    result.append(" ")
    result.append(" ")
    result.append(" ")
    for i in range(0,2):
        normal="Normal"+to_compare[i]
        for j in range(0,3):
            other=variable[j]+to_compare[i]
            division=((df[normal]-df[other])/df[normal])
            average = division.mean()*100
            U1, p = mannwhitneyu(df[other], df[normal], method="auto",alternative="less")
            result[currentLen+j]= result[currentLen+j] + " & " + str(round(average,2)) + " & " + str(round(p,2)) 
            
    
    result[currentLen]=result[currentLen]+"% Removed" + model + "\n"
    result[currentLen+1]=result[currentLen+1]+"% Random" + model+ "\n"
    result[currentLen+2]=result[currentLen+2]+"\\\\ % Genetic" + model + "\n"
            


with open("evaluation/heuristics/TotalPValues.csv", "w", newline="") as csvfile:
    for r in result:
        csvfile.write(r)
