from modal import Secret

from ... import config
from ...common import app, app_image

logger = config.get_logger(__name__)


@app.function(
    secrets=[Secret.from_name("cartesia-api-key")],
    image=app_image,
    keep_warm=1,
    container_idle_timeout=300,
    concurrency_limit=1,
    is_generator=True,
)
async def text_to_speech_service(llm_response: str):
    import os
    import asyncio
    from cartesia.tts import CartesiaTTS

    voice = 'Classy British Man'
    gen_cfg = dict(model_id="upbeat-moon", data_rtype='bytes', output_format='fp32_16000')

    # create client
    client = CartesiaTTS(api_key=os.environ["CARTERSIA_API_KEY"])
    voice = client.get_voice_embedding(voice_id="95856005-0332-41b0-935f-352e296aa0df")

    # generate audio
    output_generator = client.generate(transcript=llm_response, voice=voice, stream=True, **gen_cfg)
    try:
        for chunk in output_generator:
            yield chunk
    finally:
        yield "END_OF_AUDIO"
