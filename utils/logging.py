""" Central logging utility.

    TO CONFIGURE:
    Adjust logging levels in the "loggers" area of LOGGER_CONFIG.
    The given level is the minimum that will be logged. Default is INFO.

    TO USE:
    from utils.logging import get_logger
    logger = get_logger([name to use in logfile, or stdout to only log to console])

    After aquire the logger, use it like this (this logs the message with the level INFO):
    logger.info("Message here")

    Available log levels:
    logger.debug(), logger.info(), logger.warning(), logger.error()
"""

import os
import json
import datetime as dt
import atexit
import logging
import logging.config
import logging.handlers

# Enter your module name here
MODULE_NAME = "scripted-naca-profile-creation"

# If logs directory doesn't exist, create it
LOGS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../logs")
if not os.path.exists(LOGS_DIR):
    os.makedirs(LOGS_DIR)

LOGFILE_FILEPATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "../logs/logfile.jsonl"
)

FULL_LOGFILE_FILEPATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "../logs/complete_logfile.jsonl"
)

LOG_RECORD_BUILTIN_ATTRS = {
    "args",
    "asctime",
    "created",
    "exc_info",
    "exc_text",
    "filename",
    "funcName",
    "levelname",
    "levelno",
    "lineno",
    "module",
    "msecs",
    "message",
    "msg",
    "name",
    "pathname",
    "process",
    "processName",
    "relativeCreated",
    "stack_info",
    "thread",
    "threadName",
    "taskName",
}

LOGGER_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "simple": {
            "format": "{asctime:<23s} - {levelname:^7s} - {module} - {message}",
            "style": "{",
        },
        "json": {
            "()": "utils.logging.JSONFormatter",
            "fmt_keys": {
                "level": "levelname",
                "timestamp": "timestamp",
                "message": "message",
                "logger": "name",
                "pathname": "pathname",
                "module": "module",
                "function": "funcName",
                "line": "lineno",
                "thread_name": "threadName",
            },
        },
    },
    "filters": {"non_module": {"()": "utils.logging.FilterNonModule"}},
    "handlers": {
        "stdout": {
            "class": "logging.StreamHandler",
            "level": "DEBUG",
            "formatter": "simple",
            "stream": "ext://sys.stdout",
            "filters": ["non_module"],
        },
        "logfile": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "DEBUG",
            "formatter": "json",
            "filename": LOGFILE_FILEPATH,
            "filters": ["non_module"],
            "maxBytes": 1000000000,
            "backupCount": 5,
            "encoding": "utf-8",
        },
        "fullLogfile": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "DEBUG",
            "formatter": "json",
            "filename": FULL_LOGFILE_FILEPATH,
            "maxBytes": 1000000000,
            "backupCount": 1,
            "encoding": "utf-8",
        },
        "queue_handler": {
            "class": "logging.handlers.QueueHandler",
            "handlers": ["stdout", "logfile", "fullLogfile"],
            "respect_handler_level": True,
        },
    },
    "loggers": {"root": {"level": "DEBUG", "handlers": ["queue_handler"]}},
}


class FilterNonModule(logging.Filter):
    """
    Filter out loggers that are not part of your module
    which is defined using the MODULE_NAME variable.
    """

    def __init__(self, name=MODULE_NAME):
        super().__init__(name)

    def filter(self, record):
        return MODULE_NAME in record.pathname


class JSONFormatter(logging.Formatter):
    """This class is used to format log records as JSON strings.

    Args:
        logging (Class): Inherit from logging.Formatter.
    """

    def __init__(
        self,
        *,
        fmt_keys: dict[str, str] | None = None,
    ):
        super().__init__()
        self.fmt_keys = fmt_keys if fmt_keys is not None else {}

    # @override
    def format(self, record: logging.LogRecord) -> str:
        message = self._prepare_log_dict(record)
        return json.dumps(message, default=str)

    def _prepare_log_dict(self, record: logging.LogRecord):
        always_fields = {
            "message": record.getMessage(),
            "timestamp": dt.datetime.fromtimestamp(
                record.created, tz=dt.timezone.utc
            ).isoformat(),
        }
        if record.exc_info is not None:
            always_fields["exc_info"] = self.formatException(record.exc_info)

        if record.stack_info is not None:
            always_fields["stack_info"] = self.formatStack(record.stack_info)

        message = {
            key: (
                msg_val
                if (msg_val := always_fields.pop(val, None)) is not None
                else getattr(record, val)
            )
            for key, val in self.fmt_keys.items()
        }
        message.update(always_fields)

        for key, val in record.__dict__.items():
            if key not in LOG_RECORD_BUILTIN_ATTRS:
                message[key] = val

        return message


class CustomLogger:
    """Custom logger class."""

    def __init__(self):
        self.logger = None

    def get_logger(self, name: str, **kwargs):
        """Create logger.

        Args:
            name (str): Name of the logger; Recommendation: Use `__name__`.
            level (str): Level of the logger.
        """

        if kwargs.get("level") is not None:
            # Set the level of the stdout handler
            LOGGER_CONFIG["handlers"]["stdout"]["level"] = kwargs.get("level")

        # Configure the logger
        logging.config.dictConfig(LOGGER_CONFIG)

        # Set it up so that the queue handler is started and stopped when the program starts and stops
        queue_handler = logging.getHandlerByName("queue_handler")
        if queue_handler is not None:
            queue_handler.listener.start()
            atexit.register(queue_handler.listener.stop)

        # Get the logger
        self.logger = logging.getLogger(name)

        # Return the logger
        return self.logger
