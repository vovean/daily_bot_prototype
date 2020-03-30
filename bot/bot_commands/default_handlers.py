import logging

from telegram import Update
from telegram.ext import CallbackContext, ConversationHandler, CommandHandler, MessageHandler, Filters

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)


def _cancel(update: Update, context: CallbackContext):
    logger.info(f"User {update.effective_user} cancelled the conversation")
    return ConversationHandler.END


CancelConversationHandler = CommandHandler('cancel', _cancel)


def _error(update: Update, context: CallbackContext):
    logger.error(f"Update {update} caused error {context.error}")


ErrorHandler = MessageHandler(Filters.text, _error)
