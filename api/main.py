import os
from fastapi import FastAPI
from pydantic import BaseModel
import redis
from classes import DeleteKey, UserObject

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


@app.post("/set-key-value")
def set_key_value(item: RedisItem):
    r.set(item.key, item.value)
    return {"status": "ok", "key": item.key, "value": item.value}


@app.get("/get-key-value/{key}")
def get_key_value(key: str):
    value = r.get(key)
    if value is not None:
        return {"key": key, "value": value}
    else:
        return {"status": "error", "message": f"Key {key} does not exist."}


@app.delete("/delete-key-value")
def delete_key_value(item: DeleteKey):
    if r.exists(item.key):
        r.delete(item.key)
        return {"status": "deleted k-v pair", "key": item.key}
    else:
        return {"status": "error", "message": f"Key {item.key} does not exist."}


@app.post("/set-hash")
def set_key_hash(item: UserObject):
    redis_key = f"user:{item.user}"
    mapping = {k: v for k, v in item.dict().items() if v is not None}
    if mapping:
        r.hset(redis_key, mapping=mapping)
    return {"status": "ok", "key_set": redis_key}


@app.get("/get-hash/{user}")
def get_key_hash(user: str):
    redis_key = f"user:{user}"
    if r.exists(redis_key):
        data = r.hgetall(redis_key)
        return {"key": redis_key, "data": data}
    else:
        return {"status": "error", "message": f"User {user} does not exist."}
        

@app.delete("/delete-hash")
def delete_key_hash(item: DeleteKey):
    redis_key = f"user:{item.key}"
    if r.exists(redis_key):
        r.delete(redis_key)
        return {"status": "deleted hash", "key": redis_key}
    else:
        return {"status": "error", "message": f"Key {item.key} does not exist."}


@app.get("/get-all-items")
def get_all_items():
    keys = r.keys('*')
    items = {}
    for key in keys:
        key_type = r.type(key)
        if key_type == 'hash':
            items[key] = r.hgetall(key)
        elif key_type == 'string':
            items[key] = r.get(key)
    return items

