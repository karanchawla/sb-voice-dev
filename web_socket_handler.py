import asyncio
import websockets

class WebSocketHandler: 
    def __init__(self, websocket_url: str, message_handler=None) -> None:
        self.websocket_url = websocket_url
        self.websocket = None
        self.connection_lock = asyncio.Lock()
        self.is_active = False
        
        # Handler for incoming messages
        self.message_handler = message_handler

    async def connect(self):
        async with self.connection_lock:
            if not self.websocket or self.websocket.closed:
                try:
                    self.websocket = await websockets.connect(uri=self.websocket_url)
                    self.is_active = True
                    print("WebSocket connected.")
                    # TODO: Create a task to receive data
                except Exception as e:
                    print(f"Failed to connect to the WebSocket: {e}")
                    await asyncio.sleep(1.0)
    
    async def close(self):
        if self.websocket:
            await self.websocket.close()
            self.websocket = None
            self.is_active = False
            print("Websocket closed.")