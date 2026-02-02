import os
from contextlib import asynccontextmanager
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from config.env_loader import load_env  
from config.env_validator import validate_required_env_vars
from routers import ai_interview_management
from connections.mongo_connection import MotorMongoDBResourceManager


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('user_management.log'),
        logging.StreamHandler()
    ]
)

load_env()

@asynccontextmanager
async def lifespan(fastapi_app: FastAPI):
    if not getattr(fastapi_app.state, "initialized", False):
        print("Starting application initialization...")

        validate_required_env_vars()


        fastapi_app.state.mongo_manager = MotorMongoDBResourceManager()
        await fastapi_app.state.mongo_manager.connect()

        fastapi_app.state.realtime_interview_collection = fastapi_app.state.mongo_manager.db["ai_interview_sessions"]
        fastapi_app.state.ai_interviewers_collection = fastapi_app.state.mongo_manager.db["ai_interviewers"]

        print("Application initialization completed successfully!")
        fastapi_app.state.initialized = True

    yield

    print("Shutting down application...")
    if hasattr(fastapi_app.state, "mongo_manager"):
        fastapi_app.state.mongo_manager.close()
    print("Application shutdown completed!")



app = FastAPI(
    title="Acelucid HRMS",
    version="1.0",
    description="AI Interview Management",
    lifespan=lifespan
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("SECRET_KEY", "fallback-secret")  
)




app.include_router(
    ai_interview_management.router,
    prefix="/aiInterviewManagement",
    tags=["AI Interview Management"]
)


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Welcome to Acelucid HRMS API",
        "version": "1.0",
        "docs": "/docs",
        "redoc": "/redoc"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", "8001")),
        reload=os.getenv("ENV", "dev") == "dev"
    )
