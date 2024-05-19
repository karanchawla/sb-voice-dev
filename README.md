# sb-voice-dev

`client.py`: Local python client that records user audio while the space bar is pressed. This file then generates a wav and mp3 file that is stored locally. 


## To do

- Figure out project structure with Modal such that we can break out stt, llm, tts into separate services
- Need to figure out how to inject app configuration to modal?
- Strategy for warm containers? Client side magic? 
- App state?
- Connect to persistent database?