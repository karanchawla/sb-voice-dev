# conversation_service.py


from ..llm.llm_service import LLMService


class ConversationService:
    def __init__(self):
        self.llm_service = LLMService()

    async def get_llm_response(user_msg: str) -> str:
        pass
