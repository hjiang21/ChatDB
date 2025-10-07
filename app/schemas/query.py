# app/schemas/query.py
from typing import Any, Dict, List
from pydantic import BaseModel, Field

class QueryRequest(BaseModel):
    query: str = Field(..., example="List the symptoms associated with the flu.")

class QueryResponse(BaseModel):
    data: List[Dict[str, Any]] = Field(..., description="Results from the SQL query")

class QueryResponseSummary(BaseModel):
    diseaseDB_response: str = Field(..., example="The symptoms of the flu include fever, cough, and runny nose.")

