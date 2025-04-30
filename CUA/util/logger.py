import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from ..cfg import get_cfg


class _VERBOSE:
    @property
    def L1(self):
        return get_cfg().verbose.L1

    @property
    def L2(self):
        return get_cfg().verbose.L2

    @property
    def L3(self):
        return get_cfg().verbose.L3

    @property
    def L4(self):
        return get_cfg().verbose.L4


VERBOSE = _VERBOSE

_LOG_LEVELS = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL,
}


def _get_logger(
    log_levels: bool = get_cfg().logger.log_current_levels,
    default_level: str = get_cfg().logger.loglevel,
    name: str = get_cfg().logger.name,
    path: str | None = get_cfg().logger.logdir,
    autocreate_path: bool = True,
    rot_n_files: int = get_cfg().logger.max_logfiles,
    rot_filesize_mb: int = get_cfg().logger.max_file_size_mb,
    format: str = get_cfg().logger.format,
) -> logging.Logger:
    """
    Configures and returns a logger with a specific name and format.

    The logger is configured to display the time of logging, the severity level,
    the file where the logging was called, and the line number, along with the log message.

    Returns:
        logging.Logger: Configured logger.
    """
    logger = logging.getLogger(name)

    # Reset the handlers
    logger.handlers = []

    # Log Level
    logger.setLevel(_LOG_LEVELS.get(default_level, logging.DEBUG))

    # Log format
    def_formatter = logging.Formatter(format)

    # StreamHandler
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(def_formatter)
    stream_handler.setLevel(_LOG_LEVELS.get(default_level, logging.DEBUG))
    logger.addHandler(stream_handler)

    if path:  # Check if path is provided
        log_file = Path(path, f"{name}.log")
        if not log_file.parent.exists() and autocreate_path:
            log_file.parent.mkdir(parents=True)

        # File handler
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=rot_filesize_mb * 1024 * 1024,
            backupCount=rot_n_files,
        )
        file_handler.setFormatter(def_formatter)
        file_handler.setLevel(_LOG_LEVELS.get(default_level, logging.DEBUG))
        logger.addHandler(file_handler)

    # Set the log level
    logger.setLevel(default_level)

    # Test the log levels
    if log_levels:
        logger.info("This is an [INFO] message")
        logger.debug("This is a [DEBUG] message")
        logger.warning("This is a [WARNING] message")
        logger.error("This is an [ERROR] message")
        logger.critical("This is a [CRITICAL] message")

    return logger


logger = _get_logger()
