import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from aidp.core.config import get_settings
from aidp.core.errors import DomainError
from aidp.core.schemas import HealthResponse
from aidp.modules.capabilities.definitions import register_builtin_capabilities
from aidp.modules.capabilities.router import router as capabilities_router
from aidp.modules.catalogs.router import router as catalogs_router
from aidp.modules.identity.router import router as identity_router
from aidp.modules.knowledge_networks.router import router as knowledge_networks_router
from aidp.modules.projects.router import router as projects_router


@asynccontextmanager
async def lifespan(_: FastAPI):
    register_builtin_capabilities()
    yield


settings = get_settings()
app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="AIDP modular API and agent capability runtime",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    request_id = request.headers.get("x-request-id", str(uuid.uuid4()))
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers["x-request-id"] = request_id
    return response


@app.exception_handler(DomainError)
async def domain_error_handler(request: Request, exc: DomainError):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "code": exc.code,
            "message": exc.message,
            "request_id": getattr(request.state, "request_id", "unknown"),
        },
    )


@app.get("/health", response_model=HealthResponse, tags=["system"])
def health():
    return {"status": "ok", "service": "aidp-server", "version": app.version}


api_prefix = "/api/v1"
app.include_router(projects_router, prefix=api_prefix)
app.include_router(identity_router, prefix=api_prefix)
app.include_router(catalogs_router, prefix=api_prefix)
app.include_router(knowledge_networks_router, prefix=api_prefix)
app.include_router(capabilities_router, prefix=api_prefix)
