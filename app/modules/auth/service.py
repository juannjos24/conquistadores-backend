from sqlalchemy.orm import Session
from app.models import Consejero, ConsejeroClase
import bcrypt

def verificar_codigo(db: Session, codigo: str, clase_id: int):
    # Traer todos los consejeros activos de esa clase
    consejeros_clase = (
        db.query(ConsejeroClase)
        .filter(
            ConsejeroClase.clase_id == clase_id,
            ConsejeroClase.activo == True
        )
        .all()
    )

    if not consejeros_clase:
        return None

    # Verificar el código contra cada consejero de la clase
    for cc in consejeros_clase:
        consejero = db.query(Consejero).filter(
            Consejero.id == cc.consejero_id,
            Consejero.activo == True
        ).first()

        if consejero and bcrypt.checkpw(
            codigo.encode("utf-8"),
            consejero.codigo_hash.encode("utf-8")
        ):
            return {
                "id": consejero.id,
                "nombre": consejero.nombre,
                "apellido": consejero.apellido,
                "email": consejero.email,
                "clase_id": clase_id,
                "es_principal": cc.es_principal
            }

    return None