import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from models.settings import settings
from routes.api_routes import router as api_router
from routes.logging_routes import router as logging_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(settings.SERVER_LOG_FILE),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger("visualize-it")

# Initialize FastAPI app
app = FastAPI(
    title="Visualize-It API",
    description="API for generating visualizations from data",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
)

# Include routers
app.include_router(api_router)
app.include_router(logging_router)


# Root endpoint
@app.get("/")
async def root():
    """
    Root endpoint
    """
    return {
        "message": "Welcome to the Visualize-It API",
        "docs_url": "/docs",
        "redoc_url": "/redoc",
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
