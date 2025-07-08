from pydantic import BaseModel
from typing import Optional

class DeleteKey(BaseModel):
    key: str

class UserObject(BaseModel):
    user: str
    last: Optional[str] = ""
    age: Optional[int] = ""
    job: Optional[str] = ""