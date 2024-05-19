# app_state.py
# Manages server application state


from dataclasses import dataclass, field

from .config import Configuration
from .services.conversation.conversation_service import ConversationService
from .services.llm.llm_service import LLMService
from queue import Queue

# TODO: To be completed
@dataclass
class AppState:
    config: Configuration

    # database: Database
    conversation_service: ConversationService
    llm_service: LLMService
    task_queue = Queue()