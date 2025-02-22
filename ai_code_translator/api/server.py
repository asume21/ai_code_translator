"""
API server for AI Code Translator service
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import APIKeyHeader
from pydantic import BaseModel
import sqlite3
import uuid
from datetime import datetime
from typing import Optional

app = FastAPI(title="AI Code Translator API")

# API key header
api_key_header = APIKeyHeader(name="X-API-Key")

class TranslationRequest(BaseModel):
    source_code: str
    source_lang: str
    target_lang: str

class TranslationResponse(BaseModel):
    translated_code: str
    request_id: str
    characters_processed: int

def verify_api_key(api_key: str = Depends(api_key_header)):
    """Verify API key and check usage limits."""
    conn = sqlite3.connect('api_keys.db')
    cursor = conn.cursor()
    
    # Check if API key exists and get tier
    cursor.execute(
        "SELECT tier, monthly_limit, used_requests FROM api_keys WHERE key = ?", 
        (api_key,)
    )
    result = cursor.fetchone()
    
    if not result:
        raise HTTPException(status_code=401, detail="Invalid API key")
        
    tier, monthly_limit, used_requests = result
    
    # Check usage limits
    if used_requests >= monthly_limit:
        raise HTTPException(status_code=429, detail="Monthly limit exceeded")
    
    conn.close()
    return {"tier": tier, "api_key": api_key}

@app.post("/translate", response_model=TranslationResponse)
async def translate_code(
    request: TranslationRequest,
    api_info: dict = Depends(verify_api_key)
):
    """Translate code between programming languages."""
    try:
        # Generate unique request ID
        request_id = str(uuid.uuid4())
        
        # Record API usage
        conn = sqlite3.connect('api_keys.db')
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE api_keys SET used_requests = used_requests + 1 WHERE key = ?",
            (api_info["api_key"],)
        )
        conn.commit()
        conn.close()
        
        # TODO: Implement actual translation using the model
        # For now, return dummy response
        return TranslationResponse(
            translated_code="// Translated code will appear here",
            request_id=request_id,
            characters_processed=len(request.source_code)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/usage")
async def get_usage(api_info: dict = Depends(verify_api_key)):
    """Get current API usage statistics."""
    conn = sqlite3.connect('api_keys.db')
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT monthly_limit, used_requests FROM api_keys WHERE key = ?",
        (api_info["api_key"],)
    )
    monthly_limit, used_requests = cursor.fetchone()
    
    conn.close()
    
    return {
        "tier": api_info["tier"],
        "monthly_limit": monthly_limit,
        "used_requests": used_requests,
        "remaining_requests": monthly_limit - used_requests
    }
