# web_socket_handler.py
# This module defines an interface for managing the websocket connection with the remote server.
# It accepts the websocket_uri and a message handler that will be invoked when data is received from the server.
# TODO: This class can probably be refactored to be more generic, I'll come back to it if I have time.

import asyncio
from typing import Awaitable, Callable, Union

import websockets


class WebSocketHandler:
    def __init__(self, websocket_uri: str, message_handler: Callable[[Union[str, bytes]], Awaitable[None]]) -> None:
        self.websocket_uri = websocket_uri
        self.websocket = None
        self.connection_lock = asyncio.Lock()
        self.is_active = False

        # Handler for incoming messages
        self.message_handler = message_handler

    async def connect(self):
        async with self.connection_lock:
            retry_count = 0
            # TODO: This retry count should probably be reconfigurable
            while retry_count < 5 and (not self.websocket or self.websocket.closed):
                # ensure websocket is properly closed and reset before attempting to reconnect
                if self.websocket:
                    await self.websocket.close()

                try:
                    self.websocket = await websockets.connect(uri=self.websocket_uri)
                    self.is_active = True
                    print("WebSocket connected.")
                    asyncio.create_task(self.receive_data())
                    break  # exit the loop on successful connnection
                except Exception as e:
                    retry_count += 1
                    # exponential backoff before attemting to reconnect
                    wait_time = min(30, 2**retry_count)
                    print(f"Failed to connect to the WebSocket: {e}, retrying in {wait_time} seconds...")
                    await asyncio.sleep(wait_time)

            if retry_count == 5:
                print(f"Failed to connect after 5 attempts.")

    async def send_audio(self, audio_data: bytes):
        # If we forget to call this before calling send_audio
        await self.connect()
        if self.websocket:
            try:
                await self.websocket.send(audio_data)
                print("Audio data sent.")
            except Exception as e:
                print(f"Error sending audio data: {e}")
                await self.websocket.close()

    async def receive_data(self):
        try:
            while self.is_active:
                message = await self.websocket.recv()
                if self.message_handler:
                    await self.message_handler(message)
        except websockets.exceptions.ConnectionClosed:
            print("Websocket connection closed.")
        except Exception as e:
            print("Error receiving data: {e}")
        finally:
            self.is_active = False

    async def close(self):
        if self.websocket:
            await self.websocket.close()
            self.websocket = None
            self.is_active = False
            print("Websocket closed.")
