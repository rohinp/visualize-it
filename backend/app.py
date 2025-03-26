import io
import json
import logging
import os
import re
import time
import traceback
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Union

import pandas as pd
import requests
from ollama import AsyncClient
from fastapi import FastAPI, File, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("backend.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger("visualize-it")


# Settings class for configuration
class Settings:
    def __init__(self):
        self.DEFAULT_MODEL = os.environ.get("DEFAULT_MODEL", "llama3:8b")
        self.OLLAMA_API_TIMEOUT = int(os.environ.get("OLLAMA_API_TIMEOUT", "60"))
        self.OLLAMA_API_URL = os.environ.get(
            "OLLAMA_API_URL", "http://192.168.1.2:11434"
        )
        # Remove the http:// prefix for the Ollama client
        self.OLLAMA_HOST = self.OLLAMA_API_URL.replace("http://", "")

        logger.info(
            f"Settings initialized: DEFAULT_MODEL={self.DEFAULT_MODEL}, "
            f"OLLAMA_API_TIMEOUT={self.OLLAMA_API_TIMEOUT}, "
            f"OLLAMA_API_URL={self.OLLAMA_API_URL}, "
            f"OLLAMA_HOST={self.OLLAMA_HOST}"
        )


settings = Settings()

# Initialize FastAPI app
app = FastAPI(
    title="Visualize-It API", description="API for data visualization using LLMs"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
)


# Status endpoint
@app.get("/api/status")
async def get_status():
    """Get the status of the server and Ollama"""
    logger.info("Checking server and Ollama status")

    # Check Ollama status
    ollama_status = "error"
    try:
        response = requests.get(f"{settings.OLLAMA_API_URL}/api/tags", timeout=5)
        if response.status_code == 200:
            ollama_status = "ok"
            logger.info("Ollama is running")
        else:
            logger.warning(f"Ollama returned status code {response.status_code}")
    except Exception as e:
        logger.error(f"Error checking Ollama status: {str(e)}")

    return {
        "server": "ok",
        "ollama": ollama_status,
        "timestamp": datetime.now().isoformat(),
    }


# Endpoint to get available Ollama models
@app.get("/api/models")
async def get_models():
    """Get list of available Ollama models"""
    logger.info("Fetching available Ollama models")
    try:
        response = requests.get(f"{settings.OLLAMA_API_URL}/api/tags")
        if response.status_code == 200:
            models = response.json().get("models", [])
            # Extract just the model names and details we need
            model_list = [
                {
                    "name": model.get("name"),
                    "size": model.get("size"),
                    "modified_at": model.get("modified_at"),
                }
                for model in models
            ]
            logger.info(f"Found {len(model_list)} available models")
            return {"models": model_list}
        else:
            logger.error(f"Error fetching models: {response.status_code}")
            return {
                "error": f"Error fetching models: {response.status_code}",
                "models": [],
            }
    except Exception as e:
        logger.error(f"Error fetching models: {str(e)}")
        logger.error(traceback.format_exc())
        return {"error": str(e), "models": []}


# Endpoint to process text data
@app.post("/api/process-text")
async def process_text(text: str = Form(...), model: Optional[str] = Form(None)):
    logger.info(f"Received text processing request. Text length: {len(text)}")
    try:
        # Use the provided model or fall back to default
        model_to_use = model if model else settings.DEFAULT_MODEL
        logger.info(f"Using model: {model_to_use}")

        # Process the text data using Ollama with a timeout
        try:
            visualization_data = await asyncio.wait_for(
                generate_visualizations_from_text(text, model=model_to_use),
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


# Endpoint to manually retry visualization generation
@app.post("/api/retry-visualization")
async def retry_visualization(text: str = Form(...), model: Optional[str] = Form(None)):
    """Endpoint to manually retry visualization generation"""
    logger.info(f"Received retry visualization request. Text length: {len(text)}")
    try:
        # Use the provided model or fall back to default
        model_to_use = model if model else settings.DEFAULT_MODEL
        logger.info(f"Using model: {model_to_use}")

        # Force a new attempt with the same text
        result = await generate_visualizations_from_text(
            text, max_retries=1, model=model_to_use
        )
        logger.info(
            f"Retry generated {len(result.get('visualizations', []))} visualizations"
        )
        return result
    except Exception as e:
        logger.error(f"Error in retry visualization: {str(e)}")
        logger.error(traceback.format_exc())
        return {"error": str(e), "visualizations": []}


# Endpoint to process CSV file
@app.post("/api/process-csv")
async def process_csv(file: UploadFile = File(...), model: Optional[str] = Form(None)):
    logger.info(f"Received CSV file: {file.filename}, size: {file.size} bytes")
    try:
        # Read the CSV file
        contents = await file.read()
        df = pd.read_csv(io.StringIO(contents.decode("utf-8")))
        logger.info(
            f"Successfully parsed CSV with {len(df)} rows and {len(df.columns)} columns"
        )

        # Use the provided model or fall back to default
        model_to_use = model if model else settings.DEFAULT_MODEL
        logger.info(f"Using model: {model_to_use}")

        # Process the dataframe using Ollama with a timeout
        try:
            visualization_data = await asyncio.wait_for(
                generate_visualizations_from_dataframe(df, model=model_to_use),
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


@app.post("/api/logs/client/add")
async def add_client_log(level: str = Form(...), message: str = Form(...)):
    """Add a log entry from the client side"""
    try:
        logger.info(f"Received client log: level={level}, message={message}")

        # Format the log entry
        timestamp = datetime.now().isoformat()
        level = level.upper()
        source = "client"

        # Write to client log file
        with open("client.log", "a") as f:
            f.write(f"{timestamp} - {source} - {level} - {message}\n")

        return {"status": "success"}
    except Exception as e:
        logger.error(f"Error adding client log: {str(e)}")
        logger.error(traceback.format_exc())
        return {"status": "error", "message": str(e)}


@app.post("/api/logs/client/clear")
async def clear_client_logs():
    """Clear client logs"""
    try:
        logger.info("Clearing client logs")
        with open("client.log", "w") as f:
            f.write("")
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Error clearing client logs: {str(e)}")
        logger.error(traceback.format_exc())
        return {"status": "error", "message": str(e)}


@app.get("/api/logs/client")
async def get_client_logs():
    """Get client logs"""
    try:
        logger.info("Getting client logs")
        try:
            with open("client.log", "r") as f:
                logs = f.read()
        except FileNotFoundError:
            # Create the file if it doesn't exist
            with open("client.log", "w") as f:
                f.write("")
            logs = ""

        return {"logs": logs}
    except Exception as e:
        logger.error(f"Error getting client logs: {str(e)}")
        logger.error(traceback.format_exc())
        return {"status": "error", "message": str(e)}


@app.post("/api/logs/server/clear")
async def clear_server_logs():
    """Clear server logs"""
    try:
        logger.info("Clearing server logs")
        with open("backend.log", "w") as f:
            f.write("")
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Error clearing server logs: {str(e)}")
        logger.error(traceback.format_exc())
        return {"status": "error", "message": str(e)}


@app.get("/api/logs/server")
async def get_server_logs():
    """Get server logs"""
    try:
        logger.info("Getting server logs")
        try:
            with open("backend.log", "r") as f:
                logs = f.read()
        except FileNotFoundError:
            # Create the file if it doesn't exist
            with open("backend.log", "w") as f:
                f.write("")
            logs = ""

        return {"logs": logs}
    except Exception as e:
        logger.error(f"Error getting server logs: {str(e)}")
        logger.error(traceback.format_exc())
        return {"status": "error", "message": str(e)}


async def generate_visualizations_from_text(text, max_retries=3, model=None):
    """Generate visualizations from text using Ollama with retry mechanism"""
    logger.info(f"Generating visualizations from text with max_retries={max_retries}")

    # Get the model to use
    model_to_use = model if model else settings.DEFAULT_MODEL
    logger.info(f"Using model: {model_to_use} for text visualization")

    for attempt in range(max_retries):
        try:
            logger.info(f"Attempt {attempt + 1}/{max_retries}")
            start_time = time.time()

            # Create a prompt for Ollama - simplified for faster processing and avoiding BOS token issues
            prompt = "Analyze this data and create Plotly.js visualizations. Return ONLY valid JSON:\n\nDATA:\n" + text + "\n\nIMPORTANT INSTRUCTIONS:\n1. First, analyze the data to determine what types of visualizations would be most meaningful and informative.\n2. Only generate visualizations that provide genuine insights - don't create charts just to have more visualizations.\n3. Choose appropriate chart types based on the data characteristics (e.g., categorical vs numerical, time series, etc.)\n4. You may create up to 8 visualizations, but only include as many as are truly meaningful for this specific dataset.\n5. Prioritize quality and relevance over quantity.\n\nResponse format:\n{\n  \"visualizations\": [\n    {\n      \"title\": \"Title\",\n      \"description\": \"Description\",\n      \"type\": \"plotly\",\n      \"plotlyData\": [{\n          \"type\": \"bar/pie/scatter/line/heatmap/etc\",\n          \"x\": [...],\n          \"y\": [...],\n          \"labels\": [...],\n          \"values\": [...]\n      }],\n      \"plotlyLayout\": {\n        \"title\": \"Chart Title\"\n      }\n    }\n    // Include only meaningful visualizations, up to a maximum of 8\n  ]\n}"
            logger.info(f"Prompt length: {len(prompt)} characters")

            try:
                # Check if Ollama is available by making a quick request to the models endpoint
                try:
                    check_response = requests.get(
                        f"{settings.OLLAMA_API_URL}/api/tags",
                        timeout=2,  # Very short timeout for the check
                    )
                    if check_response.status_code != 200:
                        logger.error(
                            f"Ollama API is not available: {check_response.status_code}"
                        )
                        logger.info(
                            "Falling back to sample visualizations due to Ollama unavailability"
                        )
                        return generate_sample_plotly_visualizations()
                except requests.exceptions.RequestException as e:
                    logger.error(f"Ollama API connection error: {str(e)}")
                    logger.info(
                        "Falling back to sample visualizations due to Ollama connection error"
                    )
                    return generate_sample_plotly_visualizations()

                # If we get here, Ollama is available, so proceed with the request using AsyncClient
                try:
                    logger.info(f"Using Ollama AsyncClient with host: {settings.OLLAMA_HOST}")
                    # Create client with explicit host parameter
                    # The AsyncClient expects just the host:port without http://
                    client = AsyncClient(host=settings.OLLAMA_HOST)
                    
                    # Prepare the message for the chat endpoint
                    message = {'role': 'user', 'content': prompt}
                    
                    # Make the async request with timeout
                    logger.info(f"Sending async request to Ollama with model {model_to_use}")
                    response = await asyncio.wait_for(
                        client.chat(
                            model=model_to_use, 
                            messages=[message], 
                            format="json",
                            options={"num_predict": 2048, "add_bos": False}  # Prevent duplicate BOS tokens
                        ),
                        timeout=settings.OLLAMA_API_TIMEOUT
                    )
                    
                    logger.info(f"Received async response from Ollama: {type(response)}")
                    
                    # Extract the response content using the proper API
                    if response and hasattr(response, 'message') and hasattr(response.message, 'content'):
                        response_text = response.message.content
                        logger.info(f"Response text length: {len(response_text)}")
                    else:
                        logger.error(f"Unexpected response format from Ollama: {response}")
                        logger.error(f"Response type: {type(response)}, attributes: {dir(response) if response else 'None'}")
                        raise Exception("Unexpected response format from Ollama")

                except asyncio.TimeoutError:
                    logger.error(f"Timeout waiting for Ollama response after {settings.OLLAMA_API_TIMEOUT} seconds")
                    if attempt == max_retries - 1:
                        return generate_sample_plotly_visualizations()
                    continue  # Try again if we haven't reached max retries
                except Exception as e:
                    logger.error(f"Error with Ollama AsyncClient: {str(e)}")
                    logger.info("Falling back to sample visualizations due to Ollama client error")
                    return generate_sample_plotly_visualizations()
                
                # We'll process the response text directly from the AsyncClient response

            except requests.exceptions.Timeout:
                logger.warning(
                    f"Ollama API request timed out after {settings.OLLAMA_API_TIMEOUT} seconds (attempt {attempt+1}/{max_retries})"
                )
                # If this is the last retry, generate a fallback visualization
                if attempt == max_retries - 1:
                    logger.info("Generating fallback visualizations after timeout")
                    return generate_sample_plotly_visualizations()
                else:
                    # Otherwise, raise the exception to trigger a retry
                    raise
            except requests.exceptions.RequestException as e:
                logger.error(f"Request error: {str(e)}")
                raise
            except Exception as e:
                logger.error(f"Error processing Ollama response: {str(e)}")
                raise

            # Response text is already extracted from the AsyncClient response above

            if not response_text:
                logger.warning("No text in Ollama response")
                if attempt == max_retries - 1:
                    return generate_sample_plotly_visualizations()
                continue  # Try again

            # Log a preview of the response
            if response_text:
                preview = (
                    response_text[:100] + "..."
                    if len(response_text) > 100
                    else response_text
                )
                logger.info(f"Response text preview: {preview}")

            # Try to parse the entire response as JSON
            try:
                parsed_json = json.loads(response_text)
                logger.info("Successfully parsed entire response as JSON")

                # Validate that the response has the expected structure
                if (
                    "visualizations" not in parsed_json
                    or not parsed_json["visualizations"]
                ):
                    logger.warning("No visualizations in parsed JSON")
                    if attempt == max_retries - 1:
                        return generate_sample_plotly_visualizations()
                    continue  # Try again

                # Check if the visualizations have the required structure
                valid_visualization = False
                for viz in parsed_json["visualizations"]:
                    if (
                        viz.get("type") == "plotly"
                        and "plotlyData" in viz
                        and "plotlyLayout" in viz
                    ):
                        if (
                            isinstance(viz["plotlyData"], list)
                            and len(viz["plotlyData"]) > 0
                        ):
                            valid_visualization = True
                            break

                if not valid_visualization:
                    logger.warning("No valid Plotly visualizations found in response")
                    if attempt == max_retries - 1:
                        return generate_sample_plotly_visualizations()
                    continue  # Try again

                # If we got here, we have a valid response
                parsed_json["attempts"] = attempt + 1  # Add attempt count to response
                return parsed_json

            except json.JSONDecodeError as e:
                logger.error(f"JSON parsing error: {str(e)}")
                logger.error(
                    f"Attempted to parse (first 100 chars): {response_text[:100]}"
                )

                # Try to extract a JSON substring
                try:
                    # Look for JSON-like patterns
                    match = re.search(r"({.*})", response_text, re.DOTALL)
                    if match:
                        json_str = match.group(1)
                        parsed_json = json.loads(json_str)
                        logger.info("Successfully parsed JSON substring")

                        # Validate that the response has the expected structure
                        if (
                            "visualizations" not in parsed_json
                            or not parsed_json["visualizations"]
                        ):
                            logger.warning("No visualizations in parsed JSON substring")
                            if attempt == max_retries - 1:
                                return generate_sample_plotly_visualizations()
                            continue  # Try again

                        # Check if the visualizations have the required structure
                        valid_visualization = False
                        for viz in parsed_json["visualizations"]:
                            if (
                                viz.get("type") == "plotly"
                                and "plotlyData" in viz
                                and "plotlyLayout" in viz
                            ):
                                if (
                                    isinstance(viz["plotlyData"], list)
                                    and len(viz["plotlyData"]) > 0
                                ):
                                    valid_visualization = True
                                    break

                        if not valid_visualization:
                            logger.warning(
                                "No valid Plotly visualizations found in JSON substring"
                            )
                            if attempt == max_retries - 1:
                                return generate_sample_plotly_visualizations()
                            continue  # Try again

                        # If we got here, we have a valid response
                        parsed_json["attempts"] = (
                            attempt + 1
                        )  # Add attempt count to response
                        return parsed_json

                except Exception as e:
                    logger.error(f"Error extracting JSON substring: {str(e)}")
                    if attempt == max_retries - 1:
                        return generate_sample_plotly_visualizations()
                    continue  # Try again

        except Exception as e:
            logger.error(
                f"Error in generate_visualizations_from_text (attempt {attempt+1}): {str(e)}"
            )
            logger.error(traceback.format_exc())
            if attempt == max_retries - 1:
                return generate_sample_plotly_visualizations()
            # Continue to next attempt

    # If we get here, all retries failed
    logger.warning(f"All {max_retries} attempts failed, using sample visualizations")
    return generate_sample_plotly_visualizations()


async def generate_visualizations_from_dataframe(df, model=None):
    """Generate visualizations from dataframe using Ollama"""
    logger.info("Generating visualizations from dataframe")
    start_time = time.time()

    # Get the model to use
    model_to_use = model if model else settings.DEFAULT_MODEL
    logger.info(f"Using model: {model_to_use} for dataframe visualization")

    # Convert the dataframe to a string representation
    df_str = df.to_string(index=False)
    logger.info(f"Dataframe string representation length: {len(df_str)}")

    # Create a prompt for Ollama - simplified for faster processing and avoiding BOS token issues
    prompt = "Analyze this tabular data and create Plotly.js visualizations. Return ONLY valid JSON:\n\nDATA:\n" + df_str + "\n\nIMPORTANT INSTRUCTIONS:\n1. First, analyze the data to determine what types of visualizations would be most meaningful and informative.\n2. Only generate visualizations that provide genuine insights - don't create charts just to have more visualizations.\n3. Choose appropriate chart types based on the data characteristics (e.g., categorical vs numerical, time series, etc.)\n4. You may create up to 8 visualizations, but only include as many as are truly meaningful for this specific dataset.\n5. Prioritize quality and relevance over quantity.\n\nFor each visualization, include a title, description explaining the insight, and appropriate Plotly configuration."

    # Example JSON to guide the model - simplified
    json_example = """
{
  "visualizations": [
    {
      "title": "Title",
      "description": "Description",
      "type": "plotly",
      "plotlyData": [{
        "type": "bar",
        "x": [1, 2, 3],
        "y": [4, 5, 6]
      }],
      "plotlyLayout": {
        "title": "Chart Title"
      }
    }
  ]
}
"""

    try:
        # Check if Ollama is available by making a quick request to the models endpoint
        try:
            check_response = requests.get(
                f"{settings.OLLAMA_API_URL}/api/tags",
                timeout=2,  # Very short timeout for the check
            )
            if check_response.status_code != 200:
                logger.error(
                    f"Ollama API is not available: {check_response.status_code}"
                )
                logger.info(
                    "Falling back to dataframe visualizations due to Ollama unavailability"
                )
                return generate_dataframe_visualizations(df)
        except requests.exceptions.RequestException as e:
            logger.error(f"Ollama API connection error: {str(e)}")
            logger.info(
                "Falling back to dataframe visualizations due to Ollama connection error"
            )
            return generate_dataframe_visualizations(df)

        # If we get here, Ollama is available, so proceed with the request using AsyncClient
        try:
            logger.info(f"Using Ollama AsyncClient with host: {settings.OLLAMA_HOST}")
            full_prompt = prompt + f"\n\nYour response MUST be valid JSON and nothing else. Format your response like this example:\n{json_example}"
            
            # Create client with explicit host parameter
            # The AsyncClient expects just the host:port without http://
            client = AsyncClient(host=settings.OLLAMA_HOST)
            
            # Prepare the message for the chat endpoint
            message = {'role': 'user', 'content': full_prompt}
            
            # Make the async request with timeout
            logger.info(f"Sending async request to Ollama with model {model_to_use}")
            response = await asyncio.wait_for(
                client.chat(
                    model=model_to_use, 
                    messages=[message], 
                    format="json",
                    options={
                        "num_predict": 2048, 
                        "add_bos": False,  # Prevent duplicate BOS tokens
                        "temperature": 0.7,  # Add some creativity but not too much
                        "top_k": 50,        # Limit token selection to top 50
                        "top_p": 0.95       # Sample from tokens comprising 95% of probability mass
                    }
                ),
                timeout=settings.OLLAMA_API_TIMEOUT
            )
            
            logger.info(f"Received async response from Ollama: {type(response)}")
            
            # Extract the response content using the proper API
            if response and hasattr(response, 'message') and hasattr(response.message, 'content'):
                response_text = response.message.content
                logger.info(f"Response text length: {len(response_text)}")
            else:
                logger.error(f"Unexpected response format from Ollama: {response}")
                logger.error(f"Response type: {type(response)}, attributes: {dir(response) if response else 'None'}")
                raise Exception("Unexpected response format from Ollama")
        except asyncio.TimeoutError:
            logger.error(f"Timeout waiting for Ollama response after {settings.OLLAMA_API_TIMEOUT} seconds")
            return generate_dataframe_visualizations(df)
        except Exception as e:
            logger.error(f"Error with Ollama AsyncClient: {str(e)}")
            logger.info("Falling back to dataframe visualizations due to Ollama client error")
            return generate_dataframe_visualizations(df)
            
        logger.info(
            f"Received response from Ollama in {time.time() - start_time:.2f} seconds"
        )

        # Log the full response for debugging
        if len(response_text) > 0:
            logger.info(f"Response text preview: {response_text[:200]}...")
        else:
            logger.warning("Empty response text from Ollama")

        try:
            # First attempt - try to parse the entire response as JSON
            if len(response_text) > 0:
                try:
                    visualization_data = json.loads(response_text)
                    logger.info("Successfully parsed entire response as JSON")
                    return visualization_data
                except json.JSONDecodeError:
                    logger.info(
                        "Entire response is not valid JSON, trying to extract JSON substring"
                    )

            # Second attempt - find JSON in the response
            json_start = response_text.find("{")
            json_end = response_text.rfind("}") + 1

            if json_start >= 0 and json_end > json_start:
                json_str = response_text[json_start:json_end]
                logger.info(
                    f"Extracted JSON string (first 100 chars): {json_str[:100]}..."
                )
                visualization_data = json.loads(json_str)
                logger.info("Successfully parsed JSON from Ollama response")
            else:
                logger.warning(
                    "No JSON found in Ollama response, generating visualizations from dataframe"
                )
                visualization_data = generate_dataframe_visualizations(df)
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error: {str(e)}")
            logger.error(
                f"Attempted to parse (first 100 chars): {response_text[json_start:json_end][:100]}..."
            )
            visualization_data = generate_dataframe_visualizations(df)
        except Exception as e:
            logger.error(f"Error extracting visualization data: {str(e)}")
            logger.error(traceback.format_exc())
            visualization_data = generate_dataframe_visualizations(df)
    except requests.exceptions.ConnectionError:
        logger.error(
            "Connection error when trying to reach Ollama API. Is Ollama running?"
        )
        return generate_dataframe_visualizations(df)
    except Exception as e:
        logger.error(
            f"Unexpected error in generate_visualizations_from_dataframe: {str(e)}"
        )
        logger.error(traceback.format_exc())
        return generate_dataframe_visualizations(df)

    logger.info(f"Total processing time: {time.time() - start_time:.2f} seconds")
    return visualization_data


def generate_dataframe_visualizations(df):
    """Generate basic visualizations directly from a dataframe"""
    logger.info("Generating fallback visualizations from dataframe")

    visualizations = []

    # Get numeric columns for charts
    numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
    categorical_cols = df.select_dtypes(include=["object"]).columns.tolist()
    date_cols = [col for col in df.columns if 'date' in col.lower() or 'time' in col.lower()]
    
    # Track created visualization types to ensure variety
    created_types = set()
    
    # Analyze data characteristics to determine appropriate visualizations
    data_characteristics = {
        "has_numeric": len(numeric_cols) > 0,
        "has_categorical": len(categorical_cols) > 0,
        "has_dates": len(date_cols) > 0,
        "num_numeric_cols": len(numeric_cols),
        "num_categorical_cols": len(categorical_cols),
        "row_count": len(df),
        "high_cardinality_categorical": any(df[col].nunique() > 10 for col in categorical_cols) if categorical_cols else False,
    }
    
    logger.info(f"Data characteristics: {data_characteristics}")
    
    # Determine which visualization types make sense for this data
    viz_types_to_generate = []
    
    # Always include a table for data overview
    viz_types_to_generate.append("table")
    
    # Bar chart - if we have categorical and numeric columns with reasonable cardinality
    if data_characteristics["has_categorical"] and data_characteristics["has_numeric"]:
        viz_types_to_generate.append("bar")
    
    # Scatter plot - if we have at least 2 numeric columns and enough data points
    if data_characteristics["num_numeric_cols"] >= 2 and data_characteristics["row_count"] > 5:
        viz_types_to_generate.append("scatter")
    
    # Pie chart - if we have categorical data with low cardinality
    if data_characteristics["has_categorical"] and data_characteristics["has_numeric"] and not data_characteristics["high_cardinality_categorical"]:
        viz_types_to_generate.append("pie")
    
    # Line chart - if we have date columns or multiple numeric columns
    if (data_characteristics["has_dates"] and data_characteristics["has_numeric"]) or data_characteristics["num_numeric_cols"] >= 2:
        viz_types_to_generate.append("line")
    
    # Histogram - for numeric data with enough values
    if data_characteristics["has_numeric"] and data_characteristics["row_count"] > 5:
        viz_types_to_generate.append("histogram")
    
    # Box plot - for numeric data by category if we have enough data points per category
    if data_characteristics["has_categorical"] and data_characteristics["has_numeric"] and data_characteristics["row_count"] > 10:
        viz_types_to_generate.append("box")
    
    # Heatmap - if we have multiple numeric columns for correlation analysis
    if data_characteristics["num_numeric_cols"] >= 3:
        viz_types_to_generate.append("heatmap")
    
    # Bubble chart - if we have at least 3 numeric columns
    if data_characteristics["num_numeric_cols"] >= 3:
        viz_types_to_generate.append("bubble")
    
    logger.info(f"Selected visualization types to generate: {viz_types_to_generate}")
    
    # Generate each visualization type that was determined to be appropriate
    # 1. Bar chart
    if "bar" in viz_types_to_generate:
        cat_col = categorical_cols[0]
        num_col = numeric_cols[0]

        try:
            agg_data = df.groupby(cat_col)[num_col].sum().reset_index()

            visualizations.append({
                "type": "plotly",
                "title": f"Sum of {num_col} by {cat_col}",
                "description": f"Bar chart showing the sum of {num_col} for each {cat_col}",
                "plotlyData": [{
                    "type": "bar",
                    "x": agg_data[cat_col].tolist(),
                    "y": agg_data[num_col].tolist(),
                    "name": f"Sum of {num_col}",
                }],
                "plotlyLayout": {
                    "title": f"Sum of {num_col} by {cat_col}",
                    "xaxis": {"title": cat_col},
                    "yaxis": {"title": f"Sum of {num_col}"},
                },
            })

            logger.info(f"Created bar chart visualization with {len(agg_data)} data points")
            created_types.add('bar')
        except Exception as e:
            logger.error(f"Error creating bar chart: {str(e)}")

    # 2. Scatter plot
    if "scatter" in viz_types_to_generate:
        try:
            visualizations.append({
                "type": "plotly",
                "title": f"Relationship between {numeric_cols[0]} and {numeric_cols[1]}",
                "description": f"Scatter plot showing the relationship between {numeric_cols[0]} and {numeric_cols[1]}",
                "plotlyData": [{
                    "type": "scatter",
                    "mode": "markers",
                    "x": df[numeric_cols[0]].head(50).tolist(),
                    "y": df[numeric_cols[1]].head(50).tolist(),
                    "name": f"{numeric_cols[0]} vs {numeric_cols[1]}",
                }],
                "plotlyLayout": {
                    "title": f"{numeric_cols[0]} vs {numeric_cols[1]}",
                    "xaxis": {"title": numeric_cols[0]},
                    "yaxis": {"title": numeric_cols[1]},
                },
            })

            logger.info(f"Created scatter plot visualization with {min(50, len(df))} data points")
            created_types.add('scatter')
        except Exception as e:
            logger.error(f"Error creating scatter plot: {str(e)}")
            
    # 3. Pie chart
    if "pie" in viz_types_to_generate and 'pie' not in created_types:
        try:
            cat_col = categorical_cols[0]
            num_col = numeric_cols[0]
            agg_data = df.groupby(cat_col)[num_col].sum().reset_index()
            
            # Limit to top 8 categories if there are too many
            if len(agg_data) > 8:
                agg_data = agg_data.sort_values(by=num_col, ascending=False).head(8)
                
            visualizations.append({
                "type": "plotly",
                "title": f"Distribution of {num_col} by {cat_col}",
                "description": f"Pie chart showing the distribution of {num_col} across {cat_col} categories",
                "plotlyData": [{
                    "type": "pie",
                    "labels": agg_data[cat_col].tolist(),
                    "values": agg_data[num_col].tolist(),
                    "name": f"Distribution of {num_col}",
                }],
                "plotlyLayout": {
                    "title": f"Distribution of {num_col} by {cat_col}",
                },
            })
            
            logger.info(f"Created pie chart visualization with {len(agg_data)} categories")
            created_types.add('pie')
        except Exception as e:
            logger.error(f"Error creating pie chart: {str(e)}")

    # 4. Line chart
    if "line" in viz_types_to_generate:
        try:
            if len(date_cols) > 0:
                x_col = date_cols[0]
                y_col = numeric_cols[0]
                title = f"Trend of {y_col} over {x_col}"
            else:
                x_col = numeric_cols[0]
                y_col = numeric_cols[1]
                title = f"Line trend of {y_col} vs {x_col}"
                
            # Sort by x column for proper line display
            sorted_df = df.sort_values(by=x_col).head(50)
                
            visualizations.append({
                "type": "plotly",
                "title": title,
                "description": f"Line chart showing the trend of {y_col} over {x_col}",
                "plotlyData": [{
                    "type": "scatter",
                    "mode": "lines+markers",
                    "x": sorted_df[x_col].tolist(),
                    "y": sorted_df[y_col].tolist(),
                    "name": y_col,
                }],
                "plotlyLayout": {
                    "title": title,
                    "xaxis": {"title": x_col},
                    "yaxis": {"title": y_col},
                },
            })
            
            logger.info(f"Created line chart visualization with {len(sorted_df)} data points")
            created_types.add('line')
        except Exception as e:
            logger.error(f"Error creating line chart: {str(e)}")
    
    # 5. Histogram
    if "histogram" in viz_types_to_generate and 'histogram' not in created_types:
        try:
            num_col = numeric_cols[0]
            
            visualizations.append({
                "type": "plotly",
                "title": f"Distribution of {num_col}",
                "description": f"Histogram showing the distribution of {num_col} values",
                "plotlyData": [{
                    "type": "histogram",
                    "x": df[num_col].tolist(),
                    "name": num_col,
                }],
                "plotlyLayout": {
                    "title": f"Distribution of {num_col}",
                    "xaxis": {"title": num_col},
                    "yaxis": {"title": "Count"},
                },
            })
            
            logger.info(f"Created histogram visualization with {len(df)} data points")
            created_types.add('histogram')
        except Exception as e:
            logger.error(f"Error creating histogram: {str(e)}")
            
    # 6. Box plot
    if "box" in viz_types_to_generate and 'box' not in created_types:
        try:
            cat_col = categorical_cols[0]
            num_col = numeric_cols[0]
            
            # Create box plot data by category
            box_data = []
            for category in df[cat_col].unique()[:8]:  # Limit to 8 categories
                values = df[df[cat_col] == category][num_col].tolist()
                box_data.append({
                    "type": "box",
                    "y": values,
                    "name": str(category),
                    "boxpoints": "outliers"
                })
                
            visualizations.append({
                "type": "plotly",
                "title": f"Distribution of {num_col} by {cat_col}",
                "description": f"Box plot showing the distribution of {num_col} across {cat_col} categories",
                "plotlyData": box_data,
                "plotlyLayout": {
                    "title": f"Distribution of {num_col} by {cat_col}",
                    "yaxis": {"title": num_col},
                },
            })
            
            logger.info(f"Created box plot visualization with {len(box_data)} categories")
            created_types.add('box')
        except Exception as e:
            logger.error(f"Error creating box plot: {str(e)}")
    
    # 7. Heatmap
    if "heatmap" in viz_types_to_generate and 'heatmap' not in created_types:
        try:
            # Create correlation matrix
            corr_matrix = df[numeric_cols].corr().round(2)
            
            # Create heatmap data
            visualizations.append({
                "type": "plotly",
                "title": "Correlation Heatmap",
                "description": "Heatmap showing correlations between numeric variables",
                "plotlyData": [{
                    "type": "heatmap",
                    "z": corr_matrix.values.tolist(),
                    "x": corr_matrix.columns.tolist(),
                    "y": corr_matrix.index.tolist(),
                    "colorscale": "Viridis",
                }],
                "plotlyLayout": {
                    "title": "Correlation Heatmap",
                },
            })
            
            logger.info(f"Created heatmap visualization with {len(numeric_cols)} variables")
            created_types.add('heatmap')
        except Exception as e:
            logger.error(f"Error creating heatmap: {str(e)}")
    
    # 8. Bubble chart
    if "bubble" in viz_types_to_generate and 'bubble' not in created_types:
        try:
            visualizations.append({
                "type": "plotly",
                "title": f"Bubble Chart: {numeric_cols[0]} vs {numeric_cols[1]} (size: {numeric_cols[2]})",
                "description": f"Bubble chart showing relationship between {numeric_cols[0]}, {numeric_cols[1]}, and {numeric_cols[2]}",
                "plotlyData": [{
                    "type": "scatter",
                    "mode": "markers",
                    "x": df[numeric_cols[0]].head(50).tolist(),
                    "y": df[numeric_cols[1]].head(50).tolist(),
                    "marker": {
                        "size": df[numeric_cols[2]].head(50).tolist(),
                        "sizemode": "area",
                        "sizeref": 2.0 * max(df[numeric_cols[2]].head(50)) / (40**2),
                        "sizemin": 4
                    },
                    "name": f"{numeric_cols[0]} vs {numeric_cols[1]} (size: {numeric_cols[2]})",
                }],
                "plotlyLayout": {
                    "title": f"Bubble Chart: {numeric_cols[0]} vs {numeric_cols[1]}",
                    "xaxis": {"title": numeric_cols[0]},
                    "yaxis": {"title": numeric_cols[1]},
                },
            })
            
            logger.info(f"Created bubble chart visualization with {min(50, len(df))} data points")
            created_types.add('bubble')
        except Exception as e:
            logger.error(f"Error creating bubble chart: {str(e)}")
    
    # Table visualization
    if "table" in viz_types_to_generate and 'table' not in created_types:
        try:
            # Create a table visualization using Plotly
            headers = df.columns.tolist()
            cells = [df[col].head(10).tolist() for col in headers]

            visualizations.append({
                "type": "plotly",
                "title": "Data Table",
                "description": "Table showing a sample of the data",
                "plotlyData": [{
                    "type": "table",
                    "header": {
                        "values": headers,
                        "align": "center",
                        "line": {"width": 1, "color": "black"},
                        "fill": {"color": "grey"},
                        "font": {
                            "family": "Arial",
                            "size": 12,
                            "color": "white",
                        },
                    },
                    "cells": {
                        "values": cells,
                        "align": "center",
                        "line": {"color": "black", "width": 1},
                        "font": {
                            "family": "Arial",
                            "size": 11,
                            "color": "black",
                        },
                    },
                }],
                "plotlyLayout": {"title": "Data Table"},
            })

            logger.info(f"Created table visualization with {len(headers)} columns")
            created_types.add('table')
        except Exception as e:
            logger.error(f"Error creating table visualization: {str(e)}")

    return {"visualizations": visualizations}


def generate_sample_plotly_visualizations():
    """Generate sample Plotly visualizations when parsing fails"""
    logger.info("Generating sample Plotly visualizations")
    return {
        "visualizations": [
            {
                "type": "plotly",
                "plotlyData": [
                    {
                        "x": ["A", "B", "C", "D"],
                        "y": [10, 15, 7, 12],
                        "type": "bar",
                        "name": "Sample Data",
                    }
                ],
                "plotlyLayout": {
                    "title": "Sample Bar Chart",
                    "xaxis": {"title": "Category"},
                    "yaxis": {"title": "Value"},
                },
                "title": "Sample Bar Chart",
                "description": "A sample bar chart showing placeholder data",
            },
            {
                "type": "plotly",
                "plotlyData": [
                    {
                        "values": [30, 70],
                        "labels": ["Group 1", "Group 2"],
                        "type": "pie",
                        "name": "Sample Pie Data",
                    }
                ],
                "plotlyLayout": {"title": "Sample Pie Chart"},
                "title": "Sample Pie Chart",
                "description": "A sample pie chart showing placeholder data",
            },
            {
                "type": "plotly",
                "plotlyData": [
                    {
                        "x": [1, 2, 3, 4, 5],
                        "y": [10, 15, 13, 17, 20],
                        "type": "scatter",
                        "mode": "lines+markers",
                        "name": "Sample Series",
                    }
                ],
                "plotlyLayout": {
                    "title": "Sample Line Chart",
                    "xaxis": {"title": "X"},
                    "yaxis": {"title": "Y"},
                },
                "title": "Sample Line Chart",
                "description": "A sample line chart showing placeholder data",
            },
        ]
    }


if __name__ == "__main__":
    import uvicorn

    logger.info("Starting Visualize-It backend server")
    uvicorn.run(app, host="0.0.0.0", port=8000)
