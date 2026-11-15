"""
FUNCIONALIDAD DEL MÓDULO:
API Backend (FastAPI) para la gestión de la Agenda (Personas Físicas y Jurídicas)
y la adscripción de cuentas contables (Niveles 4, 5 y 6).
"""
import importlib.util
import sys
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy import or_
from pydantic import BaseModel

# ==========================================
# IMPORTACIÓN DINÁMICA DE MODELOS
# ==========================================
file_path = "agenda+accountStructure.py"
module_name = "agenda_accountStructure"

spec = importlib.util.spec_from_file_location(module_name, file_path)
models = importlib.util.module_from_spec(spec)
sys.modules[module_name] = models
spec.loader.exec_module(models)

# ==========================================
# CONFIGURACIÓN DE FASTAPI Y BASE DE DATOS
# ==========================================
app = FastAPI(title="API Agenda y Contabilidad")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=models.engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ==========================================
# ESQUEMAS PYDANTIC
# ==========================================
class PersonaFisicaCreate(BaseModel):
    nif: str
    nombre: str
    apellidos: str

class PersonaJuridicaCreate(BaseModel):
    cif: str
    razon_social: str

class AdscribirCuenta(BaseModel):
    persona_id: int
    tipo_persona: str
    codigo_cuenta: str
    descripcion_cuenta: str

# ==========================================
# ENDPOINTS: AGENDA
# ==========================================
@app.get("/api/personas/buscar")
def buscar_personas(q: str = "", db: Session = Depends(get_db)):
    fisicas = db.query(models.PersonaFisica).filter(
        or_(
            models.PersonaFisica.nif.ilike(f"%{q}%"),
            models.PersonaFisica.nombre.ilike(f"%{q}%"),
            models.PersonaFisica.apellidos.ilike(f"%{q}%"),
            models.PersonaFisica.id == (int(q) if q.isdigit() else -1)
        )
    ).all()
    
    juridicas = db.query(models.PersonaJuridica).filter(
        or_(
            models.PersonaJuridica.cif.ilike(f"%{q}%"),
            models.PersonaJuridica.razon_social.ilike(f"%{q}%"),
            models.PersonaJuridica.id == (int(q) if q.isdigit() else -1)
        )
    ).all()
    
    resultados = []
    for p in fisicas:
        cuenta = db.query(models.Nivel6).filter_by(id=p.cuenta_id).first() if p.cuenta_id else None
        resultados.append({
            "id": p.id,
            "tipo": "fisica",
            "identificador": p.nif,
            "denominacion": f"{p.nombre} {p.apellidos}",
            "cuenta": cuenta.codigo if cuenta else "Sin cuenta"
        })
        
    for p in juridicas:
        cuenta = db.query(models.Nivel6).filter_by(id=p.cuenta_id).first() if p.cuenta_id else None
        resultados.append({
            "id": p.id,
            "tipo": "juridica",
            "identificador": p.cif,
            "denominacion": p.razon_social,
            "cuenta": cuenta.codigo if cuenta else "Sin cuenta"
        })
        
    return resultados

@app.post("/api/personas/fisica")
def crear_fisica(persona: PersonaFisicaCreate, db: Session = Depends(get_db)):
    db_persona = models.PersonaFisica(**persona.dict())
    db.add(db_persona)
    db.commit()
    return {"mensaje": "Persona física creada", "id": db_persona.id}

@app.post("/api/personas/juridica")
def crear_juridica(persona: PersonaJuridicaCreate, db: Session = Depends(get_db)):
    db_persona = models.PersonaJuridica(**persona.dict())
    db.add(db_persona)
    db.commit()
    return {"mensaje": "Persona jurídica creada", "id": db_persona.id}

# ==========================================
# ENDPOINTS: ADSCRIPCIÓN DE CUENTAS
# ==========================================
@app.post("/api/agenda/adscribir_cuenta")
def adscribir_cuenta(req: AdscribirCuenta, db: Session = Depends(get_db)):
    if len(req.codigo_cuenta) < 6:
        raise HTTPException(status_code=400, detail="El código de cuenta debe tener al menos 6 dígitos.")
        
    codigo_n4 = req.codigo_cuenta[:4]
    codigo_n5 = req.codigo_cuenta[:5]
    
    nivel4 = db.query(models.Nivel4).filter_by(codigo=codigo_n4).first()
    if not nivel4:
        raise HTTPException(status_code=404, detail=f"No existe la cuenta de Nivel 4 ({codigo_n4}). Debe crearla primero.")
        
    nivel5 = db.query(models.Nivel5).filter_by(codigo=codigo_n5).first()
    if not nivel5:
        nivel5 = models.Nivel5(codigo=codigo_n5, nombre=nivel4.nombre, nivel4_id=nivel4.id)
        db.add(nivel5)
        db.flush()
        
    nivel6 = db.query(models.Nivel6).filter_by(codigo=req.codigo_cuenta).first()
    if not nivel6:
        nivel6 = models.Nivel6(codigo=req.codigo_cuenta, nombre=req.descripcion_cuenta, nivel5_id=nivel5.id)
        db.add(nivel6)
        db.flush()
        
    if req.tipo_persona == 'fisica':
        persona = db.query(models.PersonaFisica).filter_by(id=req.persona_id).first()
    elif req.tipo_persona == 'juridica':
        persona = db.query(models.PersonaJuridica).filter_by(id=req.persona_id).first()
    else:
        raise HTTPException(status_code=400, detail="Tipo de persona inválido.")
        
    if not persona:
        raise HTTPException(status_code=404, detail="Persona no encontrada en la agenda.")
        
    persona.cuenta_id = nivel6.id
    db.commit()
    
    return {
        "mensaje": "Cuenta adscrita correctamente.",
        "cuenta": {"codigo": nivel6.codigo, "nombre": nivel6.nombre}
    }

if __name__ == "__main__":
    import uvicorn
    print("Iniciando servidor API en http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)