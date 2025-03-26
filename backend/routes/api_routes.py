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



@router.get("/health")
async def health_check():
    """
    Health check endpoint
    """
    return {"status": "ok", "version": "1.0.0"}

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
        
        # Get models from Ollama
        response = await ollama_service.generate_async("list all available models", format="json")
        
        if "error" in response:
            logger.error(f"Error getting models: {response['error']}")
            return {"error": response["error"], "models": []}
        
        # Extract models from response
        models = []
        try:
            response_text = response.get("response", "")
            if response_text:
                # Try to parse as JSON
                try:
                    models_data = json.loads(response_text)
                    if isinstance(models_data, list):
                        models = models_data
                    elif isinstance(models_data, dict) and "models" in models_data:
                        models = models_data["models"]
                except json.JSONDecodeError:
                    # If not JSON, try to extract model names from text
                    models = [line.strip() for line in response_text.split("\n") if line.strip()]
        except Exception as e:
            logger.error(f"Error parsing models response: {str(e)}")
        
        # If we couldn't get models, use a default list
        if not models:
            models = ["llama3", "deepseek-coder", "codellama", "wizardcoder"]
        
        logger.info(f"Retrieved {len(models)} models")
        return {"models": models}
    except Exception as e:
        logger.exception(f"Unexpected error in get_models: {str(e)}")
        return {"error": str(e), "models": []}
