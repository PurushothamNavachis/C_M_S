from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import auth, users, clinical

app = FastAPI(
    title="Clinic Management System (CMS) API",
    description="Clean Architecture Production-Ready MVP Clinic Management System Backend",
    version="1.0.0"
)

# CORS middleware config
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
app.include_router(auth.router, prefix="/api/v1")
app.include_router(users.router, prefix="/api/v1")
app.include_router(clinical.router, prefix="/api/v1")

@app.get("/")
async def root():
    return {"message": "Clinic Management System (CMS) API is running."}
