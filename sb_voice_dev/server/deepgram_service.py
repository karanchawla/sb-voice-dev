import json
import os

from modal import Secret

from . import config
from .common import app, app_image

logger = config.get_logger(__name__)

@app.function(
    secrets=[Secret.from_name("deepgram-api-key")],
    image=app_image,
    keep_warm=1,
    container_idle_timeout=300,
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