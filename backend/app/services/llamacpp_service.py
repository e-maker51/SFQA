"""
llama.cpp Service - LLM Integration via llama.cpp server API
Provides compatible interface with OllamaService
"""
import requests
import json
from typing import Generator, List, Dict, Any, Optional
from flask import current_app
import logging

logger = logging.getLogger(__name__)


class LlamaCppService:
    """Service for interacting with llama.cpp server API"""

    def __init__(self, base_url: str = None):
        self.base_url = base_url or current_app.config.get('LLAMACPP_BASE_URL', 'http://localhost:8080')

    def get_models(self) -> List[Dict[str, Any]]:
        """Get list of available models (llama.cpp typically serves one model)"""
        try:
            # llama.cpp server doesn't have a /models endpoint
            # Return current model info based on server health
            response = requests.get(f"{self.base_url}/health", timeout=10)
            if response.status_code == 200:
                return [{
                    'name': 'llamacpp-model',
                    'model': 'llamacpp-model',
                    'details': {'family': 'llamacpp'}
                }]
            return []
        except Exception as e:
            logger.error(f"Failed to get models: {e}")
            return []

    def generate(self, model: str, prompt: str, system: str = None,
                 context: List[int] = None, options: dict = None) -> str:
        """Generate response (non-streaming) using /completion endpoint"""
        try:
            # Build the full prompt
            full_prompt = self._build_prompt(prompt, system, context)

            payload = {
                "prompt": full_prompt,
                "stream": False,
                "n_predict": options.get('num_predict', -1) if options else -1,
                "temperature": options.get('temperature', 0.7) if options else 0.7,
                "top_p": options.get('top_p', 0.9) if options else 0.9,
                "top_k": options.get('top_k', 40) if options else 40,
                "repeat_penalty": options.get('repeat_penalty', 1.1) if options else 1.1,
                "stop": options.get('stop', []) if options else [],
            }

            response = requests.post(
                f"{self.base_url}/completion",
                json=payload,
                timeout=300
            )
            response.raise_for_status()
            result = response.json()
            return result.get('content', '')

        except Exception as e:
            logger.error(f"Generation failed: {e}")
            raise

    def generate_stream(self, model: str, prompt: str, system: str = None,
                        context: List[int] = None, options: dict = None) -> Generator:
        """Generate response with streaming using /completion endpoint"""
        try:
            # Build the full prompt
            full_prompt = self._build_prompt(prompt, system, context)

            payload = {
                "prompt": full_prompt,
                "stream": True,
                "n_predict": options.get('num_predict', -1) if options else -1,
                "temperature": options.get('temperature', 0.7) if options else 0.7,
                "top_p": options.get('top_p', 0.9) if options else 0.9,
                "top_k": options.get('top_k', 40) if options else 40,
                "repeat_penalty": options.get('repeat_penalty', 1.1) if options else 1.1,
                "stop": options.get('stop', []) if options else [],
            }

            response = requests.post(
                f"{self.base_url}/completion",
                json=payload,
                stream=True,
                timeout=300
            )
            response.raise_for_status()

            for line in response.iter_lines():
                if line:
                    try:
                        data = json.loads(line.decode('utf-8').lstrip('data: '))
                        yield data
                    except (json.JSONDecodeError, UnicodeDecodeError):
                        continue

        except Exception as e:
            logger.error(f"Streaming generation failed: {e}")
            raise

    def chat(self, model: str, messages: List[Dict[str, str]],
             options: dict = None, think: bool = None) -> str:
        """Chat completion (non-streaming) using /chat/completions endpoint"""
        try:
            payload = {
                "model": model or "llamacpp-model",
                "messages": messages,
                "stream": False,
                "temperature": options.get('temperature', 0.7) if options else 0.7,
                "top_p": options.get('top_p', 0.9) if options else 0.9,
                "top_k": options.get('top_k', 40) if options else 40,
                "max_tokens": options.get('num_predict', -1) if options else -1,
            }

            response = requests.post(
                f"{self.base_url}/v1/chat/completions",
                json=payload,
                timeout=300
            )
            response.raise_for_status()
            result = response.json()
            return result.get('choices', [{}])[0].get('message', {}).get('content', '')

        except Exception as e:
            logger.error(f"Chat failed: {e}")
            raise

    def _messages_to_prompt(self, messages: List[Dict[str, str]]) -> tuple:
        """Convert chat messages to prompt + system for fallback"""
        system = ''
        prompt_parts = []

        for msg in messages:
            role = msg.get('role', '')
            content = msg.get('content', '')
            if role == 'system':
                system = content
            elif role == 'user':
                prompt_parts.append(f"User: {content}")
            elif role == 'assistant':
                prompt_parts.append(f"Assistant: {content}")

        prompt_parts.append("Assistant:")
        return '\n\n'.join(prompt_parts), system

    def chat_stream(self, model: str, messages: List[Dict[str, str]],
                    options: dict = None, think: bool = True) -> Generator:
        """Chat completion with streaming using /chat/completions endpoint"""
        try:
            payload = {
                "model": model or "llamacpp-model",
                "messages": messages,
                "stream": True,
                "temperature": options.get('temperature', 0.7) if options else 0.7,
                "top_p": options.get('top_p', 0.9) if options else 0.9,
                "top_k": options.get('top_k', 40) if options else 40,
                "max_tokens": options.get('num_predict', -1) if options else -1,
            }

            response = requests.post(
                f"{self.base_url}/v1/chat/completions",
                json=payload,
                stream=True,
                timeout=300
            )

            if response.status_code == 404:
                logger.warning("OpenAI-compatible chat endpoint not found, falling back to /completion")
                yield from self._chat_stream_via_completion(model, messages, options)
                return

            response.raise_for_status()

            for line in response.iter_lines():
                if line:
                    try:
                        line_text = line.decode('utf-8')
                        if line_text.startswith('data: '):
                            line_text = line_text[6:]
                        if line_text == '[DONE]':
                            continue
                        data = json.loads(line_text)
                        # Convert to Ollama-compatible format
                        delta = data.get('choices', [{}])[0].get('delta', {})
                        content = delta.get('content', '')
                        yield {
                            'message': {'role': 'assistant', 'content': content},
                            'done': data.get('choices', [{}])[0].get('finish_reason') is not None
                        }
                    except (json.JSONDecodeError, UnicodeDecodeError):
                        continue

        except requests.exceptions.HTTPError as e:
            if e.response is not None and e.response.status_code == 404:
                logger.warning("Chat endpoint returned 404, falling back to /completion")
                yield from self._chat_stream_via_completion(model, messages, options)
            else:
                logger.error(f"Streaming chat failed: {e}")
                raise
        except Exception as e:
            logger.error(f"Streaming chat failed: {e}")
            raise

    def _chat_stream_via_completion(self, model: str, messages: List[Dict[str, str]],
                                     options: dict = None) -> Generator:
        """Fallback: use /completion when /chat/completions is unavailable"""
        prompt, system = self._messages_to_prompt(messages)

        payload = {
            "prompt": prompt,
            "stream": True,
            "n_predict": options.get('num_predict', -1) if options else -1,
            "temperature": options.get('temperature', 0.7) if options else 0.7,
            "top_p": options.get('top_p', 0.9) if options else 0.9,
            "top_k": options.get('top_k', 40) if options else 40,
        }
        if system:
            # llama.cpp doesn't have native system prompt in /completion
            # Prepend to prompt
            payload["prompt"] = f"System: {system}\n\n{prompt}"

        response = requests.post(
            f"{self.base_url}/completion",
            json=payload,
            stream=True,
            timeout=300
        )
        response.raise_for_status()

        for line in response.iter_lines():
            if line:
                try:
                    data = json.loads(line.decode('utf-8').lstrip('data: '))
                    # Convert /completion format to /api/chat format
                    yield {
                        'message': {'role': 'assistant', 'content': data.get('content', '')},
                        'done': data.get('stop', False)
                    }
                except (json.JSONDecodeError, UnicodeDecodeError):
                    continue

    def _build_prompt(self, prompt: str, system: str = None, context: List[int] = None) -> str:
        """Build full prompt with system message if provided"""
        if system:
            return f"System: {system}\n\nUser: {prompt}\n\nAssistant:"
        return f"User: {prompt}\n\nAssistant:"

    def is_available(self) -> bool:
        """Check if llama.cpp server is available"""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            return response.status_code == 200
        except Exception:
            return False


def get_llamacpp_service() -> LlamaCppService:
    """Get llama.cpp service instance"""
    return LlamaCppService()
