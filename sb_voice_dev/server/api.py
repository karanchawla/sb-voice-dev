from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from . import config

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
