from pydantic import BaseModel

class VerificarCodigoRequest(BaseModel):
    codigo: str
    clase_id: int

class ConsejeroResponse(BaseModel):
    id: int
    nombre: str
    apellido: str
    email: str | None
    clase_id: int
    es_principal: bool

    class Config:
        from_attributes = True