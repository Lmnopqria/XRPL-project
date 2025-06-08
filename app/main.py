from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.api import router as api_v1_router
from app.core.database import engine
from app.models import user, record

# Creating Database
user.Base.metadata.create_all(bind=engine)
record.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="XRPL API",
    description="FastAPI Server for XRPL Project",
    version="1.0.0"
)

# CORS Settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register Router
app.include_router(api_v1_router, prefix="/api/v1")

@app.get("/")
async def root():
    return {"message": "Welcome to the XRPL Server"} 