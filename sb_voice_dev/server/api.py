from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query
from fastapi.middleware.cors import CORSMiddleware

from . import config
from .llm import llm
from .deepgram_service import speech_to_text_service
from .tts import text_to_speech_service
import asyncio

logger = config.get_logger(__name__)
web_app = FastAPI()
origins = [
    "https://karanchawla-dev--fastapi-websocket-websocket-handler-dev.modal.run",
]

web_app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

class WebSocketConnectionManager:
    def __init__(self) -> None:
        self.websocket: WebSocket = None
        self.session_id: str = None
        self.user_id: str = None
        self.current_task: asyncio.Task = None

    async def connect(self, websocket: WebSocket, session_id: str, user_id: str):
        await websocket.accept()
        self.websocket = websocket
        self.session_id = session_id
        self.user_id = user_id
        logger.info(f"Connection established: session_id={session_id}, user_id={user_id}")

    async def disconnect(self):
        if self.websocket:
            logger.info(f"Connection closed: session_id={self.session_id}")
            await self.websocket.close()
            self.session_id = None
            self.user_id = None

    async def receive_data(self):
        try:
            data = await self.websocket.receive_bytes()
            logger.info(f"Received data of size: {len(data)}")
            return data
        except Exception as e:
            print(f"Error receiving data: {e}")
            await self.disconnect(self.websocket)

manager = WebSocketConnectionManager()

# TODO: Abstract the STT -> LLM -> TTS into a ConversationInterface so that we aren't micro-managing individual methods
@web_app.websocket("/v1/speak")
async def websocket_endpoint(websocket: WebSocket):
    session_id = websocket.query_params.get("session_id")
    user_id = websocket.query_params.get("user_id")

    if not session_id or not user_id:
        await websocket.close()
        logger.info("WebSocket closed due to missing session_id or user_id.")
        return

    await manager.connect(websocket, session_id, user_id)
    await process_websocket_data(websocket)

# TODO: Create APIs for handling conversations
# TODO: Move routes into individual files via APIRouter()
# Stubbed out versions below
@web_app.get("/v1/conversations/")
def read_conversations(
    offset: int = 0,
    limit: int = Query(default=100),
):
    pass
    # Read previous conversations from db

@web_app.get("/v1/conversations/{conversation_id}")
def read_conversation(
    conversation_id: int, 
):
    pass
    # Read specific conversation from db

@web_app.delete("/v1/conversations/{conversation_id}")
def delete_conversation_endpoint(
    conversation_id: int
):
    pass
    # Delete conversations from DB

@web_app.post("/v1/conversations/{conversation_id}/end")
async def end_conversation(
    conversation_id: int
):
    # End a conversation
    # Requires interaction with AppState
    pass

# ================ utils ==============================

async def process_websocket_data(websocket: WebSocket):
    try:
        while True:
            # TODO: Generate a new token for each audio file received and add to db
            data = await manager.receive_data()
            if manager.current_task and not manager.current_task.done():
                manager.current_task.cancel()
                logger.info("Cancelled the ongoing audio processing task.")
            manager.current_task = asyncio.create_task(process_audio_data(data, websocket))
    except WebSocketDisconnect as e:
        logger.error(f"WebSocket disconnected: {e}")
        await manager.disconnect()
    except Exception as e:
        logger.error(f"Error occurred: {e}")
        await manager.disconnect()

async def process_audio_data(data, websocket):
    try:
        audio_transcript = speech_to_text_service.remote(data)
        if audio_transcript:
            response = llm.remote(audio_transcript)
            logger.debug("Received response from the LLM.")
            await stream_audio_to_client(response, websocket)
    except asyncio.CancelledError:
        logger.info("Audio processing was cancelled")
    except Exception as e:
        logger.error(f"Error processing audio data: {e}")

async def stream_audio_to_client(response, websocket):
    try:
        for chunk in text_to_speech_service.remote_gen(response):
            await websocket.send_bytes(chunk)
        await websocket.send_text("END_OF_AUDIO")
    except Exception as e:
        logger.error(f"Error streaming audio to client: {e}")