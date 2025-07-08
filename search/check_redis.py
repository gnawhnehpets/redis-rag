import os
from redis import Redis
from dotenv import load_dotenv

load_dotenv()

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_USERNAME = os.getenv("REDIS_USERNAME")
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")

REDIS_URL = f"redis://{REDIS_USERNAME}:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}" if REDIS_USERNAME and REDIS_PASSWORD else f"redis://{REDIS_HOST}:{REDIS_PORT}"

try:
    client = Redis.from_url(REDIS_URL)
    print("Redis connected:", client.ping())
    print("Existing indexes:", client.execute_command("FT._LIST"))
    try:
        info = client.ft("symptoms").info()
        print(f"Number of documents in 'symptoms' index: {info['num_docs']}")
    except Exception as e:
        print(f"Could not get info for 'symptoms' index: {e}")
except Exception as e:
    print(f"Error connecting to Redis: {e}")
