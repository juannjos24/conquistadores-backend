from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config.database import engine, Base
import app.models
from app.modules.auth.router import router as auth_router  # ← agregar

app = FastAPI(title="Conquistadores API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)  # ← agregar

@app.on_event("startup")
def startup():
    #Base.metadata.create_all(bind=engine, checkfirst=True)
    print("✅ Conexión a PostgreSQL exitosa")

@app.get("/")
def root():
    return {"message": "Conquistadores API corriendo 🚀"}