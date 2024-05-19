import logging
import yaml
from pydantic import BaseModel


def get_logger(name, level=logging.INFO):
    logger = logging.getLogger(name)
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(levelname)s: %(asctime)s: %(name)s  %(message)s"))
    logger.addHandler(handler)
    logger.setLevel(level)
    return logger

class LLMConfiguration(BaseModel):
    model: str
    api_base_url: str | None
    api_key: str | None


class DeepgramConfiguration(BaseModel):
    api_key: str
    model: str


class ElevenLabsConfiguration(BaseModel):
    api_key: str
    model: str
    voice_id: str

class Configuration(BaseModel):
    @classmethod
    def load_config_yaml(cls, config_file_path: str) -> "Configuration":
        if os.path.exists(config_file_path):
            with open(config_file_path, "r") as stream:
                config_data = yaml.safe_load(stream)

            return cls(**config_data)

    llm: LLMConfiguration
    deepgram: DeepgramConfiguration
    elevenlabs: ElevenLabsConfiguration