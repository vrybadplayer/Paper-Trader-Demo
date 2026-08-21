"""
LLM Client for Ollama Integration
Provides interfaces for System 1 (Worker: qwen2.5-coder:7b) and System 2 (Critic: deepseek-r1:14b),
loading personas from markdown files, querying tools manifest, and parsing structured JSON.
"""

import os
import json
import re
import urllib.request
import urllib.error
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

logger = logging.getLogger(__name__)

class OllamaClient:
    """
    Client for interacting with local Ollama instance (http://localhost:11434).
    Handles prompt framing, persona injection, response parsing, and fallback logic.
    """
    
    def __init__(self, base_url: str = "http://localhost:11434", timeout: int = 30):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._persona_cache: Dict[str, str] = {}
        self._manifest_cache: Dict[str, str] = {}
    
    def is_available(self) -> bool:
        """Check if the local Ollama server is reachable."""
        try:
            req = urllib.request.Request(
                f"{self.base_url}/api/tags",
                headers={"User-Agent": "PaperTraderBot"}
            )
            with urllib.request.urlopen(req, timeout=3) as resp:
                return resp.status == 200
        except Exception:
            return False

    def get_available_models(self) -> List[str]:
        """Get list of available models from the Ollama server."""
        try:
            req = urllib.request.Request(
                f"{self.base_url}/api/tags",
                headers={"User-Agent": "PaperTraderBot"}
            )
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                models = data.get("models", [])
                return [m.get("name") for m in models if m.get("name")]
        except Exception as e:
            logger.warning(f"Failed to get available models from Ollama: {e}")
            return []

    def load_persona(self, filename: str) -> str:
        """Load persona markdown file from trading_bot_core/personas/."""
        if filename in self._persona_cache:
            return self._persona_cache[filename]
        
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        persona_path = os.path.join(base_dir, "personas", filename)
        
        if os.path.exists(persona_path):
            try:
                with open(persona_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    self._persona_cache[filename] = content
                    return content
            except Exception as e:
                logger.warning(f"Failed to read persona file {filename}: {e}")
        
        return ""

    def load_manifest(self, filename: str) -> str:
        """Load tool manifest markdown file from trading_bot_core/tools_registry/."""
        if filename in self._manifest_cache:
            return self._manifest_cache[filename]
        
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        manifest_path = os.path.join(base_dir, "tools_registry", filename)
        
        if os.path.exists(manifest_path):
            try:
                with open(manifest_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    self._manifest_cache[filename] = content
                    return content
            except Exception as e:
                logger.warning(f"Failed to read manifest file {filename}: {e}")
        
        return ""

    def chat(self, model: str, messages: List[Dict[str, str]], temperature: float = 0.0, format_json: bool = False) -> Dict[str, Any]:
        """
        Send a chat completion request to the Ollama HTTP server.
        
        Args:
            model: Name of the model (e.g., 'qwen2.5-coder:7b', 'deepseek-r1:14b')
            messages: List of message objects with 'role' and 'content'
            temperature: Sampling temperature
            format_json: Whether to enforce JSON output format
            
        Returns:
            Dict containing 'raw_text', 'thinking', 'json_data', and 'status'
        """
        payload = {
            "model": model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature
            }
        }
        if format_json:
            payload["format"] = "json"
        
        try:
            req = urllib.request.Request(
                f"{self.base_url}/api/chat",
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json", "User-Agent": "PaperTraderBot"}
            )
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                content = data.get("message", {}).get("content", "")
                
                # Extract DeepSeek <think>...</think> reasoning tags
                thinking = ""
                clean_content = content
                think_match = re.search(r"<think>(.*?)</think>", content, re.DOTALL)
                if think_match:
                    thinking = think_match.group(1).strip()
                    clean_content = re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL).strip()
                
                # Parse JSON if present
                json_data = self._extract_json(clean_content)
                
                return {
                    "status": "success",
                    "raw_text": clean_content,
                    "thinking": thinking,
                    "json_data": json_data
                }
        except urllib.error.URLError as e:
            logger.warning(f"Ollama server not reachable at {self.base_url}: {e}")
            return {"status": "unavailable", "error": str(e), "raw_text": "", "thinking": "", "json_data": None}
        except Exception as e:
            logger.error(f"Error communicating with Ollama: {e}")
            return {"status": "error", "error": str(e), "raw_text": "", "thinking": "", "json_data": None}

    def _extract_json(self, text: str) -> Optional[Dict[str, Any]]:
        """Extract structured JSON from model output or code blocks."""
        if not text:
            return None
        
        # Try direct JSON parse
        try:
            return json.loads(text.strip())
        except Exception:
            pass
        
        # Try markdown code block ```json ... ```
        block_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
        if block_match:
            try:
                return json.loads(block_match.group(1).strip())
            except Exception:
                pass
        
        # Try finding first { and matching outermost }
        first_brace = text.find("{")
        last_brace = text.rfind("}")
        if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
            try:
                return json.loads(text[first_brace:last_brace + 1])
            except Exception:
                pass
        
        return None
