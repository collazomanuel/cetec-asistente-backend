
from settings import MONGODB_KEY, FRONTEND_URL, GOOGLE_CLIENT_ID

from datetime import datetime, timedelta, timezone
from enum import Enum
from uuid import uuid4

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.encoders import jsonable_encoder
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from pymongo import MongoClient

from google.oauth2 import id_token
from google.auth.transport import requests

DB_NAME = 'cetec-asistente'
USER_HISTORY_COLLECTION_NAME = 'UserHistory'

DATE_FORMAT = '%Y-%m-%d %H:%M'

class Question(BaseModel):
    text: str

class Answer(BaseModel):
    text: str

def create_app():
    app = FastAPI()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[FRONTEND_URL],
        allow_credentials=True,
        allow_methods=['*'],
        allow_headers=['*']
    )
    return app

def get_security():
    return HTTPBearer()

def get_database():
    client = MongoClient(MONGODB_KEY)
    return client[DB_NAME]

app = create_app()
security = get_security()
db = get_database()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        return id_token.verify_oauth2_token(credentials.credentials, requests.Request(), GOOGLE_CLIENT_ID)
    except ValueError:
        raise HTTPException(status_code = status.HTTP_401_UNAUTHORIZED, detail = 'Invalid authentication credentials')

@app.get('/history')
async def history(current_user: dict = Depends(get_current_user)):
    #history = list(db[USER_HISTORY_COLLECTION_NAME].find( {'user_id': current_user['sub'] }, {'_id': False}))
    return ({ "text": "Historial no disponible" })

@app.post('/ask')
async def ask(data: Question, current_user: dict = Depends(get_current_user)):
    #db[USER_HISTORY_COLLECTION_NAME].insert_one(jsonable_encoder( {'user_id': current_user['sub'], 'question': data.text} ))
    return({ "text": "Respuesta del asistente no disponible" })
