from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.config.database import get_db
from app.models import Clase, Miembro, ItemEvaluacion

router = APIRouter(prefix="/clases", tags=["Clases"])


@router.get("/")
def listar_clases(db: Session = Depends(get_db)):
    clases = db.query(Clase).filter(Clase.activo == True).order_by(Clase.orden).all()
    return [{"id": c.id, "nombre": c.nombre, "orden": c.orden} for c in clases]


@router.get("/{clase_id}/miembros")
def listar_miembros(clase_id: int, db: Session = Depends(get_db)):
    miembros = (
        db.query(Miembro)
        .filter(Miembro.clase_id == clase_id, Miembro.activo == True)
        .order_by(Miembro.apellido, Miembro.nombre)
        .all()
    )
    return [
        {"id": m.id, "nombre": m.nombre, "apellido": m.apellido}
        for m in miembros
    ]


@router.get("/items")
def listar_items(db: Session = Depends(get_db)):
    items = db.query(ItemEvaluacion).filter(ItemEvaluacion.activo == True).order_by(ItemEvaluacion.orden).all()
    return [{"id": i.id, "nombre": i.nombre, "orden": i.orden} for i in items]
