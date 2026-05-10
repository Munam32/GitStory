import os
import json
import httpx
import logging

log = logging.getLogger(__name__)

class LLMError(Exception):
    pass

class LLMClient:
    def __init__(self):
        # Aligning with SRS Section 3.3 for OpenRouter Integration
        self.api_key = os.getenv("OPENROUTER_API_KEY")
        if not self.api_key:
            log.warning("OPENROUTER_API_KEY is missing. Network calls will fail.")
            
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"
        
        # Using Mistral Nemo via OpenRouter. 
        # You can change this to "google/gemini-2.5-pro" or any other supported model later.
        self.model = "nvidia/nemotron-3-super-120b-a12b:free" 
        
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://gitstory.local", # Optional, but recommended by OpenRouter
            "X-Title": "GitStory Auto-Documentation", # Optional, helps identify traffic in your dashboard
        }

    async def complete(self, prompt: str, max_tokens: int = 2000) -> str:
        """Standard text completion for the README."""
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": 0.2 
        }
        return await self._make_request(payload)

    async def complete_json(self, prompt: str, max_tokens: int = 1500) -> dict | list:
        """Forces the LLM to return structured JSON."""
        system_instruction = (
            "You are a strict data formatting system. "
            "You must return ONLY valid, raw JSON. "
            "Do NOT wrap your response in markdown code blocks (e.g., ```json). "
            "Do NOT include any conversational text."
        )
        
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": max_tokens,
            "temperature": 0.1,
        }
        
        response_text = await self._make_request(payload)
        
        try:
            cleaned_text = response_text.strip()
            if cleaned_text.startswith("```json"):
                cleaned_text = cleaned_text[7:-3].strip()
            elif cleaned_text.startswith("```"):
                cleaned_text = cleaned_text[3:-3].strip()
                
            return json.loads(cleaned_text)
        except json.JSONDecodeError as exc:
            log.error(f"JSON Parsing failed. Raw LLM Output:\n{response_text}")
            raise LLMError(f"LLM failed to return valid JSON: {exc}")

    async def _make_request(self, payload: dict) -> str:
        if not self.api_key:
            raise LLMError("FATAL: OPENROUTER_API_KEY environment variable is not set.")
            
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    self.base_url, 
                    headers=self.headers, 
                    json=payload,
                    timeout=60.0 
                )
                response.raise_for_status()
                data = response.json()
                return data["choices"][0]["message"]["content"]
            except httpx.HTTPStatusError as exc:
                raise LLMError(f"HTTP Error {exc.response.status_code}: {exc.response.text}")
            except Exception as exc:
                raise LLMError(f"Network request failed: {str(exc)}")