import logging
import sys


class SeverityFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        if record.levelno >= logging.ERROR:
            fmt = (
                "%(asctime)s | %(levelname)s | %(name)s | "
                "%(filename)s:%(lineno)d | %(message)s"
            )
        else:
            fmt = "%(asctime)s | %(levelname)s | %(message)s"

        return logging.Formatter(
            fmt,
            datefmt="%Y-%m-%d %H:%M:%S",
        ).format(record)


def configure_logging() -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        SeverityFormatter(datefmt="%Y-%m-%d %H:%M:%S")
    )

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.handlers.clear()
    root_logger.addHandler(handler)