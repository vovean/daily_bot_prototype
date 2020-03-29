import logging

from telegram import Update
from telegram.ext import Handler, CallbackContext

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)


class BaseConversation:
    command: str
    tmp_storage: dict = dict()

    @staticmethod
    def _validate_name(name: str) -> (bool, str):
        if len(name.split(' ')) < 3:
            return False, "Имя должно содержать минимум 3 слова. Попробуйте еще раз"
        if len(name) > 50:
            return False, "Имя должно быть не длиннее 50 символов. Попробуйте еще раз"
        return True, ""

    def on_conversation_start(self, update: Update, context: CallbackContext):
        logger.info(f"User {update.effective_user} has started a conversation: {self.__class__.__name__}")

    def get_handler(self) -> Handler:
        ...
