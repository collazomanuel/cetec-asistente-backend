from app.utils.logger import Logger

class ErrorHandler:
    def __init__(self, logger: Logger):
        self.logger = logger

    def handle(self, exception: Exception, context: str = ""):
        """
        Logs the exception with optional context information.
        """
        message = f"Exception occurred"
        if context:
            message += f" during {context}"
        message += f": {str(exception)}"
        self.logger.error(message)