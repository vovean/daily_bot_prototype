import logging
import re

from telegram import Update
from telegram.ext import CallbackContext, Handler, CommandHandler, ConversationHandler, MessageHandler, Filters

from bot.bot_commands.base_conversation import BaseConversation
from models.models import Worker

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)


class RegisterWorker(BaseConversation):
    command = "register"

    def on_conversation_start(self, update: Update, context: CallbackContext):
        logger.info(f"User {update.effective_user} has attempted to register")

    def help(self):
        return "Формат команды: /register 	&lt;пригласительный код&gt;\n" \
               "Пример: <i>/register 6bf4da7a-2311-4fda-8cfd-537da63ca7c8</i>"

    def start_conv(self, update: Update, context: CallbackContext):
        self.on_conversation_start(update, context)
        if Worker.objects.filter(telegram_id=update.effective_user.id).exists():
            update.message.reply_text("Вы уже зарегистрированы как работник")
            return ConversationHandler.END
        update.message.reply_text("Введите ваш инвайт код. Чтобы отменить введите /cancel")
        return 0

    def _validate_invite_code(self, invite_code: str) -> (bool, str):
        if not re.match(r"[0-9]{5}", invite_code):
            return False, "Код должен быть длиной 5 и состоять только из цифр"
        return True, ""

    @staticmethod
    def register_by_invite_code(invite_code: str,
                                update: Update) -> (bool, Worker):
        user = Worker.objects.filter(invite_code=invite_code)
        if not user.exists():
            return False, None
        user = user.first()
        user.telegram_id = str(update.effective_user.id)
        user.save()
        return True, user

    def process_code(self, update: Update, context: CallbackContext):
        received_code = update.message.text
        ok, error = self._validate_invite_code(received_code)
        if not ok:
            update.message.reply_text(error)
            return
        user_exists, worker = self.register_by_invite_code(received_code, update)
        if not worker:
            update.message.reply_text(f"Не найдено пользователя с таким пригласительным кодом")
            return
        update.message.reply_text(f"Вы успешно зарегистрированы как работник {worker.full_name}")
        logger.info(f"User {update.effective_user} has registered as {worker.full_name}")
        return ConversationHandler.END

    def cancel(self, update: Update, context: CallbackContext):
        logger.info(f"User {update.effective_user} cancelled the registration as a Worker")
        update.message.reply_text("Регистрация отменена")
        return ConversationHandler.END

    def get_handler(self) -> Handler:
        return ConversationHandler(
            entry_points=[CommandHandler(self.command, self.start_conv)],
            states={
                0: [MessageHandler(Filters.all & Filters.regex(r"^(?!\/cancel$)"), self.process_code)]
            },
            fallbacks=[
                CommandHandler("cancel", self.cancel)
            ]
        )
