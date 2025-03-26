import requests
import json
from typing import Dict, Any, List, Optional


class OllamaService:
    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url
        self.generate_endpoint = f"{base_url}/api/generate"

    def generate(self, prompt: str, model: str = "llama3") -> Dict[str, Any]:
        """
        Generate a response from Ollama
        """
        try:
            response = requests.post(
                self.generate_endpoint,
                json={"model": model, "prompt": prompt, "stream": False},
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error calling Ollama API: {e}")
            return {"error": str(e)}

    def extract_visualization_data(self, text_data: str) -> Dict[str, Any]:
        """
        Extract structured data from text for visualization
        """
        prompt = f"""
        Analyze the following text and extract structured data suitable for visualization:

        {text_data}

        Return a JSON object with the following structure:
        {{
            "visualizations": [
                {{
                    "type": "bar|line|pie|scatter",
                    "title": "Descriptive title",
                    "data": [...],
                    "xAxis": "Label for x-axis",
                    "yAxis": "Label for y-axis"
                }}
            ]
        }}

        Identify 3-4 different visualizations that would be appropriate for this data.
        """

        response = self.generate(prompt)
        return self._extract_json_from_response(response)

    def suggest_visualizations(self, structured_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Suggest visualizations for structured data
        """
        prompt = f"""
        Given this structured data:

        {json.dumps(structured_data)}

        Suggest 3-4 different D3.js visualizations that would effectively represent this data.
        Return a JSON object with visualization specifications.
        """

        response = self.generate(prompt)
        return self._extract_json_from_response(response)

    def _extract_json_from_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract JSON from Ollama response
        """
        if "error" in response:
            return {"error": response["error"]}

        response_text = response.get("response", "")

        # Try to find JSON in the response
        try:
            # Look for JSON between triple backticks
            import re

            json_match = re.search(r"```json\s*([\s\S]*?)\s*```", response_text)
            if json_match:
                return json.loads(json_match.group(1))

            # Try to find JSON between curly braces
            json_start = response_text.find("{")
            json_end = response_text.rfind("}") + 1
            if json_start >= 0 and json_end > json_start:
                return json.loads(response_text[json_start:json_end])

            # If no JSON found, return error
            return {"error": "Could not extract JSON from response"}
        except json.JSONDecodeError:
            return {"error": "Invalid JSON in response"}
