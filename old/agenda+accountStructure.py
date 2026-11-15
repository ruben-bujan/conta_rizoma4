"""
FUNCIONALIDAD DEL MÓDULO:
Estructura de base de datos para un sistema contable y de agenda.
"""
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Table
from sqlalchemy.orm import relationship, declarative_base

# Configuración de la base de datos SQLite local
SQLALCHEMY_DATABASE_URL = "sqlite:///./contabilidad.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
Base = declarative_base()

# ==========================================
# 1. CONTABILIDAD (Niveles 1 al 6)
# ==========================================
class Nivel1(Base):
    __tablename__ = 'nivel1'
    id = Column(Integer, primary_key=True, index=True)
    codigo = Column(String(10), nullable=False)
    nombre = Column(String(100), nullable=False)
    niveles2 = relationship("Nivel2", back_populates="nivel1", cascade="all, delete-orphan")

class Nivel2(Base):
    __tablename__ = 'nivel2'
    id = Column(Integer, primary_key=True, index=True)
    codigo = Column(String(10), nullable=False)
    nombre = Column(String(100), nullable=False)
    # Cambiado a nullable=True
    nivel1_id = Column(Integer, ForeignKey('nivel1.id', ondelete='CASCADE'), nullable=True)
    nivel1 = relationship("Nivel1", back_populates="niveles2")
    niveles3 = relationship("Nivel3", back_populates="nivel2", cascade="all, delete-orphan")

class Nivel3(Base):
    __tablename__ = 'nivel3'
    id = Column(Integer, primary_key=True, index=True)
    codigo = Column(String(10), nullable=False)
    nombre = Column(String(100), nullable=False)
    # Cambiado a nullable=True
    nivel2_id = Column(Integer, ForeignKey('nivel2.id', ondelete='CASCADE'), nullable=True)
    nivel2 = relationship("Nivel2", back_populates="niveles3")
    niveles4 = relationship("Nivel4", back_populates="nivel3", cascade="all, delete-orphan")

class Nivel4(Base):
    __tablename__ = 'nivel4'
    id = Column(Integer, primary_key=True, index=True)
    codigo = Column(String(10), nullable=False)
    nombre = Column(String(100), nullable=False)
    # Cambiado a nullable=True
    nivel3_id = Column(Integer, ForeignKey('nivel3.id', ondelete='CASCADE'), nullable=True)
    nivel3 = relationship("Nivel3", back_populates="niveles4")
    niveles5 = relationship("Nivel5", back_populates="nivel4", cascade="all, delete-orphan")

class Nivel5(Base):
    __tablename__ = 'nivel5'
    id = Column(Integer, primary_key=True, index=True)
    codigo = Column(String(10), nullable=False)
    nombre = Column(String(100), nullable=False)
    # Cambiado a nullable=True
    nivel4_id = Column(Integer, ForeignKey('nivel4.id', ondelete='CASCADE'), nullable=True)
    nivel4 = relationship("Nivel4", back_populates="niveles5")
    niveles6 = relationship("Nivel6", back_populates="nivel5", cascade="all, delete-orphan")

class Nivel6(Base):
    __tablename__ = 'nivel6'
    id = Column(Integer, primary_key=True, index=True)
    codigo = Column(String(15), nullable=False)
    nombre = Column(String(100), nullable=False)
    # Cambiado a nullable=True
    nivel5_id = Column(Integer, ForeignKey('nivel5.id', ondelete='CASCADE'), nullable=True)
    nivel5 = relationship("Nivel5", back_populates="niveles6")
    personas_fisicas = relationship("PersonaFisica", back_populates="cuenta")
    personas_juridicas = relationship("PersonaJuridica", back_populates="cuenta")

# ==========================================
# 2. AGENDA (Personas Físicas y Jurídicas)
# ==========================================
personas_fisicas_juridicas = Table(
    'personas_fisicas_juridicas',
    Base.metadata,
    Column('persona_fisica_id', Integer, ForeignKey('personas_fisicas.id', ondelete='CASCADE'), primary_key=True),
    Column('persona_juridica_id', Integer, ForeignKey('personas_juridicas.id', ondelete='CASCADE'), primary_key=True),
    Column('cargo_o_relacion', String(100))
)

class PersonaFisica(Base):
    __tablename__ = 'personas_fisicas'
    id = Column(Integer, primary_key=True, index=True)
    nif = Column(String(20), unique=True, nullable=False)
    nombre = Column(String(100), nullable=False)
    apellidos = Column(String(150), nullable=False)
    cuenta_id = Column(Integer, ForeignKey('nivel6.id', ondelete='SET NULL'), nullable=True)
    cuenta = relationship("Nivel6", back_populates="personas_fisicas")
    empresas_relacionadas = relationship("PersonaJuridica", secondary=personas_fisicas_juridicas, back_populates="personas_relacionadas")

class PersonaJuridica(Base):
    __tablename__ = 'personas_juridicas'
    id = Column(Integer, primary_key=True, index=True)
    cif = Column(String(20), unique=True, nullable=False)
    razon_social = Column(String(200), nullable=False)
    cuenta_id = Column(Integer, ForeignKey('nivel6.id', ondelete='SET NULL'), nullable=True)
    cuenta = relationship("Nivel6", back_populates="personas_juridicas")
    personas_relacionadas = relationship("PersonaFisica", secondary=personas_fisicas_juridicas, back_populates="empresas_relacionadas")

if __name__ == "__main__":
    print("Generando tablas en la base de datos SQLite (contabilidad.db)...")
    Base.metadata.create_all(bind=engine)
    print("¡Tablas creadas con éxito!")