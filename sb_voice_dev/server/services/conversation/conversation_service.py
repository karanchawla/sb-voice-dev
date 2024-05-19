# conversation_service.py


import time
import os
from sb_voice_dev.server.config import LLMConfiguration
from ..llm.llm_service import LLMService
from ...common import app, app_image
from ...prompts.conversation import conversation_prompt

from modal import method, Secret, Queue
from typing import List

@app.cls(container_idle_timeout=300, 
         concurrency_limit=1, 
         keep_warm=1, 
         image=app_image,
         secrets=[Secret.from_name("groq-api-key")])
class ConversationService:
    def __init__(self):
        # TODO: Inject this from higher up in the hierarchy instead of defining this here
        config = LLMConfiguration(model="groq/llama3-8b-8192", 
                                  api_base_url="https://api.groq.com/v1/", 
                                  api_key=os.environ["GROQ_API_KEY"])
        self.llm_service = LLMService(config=config)

    @method()
    async def get_llm_response(self, input: str) -> str:
        if input == "":
            return
        
        messages = [{"role": "system", "content": conversation_prompt()}]
        messages.append({"role": "user", "content": input})
        await self.llm_service.async_llm_completion(messages)