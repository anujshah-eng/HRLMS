from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from sqlalchemy.orm import Session
from connections.postgres_connection import DBResourceManager, set_current_tenant
from models.tenant import Tenant

TENANT_HEADER = "X-Tenant"

db_manager = DBResourceManager()

class TenantMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        tenant_key = request.headers.get(TENANT_HEADER)
        tenant_id = None
        if tenant_key:
            with db_manager.connect() as session:  # type: Session
                tenant = session.query(Tenant).filter(Tenant.key == tenant_key).first()
                if tenant:
                    tenant_id = str(tenant.id)
        set_current_tenant(tenant_id)
        request.state.tenant_id = tenant_id
        response: Response = await call_next(request)
        set_current_tenant(None)
        return response
