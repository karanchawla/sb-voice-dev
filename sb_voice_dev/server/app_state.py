# app_state.py
# Manages server application state

from __future__ import annotations

from dataclasses import dataclass, field
from queue import Queue

from fastapi import FastAPI
from h11 import Request

from .config import Configuration
from .services.conversation.conversation_service import ConversationService
from .services.llm.llm_service import LLMService


# TODO: To be completed
@dataclass
class AppState:
    config: Configuration

    # database: Database
    conversation_service: ConversationService
    llm_service: LLMService
    task_queue = Queue()

    @staticmethod
    def get(from_obj: FastAPI | Request) -> AppState:
        if isinstance(from_obj, FastAPI):
            return from_obj.state._app_state
        elif isinstance(from_obj, Request):
            return from_obj.app.state._app_state
        else:
            raise TypeError("`from_obj` must be of type `FastAPI` or `Request`")
