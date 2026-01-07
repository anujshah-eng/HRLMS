import os
from contextlib import contextmanager, asynccontextmanager
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, scoped_session
from config.env_loader import load_env

load_env()

class MySQLResourceManager:
    def __init__(self, db_url_env_var: str = "MYSQL_DB_URL") -> None:
        self.database_url = os.getenv(db_url_env_var)

        if not self.database_url:
            # Fallback to generic DB_URL if specific one is not set, 
            # but verify it looks like mysql
            self.database_url = os.getenv("DB_URL")
        
        if not self.database_url:
             raise ValueError(f"{db_url_env_var} or DB_URL not found in environment variables.")

        if "mysql" not in self.database_url:
             print(f"Warning: Database URL {self.database_url} does not look like a MySQL URL.")

        # ===== SYNC ENGINE =====
        # Ensure using pymysql if not specified, though usually user supplies full string
        # If it is 'mysql://', sqlalchemy defaults to mysql-python (deprecated) or mysqlclient.
        # It's safer to ensure mysql+pymysql if strictly needed, but let's trust the input first
        # or force pymysql if generic 'mysql://' is used.
        sync_url = self.database_url
        if sync_url.startswith("mysql://"):
            sync_url = sync_url.replace("mysql://", "mysql+pymysql://")
            
        self.sync_engine = create_engine(
            sync_url, 
            pool_pre_ping=True,
            pool_recycle=3600
        )
        self.session_factory = sessionmaker(bind=self.sync_engine)
        self.session = scoped_session(self.session_factory)

        # ===== ASYNC ENGINE =====
        # Common async drivers: aiomysql, asyncmy
        # We'll default to aiomysql if pure mysql:// provided
        async_url = self.database_url
        if "mysql://" in async_url:
             async_url = async_url.replace("mysql://", "mysql+aiomysql://")
        elif "mysql+pymysql://" in async_url:
             async_url = async_url.replace("mysql+pymysql://", "mysql+aiomysql://")

        self.async_engine = create_async_engine(
            async_url,
            echo=False,
            pool_pre_ping=True,
            pool_recycle=3600,
            pool_size=10,
            max_overflow=20
        )
        self.async_session_factory = sessionmaker(
            bind=self.async_engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
            autocommit=False
        )

    @contextmanager
    def connect(self):
        """Sync context manager for database session"""
        session = self.session()
        try:
            yield session
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    @asynccontextmanager
    async def async_session(self):
        """Async context manager for database session"""
        session = self.async_session_factory()
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

    def close(self):
        """Close sync engine"""
        if hasattr(self, 'session'):
            self.session.remove()
        if hasattr(self, 'sync_engine') and self.sync_engine:
            self.sync_engine.dispose()
        print("Sync MySQL connection closed.")

    async def async_close(self):
        """Close async engine"""
        if hasattr(self, 'async_engine') and self.async_engine:
            await self.async_engine.dispose()
        print("Async MySQL connection closed.")
