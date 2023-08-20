from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, String, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from typing import List
import requests  # Import correct du module requests

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Créer une connexion à la base de données SQLite
DATABASE_URL = "postgresql://root:toor@localhost:5432/db_bma"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    code = Column(String)

# Créer la table dans la base de données (exécuter ceci une seule fois pour créer la table)
Base.metadata.create_all(bind=engine)

PRIVATE_KEY = "671d0b23-8828-4f33-b1b1-5a673bcf23c8"

class UserAuthenticate(BaseModel):
    username: str
    code: str

@app.post('/authenticate')
async def authenticate(user: UserAuthenticate):
    # Vérifier si l'utilisateur existe dans la base de données
    db = SessionLocal()
    db_user = db.query(User).filter_by(username=user.username).first()

    if not db_user:
        # Si l'utilisateur n'existe pas, l'ajouter à la base de données
        db_user = User(username=user.username, code=user.code)
        db.add(db_user)
        db.commit()
        response = requests.put(
            'https://api.chatengine.io/users/',
            data={
                "username": user.username,
                "secret": user.username,
                "first_name": user.username,
            },
            headers={"Private-key": PRIVATE_KEY}
        )
        return response.json()

    # Vérifier si le code d'authentification est correct
    elif user.code != db_user.code:
        db.close()
        raise HTTPException(status_code=403, detail="Code d'authentification incorrect")
    
    db.close()

    # Si le code est correct, continuer avec le processus d'authentification avec ChatEngine
    response = requests.put(
        'https://api.chatengine.io/users/',
        data={
            "username": user.username,
            "secret": user.username,
            "first_name": user.username,
        },
        headers={"Private-key": PRIVATE_KEY}
    )

    return response.json()


# Modèle Pydantic pour représenter un utilisateur dans la réponse
class UserResponse(BaseModel):
    id: int
    username: str
    code: str

# Route pour récupérer tous les utilisateurs
@app.get('/users')
async def get_users():
    db = SessionLocal()
    users = db.query(User).all()
    db.close()
    return [{"id": user.id, "username": user.username, "code": user.code} for user in users]
