# sb-voice-dev

`client.py`: Local python client that records user audio while the space bar is pressed. This file then generates a wav and mp3 file that is stored locally. 


## To do

1. Create a websocket connection manager for the client
2. Set up a websocket connection with a FastAPI server
3. Read audio file on the server, run the STT -> LLM -> TTS
4. Figure out what APIs to use for STT, LLM, and TTS services
5. Stream audio chunks from the server back to the client 
6. Play received audio back to the user 