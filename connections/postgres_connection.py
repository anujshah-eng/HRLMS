import os
from contextlib import contextmanager, asynccontextmanager
from sqlalchemy import create_engine, event
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, scoped_session, Session
from sqlalchemy.exc import OperationalError
from config.env_loader import load_env
from contextvars import ContextVar

load_env()

current_tenant_id: ContextVar[str | None] = ContextVar("current_tenant_id", default=None)

class DBResourceManager:
    def __init__(self, db_key: str = None) -> None:
        self.db_key = db_key
        self.database_url = os.getenv("DB_URL")

        if not self.database_url:
            raise ValueError("DB_URL not found in environment variables.")

        # ===== SYNC ENGINE =====
        self.sync_engine = create_engine(self.database_url, pool_pre_ping=True)
        self.session_factory = sessionmaker(bind=self.sync_engine)
        self.session = scoped_session(self.session_factory)

        # Attach event to set tenant_id on sync connections
        @event.listens_for(self.session_factory, "after_begin")
        def _set_tenant_config(session, transaction, connection):
            tenant_id = current_tenant_id.get()
            if tenant_id:
                session.execute("SELECT set_config('app.tenant_id', :tenant_id, true)", {"tenant_id": str(tenant_id)})

        # ===== ASYNC ENGINE =====
        async_url = self.database_url.replace("postgresql://", "postgresql+asyncpg://")
        self.async_engine = create_async_engine(
            async_url, 
            echo=False,
            pool_pre_ping=True,
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
        print("Sync database connection closed.")

    async def async_close(self):
        """Close async engine"""
        if hasattr(self, 'async_engine') and self.async_engine:
            await self.async_engine.dispose()
        print("Async database connection closed.")


def set_current_tenant(tenant_id: str | None):
    current_tenant_id.set(tenant_id)