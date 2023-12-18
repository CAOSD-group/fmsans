from enum import Enum
import string
from fm_solver.models.utils import TransformationsVector
from fm_solver.utils import utils, constraints_utils
from copy import deepcopy


# class syntax
class Tipo(Enum):
    __order__ = 'REQUIRE EXCLUDE'
    REQUIRE = 0
    EXCLUDE = 1

class OrderTransformada:
    def __init__(self, nil:int,trans:list):
        self.nil = nil
        self.transList = trans

    def __str__(self):
        strr = f'NIL: {self.nil}\n'
        for i in self.transList:
            strr+=str(i)+"\n"
        return strr
    
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

  def __repr__(self):
    if (self.tipo == Tipo.REQUIRE):
        return f"{self.v1} REQUIRE {self.v2}"
    elif (self.tipo == Tipo.EXCLUDE):
        return f"{self.v1} EXCLUDE {self.v2}"
  def __str__(self):
    if (self.tipo == Tipo.REQUIRE):
        return f"{self.v1} REQUIRE {self.v2}"
    elif (self.tipo == Tipo.EXCLUDE):
        return f"{self.v1} EXCLUDE {self.v2}"
      
  def __eq__(self, other):
    return self.v1==other.v1\
           and self.v2==other.v2\
           and self.tipo==other.tipo
  def __hash__(self):
    return hash((self.v1, self.v2, self.tipo))

  def sorting_key(self):
    if self.tipo == Tipo.REQUIRE:
        return 0
    elif self.tipo == Tipo.EXCLUDE:
        return 1
    else:
        return 2
    
  def __lt__(self, other):
    if self.tipo == Tipo.EXCLUDE and other.tipo == Tipo.REQUIRE:
        return True
    elif self.tipo == Tipo.REQUIRE and other.tipo == Tipo.EXCLUDE:
        return False
    else:
        return True

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


class Evaluate_transformation_vector:
    trans2=[]
    trans3=[]
    
    @classmethod
    def read_file(self,file_path):
        with open(file_path, 'r') as file:
            lines = file.readlines()

        data = []
        current_nil_value = None

        tList=[]
        for line in lines:
            line = line.strip()

            if line.startswith("NIL:"):
                if (len(tList)>0 and current_nil_value>0):
                    data.append(OrderTransformada(current_nil_value,tList))
                tList=[]
                current_nil_value = int(line.split(":")[1].strip())
            else:
                if current_nil_value is not None:
                    parts = line.split()
                    v1 = parts[0]
                    typeS = parts[1]
                    tipo = Tipo.REQUIRE
                    if (typeS == "EXCLUDE"):
                        tipo=Tipo.EXCLUDE
                    v2 = parts[2]

                    tList.append(Transformada(v1,v2,tipo))

        if (len(tList)>0):
            data.append(OrderTransformada(current_nil_value,tList))

        return data

    @classmethod
    def load_all(self):
        file_path = '../salida2.txt'
        Evaluate_transformation_vector.trans2 = Evaluate_transformation_vector.read_file(file_path)
#        for entry in result2:
#            print(entry)

        file_path = '../salida3.txt'
        Evaluate_transformation_vector.trans3 = Evaluate_transformation_vector.read_file(file_path)
#        for entry in result3:
#            print(entry)
    
    @classmethod
    def print(self):
       for entry in Evaluate_transformation_vector.trans2:
           print(entry)
       for entry in Evaluate_transformation_vector.trans3:
           print(entry)
        

    @classmethod
    def createTransform(self,c1):
        left_feature, right_feature = constraints_utils.left_right_features_from_simple_constraint(c1) # dada una constraints devuelve la feature izquierda y derecha en una tupla
        tipo = Tipo.EXCLUDE
        if (constraints_utils.is_requires_constraint(c1)): # dada una constraints devuelve true si es requires, hay otro is_excludes_constraint(self.constraints[i])
           tipo=Tipo.REQUIRE 
        return Transformada(left_feature,right_feature,tipo)
    
    @classmethod
    def filter(self,tt):
        name_new=['f','g','h','i','j','k']
        resultado = []

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
        tt = sorted(tt, key=Evaluate_transformation_vector.sorting_key)
        if (len(contSimilar)==0):
            resultado=tt
        
        return resultado
    @classmethod
    def sorting_key(self,obj):
        return obj.sorting_key()
    @classmethod
    def evaluate3(self,c1,c2,c3):
        tt=[]
        tt.append(Evaluate_transformation_vector.createTransform(c1))
        tt.append(Evaluate_transformation_vector.createTransform(c2))
        tt.append(Evaluate_transformation_vector.createTransform(c3))
        #Rename variables
        tt=Evaluate_transformation_vector.filter(tt)
        cont=0
        #Find the same, if found, return it value.
        while (cont < len(Evaluate_transformation_vector.trans3)):
            if (Evaluate_transformation_vector.trans3[cont].transList==tt):
                return Evaluate_transformation_vector.trans3[cont].nil
            cont+=1
      
        return 0


        


    @classmethod
    def evaluate2(self,c1,c2):
        tt=[]
        tt.append(Evaluate_transformation_vector.createTransform(c1))
        tt.append(Evaluate_transformation_vector.createTransform(c2))
        #Rename variables
        tt=Evaluate_transformation_vector.filter(tt)
        cont=0
        #Find the same, if found, return it value.
        while (cont < len(Evaluate_transformation_vector.trans2)):
            if (Evaluate_transformation_vector.trans2[cont].transList==tt):
                return Evaluate_transformation_vector.trans2[cont].nil
            cont+=1
      
        return 0
       

        return 2

    @classmethod
    def evaluate(self,constraintsOrder,data):
        metric=0
        i = 0
        constraints=[data[i] for i in constraintsOrder]
        while i < len(constraints):
            c3=0
            c2=0
            if (i+3< len(constraints)):
                c3 = Evaluate_transformation_vector.evaluate3(constraints[i],constraints[i+1],constraints[i+2])
            if (i+2< len(constraints)):
                c2 = Evaluate_transformation_vector.evaluate2(constraints[i],constraints[i+1])
            if (c3>c2):
                i+=3
                metric+=c3
            elif (c2>=c3 and c2!=0):
                i+=2
                metric+=c2
            else:
                i+=1
        return metric,
    

         
            