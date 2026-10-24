import pandas as pd
import numpy as np
import ast

data = pd.read_csv(
    "01_data/05_embeddings_DF.csv"
)

data["embedding"] = data["embedding"].apply(
    ast.literal_eval
)

chunk_vectors = np.array(
    data["embedding"].tolist(),
    dtype=np.float32
)

np.save(
    "02_vectors/chunk_vectors.npy",
    chunk_vectors
)

print("chunk_vectors.npy saved")
