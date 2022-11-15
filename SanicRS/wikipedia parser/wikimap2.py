from sentence_transformers import SentenceTransformer, util
import torch

#generate corpus  embeddings and save to tensor

embedder = SentenceTransformer('sentence-transformers/msmarco-distilbert-base-tas-b')

corpus = open('wikipagesclean2', 'r', encoding='utf-8').readlines()

embedder.encode