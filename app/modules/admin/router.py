from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from typing import Optional
import bcrypt
import os

from app.config.database import get_db
from app.models import Consejero, ConsejeroClase, Miembro, Clase
from pydantic import BaseModel

router = APIRouter(prefix="/admin", tags=["Admin"])

SUPER_ADMIN_CODE = os.getenv("SUPER_ADMIN_CODE", "admin2026")


def _verificar_admin(x_admin_code: Optional[str] = Header(None)):
    if x_admin_code != SUPER_ADMIN_CODE:
        raise HTTPException(status_code=403, detail="Código de administrador incorrecto.")


# ── Auth ──────────────────────────────────────────────

class AdminAuthRequest(BaseModel):
    codigo: str


@router.post("/auth")
def verificar_admin(req: AdminAuthRequest):
    if req.codigo != SUPER_ADMIN_CODE:
        raise HTTPException(status_code=403, detail="Código incorrecto.")
    return {"ok": True}


# ── Consejeros ────────────────────────────────────────

class CrearConsejeroRequest(BaseModel):
    nombre: str
    apellido: str
    email: Optional[str] = None
    codigo: str
    clase_id: int
    es_principal: bool = False


@router.get("/consejeros", dependencies=[Depends(_verificar_admin)])
def listar_consejeros(db: Session = Depends(get_db)):
    rows = (
        db.query(Consejero, ConsejeroClase, Clase)
        .join(ConsejeroClase, ConsejeroClase.consejero_id == Consejero.id)
        .join(Clase, Clase.id == ConsejeroClase.clase_id)
        .filter(Consejero.activo == True)
        .order_by(Clase.orden, Consejero.apellido)
        .all()
    )
    return [
        {
            "id": c.id,
            "nombre": c.nombre,
            "apellido": c.apellido,
            "email": c.email,
            "clase_id": cc.clase_id,
            "clase_nombre": cl.nombre,
            "es_principal": cc.es_principal,
        }
        for c, cc, cl in rows
    ]


@router.post("/consejero", dependencies=[Depends(_verificar_admin)])
def crear_consejero(req: CrearConsejeroRequest, db: Session = Depends(get_db)):
    clase = db.query(Clase).filter(Clase.id == req.clase_id, Clase.activo == True).first()
    if not clase:
        raise HTTPException(status_code=404, detail="Clase no encontrada.")

    if req.email:
        existe = db.query(Consejero).filter(Consejero.email == req.email).first()
        if existe:
            raise HTTPException(status_code=400, detail="Ya existe un consejero con ese email.")

    hash_codigo = bcrypt.hashpw(req.codigo.encode(), bcrypt.gensalt()).decode()

    nuevo = Consejero(
        nombre=req.nombre,
        apellido=req.apellido,
        email=req.email or None,
        codigo_hash=hash_codigo,
    )
    db.add(nuevo)
    db.flush()

    db.add(ConsejeroClase(
        consejero_id=nuevo.id,
        clase_id=req.clase_id,
        es_principal=req.es_principal,
    ))
    db.commit()

    return {"ok": True, "id": nuevo.id, "nombre": nuevo.nombre}


class ActualizarConsejeroRequest(BaseModel):
    nombre: str
    apellido: str
    email: Optional[str] = None
    codigo: Optional[str] = None   # solo si quiere cambiar
    clase_id: int
    es_principal: bool = False


@router.put("/consejero/{consejero_id}", dependencies=[Depends(_verificar_admin)])
def actualizar_consejero(consejero_id: int, req: ActualizarConsejeroRequest, db: Session = Depends(get_db)):
    c = db.query(Consejero).filter(Consejero.id == consejero_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Consejero no encontrado.")
    c.nombre   = req.nombre
    c.apellido = req.apellido
    c.email    = req.email or None
    if req.codigo and req.codigo.strip():
        c.codigo_hash = bcrypt.hashpw(req.codigo.encode(), bcrypt.gensalt()).decode()
    # Actualizar asignación de clase
    cc = db.query(ConsejeroClase).filter(ConsejeroClase.consejero_id == consejero_id).first()
    if cc:
        cc.clase_id     = req.clase_id
        cc.es_principal = req.es_principal
    db.commit()
    return {"ok": True}


@router.delete("/consejero/{consejero_id}", dependencies=[Depends(_verificar_admin)])
def desactivar_consejero(consejero_id: int, db: Session = Depends(get_db)):
    c = db.query(Consejero).filter(Consejero.id == consejero_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Consejero no encontrado.")
    c.activo = False
    db.commit()
    return {"ok": True}


# ── Miembros ──────────────────────────────────────────

class CrearMiembroRequest(BaseModel):
    nombre: str
    apellido: str
    clase_id: int
    fecha_nac: Optional[str] = None


@router.get("/miembros", dependencies=[Depends(_verificar_admin)])
def listar_miembros(db: Session = Depends(get_db)):
    rows = (
        db.query(Miembro, Clase)
        .join(Clase, Clase.id == Miembro.clase_id)
        .filter(Miembro.activo == True)
        .order_by(Clase.orden, Miembro.apellido)
        .all()
    )
    return [
        {
            "id": m.id,
            "nombre": m.nombre,
            "apellido": m.apellido,
            "clase_id": m.clase_id,
            "clase_nombre": cl.nombre,
        }
        for m, cl in rows
    ]


@router.post("/miembro", dependencies=[Depends(_verificar_admin)])
def crear_miembro(req: CrearMiembroRequest, db: Session = Depends(get_db)):
    clase = db.query(Clase).filter(Clase.id == req.clase_id, Clase.activo == True).first()
    if not clase:
        raise HTTPException(status_code=404, detail="Clase no encontrada.")

    nuevo = Miembro(
        nombre=req.nombre,
        apellido=req.apellido,
        clase_id=req.clase_id,
    )
    db.add(nuevo)
    db.commit()
    return {"ok": True, "id": nuevo.id}


class ActualizarMiembroRequest(BaseModel):
    nombre: str
    apellido: str
    clase_id: int


@router.put("/miembro/{miembro_id}", dependencies=[Depends(_verificar_admin)])
def actualizar_miembro(miembro_id: int, req: ActualizarMiembroRequest, db: Session = Depends(get_db)):
    m = db.query(Miembro).filter(Miembro.id == miembro_id).first()
    if not m:
        raise HTTPException(status_code=404, detail="Miembro no encontrado.")
    m.nombre   = req.nombre
    m.apellido = req.apellido
    m.clase_id = req.clase_id
    db.commit()
    return {"ok": True}


@router.delete("/miembro/{miembro_id}", dependencies=[Depends(_verificar_admin)])
def desactivar_miembro(miembro_id: int, db: Session = Depends(get_db)):
    m = db.query(Miembro).filter(Miembro.id == miembro_id).first()
    if not m:
        raise HTTPException(status_code=404, detail="Miembro no encontrado.")
    m.activo = False
    db.commit()
    return {"ok": True}
