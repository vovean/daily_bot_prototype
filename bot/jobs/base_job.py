import logging

from telegram.ext import CallbackContext

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)


class BaseJob:
    # seconds
    interval: int
    enabled: bool = True

    def job(self, context: CallbackContext):
        ...

    def get_delay(self):
        return 0

    def get_interval(self):
        return self.interval

    def run(self, context: CallbackContext):
        if self.enabled:
            self.job(context)
        else:
            logger.info(f"Job {self.__class__.__name__} is disabled")
