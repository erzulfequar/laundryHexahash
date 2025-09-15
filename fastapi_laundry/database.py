from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.automap import automap_base
from django.conf import settings
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "laundry_pos.settings")
django.setup()


# Build DB URL from Django settings (works for sqlite/postgres if set)
def get_sqlalchemy_url():
    db = settings.DATABASES.get("default", {})
    engine = db.get("ENGINE", "")
    if "sqlite3" in engine:
        name = db.get("NAME")
        # if NAME is Path object, convert
        if hasattr(name, "as_posix"):
            name = name.as_posix()
        return f"sqlite:///{name}"
    # Add other DB engines if needed (postgres/mysql)
    # e.g., postgresql: 'postgresql://USER:PASSWORD@HOST:PORT/NAME'
    raise RuntimeError("Unsupported DB engine in settings.DATABASES: " + engine)

SQLALCHEMY_DATABASE_URL = get_sqlalchemy_url()

# create engine
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in SQLALCHEMY_DATABASE_URL else {}
)

metadata = MetaData()
metadata.reflect(bind=engine)
Base = automap_base(metadata=metadata)
Base.prepare()

# Exposed mapped classes by name: e.g., Customer = Base.classes.laundry_customer (table name)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
