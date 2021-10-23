import logging
import sys


def get_stdout_logger(obj, extra=None):
    obj_name = obj.__class__.__name__

    name = f"{obj_name}_{extra}" if extra else obj_name

    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    handler = logging.StreamHandler(stream=sys.stdout)
    handler.setFormatter(formatter)

    logger.addHandler(handler)

    return logger
