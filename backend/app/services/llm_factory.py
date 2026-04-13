"""
LLM Factory - Unified interface for different LLM providers
Supports Ollama and llama.cpp backends
"""
from typing import Generator, List, Dict, Any, Optional, Union
from flask import current_app
import logging

from .ollama_service import OllamaService, get_ollama_service
from .llamacpp_service import LlamaCppService, get_llamacpp_service

logger = logging.getLogger(__name__)


class LLMService:
    """
    Unified LLM Service that wraps both Ollama and llama.cpp backends.
    Automatically selects the appropriate backend based on LLM_PROVIDER config.
    """

    def __init__(self):
        self._provider = None
        self._ollama_service = None
        self._llamacpp_service = None

    @property
    def provider(self) -> str:
        """Get current LLM provider"""
        if self._provider is None:
            try:
                self._provider = current_app.config.get('LLM_PROVIDER', 'ollama')
            except RuntimeError:
                # Outside Flask app context, default to ollama
                self._provider = 'ollama'
        return self._provider

    @property
    def ollama_service(self) -> OllamaService:
        """Lazy load Ollama service"""
        if self._ollama_service is None:
            self._ollama_service = get_ollama_service()
        return self._ollama_service

    @property
    def llamacpp_service(self) -> LlamaCppService:
        """Lazy load llama.cpp service"""
        if self._llamacpp_service is None:
            self._llamacpp_service = get_llamacpp_service()
        return self._llamacpp_service

    def _get_service(self):
        """Get the appropriate service based on provider config"""
        if self.provider == 'llamacpp':
            return self.llamacpp_service
        return self.ollama_service

    def get_models(self) -> List[Dict[str, Any]]:
        """Get list of available models"""
        return self._get_service().get_models()

    def generate(self, model: str, prompt: str, system: str = None,
                 context: List[int] = None, options: dict = None) -> str:
        """Generate response (non-streaming)"""
        return self._get_service().generate(model, prompt, system, context, options)

    def generate_stream(self, model: str, prompt: str, system: str = None,
                        context: List[int] = None, options: dict = None) -> Generator:
        """Generate response with streaming"""
        yield from self._get_service().generate_stream(model, prompt, system, context, options)

    def chat(self, model: str, messages: List[Dict[str, str]],
             options: dict = None, think: bool = None) -> str:
        """Chat completion (non-streaming)"""
        return self._get_service().chat(model, messages, options, think)

    def chat_stream(self, model: str, messages: List[Dict[str, str]],
                    options: dict = None, think: bool = True) -> Generator:
        """Chat completion with streaming"""
        yield from self._get_service().chat_stream(model, messages, options, think)

    def is_available(self) -> bool:
        """Check if LLM service is available"""
        return self._get_service().is_available()

    def get_default_model(self) -> str:
        """Get the default model based on provider"""
        try:
            if self.provider == 'llamacpp':
                return 'llamacpp-model'
            return current_app.config.get('OLLAMA_DEFAULT_MODEL', 'qwen2.5:7b')
        except RuntimeError:
            return 'qwen2.5:7b'


class LLMFactory:
    """Factory for creating LLM service instances"""

    _instance = None

    @classmethod
    def get_service(cls) -> LLMService:
        """Get singleton LLM service instance"""
        if cls._instance is None:
            cls._instance = LLMService()
        return cls._instance

    @classmethod
    def reset_instance(cls):
        """Reset the singleton instance (useful for testing)"""
        cls._instance = None

    @classmethod
    def get_provider(cls) -> str:
        """Get current LLM provider from config"""
        try:
            return current_app.config.get('LLM_PROVIDER', 'ollama')
        except RuntimeError:
            return 'ollama'

    @classmethod
    def is_ollama(cls) -> bool:
        """Check if using Ollama provider"""
        return cls.get_provider() == 'ollama'

    @classmethod
    def is_llamacpp(cls) -> bool:
        """Check if using llama.cpp provider"""
        return cls.get_provider() == 'llamacpp'


def get_llm_service() -> LLMService:
    """Get the unified LLM service instance"""
    return LLMFactory.get_service()


def get_llm_provider() -> str:
    """Get current LLM provider name"""
    return LLMFactory.get_provider()
