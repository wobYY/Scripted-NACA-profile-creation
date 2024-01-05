""" Central logging utility.

    TO CONFIGURE:
    Adjust logging levels in the "loggers" area of LOGGER_CONFIG.
    The given level is the minimum that will be logged. Default is INFO.

    TO USE:
    from utils.logging import get_logger
    logger = get_logger([name to use in logfile, or stdout to only log to console])

    Then log messages with:
    logger.info("Message here")

    Available log levels:
    logger.debug(), logger.info(), logger.warning(), logger.error()
"""
import logging
import logging.config


LOGGER_CONFIG = {
    "version": 1,
    "formatters": {
        "default": {
            "format": "{asctime:<23s} - {levelname:^7s} - {name} - {message}",
            "style": "{",
        }
    },
    "handlers": {
        "stdout": {
            "class": "logging.StreamHandler",
            "formatter": "default",
            "stream": "ext://sys.stdout",
        },
        "logfile": {
            "class": "logging.FileHandler",
            "formatter": "default",
            "filename": "logfile.log",
        },
    },
    "loggers": {
        "root": {
            "handlers": ["stdout", "logfile"],
            "level": "DEBUG",
            "propagate": True,
        },
        "stdout": {"handlers": ["stdout"], "level": "DEBUG", "propagate": False},
    },
}


def get_logger(name=None, level=None):
    """Create logger."""
    if name:
        if name == "stdout":
            del LOGGER_CONFIG["handlers"]["logfile"]
            LOGGER_CONFIG["loggers"]["root"]["handlers"] = ["stdout"]
        else:
            LOGGER_CONFIG["handlers"]["logfile"]["filename"] = f"logfile-{name}.log"
    if level:
        LOGGER_CONFIG["loggers"]["root"]["level"] = level

    logging.config.dictConfig(LOGGER_CONFIG)
    logger = logging.getLogger(name)

    return logger
