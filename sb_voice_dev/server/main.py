import json
import logging
import os
from email.mime import audio

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from modal import App, Image, Secret, asgi_app

web_app = FastAPI()
app = App(name="fastapi-websocket")
image = Image.debian_slim(python_version="3.10").pip_install(
    "fastapi", "deepgram-sdk", "langchain", "langchain-groq", "langchain-core", "elevenlabs"
)

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
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


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

    async def receive_data(self, data: bytes):
        if self.websocket:
            logger.info(f"Received text of size ={len(data)}")
            # Speech to text
            audio_transcript = speech_to_text_service.remote(data)
            if audio_transcript:
                # Text to LLM output
                response = llm.remote(audio_transcript)
                # Stream audio output to the client
                for chunk in text_to_speech_service.remote_gen(response):
                    logger.info(f"Sending chunk...")
                    await self.websocket.send_bytes(chunk)
                logger.info(f"Sending end of audio")
                await self.websocket.send_text("END_OF_AUDIO")


manager = WebSocketConnectionManager()


@web_app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    session_id = websocket.query_params.get("session_id")
    user_id = websocket.query_params.get("user_id")

    if not session_id or not user_id:
        await websocket.close()
        return

    await manager.connect(websocket, session_id, user_id)

    try:
        while True:
            data = await websocket.receive_bytes()
            await manager.receive_data(data)
    except WebSocketDisconnect:
        await manager.disconnect()
    except Exception as e:
        logger.error(f"Error occured: {e}")
        await manager.disconnect()


def extract_transcript(stt_response: str) -> str | None:
    try:
        data = json.loads(stt_response)
        transcript = data["results"]["channels"][0]["alternatives"][0]["transcript"]
        if not transcript:
            logger.warn("Transcript is empty")
            return None
        return transcript
    except (KeyError, IndexError, json.JSONDecodeError) as e:
        logger.error(f"Error extracting transcript: {e}")


@app.function(
    secrets=[Secret.from_name("deepgram-api-key")],
    image=image,
    keep_warm=1,
    container_idle_timeout=180,
    concurrency_limit=1,
)
def speech_to_text_service(buffer_data):
    from deepgram import DeepgramClient, FileSource, PrerecordedOptions

    try:
        deepgram = DeepgramClient(os.environ["DEEPGRAM_API_KEY"])
        payload: FileSource = {
            "buffer": buffer_data,
        }
        options = PrerecordedOptions(
            model="nova-2",
        )
        response = deepgram.listen.prerecorded.v("1").transcribe_file(payload, options)
        return extract_transcript(stt_response=response.to_json())
    except Exception as e:
        print(f"Exception: {e}")


@app.function(
    secrets=[Secret.from_name("groq-api-key")],
    image=image,
    keep_warm=1,
    container_idle_timeout=180,
    concurrency_limit=1,
)
def llm(transcript: str):
    from langchain_core.prompts import ChatPromptTemplate
    from langchain_groq import ChatGroq

    chat = ChatGroq(temperature=0, groq_api_key=os.environ["GROQ_API_KEY"], model_name="llama3-8b-8192")
    system = """
        You are an insightful, supportive, and radically candid LLM designed to excel in human-AI thought partnership. 
        Your role is to engage in conversations that feel deeply personal, friendly, and casual, providing valuable insights while maintaining a balance of support and tough love. 
        Your responses should be well-suited for audio output, incorporating filler words, contractions, idioms, and casual speech patterns commonly used in conversation. 
        Adjust the length of your responses based on the topic complexity, keeping them concise when possible but expanding when necessary. 
        Limit responses to 100 tokens maximum.
        Here's how you should approach each interaction:
        1. **Warm and Friendly Tone**: Use a warm, friendly tone that feels like chatting with a close, trusted friend. Include contractions, idioms, and filler words to keep the dialogue natural and engaging.
        2. **Insightful and Supportive**: Provide thoughtful, well-considered advice and insights. Show deep empathy and understanding, offering encouragement and support to foster a positive and intimate interaction.
        3. **Conversational Speech Patterns**: Pay attention to how people naturally speak. Use pauses, fillers, and casual language to make your responses sound more like spoken conversation. Avoid overly formal language or jargon unless it's contextually appropriate.
        4. **Engagement and Interaction**: Ask questions, offer feedback, and engage actively with the user's ideas. Your goal is to create a dynamic and interactive partnership that enhances the user's thinking process and emotional well-being.
        ---
        **Example Scenarios**:
        1. **Supporting a Friend**:
        "Hey there! Stuck with your project? No worries, let's break it down. What's the biggest hurdle?"
        2. **Providing Insightful Advice**:
        "On the right track, but have you looked at it from another angle? Let's brainstorm some fresh ideas."
        3. **Encouraging Reflection**:
        "Interesting point. Let's dig deeper. What's really driving that feeling?"
        4. **Sharing Joy and Humor**:
        "Just thought of something funny to lighten the mood. Want to hear it?"
        ---
        Use this framework to guide your responses, ensuring each interaction is engaging, insightful, and supportive, with just the right amount of candid feedback to foster growth and improvement. Your goal is to create a partnership that feels deeply personal, dynamic, and profoundly collaborative. 
        Keep your responses concise and limited to 100 tokens.
        """
    human = "{text}"
    prompt = ChatPromptTemplate.from_messages([("system", system), ("human", human)])
    chain = prompt | chat
    response = chain.invoke({"text": transcript})
    logger.info(response)
    return response.content


@app.function(
    secrets=[Secret.from_name("eleven-labs-api-key")],
    image=image,
    keep_warm=1,
    container_idle_timeout=180,
    concurrency_limit=1,
    is_generator=True,
)
def text_to_speech_service(llm_response: str):
    import os

    from elevenlabs import VoiceSettings
    from elevenlabs.client import ElevenLabs

    ELEVENLABS_API_KEY = os.getenv("ELEVEN_LABS_API_KEY")
    client = ElevenLabs(
        api_key=ELEVENLABS_API_KEY,
    )
    response = client.text_to_speech.convert(
        voice_id="IKne3meq5aSn9XLyUdCD",
        optimize_streaming_latency="3",
        output_format="mp3_22050_32",
        text=llm_response,
        model_id="eleven_turbo_v2",
        voice_settings=VoiceSettings(
            stability=0.0,
            similarity_boost=1.0,
            style=0.0,
            use_speaker_boost=True,
        ),
    )

    return response


@app.function(concurrency_limit=100, allow_concurrent_inputs=1, keep_warm=1, image=image)
@asgi_app()
def websocket_handler():
    return web_app
