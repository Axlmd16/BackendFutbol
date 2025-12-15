from sqlalchemy import Column, String, Integer, ForeignKey
from app.models.base import BaseModel
from sqlalchemy.orm import relationship


class Representative(BaseModel):
    """
    Representante legal de un deportista menor de edad.
    
    Almacena la información completa del tutor o padre/madre
    que autoriza la participación del menor en la escuela de fútbol.
    """

    __tablename__ = "representatives"
    
    first_name = Column(String(100), nullable=False, comment="Nombres del representante")
    last_name = Column(String(100), nullable=False, comment="Apellidos del representante")
    dni = Column(String(20), unique=True, index=True, nullable=False, comment="Documento de identidad único")
    address = Column(String(255), nullable=False, comment="Dirección de domicilio")
    phone = Column(String(20), nullable=False, comment="Número de teléfono de contacto")
    email = Column(String(100), nullable=False, comment="Correo electrónico")
    
    # Relaciones
    athletes = relationship(
        "Athlete",
        back_populates="representative",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self):
        return f"<Representative(id={self.id}, dni='{self.dni}', name='{self.first_name} {self.last_name}')>"
