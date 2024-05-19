from modal import asgi_app

from . import config
from .api import web_app
from .common import app, app_image

logger = config.get_logger(__name__)

# TODO: Track App state such that we can handle interruptions to the pipeline
# such as when the user speaks before the pipeline is finished processing
# or checking if the conversation_id already exists in the database which
# would provide continuity

# Right now we launch a separate server for each user, but once we have conversation_uuid, we'll be able to handle
# multiple users (number TBD) via the same socket.
# This keeps things simple and scales, but might not be the most cost-effective solution
@app.function(concurrency_limit=100, allow_concurrent_inputs=1, keep_warm=1, image=app_image)
@asgi_app()
def web():
    from .api import web_app

    return web_app
