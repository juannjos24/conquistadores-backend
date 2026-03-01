from pydantic import BaseModel
from datetime import date, datetime
from typing import Optional


class AbrirSesionRequest(BaseModel):
    clase_id: int
    consejero_id: int


class SesionResponse(BaseModel):
    id: int
    clase_id: int
    consejero_id: int
    fecha_sesion: date
    estado: str
    abierta_en: datetime

    class Config:
        from_attributes = True


class RegistroItemRequest(BaseModel):
    miembro_id: int
    item_id: int
    cumplido: bool


class RegistroLoteRequest(BaseModel):
    sesion_id: int
    registros: list[RegistroItemRequest]


class VistoBuenoRequest(BaseModel):
    sesion_id: int
    consejero_id: int
