import os
import warnings
import json
import pandas as pd

from redis_helper import client
from index_helper import populate_index, main as create_index_main
from vector_helper import hf

# load json file
df = pd.read_json("assets/symptoms.jsonl", lines=True)
print("Loaded", len(df), " entries")
print(df.head())

# create embeddings cache
# disable parallelism to avoid warnings
os.environ["TOKENIZERS_PARALLELISM"] = "false"



# vectorize descriptions
# use as_buffer=True to store vectors in Redis as binary data
# this is more efficient for storage and retrieval
# if you want to store vectors as lists, use as_buffer=False
df["vector"] = hf.embed_many(df["description"].tolist(), as_buffer=True)
print(df.head())

# create/get index
index_name = "symptoms"
index = create_index_main(index_name)

populate_index(index, df)
print("Index population complete.")