from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.config.database import get_db
from app.modules.auth.schemas import VerificarCodigoRequest, ConsejeroResponse
from app.modules.auth import service

router = APIRouter(prefix="/auth", tags=["Auth"])

@router.post("/verificar-codigo", response_model=ConsejeroResponse)
def verificar_codigo(
    request: VerificarCodigoRequest,
    db: Session = Depends(get_db)
):
    consejero = service.verificar_codigo(db, request.codigo, request.clase_id)

    if not consejero:
        raise HTTPException(
            status_code=401,
            detail="Código incorrecto o consejero no asignado a esta clase"
        )

    return consejero