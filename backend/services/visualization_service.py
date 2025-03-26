import json
import logging
import pandas as pd
from typing import Dict, List, Any, Optional, Union

from models.settings import settings
from services.ollama_service import OllamaService
from utils.data_utils import DataUtils
from utils.visualization_utils import VisualizationUtils

logger = logging.getLogger("visualize-it")

class VisualizationService:
    """
    Service for generating visualizations from various data sources
    """
    def __init__(self, ollama_service: Optional[OllamaService] = None):
        self.ollama_service = ollama_service or OllamaService()
        self.data_utils = DataUtils()
        self.viz_utils = VisualizationUtils()
        self.max_visualizations = settings.MAX_VISUALIZATIONS
        
        logger.info(f"VisualizationService initialized with max_visualizations={self.max_visualizations}")
    
    async def generate_from_text(self, text: str, model: str = None) -> Dict[str, Any]:
        """
        Generate visualizations from text input
        """
        logger.info(f"Generating visualizations from text input of length {len(text)}")
        
        # Try to generate visualizations using Ollama
        response = await self.ollama_service.generate_visualizations_from_text(text, model)
        
        # Check if there was an error with Ollama
        if "error" in response:
            logger.warning(f"Error from Ollama: {response['error']}. Falling back to dataframe extraction.")
            # Try to extract a dataframe from the text and use fallback visualization
            try:
                df = self.data_utils.extract_dataframe_from_text(text)
                if df is not None and not df.empty:
                    logger.info(f"Successfully extracted dataframe with shape {df.shape}")
                    return self.generate_fallback_visualizations(df)
                else:
                    logger.error("Could not extract dataframe from text")
                    return {"error": "Could not generate visualizations from text", "visualizations": []}
            except Exception as e:
                logger.error(f"Error extracting dataframe from text: {str(e)}")
                return {"error": str(e), "visualizations": []}
        
        # Process the Ollama response
        return self._process_ollama_response(response)
    
    async def generate_from_dataframe(self, df: pd.DataFrame, model: str = None) -> Dict[str, Any]:
        """
        Generate visualizations from a pandas DataFrame
        """
        logger.info(f"Generating visualizations from dataframe with shape {df.shape}")
        
        # Convert dataframe to string for the prompt
        df_str = df.head(100).to_string()
        
        # Try to generate visualizations using Ollama
        response = await self.ollama_service.generate_visualizations_from_dataframe(df_str, model)
        
        # Check if there was an error with Ollama
        if "error" in response:
            logger.warning(f"Error from Ollama: {response['error']}. Using fallback visualization.")
            return self.generate_fallback_visualizations(df)
        
        # Process the Ollama response
        return self._process_ollama_response(response)
    
    async def generate_from_file(self, file_content: bytes, filename: str, model: str = None) -> Dict[str, Any]:
        """
        Generate visualizations from a file
        """
        logger.info(f"Generating visualizations from file: {filename}")
        
        # Extract dataframe from file
        try:
            df = self.data_utils.extract_dataframe_from_file(file_content, filename)
            if df is not None and not df.empty:
                logger.info(f"Successfully extracted dataframe with shape {df.shape}")
                return await self.generate_from_dataframe(df, model)
            else:
                logger.error("Could not extract dataframe from file")
                return {"error": "Could not extract data from file", "visualizations": []}
        except Exception as e:
            logger.error(f"Error extracting dataframe from file: {str(e)}")
            return {"error": str(e), "visualizations": []}
    
    def generate_fallback_visualizations(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Generate fallback visualizations from a dataframe when Ollama is not available
        """
        logger.info(f"Generating fallback visualizations for dataframe with shape {df.shape}")
        return self.viz_utils.generate_dataframe_visualizations(df)
    
    def _process_ollama_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process the response from Ollama and extract visualizations
        """
        if "error" in response:
            return {"error": response["error"], "visualizations": []}
        
        # Extract visualizations from the response
        visualizations = response.get("visualizations", [])
        
        # Limit the number of visualizations
        if len(visualizations) > self.max_visualizations:
            logger.info(f"Limiting visualizations from {len(visualizations)} to {self.max_visualizations}")
            visualizations = visualizations[:self.max_visualizations]
        
        # Validate each visualization
        valid_visualizations = []
        for viz in visualizations:
            if self.viz_utils.is_valid_visualization(viz):
                valid_visualizations.append(viz)
            else:
                logger.warning(f"Invalid visualization: {json.dumps(viz)[:100]}...")
        
        logger.info(f"Processed {len(valid_visualizations)} valid visualizations")
        return {"visualizations": valid_visualizations}
