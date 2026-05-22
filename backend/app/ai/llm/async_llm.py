import time
from typing import AsyncGenerator, List, Dict, Any, Optional
from backend.app.core.config import settings
from backend.app.core.logger import logger

from groq import AsyncGroq

class AsyncLLMService:
    def __init__(self):
        self.model = "llama-3.1-8b-instant"  # fast + smart on Groq
        self._client = AsyncGroq(api_key=settings.GROQ_API_KEY)

    def _clean(self, content: str) -> str:
        for prefix in ("Assistant:", "assistant:", "User:", "user:"):
            if content.startswith(prefix):
                content = content[len(prefix):].strip()
        return content

    async def generate(self, prompt: str, system_prompt: str, history: Optional[List[Dict[str, str]]] = None) -> str:
        messages = [{"role": "system", "content": system_prompt}]
        if history:
            messages.extend(history)
        messages.append({"role": "user", "content": prompt})
        start = time.time()
        try:
            response = await self._client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.1,
                max_tokens=120,
            )
            content = response.choices[0].message.content.strip()
            logger.info(f"Groq LLM response in {time.time() - start:.2f}s")
            return self._clean(content)
        except Exception as e:
            logger.error(f"Groq LLM Error: {str(e)}")
            return "I'm having trouble connecting right now. Please try again."

    async def stream_generate(self, prompt: str, system_prompt: str, history: Optional[List[Dict[str, str]]] = None) -> AsyncGenerator[str, None]:
        messages = [{"role": "system", "content": system_prompt}]
        if history:
            messages.extend(history)
        messages.append({"role": "user", "content": prompt})
        try:
            stream = await self._client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.1,
                max_tokens=120,
                stream=True,
            )
            async for chunk in stream:
                token = chunk.choices[0].delta.content
                if token:
                    yield token
        except Exception as e:
            logger.error(f"Groq stream error: {str(e)}")
            yield "I'm having trouble connecting right now."

async_llm = AsyncLLMService()
