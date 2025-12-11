from pydantic import BaseModel 
from typing import List

class Option(BaseModel):
    key: str
    value: str

class MetaPayload(BaseModel):
    columns: List[Option]
    chart_type: List[Option]

