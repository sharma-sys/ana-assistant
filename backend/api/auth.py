from fastapi import Header, HTTPException
import os

def verify_api_key(x_api_key: str = Header(None)):
    api_key = os.getenv("ANA_API_KEY")
    if not x_api_key or x_api_key != api_key:
        raise HTTPException(status_code=401, detail="Invalid or missing X-API-Key header")
