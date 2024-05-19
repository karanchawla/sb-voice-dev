# sb-voice-dev

`client.py`: Local python client that records user audio while the space bar is pressed. This file then generates a wav and mp3 file that is stored locally. 


## To do

~ - Create a websocket connection manager for the client~
~ - Set up a simple dir structure ~
- Set up a websocket connection with a FastAPI server
- Read audio file on the server, run the STT -> LLM -> TTS
- Figure out what APIs to use for STT, LLM, and TTS services
- Stream audio chunks from the server back to the client 
- Play received audio back to the user 