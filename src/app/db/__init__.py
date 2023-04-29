from .tables import *
from .session import Base, SessionLocal, database, engine
from .init_db import init_db
from .models import AccessType, MediaType


# Dependency
def get_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
