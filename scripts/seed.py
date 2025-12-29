from config.env_loader import load_env
from connections.postgres_connection import DBResourceManager
from connections.db_init import create_database_if_not_exists
from connections.seed_data import seed_initial_data
from models import Base

load_env()

def run_seeds():
    # Ensure DB exists
    create_database_if_not_exists()

    db_manager = DBResourceManager()
    engine = db_manager.sync_engine

    # Ensure tables exist
    Base.metadata.create_all(engine)

    # Seed initial data (roles, superadmin, etc.)
    with db_manager.connect() as session:
        seed_initial_data(session)

    db_manager.close()

if __name__ == "__main__":
    print("Running database initialization...")
    run_seeds()
    print("Database initialization complete!")
