import pandas as pd
from rdfpandas.graph import to_dataframe
import rdflib

graph = rdflib.Graph()
print("start parse")
graph.parse('D:/wdump-2784.nt', format="nt, ")
print("end parse")
print("start df conversion")
df = to_dataframe(graph)

print(df.shape())
print(df.head())

df.to_csv('D:/wikiCS.csv')





