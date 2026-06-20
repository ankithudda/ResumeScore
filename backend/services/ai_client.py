import os
import json
import httpx
import logging
from typing import Type, TypeVar, Any, Dict
from pydantic import BaseModel, ValidationError

logger = logging.getLogger("ResumeScore.AIClient")
NVIDIA_API_URL = "https://integrate.api.nvidia.com/v1/chat/completions"

T = TypeVar("T", bound=BaseModel)

async def call_nvidia_llm(prompt: str, temperature: float = 0.6, max_tokens: int = 1200) -> dict:
    """Executes the raw HTTP request to the NVIDIA LLM API endpoint and extracts clean text."""
    api_key = os.getenv("NVIDIA_API_KEY")
    
    if not api_key:
        logger.error("NVIDIA_API_KEY environment variable is missing.")
        return {"error": "Missing NVIDIA API Key. Please run $env:NVIDIA_API_KEY='your_key' in your backend terminal."}

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "meta/llama-3.3-70b-instruct", 
        "messages": [{"role": "user", "content": prompt}],
        "temperature": temperature,
        "max_tokens": max_tokens
    }

    content = ""
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(NVIDIA_API_URL, headers=headers, json=payload)
            
            if response.status_code != 200:
                logger.error(f"NVIDIA API Error {response.status_code}: {response.text}")
                return {"error": f"NVIDIA rejected the request (Code {response.status_code}). Check backend console for details."}

            data = response.json()
            content = data["choices"][0]["message"]["content"]

            if not content:
                logger.error(f"NVIDIA API returned an empty response. Full data: {data}")
                return {"error": "The AI model returned an empty response. Please try again."}

            clean_text = content.strip()
            
            if "```json" in clean_text:
                clean_text = clean_text.split("```json")[1].split("```")[0]
            elif "```" in clean_text:
                clean_text = clean_text.split("```")[1].split("```")[0]

            clean_text = clean_text.replace("{{", "{").replace("}}", "}")
                
            start_idx = clean_text.find('{')
            end_idx = clean_text.rfind('}')
            
            if start_idx != -1 and end_idx != -1:
                clean_text = clean_text[start_idx:end_idx+1]

            return json.loads(clean_text, strict=False)

    except httpx.ReadTimeout:
        logger.error("NVIDIA API timed out.")
        return {"error": "NVIDIA API took too long to respond. Please try again."}
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse LLM JSON: {str(e)}\nRaw Output: {content}")
        return {"error": "The AI returned an invalid response format. Please try again."}
    except Exception as e:
        logger.error(f"Unexpected error in call_nvidia_llm: {str(e)}")
        raise RuntimeError(f"An unexpected AI connection error occurred: {str(e)}") from e


async def call_and_validate(
    prompt: str, 
    schema: Type[T], 
    temperature: float = 0.5, 
    max_tokens: int = 1200
) -> Dict[str, Any]:
    """
    Centralized utility to execute LLM calls and validate the output against a Pydantic schema.
    Eliminates redundant try/except boilerplate across all domain services.
    """
    raw_response = await call_nvidia_llm(prompt, temperature=temperature, max_tokens=max_tokens)
    
    if not raw_response or "error" in raw_response:
        error_msg = raw_response.get("error", "Unknown AI Service Error") if isinstance(raw_response, dict) else "Empty response"
        logger.error(f"LLM Processing Exception: {error_msg}")
        raise RuntimeError(f"AI Service Failure: {error_msg}")
        
    try:
        validated_data = schema(**raw_response)
        return validated_data.model_dump()
    except ValidationError as e:
        logger.error(f"Schema contract violation for {schema.__name__}: {str(e)} | Raw Output: {raw_response}")
        raise ValueError(f"AI engine returned inconsistent structure failing {schema.__name__} validation constraints.") from e
    except Exception as e:
        logger.error(f"Unexpected parsing anomaly for {schema.__name__}: {str(e)} | Raw Output: {raw_response}")
        raise ValueError("Unexpected error processing AI response payload structure.") from e