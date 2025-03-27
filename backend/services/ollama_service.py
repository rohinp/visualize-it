import asyncio
import json
import logging
import re
import requests
from typing import Dict, Any

from ollama import AsyncClient

from models.settings import settings

logger = logging.getLogger("visualize-it")


class OllamaService:
    def __init__(self, base_url: str = None, host: str = None):
        """Initialize the OllamaService with either base_url or host
        
        Args:
            base_url: Full URL with http:// prefix for REST API calls
            host: Host without http:// prefix for AsyncClient
        """
        self.base_url = base_url or settings.OLLAMA_API_URL
        self.host = host or settings.OLLAMA_HOST
        self.generate_endpoint = f"{self.base_url}/api/generate"
        self.timeout = settings.OLLAMA_API_TIMEOUT
        
        logger.info(f"OllamaService initialized with base_url={self.base_url}, host={self.host}")

    def generate(self, prompt: str, model: str = None) -> Dict[str, Any]:
        """
        Generate a response from Ollama using the REST API
        """
        model = model or settings.DEFAULT_MODEL
        try:
            logger.info(f"Sending request to Ollama API with model {model}")
            response = requests.post(
                self.generate_endpoint,
                json={"model": model, "prompt": prompt, "stream": False},
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error calling Ollama API: {e}")
            return {"error": str(e)}
            
    async def generate_async(self, prompt: str, model: str = None, format: str = "json") -> Dict[str, Any]:
        """
        Generate a response from Ollama using the AsyncClient
        """
        model = model or settings.DEFAULT_MODEL
        try:
            logger.info(f"Creating AsyncClient with host: {self.host}")
            client = AsyncClient(host=self.host)
            
            # Prepare the message for the chat endpoint
            message = {'role': 'user', 'content': prompt}
            
            # Make the async request with timeout
            logger.info(f"Sending async request to Ollama with model {model}")
            response = await asyncio.wait_for(
                client.chat(
                    model=model, 
                    messages=[message], 
                    format=format,
                    options={
                        "num_predict": 2048, 
                        "add_bos": False,  # Prevent duplicate BOS tokens
                        "temperature": 0.7,  # Add some creativity but not too much
                        "top_k": 50,        # Limit token selection to top 50
                        "top_p": 0.95       # Sample from tokens comprising 95% of probability mass
                    }
                ),
                timeout=self.timeout
            )
            
            logger.info(f"Received async response from Ollama: {type(response)}")
            
            # Extract the response content using the proper API
            if response and hasattr(response, 'message') and hasattr(response.message, 'content'):
                response_text = response.message.content
                logger.info(f"Response text length: {len(response_text)}")
                return {"response": response_text}
            else:
                logger.error(f"Unexpected response format from Ollama: {response}")
                logger.error(f"Response type: {type(response)}, attributes: {dir(response) if response else 'None'}")
                return {"error": "Unexpected response format from Ollama"}
        except asyncio.TimeoutError:
            logger.error(f"Timeout waiting for Ollama response after {self.timeout} seconds")
            return {"error": f"Timeout after {self.timeout} seconds"}
        except Exception as e:
            logger.error(f"Error with Ollama AsyncClient: {str(e)}")
            return {"error": str(e)}

    async def generate_visualizations_from_text(self, text: str, model: str = None) -> Dict[str, Any]:
        """
        Generate visualizations from text input using the Ollama API
        """
        model = model or settings.DEFAULT_MODEL
        
        # Create a prompt for Ollama - simplified for faster processing and avoiding BOS token issues
        prompt = "Analyze this data and create Plotly.js visualizations. Return ONLY valid JSON:\n\nDATA:\n" + text + "\n\nIMPORTANT INSTRUCTIONS:\n1. First, analyze the data to determine what types of visualizations would be most meaningful and informative.\n2. Only generate visualizations that provide genuine insights - don't create charts just to have more visualizations.\n3. Choose appropriate chart types based on the data characteristics (e.g., categorical vs numerical, time series, etc.)\n4. You may create up to 8 visualizations, but only include as many as are truly meaningful for this specific dataset.\n5. Prioritize quality and relevance over quantity.\n\nResponse format:\n{\n  \"visualizations\": [\n    {\n      \"title\": \"Title\",\n      \"description\": \"Description\",\n      \"type\": \"plotly\",\n      \"plotlyData\": [{\n          \"type\": \"bar/pie/scatter/line/heatmap/etc\",\n          \"x\": [...],\n          \"y\": [...],\n          \"labels\": [...],\n          \"values\": [...]\n      }],\n      \"plotlyLayout\": {\n        \"title\": \"Chart Title\"\n      }\n    }\n    // Include only meaningful visualizations, up to a maximum of 8\n  ]\n}"
        
        logger.info(f"Prompt length: {len(prompt)} characters")
        
        # Check if Ollama is available by making a quick request to the models endpoint
        try:
            check_response = requests.get(
                f"{self.base_url}/api/tags",
                timeout=2,  # Very short timeout for the check
            )
            if check_response.status_code != 200:
                logger.error(f"Ollama API is not available: {check_response.status_code}")
                return {"error": "Ollama API is not available"}
        except requests.exceptions.RequestException as e:
            logger.error(f"Ollama API connection error: {str(e)}")
            return {"error": str(e)}
        
        # If we get here, Ollama is available, so proceed with the request using AsyncClient
        response = await self.generate_async(prompt, model)
        
        if "error" in response:
            return response
            
        return self._extract_json_from_response(response)

    async def generate_visualizations_from_dataframe(self, df_str: str, model: str = None) -> Dict[str, Any]:
        """
        Generate visualizations from a dataframe string representation
        """
        model = model or settings.DEFAULT_MODEL
        
        # Create a prompt for Ollama - simplified for faster processing and avoiding BOS token issues
        prompt = "Analyze this tabular data and create Plotly.js visualizations. Return ONLY valid JSON:\n\nDATA:\n" + df_str + "\n\nIMPORTANT INSTRUCTIONS:\n1. First, analyze the data to determine what types of visualizations would be most meaningful and informative.\n2. Only generate visualizations that provide genuine insights - don't create charts just to have more visualizations.\n3. Choose appropriate chart types based on the data characteristics (e.g., categorical vs numerical, time series, etc.)\n4. You may create up to 8 visualizations, but only include as many as are truly meaningful for this specific dataset.\n5. Prioritize quality and relevance over quantity.\n\nFor each visualization, include a title, description explaining the insight, and appropriate Plotly configuration."
        
        # Example JSON to guide the model - simplified
        json_example = """
{
  "visualizations": [
    {
      "title": "Monthly Sales Trend",
      "description": "Shows the sales trend over time with a clear upward trajectory",
      "type": "plotly",
      "plotlyData": [{
        "type": "line",
        "x": ["Jan", "Feb", "Mar"],
        "y": [10, 15, 13],
        "name": "Sales"
      }],
      "plotlyLayout": {
        "title": "Monthly Sales",
        "xaxis": {"title": "Month"},
        "yaxis": {"title": "Amount ($)"}
      }
    }
  ]
}
"""
        
        full_prompt = prompt + f"\n\nYour response MUST be valid JSON and nothing else. Format your response like this example:\n{json_example}"
        
        logger.info(f"Prompt length: {len(full_prompt)} characters")
        
        # Check if Ollama is available by making a quick request to the models endpoint
        try:
            check_response = requests.get(
                f"{self.base_url}/api/tags",
                timeout=2,  # Very short timeout for the check
            )
            if check_response.status_code != 200:
                logger.error(f"Ollama API is not available: {check_response.status_code}")
                return {"error": "Ollama API is not available"}
        except requests.exceptions.RequestException as e:
            logger.error(f"Ollama API connection error: {str(e)}")
            return {"error": str(e)}
        
        # If we get here, Ollama is available, so proceed with the request using AsyncClient
        response = await self.generate_async(full_prompt, model)
        
        if "error" in response:
            return response
            
        return self._extract_json_from_response(response)

    def _extract_json_from_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract JSON from Ollama response
        """
        if "error" in response:
            return {"error": response["error"]}

        response_text = response.get("response", "")
        logger.info(f"Extracting JSON from response text of length {len(response_text)}")

        # Log the full response for debugging
        if len(response_text) > 0:
            logger.info(f"Response text preview: {response_text[:200]}...")
        else:
            logger.warning("Empty response text from Ollama")

        # Try to find JSON in the response
        try:
            # First attempt - try to parse the entire response as JSON
            try:
                return json.loads(response_text)
            except json.JSONDecodeError:
                logger.info("Could not parse entire response as JSON, trying to extract JSON")

            # Look for JSON between triple backticks
            json_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", response_text)
            if json_match:
                logger.info("Found JSON between backticks")
                json_content = json_match.group(1).strip()
                return json.loads(json_content)

            # Try to find JSON between curly braces
            json_start = response_text.find("{")
            json_end = response_text.rfind("}") + 1
            if json_start >= 0 and json_end > json_start:
                logger.info(f"Extracting JSON from position {json_start} to {json_end}")
                json_content = response_text[json_start:json_end]
                return json.loads(json_content)

            # If no JSON found, return error
            logger.error("Could not extract JSON from response")
            return {"error": "Could not extract JSON from response"}
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in response: {str(e)}")
            return {"error": f"Invalid JSON in response: {str(e)}"}
        except Exception as e:
            logger.error(f"Error extracting JSON: {str(e)}")
            return {"error": f"Error extracting JSON: {str(e)}"}
            
    async def is_available(self) -> bool:
        """
        Check if the Ollama API is available
        """
        try:
            # First try with AsyncClient
            try:
                logger.info(f"Checking Ollama availability with AsyncClient at {self.host}")
                client = AsyncClient(host=self.host)
                await client.list()
                logger.info("Ollama is available via AsyncClient")
                return True
            except Exception as e:
                logger.warning(f"AsyncClient check failed: {str(e)}")
                
            # Fallback to direct API call
            logger.info(f"Trying fallback check with direct API call to {self.base_url}/api/tags")
            response = requests.get(
                f"{self.base_url}/api/tags",
                timeout=2,  # Very short timeout for the check
            )
            available = response.status_code == 200
            logger.info(f"Ollama API direct check result: {'available' if available else 'unavailable'}")
            return available
        except requests.exceptions.RequestException as e:
            logger.error(f"Ollama API is not available: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error checking Ollama availability: {str(e)}")
            return False
            
    async def list_models(self) -> Dict[str, Any]:
        """
        List available models directly from the Ollama API
        """
        try:
            # Try using AsyncClient first
            try:
                logger.info(f"Attempting to list models using AsyncClient with host: {self.host}")
                client = AsyncClient(host=self.host)
                response = await client.list()
                if response and 'models' in response:
                    logger.info(f"Successfully retrieved {len(response['models'])} models from Ollama API using AsyncClient")
                    return {"models": response["models"], "success": True}
                else:
                    logger.warning("No models found in Ollama API response using AsyncClient")
            except Exception as e:
                logger.error(f"Error listing models using AsyncClient: {str(e)}")
                
            # Fallback to direct API call
            logger.info(f"Falling back to direct API call to {self.base_url}/api/tags")
            response = requests.get(
                f"{self.base_url}/api/tags",
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                data = response.json()
                if 'models' in data and isinstance(data['models'], list):
                    logger.info(f"Successfully retrieved {len(data['models'])} models from direct API call")
                    return {"models": data["models"], "success": True}
                else:
                    logger.warning(f"Unexpected response format from direct API call: {data.keys()}")
            else:
                logger.error(f"Failed to get models from direct API call: {response.status_code}")
                
            # If we reach here, both methods failed
            return {"models": [], "success": False, "error": "Failed to retrieve models from Ollama API"}
        except Exception as e:
            logger.error(f"Unexpected error listing models from Ollama API: {str(e)}")
            return {"models": [], "success": False, "error": str(e)}
