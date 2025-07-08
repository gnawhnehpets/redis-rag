import os
import warnings
from redis import Redis
from dotenv import load_dotenv
import json

from redisvl.utils.vectorize import HFTextVectorizer
from redisvl.extensions.cache.embeddings import EmbeddingsCache

load_dotenv()

warnings.filterwarnings("ignore")

REDIS_HOST = "localhost" #os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_USERNAME = os.getenv("REDIS_USERNAME")
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")
REDIS_URL = f"redis://{REDIS_USERNAME}:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}"

client = Redis.from_url(REDIS_URL)
print(client.ping())

os.environ["TOKENIZERS_PARALLELISM"] = "false"

hf = HFTextVectorizer(
    model="sentence-transformers/all-MiniLM-L6-v2",
    cache=EmbeddingsCache(
        name="embedcache",
        ttl=600,
        redis_client=client,
    )
)

df["vector"] = hf.embed_many(df["description"].tolist(), as_buffer=True)

df.head()