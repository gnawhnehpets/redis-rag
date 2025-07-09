import os
from fastapi import FastAPI, Body
from pydantic import BaseModel
import redis
from classes import DeleteKey, UserObject, UserObjectJson, UserObjectList
from index_helper import delete_all_indexes
import json
from redisvl.query import VectorQuery, HybridQuery

from vector_helper import hf
from index_helper import main as get_index_helper_main
from redis_helper import REDIS_URL

app = FastAPI()

class RedisItem(BaseModel):
    key: str
    value: str

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
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
    """Set a key-value pair"""
    r.set(item.key, item.value)
    return {"status": "ok", "key": item.key, "value": item.value}


@app.post("/set-hash")
def set_key_hash(item: UserObject = Body(
        ...,
        example={
            "user": "stephen",
            "job": "solutions architect"
        })):
    """Set a key with a hash"""
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
    """Set a key with JSON data"""
    redis_key = f"user:{item.user}"
    mapping = {k: v for k, v in item.dict().items() if v is not None}
    print(json.dumps(mapping, indent=2))
    if mapping:
        r.json().set(redis_key, '$', mapping)
    return {"status": "ok", "key_set": redis_key}


@app.post("/push-list")
def push_list(item: UserObjectList = Body(
        ...,
        example={
            "user": "john",
            "messages": [
                {"role": "user", "content": "Hello what can you do for me?"},
                {"role": "assistant", "content": "Hi, I am a helpful virtual assistant."}
            ]
        })):
    """Push a list of messages to a key"""
    redis_key = f"messages:{item.user}"
    
    messages_to_push = [msg.json() for msg in item.messages]
    
    if messages_to_push:
        r.rpush(redis_key, *messages_to_push)
        
    return {"status": "ok", "key": redis_key, "items_pushed": len(messages_to_push)}


@app.get("/get/{key:path}")
def get_any_key(key: str):
    """Retrieve any key-value"""
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
    elif key_type == 'list':
        list_data = r.lrange(key, 0, -1)
        data = []
        for item in list_data:
            try:
                data.append(json.loads(item))
            except (json.JSONDecodeError, TypeError):
                data.append(item)
    else:
        data = f"Unsupported data type: {key_type}"

    return {"key": key, "type": key_type, "data": data}


@app.delete("/delete/{key:path}")
def delete_any_key(key: str):
    """Delete a key"""
    if r.exists(key):
        r.delete(key)
        return {"status": "deleted", "key": key}
    else:
        return {"status": "error", "message": f"Key '{key}' does not exist."}


@app.get("/get-all-items")
def get_all_items():
    """Retrieve all items"""
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
        elif key_type == 'list':
            list_data = r.lrange(key, 0, -1)
            data = []
            for item in list_data:
                try:
                    data.append(json.loads(item))
                except (json.JSONDecodeError, TypeError):
                    data.append(item)
            items[key] = data
    return items


@app.delete("/delete-all")
def delete_all_items():
    """Delete all keys"""
    keys = r.keys('*')
    if not keys:
        return {"status": "error", "message": "No keys to delete."}
    
    r.delete(*keys)
    return {"status": "deleted", "keys_deleted": len(keys)}


@app.get("/count-records")
def count_records():
    """Return the number of keys"""
    count = r.dbsize()
    return {"total_keys": count}


@app.get("/get-indexes")
def get_indexes():
    """Get all RediSearch indexes"""
    try:
        index_names = r.execute_command("FT._LIST")  # returns list of index names
        return {"indexes": index_names}
    except Exception as e:
        return {"error": f"Failed to retrieve indexes: {str(e)}"}

@app.delete("/delete-indexes")
def delete_indexes():
    """Delete all indexes and associated data"""
    return delete_all_indexes()


class VectorQueryRequest(BaseModel):
    query: str
    num_results: int = 3
    index_name: str = "symptoms"


@app.post("/query-vector-search")
def query_vector_search(request: VectorQueryRequest):
    """Perform a vector similarity search"""
    try:
        embedded_user_query = hf.embed(request.query)

        vec_query = VectorQuery(
            vector=embedded_user_query,
            vector_field_name="vector",
            num_results=request.num_results,
            return_fields=["description", "source"],
            return_score=True
        )

        index = get_index_helper_main(request.index_name)
        result = index.query(vec_query)
        
        formatted_results = []
        for item in result:
            print(item)
            formatted_results.append({
                "description": item['description'],
                "source": item['source'],
                "score": item['vector_distance'],
            })
        
        return {"status": "ok", "results": formatted_results}
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"status": "error", "message": str(e)}


@app.post("/query-hybrid-search")
def query_vector_search(request: VectorQueryRequest):
    """Perform a hybrid search combining text and vector similarity search"""
    try:
        embedded_user_query = hf.embed(request.query)

        vec_query = HybridQuery(
            text=request.query,
            text_field_name="description",
            text_scorer="BM25STD", # [TFIDF, TFIDF.DOCNORM, BM25, DISMAX, DOCSCORE, BM25STD]
            
            vector=embedded_user_query,
            vector_field_name="vector",
            alpha=0.25, # weight the vector score lower
            
            num_results=request.num_results,
            return_fields=["description", "source"],
            stopwords="english"
        )

        index = get_index_helper_main(request.index_name)
        result = index.query(vec_query)
        
        formatted_results = []
        for item in result:
            print(item)
            formatted_results.append({
                "description": item['description'],
                "source": item['source'],
                "vector_distance": item['vector_distance'],
                "vector_similarity": item['vector_similarity'],
                "text_score": item['text_score'],
                "hybrid_score": item['hybrid_score']
            })
        
        return {"status": "ok", "results": formatted_results}
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"status": "error", "message": str(e)}