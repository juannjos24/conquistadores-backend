from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config.database import engine, Base
import app.models
from app.modules.auth.router import router as auth_router
from app.modules.clases.router import router as clases_router
from app.modules.registro.router import router as registro_router
from app.modules.dashboard.router import router as dashboard_router
from app.modules.admin.router import router as admin_router

app = FastAPI(title="Conquistadores API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(clases_router)
app.include_router(registro_router)
app.include_router(dashboard_router)
app.include_router(admin_router)

@app.on_event("startup")
def startup():
    print("✅ Conexión a PostgreSQL exitosa")

@app.get("/")
def root():
    return {"message": "Conquistadores API corriendo 🚀"}
