# ============================================================
# SQLALCHEMY ORM CHEATSHEET — Para crear tus propios Repositories
# ============================================================

# IMPORTS MÁS USADOS
from sqlalchemy import select
from sqlalchemy.orm import Session
from ..src.domain.models import (
    Patient,
    Staff,
    SampleType,
    Container,
    ResearchProject,
    Sample,
    Protocol,
    LogTemperature,
    QualityControl,
    ResearchProjectSamples,
    ProjectTeam
)
session = Session
# ============================================================
# 1. INSERTAR DATOS (CREATE)
# ============================================================

nuevo = Patient(name="Ana", age=30)

session.add(nuevo)       # marca para insertar
session.commit()         # guarda en BD
session.refresh(nuevo)   # actualiza el objeto con datos reales (ej: id)

# ------------------------------------------------------------

# Insertar varios
session.add_all([obj1, obj2, obj3])
session.commit()

# ============================================================
# 2. CONSULTAR DATOS (READ)
# ============================================================

# Buscar por clave primaria
obj = session.get(Patient, 1)

# Obtener todos
objs = session.scalars(select(Patient)).all()

# ============================================================
# 3. FILTRAR CONSULTAS
# ============================================================

# WHERE simple
objs = session.scalars(
    select(Patient).where(Patient.age > 18)
).all()

# Varias condiciones
objs = session.scalars(
    select(Patient).where(
        Patient.age > 18,
        Patient.active == True
    )
).all()

# Primer resultado
obj = session.scalars(
    select(Patient).where(Patient.name == "Ana")
).first()

# Uno exacto (lanza error si no existe o hay varios)
obj = session.scalars(
    select(Patient).where(Patient.email == "ana@mail.com")
).one()

# ============================================================
# 4. ORDENAR / LIMITAR
# ============================================================

# ORDER BY
objs = session.scalars(
    select(Patient).order_by(Patient.name)
).all()

# LIMIT
objs = session.scalars(
    select(Patient).limit(5)
).all()

# ============================================================
# 5. ACTUALIZAR DATOS (UPDATE)
# ============================================================

obj = session.get(Patient, 1)

if obj:
    obj.name = "Carlos"
    obj.age = 35
    session.commit()

# ============================================================
# 6. BORRAR DATOS (DELETE)
# ============================================================

obj = session.get(Patient, 1)

if obj:
    session.delete(obj)
    session.commit()

# ============================================================
# 7. ROLLBACK
# ============================================================

try:
    session.commit()
except:
    session.rollback()

# ============================================================
# 8. PATRONES PARA REPOSITORY
# ============================================================

# CREATE
def create(self, obj):
    self.session.add(obj)
    self.session.commit()
    self.session.refresh(obj)
    return obj

# GET BY ID
def get_by_id(self, id):
    return self.session.get(self.model, id)

# GET ALL
def get_all(self):
    return self.session.scalars(select(self.model)).all()

# DELETE
def delete(self, obj):
    self.session.delete(obj)
    self.session.commit()

# ============================================================
# 9. OPERADORES ÚTILES
# ============================================================

# ==   igual
# !=   distinto
# >    mayor
# <    menor
# >=   mayor o igual
# <=   menor o igual

# LIKE
select(Patient).where(Patient.name.like("%Ana%"))

# IN
select(Patient).where(Patient.id.in_([1, 2, 3]))

# IS NULL
select(Patient).where(Patient.email == None)

# ============================================================
# 10. IDEA CLAVE
# ============================================================

# session = conexión / contexto con la BD
# model   = tabla representada como clase
# object  = fila concreta
# select  = construir consulta
# commit  = guardar cambios