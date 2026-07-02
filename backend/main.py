import os
import json
import sys
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from backend.limiter import limiter

# ===================================================================
# ENTERPRISE ROOT LOGGING ENGINE SETUP 
# ===================================================================
log_format = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
date_format = "%Y-%m-%d %H:%M:%S"

logging.basicConfig(
    level=logging.INFO,
    format=log_format,
    datefmt=date_format,
    handlers=[logging.StreamHandler(sys.stdout)]
)
for uvicorn_logger_name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
    uv_logger = logging.getLogger(uvicorn_logger_name)
    uv_logger.handlers.clear()
    uv_logger.propagate = True

logger = logging.getLogger("ResumeScore.Main")

load_dotenv()

# ===================================================================
# LOCAL ROUTER IMPORTS 
# ===================================================================
from backend.routers.analysis import router as analysis_router
from backend.routers.cover_letter import router as cover_letter_router
from backend.routers.interview import router as interview_router
from backend.routers.roadmap import router as roadmap_router
from backend.routers.job_matcher import router as job_matcher_router
from backend.routers.batch_ranking import router as batch_ranking_router

# ===================================================================
# FASTAPI LIFESPAN & APP INIT
# ===================================================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 ResumeScore API Engine starting up...")
    yield
    logger.info("🛑 ResumeScore API Engine safely shutting down...")

app = FastAPI(
    title="ResumeScore API",
    version="0.1.0",
    lifespan=lifespan
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ===================================================================
# CORS CONFIGURATION
# ===================================================================
env_origins = os.getenv("ALLOWED_ORIGINS")
if env_origins:
    try:
        origins = json.loads(env_origins)
    except json.JSONDecodeError:
        logger.error("CORS Initialization Failure: ALLOWED_ORIGINS string in env is invalid JSON.")
        origins = ["http://localhost:8501", "http://127.0.0.1:8501"]
else:
    origins = ["http://localhost:8501",
               "http://127.0.0.1:8501"
               # "https://your-production-app.com"  
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins, 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==========================================
# GLOBAL EXCEPTION HANDLERS
# ==========================================

@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    logger.warning(f"Validation Error on {request.method} {request.url.path}: {str(exc)}")
    return JSONResponse(status_code=422, content={"detail": str(exc)})

@app.exception_handler(RuntimeError)
async def runtime_error_handler(request: Request, exc: RuntimeError):
    logger.error(f"Runtime Engine Error on {request.method} {request.url.path}: {str(exc)}")
    return JSONResponse(status_code=502, content={"detail": str(exc)})

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception(f"Unhandled error on {request.method} {request.url.path}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

# ==========================================
# ROUTER REGISTRATION
# ==========================================
app.include_router(analysis_router)
app.include_router(cover_letter_router)
app.include_router(interview_router)
app.include_router(roadmap_router)
app.include_router(job_matcher_router)
app.include_router(batch_ranking_router)

@app.get("/health")
def health_check():
    return {"status": "ok", "message": "ResumeScore API is running"}