# app/main.py
from sqlalchemy import text
from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import engine, get_db
from app.db.base import Base
from app.llm.text_to_sql import get_sql_query
from app.llm.sql_to_text import get_text_response
from app.schemas.query import QueryRequest, QueryResponse, QueryResponseSummary


app = FastAPI(title="ChatDB API", version="1.0")


# this is a simple endpoint to confirm that the API is up and running 
@app.get("/heartbeat", summary="Check API Health")
async def heartbeat():
    return {"status": "ok", "message": "API is running successfully"}


# this retrieves & returns the first 5 rows from each table (a sanity check)
@app.get("/preview", summary="Preview the first 5 rows from each table")
async def preview_tables(db: AsyncSession = Depends(get_db)):

    tables = ['disease', 'disease_symptom', 'symptom', 'patient']
    results = {}
    for table in tables:
        try:
            query = text(f"SELECT * FROM {table} LIMIT 5")
            result = await db.execute(query)
            rows = result.fetchall()
            results[table] = [dict(row._mapping) for row in rows]
        except Exception as e:
            results[table] = f"Error: {str(e)}"
    return results
    

# read-only query endpoint 
@app.post("/query", summary="Execute a natural language query")
async def execute_query(query_req: QueryRequest, db: AsyncSession = Depends(get_db)) -> QueryResponseSummary:
    # generate SQL query from LLM 
    try:
        sql_query = await get_sql_query(query_req.query)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating SQL: {str(e)}")
    try:
        result = await db.execute(text(sql_query))
        rows = result.fetchall()
        data = [dict(row._mapping) for row in rows]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error executing SQL: {str(e)}")

    # generate human-readable response from data returned by execution of LLM-generated SQL query 
    try:
        text_query = await get_text_response(str(data))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating TEXT: {str(e)}")
    return QueryResponseSummary(diseaseDB_response=text_query)


# modify endpoint 
@app.post("/modify", summary="Used for insertions and deletions.")
async def execute_query(query_req: QueryRequest, db: AsyncSession = Depends(get_db)) -> QueryResponseSummary:
    try:
        sql_query = await get_sql_query(query_req.query)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating SQL: {str(e)}")

    try:
        await db.execute(text(sql_query))
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Error executing SQL: {str(e)}")

    return QueryResponseSummary(diseaseDB_response="Operation completed.")