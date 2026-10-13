# ai/llms/models.py
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from PIL import Image
import json
import logging
from typing import Optional, Dict, Any, List, Union
from pathlib import Path
import io
import re
import time
from .config import settings

# Configure logging
logger = logging.getLogger(__name__)

class NanoBananaClient:
    def __init__(self):
        genai.configure(api_key=settings.GEMINI_API_KEY)
        # Use the model from settings instead of hardcoded "pro"
        self.model_name = settings.NANOBANANA_MODEL
        self.model = genai.GenerativeModel(self.model_name)

    
    def roast_resume(self, image_bytes: bytes, prompt: str) -> Dict[str, Any]:
        try:
            image = Image.open(io.BytesIO(image_bytes))
            
            # Use safety settings and generation config for production stability
            generation_config = {"temperature": 0.4, "top_p": 0.9}
            
            response = self.model.generate_content(
                [prompt, image],
                generation_config=generation_config
            )

            # Metadata extraction
            usage = response.usage_metadata
            input_tokens = usage.prompt_token_count or 0
            output_tokens = usage.candidates_token_count or 0
            
            result = {
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": input_tokens + output_tokens,
                "image_bytes": None,
                "text": None
            }

            # Check for Image Output (Specific to Image-to-Image models)
            for part in response.candidates[0].content.parts:
                if part.inline_data:
                    result["image_bytes"] = part.inline_data.data
                    return result

            # Fallback to text if the model explains the roast instead of drawing it
            if response.text:
                result["text"] = response.text
                return result

            raise ValueError("API returned successful but contains no valid data parts.")

        except Exception as e:
            logger.error(f"LLM Call failed: {str(e)}")
            raise

class GeminiClient:
    """
    Professional Gemini API client for various AI tasks including resume parsing.
    """
    
    def __init__(self):
        """Initialize the Gemini client with configuration from settings."""
        self._configure_api()
        self._model = None
        self._initialize_model()
    
    def _configure_api(self) -> None:
        """Configure the Gemini API with the provided API key."""
        try:
            genai.configure(api_key=settings.GEMINI_API_KEY)
            logger.info("Gemini API configured successfully")
        except Exception as e:
            logger.error(f"Failed to configure Gemini API: {str(e)}")
            raise
    
    def _initialize_model(self) -> None:
        """Initialize the Gemini model with safety settings and generation config."""
        try:
            generation_config = genai.types.GenerationConfig(
                temperature=settings.GEMINI_TEMPERATURE,
                max_output_tokens=settings.GEMINI_MAX_OUTPUT_TOKENS,
                top_p=settings.GEMINI_TOP_P,
                top_k=settings.GEMINI_TOP_K,
                response_mime_type="application/json",
            )
            
            # Configure safety settings to allow most content for professional use
            safety_settings = {
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            }
            
            self._model = genai.GenerativeModel(
                model_name=settings.GEMINI_MODEL_NAME,
                generation_config=generation_config,
                safety_settings=safety_settings
            )
            logger.info(f"Gemini model {settings.GEMINI_MODEL_NAME} initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Gemini model: {str(e)}")
            raise
    
    def generate_content_with_file(
        self, 
        prompt: str, 
        file_path: Optional[Union[str, Path]] = None,
        file_data: Optional[bytes] = None,
        mime_type: str = "application/pdf"
    ) -> Dict[str, Any]:
        """
        Generate content using Gemini with file input (PDF, image, etc.).
        
        Args:
            prompt: The text prompt to send to the model
            file_path: Path to the file to upload (optional)
            file_data: Raw file data as bytes (optional)
            mime_type: MIME type of the file
            
        Returns:
            Dictionary containing 'text', 'usage_metadata', and 'model_version'
            
        Raises:
            ValueError: If neither file_path nor file_data is provided
            Exception: For API errors or other failures
        """
        if not file_path and not file_data:
            raise ValueError("Either file_path or file_data must be provided")
        
        try:
            # Upload file to Gemini
            if file_path:
                file_path = Path(file_path)
                if not file_path.exists():
                    raise FileNotFoundError(f"File not found: {file_path}")
                
                uploaded_file = genai.upload_file(
                    path=str(file_path),
                    mime_type=mime_type
                )
            else:
                # Create a temporary file-like object from bytes
                uploaded_file = genai.upload_file(
                    path=io.BytesIO(file_data),
                    mime_type=mime_type
                )
            
            logger.info(f"File uploaded successfully: {uploaded_file.name}")
            
            # Generate content with the uploaded file
            t0 = time.perf_counter()
            response = self._model.generate_content([prompt, uploaded_file])
            duration_ms = int((time.perf_counter() - t0) * 1000)
            logger.info(json.dumps({"event": "external_call", "service": "gemini", "operation": "generate_with_file", "duration_ms": duration_ms}))
            
            if not response.text:
                logger.error("Empty response from Gemini API")
                raise Exception("Empty response from Gemini API")
            
            logger.info("Content generated successfully")
            
            # Extract metadata
            usage_metadata = {}
            if hasattr(response, "usage_metadata"):
                usage_metadata = {
                    "prompt_token_count": response.usage_metadata.prompt_token_count,
                    "candidates_token_count": response.usage_metadata.candidates_token_count,
                    "total_token_count": response.usage_metadata.total_token_count
                }
            
            model_version = "unknown"
            # Try to get model_version from response if available, otherwise use settings
            if hasattr(response, "model_version"):
                model_version = response.model_version
            elif hasattr(response, "result") and hasattr(response.result, "model_version"):
                model_version = response.result.model_version
            else:
                model_version = settings.GEMINI_MODEL_NAME

            return {
                "text": response.text.strip(),
                "usage_metadata": usage_metadata,
                "model_version": model_version
            }
            
        except Exception as e:
            logger.error(f"Failed to generate content with file: {str(e)}")
            raise
    
    def generate_content(self, prompt: str) -> Dict[str, Any]:
        """
        Generate content using Gemini with text-only input.
        
        Args:
            prompt: The text prompt to send to the model
            
        Returns:
            Dictionary containing 'text', 'usage_metadata', and 'model_version'
        """
        try:
            t0 = time.perf_counter()
            response = self._model.generate_content(prompt)
            duration_ms = int((time.perf_counter() - t0) * 1000)
            logger.info(json.dumps({"event": "external_call", "service": "gemini", "operation": "generate", "duration_ms": duration_ms}))
            
            if not response.text:
                logger.error("Empty response from Gemini API")
                raise Exception("Empty response from Gemini API")
            
            logger.info("Text content generated successfully")
            
            # Extract metadata
            usage_metadata = {}
            if hasattr(response, "usage_metadata"):
                usage_metadata = {
                    "prompt_token_count": response.usage_metadata.prompt_token_count,
                    "candidates_token_count": response.usage_metadata.candidates_token_count,
                    "total_token_count": response.usage_metadata.total_token_count
                }
            
            model_version = "unknown"
            if hasattr(response, "model_version"):
                model_version = response.model_version
            elif hasattr(response, "result") and hasattr(response.result, "model_version"):
                model_version = response.result.model_version
            else:
                model_version = settings.GEMINI_MODEL_NAME

            return {
                "text": response.text.strip(),
                "usage_metadata": usage_metadata,
                "model_version": model_version
            }
            
        except Exception as e:
            logger.error(f"Failed to generate text content: {str(e)}")
            raise
    
    def parse_json_response(self, response: str) -> Dict[str, Any]:
        """
        Parse JSON response from Gemini, handling potential formatting issues.
        
        Args:
            response: Raw response string from Gemini
            
        Returns:
            Parsed JSON as dictionary
            
        Raises:
            json.JSONDecodeError: If response cannot be parsed as JSON
        """
        try:
            s = response.strip()
            if s.startswith("```json"):
                s = s[7:]
            elif s.startswith("```"):
                s = s[3:]
            if s.endswith("```"):
                s = s[:-3]
            s = s.strip()
            return json.loads(s)
        except json.JSONDecodeError:
            cleaned = s.replace("\r\n", "\\n").replace("\n", "\\n")
            cleaned = cleaned.replace("“", '"').replace("”", '"').replace("’", "'")
            cleaned = re.sub(r",\s*([}\]])", r"\1", cleaned)
            start = cleaned.find("{")
            end = cleaned.rfind("}")
            if start != -1 and end != -1 and end > start:
                cleaned = cleaned[start:end + 1]
            parsed_json = json.loads(cleaned)
            logger.info("JSON response parsed successfully after cleanup")
            return parsed_json
    
    def validate_connection(self) -> bool:
        """
        Validate the connection to Gemini API.
        
        Returns:
            True if connection is valid, False otherwise
        """
        try:
            test_response = self.generate_content("Test connection")
            return bool(test_response)
        except Exception as e:
            logger.error(f"Connection validation failed: {str(e)}")
            return False

# Global client instance
gemini_client = GeminiClient()
nano_banana_client = NanoBananaClient()

# Unified multi-provider gateway. Existing clients above remain compatibility
# exports for applications already using the Gemini-specific API.
from .gateway import llm_gateway
