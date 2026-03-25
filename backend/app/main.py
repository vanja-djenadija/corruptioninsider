from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import suppliers, procedures, authorities, awards, dashboard

app = FastAPI(
    title="Balkan Corruption Insider API",
    description="API for accessing public procurement data and corruption risk indicators",
    version="1.0.0",
    root_path="/api",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(suppliers.router, prefix="/api/v1")
app.include_router(procedures.router, prefix="/api/v1")
app.include_router(authorities.router, prefix="/api/v1")
app.include_router(awards.router, prefix="/api/v1")
app.include_router(dashboard.router, prefix="/api/v1")


@app.get("/")
def root():
    return {
        "message": "Balkan Corruption Insider API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/api/v1/health")
def health_check():
    return {"status": "healthy"}
