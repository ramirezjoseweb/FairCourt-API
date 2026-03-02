import os
import sys

# Añade el directorio raíz del proyecto al path para que Alembic
# pueda importar correctamente los módulos de la aplicación.
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.db import Base
from app import models  # Importante: fuerza la carga de los modelos para autogenerate

from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# Objeto de configuración de Alembic.
# Proporciona acceso a los valores definidos en el archivo alembic.ini.
config = context.config

# Interpreta el archivo de configuración para el sistema de logging.
# Esta línea configura los loggers definidos en el .ini.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# ---------------------------------------------------------------------
# Configuración de metadata para autogeneración
# ---------------------------------------------------------------------

# Se establece el metadata de los modelos ORM para permitir que
# Alembic detecte automáticamente cambios en el esquema.
target_metadata = Base.metadata

# ---------------------------------------------------------------------
# Modo OFFLINE
# ---------------------------------------------------------------------

def run_migrations_offline() -> None:
    """
    Ejecuta las migraciones en modo 'offline'.

    En este modo:
    - No se crea un Engine real.
    - No se establece conexión directa con la base de datos.
    - No es necesario que exista un driver DBAPI disponible.

    En su lugar:
    - Se utiliza únicamente la URL de conexión.
    - Las operaciones generan directamente sentencias SQL en el
      script de salida.

    Este modo es útil cuando se desea generar scripts SQL sin
    conectarse a la base de datos.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


# ---------------------------------------------------------------------
# Modo ONLINE
# ---------------------------------------------------------------------

def run_migrations_online() -> None:
    """
    Ejecuta las migraciones en modo 'online'.

    En este modo:
    - Se crea un Engine de SQLAlchemy.
    - Se establece una conexión real con la base de datos.
    - Las migraciones se aplican directamente sobre la BD.

    Este es el modo habitual en desarrollo y producción.
    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


# ---------------------------------------------------------------------
# Punto de entrada según modo de ejecución
# ---------------------------------------------------------------------

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
