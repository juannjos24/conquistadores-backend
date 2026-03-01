from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.config.database import get_db
from app.models import Clase, Miembro, SesionRegistro, RegistroItem, ItemEvaluacion

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/progreso")
def obtener_progreso(db: Session = Depends(get_db)):
    clases = db.query(Clase).filter(Clase.activo == True).order_by(Clase.orden).all()
    total_items = db.query(func.count(ItemEvaluacion.id)).filter(ItemEvaluacion.activo == True).scalar() or 1

    resultado = []

    for clase in clases:
        miembros = db.query(Miembro).filter(
            Miembro.clase_id == clase.id,
            Miembro.activo == True
        ).all()

        total_sesiones = db.query(func.count(SesionRegistro.id)).filter(
            SesionRegistro.clase_id == clase.id
        ).scalar() or 0

        miembros_data = []
        suma_clase = 0

        for miembro in miembros:
            # Contar cuántos items ha cumplido en total sobre todas las sesiones
            cumplidos = db.query(func.count(RegistroItem.id)).join(
                SesionRegistro, SesionRegistro.id == RegistroItem.sesion_id
            ).filter(
                SesionRegistro.clase_id == clase.id,
                RegistroItem.miembro_id == miembro.id,
                RegistroItem.cumplido == True
            ).scalar() or 0

            total_posible = total_items * total_sesiones if total_sesiones > 0 else total_items
            porcentaje = round((cumplidos / total_posible) * 100) if total_posible > 0 else 0

            miembros_data.append({
                "miembro_id": miembro.id,
                "nombre": miembro.nombre,
                "apellido": miembro.apellido,
                "porcentaje": porcentaje,
            })
            suma_clase += porcentaje

        promedio_clase = round(suma_clase / len(miembros)) if miembros else 0

        resultado.append({
            "clase_id": clase.id,
            "clase_nombre": clase.nombre,
            "total_miembros": len(miembros),
            "total_sesiones": total_sesiones,
            "promedio_cumplimiento": promedio_clase,
            "miembros": sorted(miembros_data, key=lambda x: x["apellido"]),
        })

    return resultado
