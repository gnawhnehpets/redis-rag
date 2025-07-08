import os
from fastapi import FastAPI
from pydantic import BaseModel
import redis

app = FastAPI()

class RedisItem(BaseModel):
    key: str
    value: str

REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_USERNAME = os.getenv("REDIS_USERNAME")
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")

r = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    username=REDIS_USERNAME,
    password=REDIS_PASSWORD,
    db=0,
    decode_responses=True)

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.get("/hits")
def read_hits():
    r.incr('hits')
    return {"hits": r.get('hits')}

@app.post("/set")
def set_key(item: RedisItem):
    r.set(item.key, item.value)
    return {"status": "ok", "key": item.key, "value": item.value}

@app.get("/get-all-items")
def get_all():
    keys = r.keys('*')
    items = {}
    for key in keys:
        items[key] = r.get(key)
    return items