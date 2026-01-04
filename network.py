"""
Сетевой модуль для работы с LLM API.
Асинхронные запросы через httpx с поддержкой разных провайдеров.
"""

import os
import asyncio
from typing import Optional, AsyncGenerator, Callable
from dataclasses import dataclass
from enum import Enum

import httpx
from dotenv import load_dotenv

from models import Model


# Загрузка переменных окружения
load_dotenv()


class APIProvider(Enum):
    """Провайдеры API."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    DEEPSEEK = "deepseek"
    GROQ = "groq"
    CUSTOM = "custom"


@dataclass
class APIResponse:
    """Ответ от API."""
    success: bool
    content: str
    error: Optional[str] = None
    tokens_used: int = 0


def get_api_key(provider: APIProvider) -> Optional[str]:
    """Получить API ключ для провайдера."""
    key_mapping = {
        APIProvider.OPENAI: "OPENAI_API_KEY",
        APIProvider.ANTHROPIC: "ANTHROPIC_API_KEY",
        APIProvider.DEEPSEEK: "DEEPSEEK_API_KEY",
        APIProvider.GROQ: "GROQ_API_KEY",
    }
    env_var = key_mapping.get(provider)
    if env_var:
        return os.getenv(env_var)
    return None


def detect_provider(api_url: str) -> APIProvider:
    """Определить провайдера по URL."""
    url_lower = api_url.lower()
    if "openai.com" in url_lower:
        return APIProvider.OPENAI
    elif "anthropic.com" in url_lower:
        return APIProvider.ANTHROPIC
    elif "deepseek.com" in url_lower:
        return APIProvider.DEEPSEEK
    elif "groq.com" in url_lower:
        return APIProvider.GROQ
    return APIProvider.CUSTOM


class LLMClient:
    """Клиент для работы с LLM API."""
    
    def __init__(self, timeout: int = 30):
        self.timeout = timeout
        self._custom_api_key: Optional[str] = None
    
    def set_custom_api_key(self, api_key: str):
        """Установить кастомный API ключ."""
        self._custom_api_key = api_key
    
    def _get_headers(self, provider: APIProvider) -> dict:
        """Получить заголовки для запроса."""
        api_key = self._custom_api_key or get_api_key(provider)
        
        if provider == APIProvider.ANTHROPIC:
            return {
                "Content-Type": "application/json",
                "x-api-key": api_key or "",
                "anthropic-version": "2023-06-01"
            }
        else:
            # OpenAI-совместимый формат (OpenAI, DeepSeek, Groq и др.)
            return {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key or ''}"
            }
    
    def _build_request_body(
        self, 
        provider: APIProvider, 
        model_id: str, 
        prompt: str,
        max_tokens: int = 4096
    ) -> dict:
        """Сформировать тело запроса."""
        if provider == APIProvider.ANTHROPIC:
            return {
                "model": model_id,
                "max_tokens": max_tokens,
                "messages": [
                    {"role": "user", "content": prompt}
                ]
            }
        else:
            # OpenAI-совместимый формат
            return {
                "model": model_id,
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": max_tokens
            }
    
    def _parse_response(self, provider: APIProvider, data: dict) -> APIResponse:
        """Распарсить ответ от API."""
        try:
            if provider == APIProvider.ANTHROPIC:
                content = data.get("content", [{}])[0].get("text", "")
                tokens = data.get("usage", {}).get("output_tokens", 0)
            else:
                # OpenAI-совместимый формат
                content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                tokens = data.get("usage", {}).get("completion_tokens", 0)
            
            return APIResponse(
                success=True,
                content=content,
                tokens_used=tokens
            )
        except (KeyError, IndexError) as e:
            return APIResponse(
                success=False,
                content="",
                error=f"Ошибка парсинга ответа: {e}"
            )
    
    async def send_prompt(
        self, 
        model: Model, 
        prompt: str,
        max_tokens: int = 4096
    ) -> APIResponse:
        """Отправить промпт в модель и получить ответ."""
        provider = detect_provider(model.api_url)
        headers = self._get_headers(provider)
        body = self._build_request_body(provider, model.api_id, prompt, max_tokens)
        
        # Проверка наличия API ключа
        if not self._custom_api_key and not get_api_key(provider):
            return APIResponse(
                success=False,
                content="",
                error=f"API ключ не найден для провайдера {provider.value}"
            )
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    model.api_url,
                    headers=headers,
                    json=body
                )
                
                if response.status_code == 200:
                    return self._parse_response(provider, response.json())
                else:
                    error_text = response.text
                    return APIResponse(
                        success=False,
                        content="",
                        error=f"HTTP {response.status_code}: {error_text[:200]}"
                    )
                    
        except httpx.TimeoutException:
            return APIResponse(
                success=False,
                content="",
                error="Превышено время ожидания ответа"
            )
        except httpx.RequestError as e:
            return APIResponse(
                success=False,
                content="",
                error=f"Ошибка сети: {e}"
            )
        except Exception as e:
            return APIResponse(
                success=False,
                content="",
                error=f"Неизвестная ошибка: {e}"
            )
    
    async def send_prompt_streaming(
        self,
        model: Model,
        prompt: str,
        on_chunk: Callable[[str], None],
        max_tokens: int = 4096
    ) -> APIResponse:
        """Отправить промпт с потоковой передачей ответа."""
        provider = detect_provider(model.api_url)
        headers = self._get_headers(provider)
        body = self._build_request_body(provider, model.api_id, prompt, max_tokens)
        body["stream"] = True
        
        if not self._custom_api_key and not get_api_key(provider):
            return APIResponse(
                success=False,
                content="",
                error=f"API ключ не найден для провайдера {provider.value}"
            )
        
        full_content = ""
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                async with client.stream(
                    "POST",
                    model.api_url,
                    headers=headers,
                    json=body
                ) as response:
                    if response.status_code != 200:
                        error_text = await response.aread()
                        return APIResponse(
                            success=False,
                            content="",
                            error=f"HTTP {response.status_code}: {error_text.decode()[:200]}"
                        )
                    
                    async for line in response.aiter_lines():
                        if line.startswith("data: "):
                            data_str = line[6:]
                            if data_str == "[DONE]":
                                break
                            try:
                                import json
                                data = json.loads(data_str)
                                
                                if provider == APIProvider.ANTHROPIC:
                                    delta = data.get("delta", {}).get("text", "")
                                else:
                                    delta = data.get("choices", [{}])[0].get("delta", {}).get("content", "")
                                
                                if delta:
                                    full_content += delta
                                    on_chunk(delta)
                            except:
                                pass
            
            return APIResponse(
                success=True,
                content=full_content
            )
            
        except httpx.TimeoutException:
            return APIResponse(
                success=False,
                content=full_content,
                error="Превышено время ожидания ответа"
            )
        except Exception as e:
            return APIResponse(
                success=False,
                content=full_content,
                error=f"Ошибка: {e}"
            )


async def send_to_multiple_models(
    models: list[Model],
    prompt: str,
    timeout: int = 30
) -> dict[int, APIResponse]:
    """Отправить промпт во все указанные модели параллельно."""
    client = LLMClient(timeout=timeout)
    
    async def send_one(model: Model) -> tuple[int, APIResponse]:
        response = await client.send_prompt(model, prompt)
        return model.id, response
    
    tasks = [send_one(model) for model in models]
    results = await asyncio.gather(*tasks)
    
    return {model_id: response for model_id, response in results}

