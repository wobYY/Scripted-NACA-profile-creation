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
import os
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
            "propagate": False,
        },
        "stdout": {"handlers": ["stdout"], "level": "DEBUG", "propagate": True},
    },
}


def get_logger(name=None, level=None, centralised_logging=True):
    """Create logger."""
    if name:
        if name == "stdout":
            del LOGGER_CONFIG["handlers"]["logfile"]
            LOGGER_CONFIG["loggers"]["root"]["handlers"] = ["stdout"]

        if centralised_logging:
            # Store all logs in the centralised file
            LOGGER_CONFIG["handlers"]["logfile"]["filename"] = os.path.join(
                os.path.dirname(os.path.abspath(__file__)), "../logs.log"
            )
        else:
            # Check if logs directory exists, if not create it
            filepath = os.path.dirname(os.path.abspath(__file__))
            if not os.path.exists(os.path.join(filepath, "../logs")):
                os.makedirs(os.path.join(filepath, "../logs"))
            # Store logs in the logs directory of the grtb package
            logfile_name = f"../logs/logs_{name}.log"
            LOGGER_CONFIG["handlers"]["logfile"]["filename"] = os.path.join(
                filepath, logfile_name
            )
    if level:
        LOGGER_CONFIG["loggers"]["root"]["level"] = level

    logging.config.dictConfig(LOGGER_CONFIG)
    logger = logging.getLogger(name)

    return logger
