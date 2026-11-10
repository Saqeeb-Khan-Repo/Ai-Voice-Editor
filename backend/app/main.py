import os
import time
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.database.session import init_db
from app.workers.job_runner import job_runner
from app.monitoring.system import log_system_error
from app.api import health, audio, processing, outputs, monitoring, profiles, settings as settings_api

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("ai_naat_studio")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Initializing AI Naat Studio Database and Storage...")
    init_db()
    logger.info("Checking for interrupted processing jobs...")
    job_runner.recover_interrupted_jobs()
    logger.info("AI Naat Studio Audio Engine ready.")
    yield
    # Shutdown
    logger.info("Shutting down worker threads...")
    job_runner.executor.shutdown(wait=False)

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Local-first automatic vocal enhancement studio for Naat and Islamic recitation recordings.",
    lifespan=lifespan
)

# CORS configuration (supports local development and cloud deployments)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_origin_regex=r"^https?://.*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Request timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    try:
        response = await call_next(request)
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = f"{process_time:.4f}s"
        return response
    except Exception as exc:
        process_time = time.time() - start_time
        log_system_error(
            stage="http_request",
            message=str(exc),
            context={"path": str(request.url.path), "duration_s": process_time}
        )
        return JSONResponse(
            status_code=500,
            content={"detail": "An internal server error occurred in audio processing service."}
        )

# Register routes with /api prefix
app.include_router(health.router, prefix="/api")
app.include_router(audio.router, prefix="/api")
app.include_router(processing.router, prefix="/api")
app.include_router(outputs.router, prefix="/api")
app.include_router(monitoring.router, prefix="/api")
app.include_router(profiles.router, prefix="/api")
app.include_router(settings_api.router, prefix="/api")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)
