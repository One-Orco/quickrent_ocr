from fastapi import FastAPI
from app.routers import upload

app = FastAPI()

# Include the upload router
app.include_router(upload.router)
