from fastapi import APIRouter, HTTPException
from typing import Dict
from .ollama_python_test import OllamaSQLQueryTool

router = APIRouter()
sql_tool = OllamaSQLQueryTool("mysql+pymysql://root:12345678@localhost:3306/new_db")

@router.post("/api/sql-query")
async def handle_sql_query(request: Dict[str, str]):
    try:
        question = request.get("question")
        if not question:
            raise HTTPException(status_code=400, detail="No question provided")
        
        result = sql_tool.query(question)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))