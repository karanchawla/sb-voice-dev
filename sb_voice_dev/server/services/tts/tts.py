from modal import Secret

from ... import config
from ...common import app, app_image

logger = config.get_logger(__name__)


@app.function(
    secrets=[Secret.from_name("eleven-labs-api-key")],
    image=app_image,
    keep_warm=1,
    container_idle_timeout=300,
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
