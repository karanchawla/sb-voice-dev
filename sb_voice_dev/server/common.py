from modal import App, Image

app = App(name="fastapi-websocket")
app_image = Image.debian_slim(python_version="3.10").pip_install(
    "fastapi", "deepgram-sdk", "langchain", "langchain-groq", "langchain-core", "elevenlabs"
)
