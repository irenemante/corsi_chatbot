#import sentence_transformers
import torch
import pandas as pd

#Rifare i tensori del nuovo Merlot
df = pd.read_csv("C:/Users/Mixy/Downloads/MERLOTfull.csv", sep=";")
list = df['level_1'].unique().tolist()
list2 = df['domain_level_0'].unique().tolist()
list3 = df['level_2'].unique().tolist()
print(list)
print("\n\n\n")
print(list2)
print("\n\n\n")
print(list3)


