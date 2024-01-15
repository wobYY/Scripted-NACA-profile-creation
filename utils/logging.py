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
    "disable_existing_loggers": False,
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
            "level": "INFO",
        },
        "logfile": {
            "class": "logging.FileHandler",
            "formatter": "default",
            "filename": "logfile.log",
            "encoding": "utf-8",
            "level": "DEBUG",
        },
    },
    "loggers": {
        "root": {
            "handlers": ["logfile", "stdout"],
            "level": "DEBUG",
            "propagate": False,
            "encoding": "utf-8",
        },
    },
}


def get_logger(
    name=__name__,
    level: str = "INFO",
    centralised_logging: bool = True,
    ignore_other_loggers: bool = True,
):
    """Create logger."""
    if name:
        if centralised_logging:
            # Store all logs in the centralised file
            LOGGER_CONFIG["handlers"]["logfile"]["filename"] = os.path.join(
                os.path.dirname(os.path.abspath(__file__)), "../logfile.log"
            )
        else:
            # Check if logs directory exists, if not create it
            filepath = os.path.dirname(os.path.abspath(__file__))
            if not os.path.exists(os.path.join(filepath, "../logs")):
                os.makedirs(os.path.join(filepath, "../logs"))
            # Store logs in the parent directory
            logfile_name = f"../logs/logfile_{name}.log"
            LOGGER_CONFIG["handlers"]["logfile"]["filename"] = os.path.join(
                filepath, logfile_name
            )
    if level:
        # Set the level of the stdout handler
        LOGGER_CONFIG["handlers"]["stdout"]["level"] = level

    # Configure the logger
    logging.config.dictConfig(LOGGER_CONFIG)

    # Get the logger
    logger = logging.getLogger(name)

    # Ignore loggers from other packages
    if ignore_other_loggers:
        for log_name, log_obj in logging.Logger.manager.loggerDict.items():
            # Replace the "snpc" with the name of your package if you're using this
            # in your own package, otherwise set the name of the logger when you
            # call get_logger() and set the if statement to that name
            if "snpc" not in log_name:
                log_obj.disabled = True

    # Return the logger
    return logger
