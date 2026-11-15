"""
FUNCIONALIDAD DEL MÓDULO:
Script de migración (ETL) para traspasar los datos del plan contable (Niveles 1 al 6)
desde MariaDB hacia SQLite local, con mapeo de nombres de columnas.
"""
import importlib.util
import sys
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# ==========================================
# IMPORTACIÓN DINÁMICA DEL MÓDULO
# ==========================================
file_path = "agenda+accountStructure.py"
module_name = "agenda_accountStructure"

spec = importlib.util.spec_from_file_location(module_name, file_path)
models = importlib.util.module_from_spec(spec)
sys.modules[module_name] = models
spec.loader.exec_module(models)

# ==========================================
# CONFIGURACIÓN DE CONEXIONES
# ==========================================
MARIADB_USER = os.environ.get("MARIADB_USER", "ruben")
MARIADB_PASSWORD = os.environ.get("MARIADB_PASSWORD", "")
if not MARIADB_PASSWORD:
    raise ValueError(
        "Falta MARIADB_PASSWORD. Exporta la variable antes de ejecutar:\n"
        "  export MARIADB_PASSWORD='tu_contraseña'"
    )
MARIADB_HOST = os.environ.get("MARIADB_HOST", "localhost")
MARIADB_PORT = os.environ.get("MARIADB_PORT", "3306")
MARIADB_DB = os.environ.get("MARIADB_DB", "Contabilidad")

MARIADB_URL = f"mysql+pymysql://{MARIADB_USER}:{MARIADB_PASSWORD}@{MARIADB_HOST}:{MARIADB_PORT}/{MARIADB_DB}"
source_engine = create_engine(MARIADB_URL)

# ==========================================
# LÓGICA DE MIGRACIÓN
# ==========================================
def migrar_tabla(src_conn, tgt_session, tabla_nombre, ModeloDestino, mapeo_columnas):
    print(f"Migrando {tabla_nombre}...")
    columnas_mariadb = list(mapeo_columnas.keys())
    
    try:
        query = text(f"SELECT {', '.join(columnas_mariadb)} FROM {tabla_nombre}")
        resultados = src_conn.execute(query).mappings().all()
    except Exception as e:
        print(f"\n[!] ERROR al leer la tabla {tabla_nombre}.")
        try:
            cols = src_conn.execute(text(f"SHOW COLUMNS FROM {tabla_nombre}")).fetchall()
            nombres_cols = [c[0] for c in cols]
            print(f"-> COLUMNAS REALES EN MARIADB PARA '{tabla_nombre}': {nombres_cols}")
        except:
            pass
        raise e
    
    # Transformar los datos usando el mapeo
    registros = []
    for fila in resultados:
        datos_sqlite = {col_sqlite: fila[col_maria] for col_maria, col_sqlite in mapeo_columnas.items()}
        registros.append(ModeloDestino(**datos_sqlite))
    
    if registros:
        tgt_session.bulk_save_objects(registros)
        tgt_session.commit()
        print(f"  -> {len(registros)} registros insertados en {tabla_nombre}.")
    else:
        print(f"  -> No se encontraron registros en {tabla_nombre}.")

def ejecutar_migracion():
    print("Iniciando proceso de migración desde MariaDB a SQLite...")
    
    # 1. Edb_path = "contabilidad.db"
    backup_path = f"{db_path}.backup"
    if os.path.exists(db_path):
        # Renombrar, no borrar. Si algo falla, el backup sigue ahí.
        if os.path.exists(backup_path):
            os.remove(backup_path)
        os.rename(db_path, backup_path)
    print(f"Archivo {db_path} movido a {backup_path}. Recuperable si algo falla.")
    
    
    # 2. CREAR LA NUEVA ESTRUCTURA DESDE CERO
    target_engine = create_engine("sqlite:///./contabilidad.db", connect_args={"check_same_thread": False})
    models.Base.metadata.create_all(bind=target_engine)
    TargetSession = sessionmaker(bind=target_engine)
    tgt_session = TargetSession()
    
    try:
        with source_engine.connect() as src_conn:
            
            # =====================================================================
            # MAPEO DE COLUMNAS: {"nombre_en_mariadb": "nombre_en_sqlite"}
            # =====================================================================
            
            migrar_tabla(src_conn, tgt_session, "Nivel1", models.Nivel1, {
                "id": "id", 
                "cuenta": "codigo",
                "descripcion": "nombre"
            })
            
            migrar_tabla(src_conn, tgt_session, "Nivel2", models.Nivel2, {
                "id": "id", 
                "cuenta": "codigo", 
                "descripcion": "nombre",
                "grupo": "nivel1_id"
            })
            
            migrar_tabla(src_conn, tgt_session, "Nivel3", models.Nivel3, {
                "new_id": "id",           # Nivel 3 usa new_id
                "cuenta": "codigo", 
                "descripcion": "nombre",
                "id_nivel2": "nivel2_id"  
            })
            
            migrar_tabla(src_conn, tgt_session, "Nivel4", models.Nivel4, {
                "id": "id",               # <-- Vuelve a usar id
                "cuenta": "codigo", 
                "descripcion": "nombre",
                "id_nivel3": "nivel3_id"
            })
            
            migrar_tabla(src_conn, tgt_session, "Nivel5", models.Nivel5, {
                "id": "id",               # <-- Vuelve a usar id
                "cuenta": "codigo", 
                "descripcion": "nombre",
                "id_nivel4": "nivel4_id"
            })
            
            migrar_tabla(src_conn, tgt_session, "Nivel6", models.Nivel6, {
                "id": "id",               # <-- Vuelve a usar id
                "cuenta": "codigo", 
                "descripcion": "nombre",
                "id_nivel5": "nivel5_id"
            })
            
        print("¡Migración completada con éxito!")
    except Exception as e:
        tgt_session.rollback()
        print(f"ERROR durante la migración: {e}")
    finally:
        tgt_session.close()

if __name__ == "__main__":
    ejecutar_migracion()