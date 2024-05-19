from cgitb import text
import json
import os

from fastapi import WebSocket, WebSocketDisconnect
from modal import Image, asgi_app

from . import config
from .api import WebSocketConnectionManager, web_app
from .conversation_service import llm
from .deepgram_service import speech_to_text_service
from .tts import text_to_speech_service
from .common import app, app_image

logger = config.get_logger(__name__)

manager = WebSocketConnectionManager()

@web_app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    session_id = websocket.query_params.get("session_id")
    user_id = websocket.query_params.get("user_id")

    if not session_id or not user_id:
        await websocket.close()
        logger.info("WebSocket closed due to missing session_id or user_id.")
        return

    await manager.connect(websocket, session_id, user_id)

    try:
        while True:
            data = await manager.receive_data()
            audio_transcript = speech_to_text_service.remote(data)
            # Process data here
            if audio_transcript:
                # Text to LLM output
                response = llm.remote(audio_transcript)
                logger.debug("Received response from the LLM.")
                # Stream audio output to the client
                for chunk in text_to_speech_service.remote_gen(response):
                    await websocket.send_bytes(chunk)
                await websocket.send_text("END_OF_AUDIO")
            logger.info(f"Data received.")
            logger.info(f"Data received.")
    except WebSocketDisconnect as e:
        logger.error(f"WebSocket disconnected: {e}")
        await manager.disconnect()
    except Exception as e:
        logger.error(f"Error occured: {e}")
        await manager.disconnect()

@app.function(concurrency_limit=100, allow_concurrent_inputs=1, keep_warm=1, image=app_image)
@asgi_app()
def websocket_handler():
    from .api import web_app

    return web_app
