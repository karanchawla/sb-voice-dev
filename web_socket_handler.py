# web_socket_handler.py
# This module defines the WebSocketHandler class, which provides a robust interface for managing WebSocket connections.
# It facilitates connecting to a WebSocket server, sending audio data, and handling incoming messages through a user-defined callback.
# The class is designed to handle asynchronous operations and ensures proper management of the WebSocket lifecycle.

import asyncio
import websockets
from typing import Callable, Union

class WebSocketHandler: 
    def __init__(self, websocket_uri: str, message_handler: Callable[[Union[str, bytes]], None]) -> None:
        self.websocket_uri = websocket_uri
        self.websocket = None
        self.connection_lock = asyncio.Lock()
        self.is_active = False
        
        # Handler for incoming messages
        self.message_handler = message_handler

    async def connect(self):
        async with self.connection_lock:
            if not self.websocket or self.websocket.closed:
                try:
                    self.websocket = await websockets.connect(uri=self.websocket_uri)
                    self.is_active = True
                    print("WebSocket connected.")
                    asyncio.create_task(self.receive_data())
                except Exception as e:
                    print(f"Failed to connect to the WebSocket: {e}")
                    await asyncio.sleep(1.0)
    
    async def send_audio(self, audio_data: bytes):
        if self.websocket:
            try:
                await self.websocket.send(audio_data)
                print("Audio data sent.")
            except Exception as e:
                print("Error sending audio data: {e}")
                await self.websocket.close()
                self.websocket = None
    
    async def receive_data(self):
        try:
            while self.is_active:
                message = await self.websocket.recv()
                if self.message_handler:
                    await self.message_handler(message)
        except websockets.exceptions.ConnectionClosed:
            print("Websocket connection closed.")
            self.is_active = False
        except Exception as e:
            print("Error receiving data: {e}")
            self.is_active = False

    async def close(self):
        if self.websocket:
            await self.websocket.close()
            self.websocket = None
            self.is_active = False
            print("Websocket closed.")