from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import date, datetime, time
import pytz

from sqlalchemy import func
from app.config.database import get_db
from app.models import SesionRegistro, RegistroItem, ConsejeroClase, ItemEvaluacion
from app.modules.registro.schemas import (
    AbrirSesionRequest,
    SesionResponse,
    RegistroLoteRequest,
    VistoBuenoRequest,
)

router = APIRouter(prefix="/registro", tags=["Registro"])

ZONA_HORARIA = pytz.timezone("America/Mexico_City")
HORA_APERTURA = time(12, 0)
HORA_CIERRE = time(19, 0)


def _verificar_ventana_horaria():
    ahora = datetime.now(ZONA_HORARIA)
    # if ahora.weekday() !=5:  # 5 = sábado
    #     raise HTTPException(
    #         status_code=403,
    #         detail="El registro solo está disponible los sábados."
    #     )
    # hora_actual = ahora.time()
    # if not (HORA_APERTURA <= hora_actual <= HORA_CIERRE):
    #     raise HTTPException(
    #         status_code=403,
    #         detail="El registro solo está disponible los sábados de 12:00 pm a 7:00 pm."
    #     )


@router.post("/sesion/abrir", response_model=SesionResponse)
def abrir_sesion(request: AbrirSesionRequest, db: Session = Depends(get_db)):
    _verificar_ventana_horaria()

    asignacion = db.query(ConsejeroClase).filter(
        ConsejeroClase.consejero_id == request.consejero_id,
        ConsejeroClase.clase_id == request.clase_id,
        ConsejeroClase.activo == True
    ).first()

    if not asignacion:
        raise HTTPException(status_code=403, detail="El consejero no está asignado a esta clase.")

    hoy = date.today()
    sesion_existente = db.query(SesionRegistro).filter(
        SesionRegistro.clase_id == request.clase_id,
        SesionRegistro.fecha_sesion == hoy
    ).first()

    if sesion_existente:
        return sesion_existente

    nueva_sesion = SesionRegistro(
        clase_id=request.clase_id,
        consejero_id=request.consejero_id,
        fecha_sesion=hoy,
        abierta_en=datetime.now(),
        estado="abierta",
    )
    db.add(nueva_sesion)
    db.commit()
    db.refresh(nueva_sesion)
    return nueva_sesion


@router.get("/sesion/{clase_id}/hoy")
def obtener_sesion_hoy(clase_id: int, db: Session = Depends(get_db)):
    hoy = date.today()
    sesion = db.query(SesionRegistro).filter(
        SesionRegistro.clase_id == clase_id,
        SesionRegistro.fecha_sesion == hoy
    ).first()
    if not sesion:
        return None
    return {
        "id": sesion.id,
        "clase_id": sesion.clase_id,
        "consejero_id": sesion.consejero_id,
        "fecha_sesion": sesion.fecha_sesion,
        "estado": sesion.estado,
        "visto_bueno_consejero_id": sesion.visto_bueno_consejero_id,
    }


@router.get("/sesion/{sesion_id}/detalle")
def obtener_detalle_sesion(sesion_id: int, db: Session = Depends(get_db)):
    registros = (
        db.query(RegistroItem)
        .filter(RegistroItem.sesion_id == sesion_id)
        .all()
    )
    return [
        {
            "miembro_id": r.miembro_id,
            "item_id": r.item_id,
            "cumplido": r.cumplido,
        }
        for r in registros
    ]


@router.post("/guardar")
def guardar_registros(request: RegistroLoteRequest, db: Session = Depends(get_db)):
    _verificar_ventana_horaria()

    sesion = db.query(SesionRegistro).filter(
        SesionRegistro.id == request.sesion_id,
        SesionRegistro.estado == "abierta"
    ).first()

    if not sesion:
        raise HTTPException(status_code=404, detail="Sesión no encontrada o ya cerrada.")

    for reg in request.registros:
        existente = db.query(RegistroItem).filter(
            RegistroItem.sesion_id == request.sesion_id,
            RegistroItem.miembro_id == reg.miembro_id,
            RegistroItem.item_id == reg.item_id,
        ).first()

        if existente:
            existente.cumplido = reg.cumplido
        else:
            db.add(RegistroItem(
                sesion_id=request.sesion_id,
                miembro_id=reg.miembro_id,
                item_id=reg.item_id,
                cumplido=reg.cumplido,
            ))

    db.commit()
    return {"ok": True, "guardados": len(request.registros)}


@router.post("/sesion/cerrar")
def cerrar_sesion(sesion_id: int, db: Session = Depends(get_db)):
    sesion = db.query(SesionRegistro).filter(SesionRegistro.id == sesion_id).first()
    if not sesion:
        raise HTTPException(status_code=404, detail="Sesión no encontrada.")
    sesion.estado = "cerrada"
    sesion.cerrada_en = datetime.now()
    db.commit()
    return {"ok": True}


@router.post("/visto-bueno")
def dar_visto_bueno(request: VistoBuenoRequest, db: Session = Depends(get_db)):
    sesion = db.query(SesionRegistro).filter(SesionRegistro.id == request.sesion_id).first()
    if not sesion:
        raise HTTPException(status_code=404, detail="Sesión no encontrada.")

    if sesion.consejero_id == request.consejero_id:
        raise HTTPException(status_code=400, detail="No puedes dar visto bueno a tu propio registro.")

    asignacion = db.query(ConsejeroClase).filter(
        ConsejeroClase.consejero_id == request.consejero_id,
        ConsejeroClase.clase_id == sesion.clase_id,
        ConsejeroClase.activo == True
    ).first()

    if not asignacion:
        raise HTTPException(status_code=403, detail="No tienes asignación en esta clase.")

    sesion.visto_bueno_consejero_id = request.consejero_id
    sesion.visto_bueno_en = datetime.now()
    db.commit()
    return {"ok": True}


@router.get("/historial/{clase_id}")
def historial_clase(clase_id: int, db: Session = Depends(get_db)):
    total_items = db.query(func.count(ItemEvaluacion.id)).filter(ItemEvaluacion.activo == True).scalar() or 1

    sesiones = (
        db.query(SesionRegistro)
        .filter(SesionRegistro.clase_id == clase_id)
        .order_by(SesionRegistro.fecha_sesion.desc())
        .limit(10)
        .all()
    )

    resultado = []
    for s in sesiones:
        total = db.query(func.count(RegistroItem.id)).filter(
            RegistroItem.sesion_id == s.id
        ).scalar() or 0
        cumplidos = db.query(func.count(RegistroItem.id)).filter(
            RegistroItem.sesion_id == s.id,
            RegistroItem.cumplido == True
        ).scalar() or 0
        porcentaje = round((cumplidos / (total or 1)) * 100)

        resultado.append({
            "sesion_id": s.id,
            "fecha": s.fecha_sesion.isoformat(),
            "estado": s.estado,
            "porcentaje": porcentaje,
            "cumplidos": cumplidos,
            "total": total,
            "visto_bueno": s.visto_bueno_consejero_id is not None,
        })

    return resultado
