from enum import Enum
import string
import itertools
from copy import deepcopy
from itertools import groupby


transformationNumber=4

#2
name_var=['a','b','c']
name_new=['f','g','h']
variables = 3
#3
if (transformationNumber==3):
    variables = 4
    name_var=['a','b','c','d']
    name_new=['f','g','h','i']
#4
if (transformationNumber==4):
    variables = 6
    name_var=['a','b','c','d','e','g']
    name_new=['f','g','h','i','j','k']
# class syntax
class Tipo(Enum):
    __order__ = 'REQUIRE EXCLUDE'
    REQUIRE = 0
    EXCLUDE = 1

class OrderTransformada:
    def __init__(self, nil:int,trans:list):
        self.nil = nil
        self.transList = trans
    def __eq__(self, other):
        return self.nil==other.nil\
           and self.transList==other.transList
    def __hash__(self):
        hashh=hash(self.transList[0])
        for i in range(1,len(self.transList)):
            hashh+=hash(self.transList[i])
        return hashh
    def sorting_key(self):
        return -self.nil
    def getNil():
        return self.nil
    def getList():
        return self.transList
    

class Transformada:
  def __init__(self, v1:string,v2:string,t:Tipo):
    self.v1 = v1
    self.v2 = v2
    if not isinstance(t, Tipo):
            raise ValueError("El tipo debe ser EXCLUDE o REQUIRE.")
    self.tipo = t

  def __eq__(self, other):
    return self.v1==other.v1\
           and self.v2==other.v2\
           and self.tipo==other.tipo
  def __hash__(self):
    return hash((self.v1, self.v2, self.tipo))
  

    #The same or the same variables but oppositve type.
  def avoid(self,other):
      return self==other or (self.v1==other.v1 and self.v2==other.v2 and self.tipo!=other.tipo)

  def sorting_key(self):
    i = -1
    if (self.v1 in name_new):
        i=name_new.index(self.v1)
    elif (self.v1 in name_var):
        i=name_var.index(self.v1)
    else:
        print("error ordering")

    if self.tipo == Tipo.REQUIRE:
        return i*variables
    elif self.tipo == Tipo.EXCLUDE:
        return i*variables+1
    else:
        return -1
    
  def __lt__(self, other):
    if self.tipo == Tipo.EXCLUDE and other.tipo == Tipo.REQUIRE:
        return True
    elif self.tipo == Tipo.REQUIRE and other.tipo == Tipo.EXCLUDE:
        return False
    else:
        return True

  def toString(self):
      if (self.tipo == Tipo.REQUIRE):
          return f"{self.v1} REQUIRE {self.v2}"
      elif (self.tipo == Tipo.EXCLUDE):
          return f"{self.v1} EXCLUDE {self.v2}"

  def getV1(self):
      return self.v1
  def getV2(self):
      return self.v2
  def setV1(self,newv):
      self.v1=newv
  def setV2(self,newv):
      self.v2=newv
  def trans(self):
      if (self.tipo == Tipo.REQUIRE):
          str1 = "+"+self.v2
          str2 = "-"+self.v1
          str3= "-"+self.v2
          result=list()
          result.append([str1])
          result.append([str2,str3])
          return result
      elif (self.tipo == Tipo.EXCLUDE):
          str1 = "-"+self.v2
          str2 = "-"+self.v1
          str3="+"+self.v2
          result=list()
          result.append([str1])
          result.append([str2,str3])
          return result
      
def generate_recursive(lista:list,tg):
    if (len(tg)==0):
        return lista
    elif (len(lista)==0):
        lista = tg.pop().trans()
        lista = generate_recursive(lista,tg)
        return lista
    else:
        listaNueva = list()
        cont = 0
        newTg = tg.pop()
        while (cont<len(lista)):
            for t in newTg.trans():
                listaNueva.append(lista[cont]+list(t))
            cont+=1

        lista = generate_recursive(listaNueva,tg)
        return lista


      
def evaluate(tg):
    total=generate_recursive([],list(tg))
    tran = 0
    numNil = 0
    while (tran < len(total)):
        #Cogemos la primera transformada
        tt = total[tran]
        cont = 0
        salir = False
        while (cont < len(tt) and not salir):
            init=tt[cont]
            contInt = cont+1
            while (contInt < len(tt) and not salir):
                comp=tt[contInt]
                if(init[0]!=comp[0] and init[1]==comp[1]):
                    salir=True
                contInt+=1


            cont+=1
        if (salir):
            numNil+=1

        tran+=1


    return numNil

def sorting_key(obj):
    return obj.sorting_key()
    
def filter(tg):
    
    resultado = []
    contT=0
    #Rename the variables
    while(contT<len(tg)): 
        tt = deepcopy(tg[contT])
        unique_list = list(dict.fromkeys(tt))

        if (len(tt)==len(unique_list)):
            contI=0
            contV=0
            contSimilar=[]
            rename_var=dict()
            while(contI<len(tt)):
                

                if (tt[contI].getV1()==tt[contI].getV2()):
                    contSimilar.append(contI)  

                if (tt[contI].getV1() in rename_var):
                    tt[contI].setV1(rename_var[tt[contI].getV1()])
                else:
                    rename_var[tt[contI].getV1()]=name_new[contV]
                    tt[contI].setV1(rename_var[tt[contI].getV1()])
                    contV+=1

                if (tt[contI].getV2() in rename_var):
                    tt[contI].setV2(rename_var[tt[contI].getV2()])
                else:
                    rename_var[tt[contI].getV2()]=name_new[contV]
                    tt[contI].setV2(rename_var[tt[contI].getV2()])
                    contV+=1
                if (tt[contI].getV1()==tt[contI].getV2()):
                    contSimilar.append(contI)    
                contI += 1
            
            tt=list(dict.fromkeys(tt))
            tt = sorted(tt, key=sorting_key)
            if (len(contSimilar)==0):
                avoidtt=False
                cont = 0
                while(cont<len(tt) and not avoidtt):
                    contI=cont+1
                    while(contI<len(tt) and not avoidtt):
                        avoidtt=tt[cont].avoid(tt[contI])
                        contI+=1
                    cont+=1
                if (not avoidtt):
                    resultado.append(tt)
        
        
        contT+=1
    
    return resultado

def mostrar(tg):
    for tt in tg:
        print(f"NIL: {tt.nil}")
        for c in tt.transList:
            print(c.toString())


if __name__ == "__main__":
    #Three constraint, can use 3 variables.

    lV= list(itertools.permutations(name_var, variables))
    posibleTrans = []
    for l in lV:
        for t in Tipo:
            posibleTrans.append(Transformada(l[0],l[1],t))

    posibleTrans = list(set(posibleTrans))
    transGroup= list(itertools.permutations(posibleTrans, transformationNumber))
    transGroup=filter(transGroup.copy())
    
    transGroup=[k for k,v in groupby(sorted(transGroup))]

    
    prioList = []
    for tg in transGroup:
        prio = evaluate(tg)
        prioList.append(OrderTransformada(prio,tg))  
        
    sorted_list = sorted(prioList, key=sorting_key)
    filtered_list=list(dict.fromkeys(sorted_list))

    mostrar(filtered_list)

