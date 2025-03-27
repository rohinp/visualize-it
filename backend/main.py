import logging
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

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


# Check if frontend build directory exists
frontend_build_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend", "build")
if os.path.exists(frontend_build_dir):
    # Mount the static files from the frontend build directory
    app.mount("/static", StaticFiles(directory=os.path.join(frontend_build_dir, "static")), name="static")
    
    # Serve index.html for the root path and any other path not handled by the API
    @app.get("/")
    async def serve_frontend_root():
        return FileResponse(os.path.join(frontend_build_dir, "index.html"))
    
    # Catch-all route to serve the React app for client-side routing
    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        # First check if the path exists as a file in the build directory
        file_path = os.path.join(frontend_build_dir, full_path)
        if os.path.exists(file_path) and os.path.isfile(file_path):
            return FileResponse(file_path)
        # Otherwise return index.html to let React handle the routing
        return FileResponse(os.path.join(frontend_build_dir, "index.html"))
    
    logger.info(f"Serving frontend from {frontend_build_dir}")
else:
    # If frontend build doesn't exist, just serve API info
    @app.get("/")
    async def root():
        """
        Root endpoint
        """
        return {
            "message": "Welcome to the Visualize-It API",
            "docs_url": "/docs",
            "redoc_url": "/redoc",
            "note": "Frontend build not found. Run 'npm run build' in the frontend directory to serve the UI."
        }
    logger.warning(f"Frontend build directory not found at {frontend_build_dir}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
