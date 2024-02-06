import pandas as pd
from scipy.stats import mannwhitneyu
import csv



#Montamos el df con los csvs
models=['FQAs','ApoGames','BerkeleyDb', 'JHipster']
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
    to_compare = {0: 'T',1:'A'}
    variable = {0:'Removed',1:'Random',2:'Genetic'}

    

    for i in range(0,2):
        for j in range(0,3):
            normal="Normal"+to_compare[i]
            other=variable[j]+to_compare[i]
            U1, p = mannwhitneyu(df[other], df[normal], method="auto",alternative="less")
            result.append([model+"-"+other+"<"+normal,p])


with open("evaluation/heuristics/TotalPValues.csv", "w", newline="") as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(["model p comparison", "p-value"])  
    writer.writerows(result)  