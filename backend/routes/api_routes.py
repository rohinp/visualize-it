import json
import logging
import pandas as pd
from fastapi import APIRouter, File, Form, UploadFile, Depends
from typing import Dict, Any, Optional

from services.visualization_service import VisualizationService
from services.ollama_service import OllamaService

logger = logging.getLogger("visualize-it")

router = APIRouter(prefix="/api", tags=["api"])

# Dependency for services
def get_visualization_service():
    return VisualizationService()


def get_ollama_service():
    return OllamaService()


import asyncio
from models.settings import Settings
from utils.visualization_utils import generate_sample_plotly_visualizations
import traceback


@router.get("/health")
async def health_check():
    """
    Health check endpoint
    """
    return {"status": "ok", "version": "1.0.0"}


@router.get("/status")
async def status_check(ollama_service: OllamaService = Depends(get_ollama_service)):
    """
    Check the status of the server and Ollama
    """
    # Check if Ollama is available
    ollama_available = await ollama_service.is_available()
    
    return {
        "server": "ok",
        "ollama": "ok" if ollama_available else "error"
    }


@router.post("/process-text")
async def process_text(
    text: str = Form(...),
    model: Optional[str] = Form(None),
    ollama_service: OllamaService = Depends(get_ollama_service),
):
    """
    Process text data and generate visualizations using Ollama
    """
    logger.info(f"Received text processing request. Text length: {len(text)}")
    try:
        # Use the provided model or fall back to default
        settings = Settings()
        model_to_use = model if model else settings.DEFAULT_MODEL
        logger.info(f"Using model: {model_to_use}")

        # Process the text data using Ollama with a timeout
        try:
            visualization_data = await asyncio.wait_for(
                ollama_service.generate_visualizations_from_text(text, model=model_to_use),
                timeout=settings.OLLAMA_API_TIMEOUT,
            )
            logger.info(
                f"Successfully processed text. Generated {len(visualization_data.get('visualizations', []))} visualizations"
            )
            return visualization_data
        except asyncio.TimeoutError:
            logger.error("Timeout occurred while processing text")
            # Return sample visualizations on timeout
            sample_data = generate_sample_plotly_visualizations()
            return {
                "error": "Timeout occurred",
                "visualizations": sample_data["visualizations"],
            }
    except Exception as e:
        logger.error(f"Error processing text: {str(e)}")
        logger.error(traceback.format_exc())
        # Always return sample visualizations even on error
        sample_data = generate_sample_plotly_visualizations()
        return {"error": str(e), "visualizations": sample_data["visualizations"]}


@router.post("/retry-visualization")
async def retry_visualization(
    text: str = Form(...),
    model: Optional[str] = Form(None),
    ollama_service: OllamaService = Depends(get_ollama_service),
):
    """
    Endpoint to manually retry visualization generation
    """
    logger.info(f"Received retry visualization request. Text length: {len(text)}")
    try:
        # Use the provided model or fall back to default
        settings = Settings()
        model_to_use = model if model else settings.DEFAULT_MODEL
        logger.info(f"Using model: {model_to_use}")

        # Force a new attempt with the same text
        result = await ollama_service.generate_visualizations_from_text(
            text, model=model_to_use
        )
        logger.info(
            f"Retry generated {len(result.get('visualizations', []))} visualizations"
        )
        return result
    except Exception as e:
        logger.error(f"Error in retry visualization: {str(e)}")
        logger.error(traceback.format_exc())
        return {"error": str(e), "visualizations": []}


@router.post("/process-csv")
async def process_csv(
    file: UploadFile = File(...),
    model: Optional[str] = Form(None),
    ollama_service: OllamaService = Depends(get_ollama_service),
):
    """
    Process CSV file and generate visualizations using Ollama
    """
    logger.info(f"Received CSV file: {file.filename}, size: {file.size} bytes")
    try:
        # Read the CSV file
        contents = await file.read()
        try:
            df = pd.read_csv(pd.io.common.StringIO(contents.decode("utf-8")))
            logger.info(
                f"Successfully parsed CSV with {len(df)} rows and {len(df.columns)} columns"
            )
        except Exception as e:
            logger.error(f"Error parsing CSV: {str(e)}")
            return {"error": f"Error parsing CSV: {str(e)}", "visualizations": []}

        # Use the provided model or fall back to default
        settings = Settings()
        model_to_use = model if model else settings.DEFAULT_MODEL
        logger.info(f"Using model: {model_to_use}")

        # Process the dataframe using Ollama with a timeout
        try:
            # Convert the dataframe to a string representation
            df_str = df.to_string(index=False)
            logger.info(f"Dataframe string representation length: {len(df_str)}")
            
            # Generate visualizations with a timeout
            visualization_data = await asyncio.wait_for(
                ollama_service.generate_visualizations_from_dataframe(df_str, model=model_to_use),
                timeout=settings.OLLAMA_API_TIMEOUT,
            )
            logger.info(
                f"Successfully processed CSV. Generated {len(visualization_data.get('visualizations', []))} visualizations"
            )
            return visualization_data
        except asyncio.TimeoutError:
            logger.error(
                f"Timeout occurred while processing CSV after {settings.OLLAMA_API_TIMEOUT} seconds"
            )
            # Return sample visualizations on timeout
            sample_data = generate_sample_plotly_visualizations()
            return {
                "error": f"Timeout occurred after {settings.OLLAMA_API_TIMEOUT} seconds",
                "visualizations": sample_data["visualizations"],
            }
    except Exception as e:
        logger.error(f"Error processing CSV file: {str(e)}")
        logger.error(traceback.format_exc())
        # Always return sample visualizations even on error
        sample_data = generate_sample_plotly_visualizations()
        return {"error": str(e), "visualizations": sample_data["visualizations"]}

@router.post("/visualize/text")
async def visualize_text(
    text: str = Form(...),
    model: Optional[str] = Form(None),
    visualization_service: VisualizationService = Depends(get_visualization_service)
):
    """
    Generate visualizations from text input
    """
    logger.info(f"Received text visualization request with {len(text)} characters")
    
    try:
        result = await visualization_service.generate_from_text(text, model)
        
        if "error" in result:
            logger.error(f"Error generating visualizations: {result['error']}")
            return {"error": result["error"], "visualizations": result.get("visualizations", [])}
        
        logger.info(f"Generated {len(result['visualizations'])} visualizations from text")
        return result
    except Exception as e:
        logger.exception(f"Unexpected error in visualize_text: {str(e)}")
        return {"error": str(e), "visualizations": []}

@router.post("/visualize/file")
async def visualize_file(
    file: UploadFile = File(...),
    model: Optional[str] = Form(None),
    visualization_service: VisualizationService = Depends(get_visualization_service)
):
    """
    Generate visualizations from a file
    """
    logger.info(f"Received file visualization request for file {file.filename}")
    
    try:
        # Read file content
        file_content = await file.read()
        
        # Generate visualizations
        result = await visualization_service.generate_from_file(file_content, file.filename, model)
        
        if "error" in result:
            logger.error(f"Error generating visualizations: {result['error']}")
            return {"error": result["error"], "visualizations": result.get("visualizations", [])}
        
        logger.info(f"Generated {len(result['visualizations'])} visualizations from file")
        return result
    except Exception as e:
        logger.exception(f"Unexpected error in visualize_file: {str(e)}")
        return {"error": str(e), "visualizations": []}

@router.post("/visualize/json")
async def visualize_json(
    data: Dict[str, Any],
    model: Optional[str] = Form(None),
    visualization_service: VisualizationService = Depends(get_visualization_service)
):
    """
    Generate visualizations from JSON data
    """
    logger.info(f"Received JSON visualization request")
    
    try:
        # Convert JSON to DataFrame
        df = pd.DataFrame(data)
        
        # Generate visualizations
        result = await visualization_service.generate_from_dataframe(df, model)
        
        if "error" in result:
            logger.error(f"Error generating visualizations: {result['error']}")
            return {"error": result["error"], "visualizations": result.get("visualizations", [])}
        
        logger.info(f"Generated {len(result['visualizations'])} visualizations from JSON")
        return result
    except Exception as e:
        logger.exception(f"Unexpected error in visualize_json: {str(e)}")
        return {"error": str(e), "visualizations": []}

@router.get("/models")
async def get_models(
    ollama_service: OllamaService = Depends(get_ollama_service)
):
    """
    Get available Ollama models
    """
    try:
        # Check if Ollama is available
        is_available = await ollama_service.is_available()
        
        if not is_available:
            logger.error("Ollama API is not available")
            return {"error": "Ollama API is not available", "models": []}
        
        # Get models directly from Ollama API
        result = await ollama_service.list_models()
        
        if not result["success"]:
            error_msg = result.get("error", "Unknown error listing models")
            logger.error(f"Error listing models: {error_msg}")
            return {"error": error_msg, "models": []}
        
        # Add debug logging to understand the structure
        logger.info(f"Raw model data: {result['models'][:1]}")
        
        # Process the models to return objects with name and size
        models = []
        for model_info in result["models"]:
            # Log each model for debugging
            logger.info(f"Processing model: {model_info}")
            
            # Extract model name and size
            name = model_info.get("name") or model_info.get("model", "Unknown")
            size = model_info.get("size", 0)
            
            # Create a model object with name and size
            model_obj = {
                "name": name,
                "size": size
            }
            models.append(model_obj)
            logger.info(f"Added model: {model_obj}")
        
        logger.info(f"Processed {len(models)} models for frontend")
        return {"models": models}
    except Exception as e:
        logger.exception(f"Unexpected error in get_models: {str(e)}")
        return {"error": str(e), "models": []}
