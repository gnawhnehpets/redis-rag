from pydantic import BaseModel
from typing import Optional, List
import json

class DeleteKey(BaseModel):
    key: str


class UserObject(BaseModel):
    user: str
    age: Optional[int] = None
    job: Optional[str] = None

class Occupation(BaseModel):
    title: str
    salary: int

class Address(BaseModel):
    city: str
    state: str
    zip: int

class Details(BaseModel):
    occupation: Optional[Occupation] = None
    address: Optional[Address] = None

class UserObjectJson(BaseModel):
    user: str
    details: Optional[Details] = None

class Message(BaseModel):
    role: str
    content: str

class UserObjectList(BaseModel):
    user: str
    messages: List[Message]