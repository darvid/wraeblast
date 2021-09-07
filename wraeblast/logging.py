import logging
import logging.config
import os

import structlog
from pythonjsonlogger import jsonlogger


def initialize_logging(
    default_level: str = "INFO",
    default_formatter: str = "colored",
    timestamp_format: str = "%Y-%m-%d %H:%M:%S",
) -> None:
    timestamper = structlog.processors.TimeStamper(fmt=timestamp_format)
    pre_chain = [
        structlog.stdlib.add_log_level,
        timestamper,
    ]

    log_level = os.getenv("LOG_LEVEL", default_level)
    log_formatter = os.getenv("LOG_FORMATTER", default_formatter)

    logging.config.dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "plain": {
                    "()": structlog.stdlib.ProcessorFormatter,
                    "processor": structlog.dev.ConsoleRenderer(colors=False),
                    "foreign_pre_chain": pre_chain,
                },
                "colored": {
                    "()": structlog.stdlib.ProcessorFormatter,
                    "processor": structlog.dev.ConsoleRenderer(colors=True),
                    "foreign_pre_chain": pre_chain,
                },
                "json": {
                    "()": jsonlogger.JsonFormatter,
                },
            },
            "handlers": {
                "default": {
                    "level": log_level,
                    "class": "logging.StreamHandler",
                    "formatter": log_formatter,
                },
            },
            "loggers": {
                "": {
                    "handlers": ["default"],
                    "level": log_level,
                    "propagate": True,
                },
            },
        }
    )
    structlog.configure(
        processors=[
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            timestamper,
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
