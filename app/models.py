from sqlalchemy import Column, Integer, String, Boolean, Date, DateTime, ForeignKey, CheckConstraint, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.config.database import Base

class Club(Base):
    __tablename__ = "club"
    __table_args__ = {"schema": "conquistadores"}

    id         = Column(Integer, primary_key=True)
    nombre     = Column(String(100), nullable=False)
    descripcion= Column(String)
    activo     = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    clases     = relationship("Clase", back_populates="club")

class Clase(Base):
    __tablename__ = "clase"
    __table_args__ = {"schema": "conquistadores"}

    id         = Column(Integer, primary_key=True)
    club_id    = Column(Integer, ForeignKey("conquistadores.club.id"))
    nombre     = Column(String(50), nullable=False)
    orden      = Column(Integer, nullable=False)
    activo     = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    club       = relationship("Club", back_populates="clases")
    miembros   = relationship("Miembro", back_populates="clase")

class Consejero(Base):
    __tablename__ = "consejero"
    __table_args__ = {"schema": "conquistadores"}

    id          = Column(Integer, primary_key=True)
    nombre      = Column(String(100), nullable=False)
    apellido    = Column(String(100), nullable=False)
    email       = Column(String(150), unique=True)
    codigo_hash = Column(String(255), nullable=False)
    activo      = Column(Boolean, default=True)
    created_at  = Column(DateTime, default=func.now())

class ConsejeroClase(Base):
    __tablename__ = "consejero_clase"
    __table_args__ = (
        UniqueConstraint("consejero_id", "clase_id"),
        {"schema": "conquistadores"}
    )

    id           = Column(Integer, primary_key=True)
    consejero_id = Column(Integer, ForeignKey("conquistadores.consejero.id"))
    clase_id     = Column(Integer, ForeignKey("conquistadores.clase.id"))
    es_principal = Column(Boolean, default=False)
    activo       = Column(Boolean, default=True)

class Miembro(Base):
    __tablename__ = "miembro"
    __table_args__ = {"schema": "conquistadores"}

    id         = Column(Integer, primary_key=True)
    nombre     = Column(String(100), nullable=False)
    apellido   = Column(String(100), nullable=False)
    fecha_nac  = Column(Date)
    clase_id   = Column(Integer, ForeignKey("conquistadores.clase.id"))
    activo     = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    clase      = relationship("Clase", back_populates="miembros")

class ItemEvaluacion(Base):
    __tablename__ = "item_evaluacion"
    __table_args__ = {"schema": "conquistadores"}

    id     = Column(Integer, primary_key=True)
    nombre = Column(String(100), nullable=False)
    orden  = Column(Integer, nullable=False)
    activo = Column(Boolean, default=True)

class SesionRegistro(Base):
    __tablename__ = "sesion_registro"
    __table_args__ = (
        UniqueConstraint("clase_id", "fecha_sesion"),
        {"schema": "conquistadores"}
    )

    id                       = Column(Integer, primary_key=True)
    clase_id                 = Column(Integer, ForeignKey("conquistadores.clase.id"))
    consejero_id             = Column(Integer, ForeignKey("conquistadores.consejero.id"))
    fecha_sesion             = Column(Date, nullable=False)
    abierta_en               = Column(DateTime, nullable=False)
    cerrada_en               = Column(DateTime)
    estado                   = Column(String(20), default="abierta")
    visto_bueno_consejero_id = Column(Integer, ForeignKey("conquistadores.consejero.id"), nullable=True)
    visto_bueno_en           = Column(DateTime, nullable=True)
    registros                = relationship("RegistroItem", back_populates="sesion")

class RegistroItem(Base):
    __tablename__ = "registro_item"
    __table_args__ = (
        UniqueConstraint("sesion_id", "miembro_id", "item_id"),
        {"schema": "conquistadores"}
    )

    id         = Column(Integer, primary_key=True)
    sesion_id  = Column(Integer, ForeignKey("conquistadores.sesion_registro.id"))
    miembro_id = Column(Integer, ForeignKey("conquistadores.miembro.id"))
    item_id    = Column(Integer, ForeignKey("conquistadores.item_evaluacion.id"))
    cumplido   = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())
    sesion     = relationship("SesionRegistro", back_populates="registros")