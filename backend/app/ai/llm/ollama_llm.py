import ollama
import time
from backend.app.core.logger import logger
from backend.app.core.config import settings

class LLMService:
    def __init__(self):
        self.model = settings.OLLAMA_MODEL
        
    def generate(self, prompt: str, system_prompt: str) -> str:
        """
        Base generation method.
        """
        start_time = time.time()
        try:
            response = ollama.chat(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt},
                ],
                options={
                    "temperature": 0.2,
                    "num_predict": 200
                }
            )
            duration = time.time() - start_time
            logger.info(f"LLM generation completed in {duration:.2f}s")
            return response["message"]["content"].strip()
        except Exception as e:
            logger.error(f"LLM Error: {str(e)}")
            return "I'm having trouble connecting to my brain right now."

llm_service = LLMService()
