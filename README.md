# sb-voice-dev

```
sb_voice_dev/
│
├── client.py
│   └── Contains the client-side logic for recording audio, managing state, and communicating with the server via WebSocket.
│
├── server/
│   ├── api.py
│   │   └── Defines the FastAPI application, WebSocket endpoints, and REST API routes for managing conversations.
│   ├── app_state.py
│   │   └── Manages the server application state, including services and task queues.
│   ├── common.py
│   │   └── Sets up the FastAPI application and its dependencies.
│   ├── main.py
│   │   └── Entry point for the server application, configuring and running the FastAPI app.
│   ├── config/
│   │   └── settings.py
│   │       └── Contains configuration settings for the application, such as database URLs, API keys, etc.
│   ├── services/
│   │   ├── conversation/
│   │   │   └── llm.py
│   │   │       └── Handles logic for interacting with language models.
│   │   ├── stt/
│   │   │   └── deepgram_service.py
│   │   │       └── Implements speech-to-text functionality using the Deepgram API.
│   │   └── tts/
│   │       └── tts.py
│   │           └── Provides text-to-speech services, potentially using multiple providers.
│   └── prompts/
│       └── conversation.py
│           └── Contains templates or utilities for generating conversation prompts.
│
├── tests/
│   ├── test_api.py
│   │   └── Contains tests for the API endpoints.
│   └── test_multiple_clients.py
│       └── Contains tests for simulating multiple client instances to test the system's concurrency and scalability.
│
└── web_socket_handler.py
    └── Manages WebSocket connections, including sending and receiving messages, and handling connection lifecycle events.
```

## Running the repo

### Prerequisites

- Install `poetry` 
```shell
curl -sSL https://install.python-poetry.org | python3 -
```

- Install project dependencies and switch to poetry virtual environment
```shell
make install
```

- Start the client
```python
python sb_voice_dev/client.py
```
You should see the client connect to the remote server with `WebSocket connected` displayed on your terminal. Once the connection is established, press and hold `Spacebar` key to record your prompt and then wait for response from the server. Press `q` to quit the application.

## To do

- Figure out a better way to inject secrets (at run time) in the App
- Spawn containers for various services when we first notice user activity.
- Create FastAPI app with AppState
- Integrate the app with a database 
- Flesh out the conversations API and integrate this with the LLM and the database
- Check if `conversation_uuid` already exists in database, to ensure conversation continuity if the user loses connection
- For longer LLM responses, split text based on `. , !` etc. and stream that to the Deepgram via websocket (instead of a POST request)
- Stream audio and perform VAD (likely with `silero`) so that we reduce latency from saving audio file and then sending that
- Integrate `ConversationService` to generalize across various LLM providers
- Abstract away STT and TTS services

## Optimization notes

### Interruptions
This app currently doesn't handle interruptions. We do pre-empt the text to speech task if the user sends another audio file while the current one is processing. But we don't stop the audio and re-compute the pipeline if the user speaks while the audio-player is on. This can probably be fixed with some client side logic (such as if microphone is turned on, we stop the audio player and start the pipeline again? How is conversation history managed in this case?). We can also stream audio and perform VAD on the server side to reduce latency that currently exists from saving audio and then sending it to the server. Some good ideas [here](https://alphacephei.com/nsh/2023/09/22/time-brain-ctc-blank.html).

### Better concurrency
Trade-off here is we can run ephemeral containers that provide STT, LLM, and TTS services and handle inputs from the same user vs queue all inputs coming into the system and parallel process them via `spawn` on Modal. Cost vs speed. Need to run experiments here to determine what's best. 

### End to End
Unsure how the new GPT-4o API for speech works, but this would probably be phenomenal for latency if wew can integrate this with RAG.

