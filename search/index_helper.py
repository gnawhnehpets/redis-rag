from redis_helper import client, REDIS_URL
from redisvl.schema import IndexSchema
from redisvl.index import SearchIndex

import subprocess
import pandas as pd

print("Redis connected:", client.ping())

def create_index(schema: IndexSchema):
    index = SearchIndex(schema, client)
    index.create(overwrite=True, drop=True)
    return index

def check_index_exists(index_name: str) -> bool:
    cmd = ["rvl", "index", "info", "-i", index_name, "-u", REDIS_URL]
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode == 0:
        print(f"Index '{index_name}' exists.")
        print(result.stdout)
        return True
    else:
        print(f"Index '{index_name}' does not exist.")
        print("CLI Error:", result.stderr.strip())
        return False

def populate_index(index: SearchIndex, df: pd.DataFrame):
    index.load(df.to_dict(orient="records"))

def main(index_name: str = "symptoms_index"):
    schema = IndexSchema.from_dict({
        "index": {
            "name": index_name,
            "prefix": index_name,
            "storage_type": "hash"
        },
        "fields": [
            {"name": "description", "type": "text"},
            {"name": "source", "type": "text"},
            {
                "name": "vector",
                "type": "vector",
                "attrs": {
                    "dims": 384,
                    "distance_metric": "cosine",
                    "algorithm": "flat",
                    "datatype": "float32"
                }
            }
        ]
    })

    if not check_index_exists(index_name):
        index = create_index(schema)
    else:
        index = SearchIndex(schema, client)
    return index

if __name__ == "__main__":
    main()
