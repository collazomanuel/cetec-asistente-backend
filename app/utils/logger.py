import logging
import inspect
from pathlib import Path
from logging.handlers import RotatingFileHandler

class Logger:
    def __init__(self, log_file: str = "logs/logs.txt", level: int = logging.INFO):
        # Ensure logs directory exists
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        # Get dynamic logger name from caller
        caller = inspect.stack()[1].filename
        logger_name = Path(caller).stem

        self.logger = logging.getLogger(logger_name)
        self.logger.setLevel(level)
        self.logger.propagate = False

        if self.logger.hasHandlers():
            self.logger.handlers.clear()

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        console_handler.setFormatter(self._get_formatter())

        # Rotating file handler
        file_handler = RotatingFileHandler(log_file, maxBytes=5*1024*1024, backupCount=5)
        file_handler.setLevel(level)
        file_handler.setFormatter(self._get_formatter())

        self.logger.addHandler(console_handler)
        self.logger.addHandler(file_handler)

    def _get_formatter(self):
        return logging.Formatter(
            fmt="[{asctime}] [{levelname}] [{filename}:{lineno} - {funcName}] {message}",
            datefmt="%Y-%m-%d %H:%M:%S",
            style="{"
        )

    def info(self, msg: str):
        self.logger.info(msg, stacklevel=2)

    def warning(self, msg: str):
        self.logger.warning(msg, stacklevel=2)

    def error(self, msg: str):
        self.logger.error(msg, stacklevel=2)

    def debug(self, msg: str):
        self.logger.debug(msg, stacklevel=2)

    def critical(self, msg: str):
        self.logger.critical(msg, stacklevel=2)
