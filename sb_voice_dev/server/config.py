import logging


def get_logger(name, level=logging.INFO):
    logger = logging.getLogger(name)
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(levelname)s: %(asctime)s: %(name)s  %(message)s"))
    logger.addHandler(handler)
    logger.setLevel(level)
    return logger
