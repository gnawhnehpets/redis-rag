import os
import warnings
import json
import pandas as pd

from redis import Redis
from redisvl.utils.vectorize import HFTextVectorizer
from redisvl.extensions.cache.embeddings import EmbeddingsCache

from redis_helper import client
from index_helper import populate_index, main as create_index_main

# load json file
df = pd.read_json("assets/symptoms.jsonl", lines=True)
print("Loaded", len(df), " entries")
print(df.head())

# create embeddings cache
# disable parallelism to avoid warnings
os.environ["TOKENIZERS_PARALLELISM"] = "false"

hf = HFTextVectorizer(
    model="sentence-transformers/all-MiniLM-L6-v2",
    cache=EmbeddingsCache(
        name="embedcache",
        ttl=600,
        redis_client=client,
    )
)

# vectorize descriptions
# use as_buffer=True to store vectors in Redis as binary data
# this is more efficient for storage and retrieval
# if you want to store vectors as lists, use as_buffer=False
df["vector"] = hf.embed_many(df["description"].tolist(), as_buffer=True)
print(df.head())

# create/get index
index_name = "symptoms"
index = create_index_main(index_name)

# populate_index(index, df)
# print("Index population complete.")