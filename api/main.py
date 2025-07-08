import os
from fastapi import FastAPI, Body
from pydantic import BaseModel
import redis
from classes import DeleteKey, UserObject, UserObjectJson
import json

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
    """Root endpoint"""
    r.set('hits', 0)
    return {"Hello": "World"}


@app.get("/hits")
def read_hits():
    """Get the number of hits to this endpoint - test"""
    r.incr('hits')
    return {"hits": r.get('hits')}


@app.post("/set-key-value")
def set_key_value(item: RedisItem):
    """Set a key-value pair in Redis"""
    r.set(item.key, item.value)
    return {"status": "ok", "key": item.key, "value": item.value}


@app.post("/set-hash")
def set_key_hash(item: UserObject = Body(
        ...,
        example={
            "user": "stephen",
            "job": "solutions architect"
        })):
    """Set a key in Redis with a hash"""
    redis_key = f"user:{item.user}"
    mapping = {k: v for k, v in item.dict().items() if v is not None}
    if mapping:
        r.hset(redis_key, mapping=mapping)
    return {"status": "ok", "key_set": redis_key}


@app.post("/set-key-json")
def set_key_json(item: UserObjectJson = Body(
        ...,
        example={
            "user": "stephen2",
            "details": {
                "occupation": {"title": "solutions engineer", "salary": 100000000},
                "address": {"city": "Apex", "state": "NC", "zip": 27502}
            }
        })):
    """Set a key in Redis with JSON data"""
    redis_key = f"user:{item.user}"
    mapping = {k: v for k, v in item.dict().items() if v is not None}
    print(json.dumps(mapping, indent=2))
    if mapping:
        r.json().set(redis_key, '$', mapping)
    return {"status": "ok", "key_set": redis_key}


@app.get("/get/{key:path}")
def get_any_key(key: str):
    """Retrieve any key-value from Redis"""
    if not r.exists(key):
        return {"status": "error", "message": f"Key '{key}' does not exist."}

    key_type = r.type(key)
    data = None
    
    if key_type == 'string':
        data = r.get(key)
    elif key_type == 'hash':
        data = r.hgetall(key)
        for field, value in data.items():
            try:
                data[field] = json.loads(value)
            except (json.JSONDecodeError, TypeError):
                pass
    elif key_type == 'ReJSON-RL':
        data = r.json().get(key)
    else:
        data = f"Unsupported data type: {key_type}"

    return {"key": key, "type": key_type, "data": data}


@app.delete("/delete/{key:path}")
def delete_any_key(key: str):
    """Delete a key from Redis"""
    if r.exists(key):
        r.delete(key)
        return {"status": "deleted", "key": key}
    else:
        return {"status": "error", "message": f"Key '{key}' does not exist."}

@app.get("/get-all-items")
def get_all_items():
    """Retrieve all items from Redis"""
    keys = r.keys('*')
    items = {}
    for key in keys:
        key_type = r.type(key)
        if key_type == 'hash':
            hash_data = r.hgetall(key)
            for field, value in hash_data.items():
                try:
                    hash_data[field] = json.loads(value)
                except (json.JSONDecodeError, TypeError):
                    pass
            items[key] = hash_data
        elif key_type == 'string':
            items[key] = r.get(key)
        elif key_type == 'ReJSON-RL':
            items[key] = r.json().get(key)
    return items

