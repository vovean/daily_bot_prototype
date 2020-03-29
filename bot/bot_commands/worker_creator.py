import logging
import string
from datetime import datetime

from telegram import Update, ParseMode
from telegram.ext import ConversationHandler, Handler, CallbackContext, CommandHandler, MessageHandler, Filters

from bot.bot_commands.base_conversation import BaseConversation
from models.models import Worker, Admin

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)


class WorkerCreator(BaseConversation):
    command = "create_worker"
    GET_NAME, GET_POSITION, GET_BOSS, GET_CITY, GET_TIMEDELTA = range(5)

    def on_conversation_start(self, update: Update, context: CallbackContext):
        logger.info(f"User {update.effective_user} has just started creating a worker")

    def start_conversation(self, update: Update, context: CallbackContext):
        self.on_conversation_start(update, context)
        self.tmp_storage[update.effective_user.id] = dict()
        is_admin = Admin.objects.filter(telegram_id=update.effective_user.id).exists()
        if not is_admin:
            update.message.reply_text("Только администраторы могут создавать работников")
            return ConversationHandler.END
        update.message.reply_text("Создание сотрудника (чтобы прекратить отправьте /cancel)\nВведите ФИО работника")
        return self.GET_NAME

    def get_name(self, update: Update, context: CallbackContext):
        received_text = update.message.text
        ok, error = self._validate_name(received_text)
        if not ok:
            update.message.reply_text(error)
            return self.GET_NAME
        self.tmp_storage[update.effective_user.id]["full_name"] = received_text
        # если компания уже есть из менеджера, то скипаем вопрос
        if not self.tmp_storage[update.effective_user.id].get("position", None):
            update.message.reply_text("Отлично, теперь введите название должности на которой он работает")
            return self.GET_POSITION
        update.message.reply_text("Отлично, теперь введите город, в котором работает сотрудник")
        return self.GET_CITY

    def get_position(self, update: Update, context: CallbackContext):
        received_text = update.message.text
        if len(received_text) > 40:
            update.message.reply_text("Название должности должно быть не длиннее 40 символов. Попробуйте еще раз")
            return self.GET_POSITION
        self.tmp_storage[update.effective_user.id]["position"] = received_text
        update.message.reply_text("Отлично, теперь введите город, в котором работает сотрудник")
        return self.GET_CITY

    def get_city(self, update: Update, context: CallbackContext):
        received_text = update.message.text
        if len(received_text) > 40:
            update.message.reply_text("Название города должно быть не длиннее 40 символов. Попробуйте еще раз")
            return self.GET_CITY
        self.tmp_storage[update.effective_user.id]["city"] = received_text
        update.message.reply_text("Отлично, теперь, чтобы определить в какой временной зоне находится работник "
                                  "введите, сколько у него сейчас целых часов по 24-часовой системе")
        return self.GET_TIMEDELTA

    @staticmethod
    def _validate_hours(hours: str) -> (bool, str):
        if not all([char in string.digits for char in hours[-2:]]):
            return False, "Кол-во часов может содержать только цифры"
        hours = int(hours)
        if hours < 0 or hours > 24:
            return False, "Количество часов должно быть в пределе 0 и 24"
        return True, ""

    def get_timedelta(self, update: Update, context: CallbackContext):
        received_text = update.message.text
        ok, error = self._validate_hours(received_text)
        if not ok:
            update.message.reply_text(error)
            return self.GET_TIMEDELTA
        self.tmp_storage[update.effective_user.id]["timedelta"] = int(received_text) - datetime.now().hour
        update.message.reply_text("Отлично, теперь введите ФИО начальника сотрудника")
        return self.GET_BOSS

    def create_new_worker(self, update):
        new_worker = Worker.objects.create(**self.tmp_storage[update.effective_user.id])
        update.message.reply_text(f"Отлично, новый сотрудник создан:\n"
                                  f"<b>{new_worker}</b>\n"
                                  f"Пригласительный код сотрудника:", parse_mode=ParseMode.HTML)
        update.message.reply_text(f"{new_worker.invite_code}")
        logger.info(f"Пользователь {update.effective_user} создал нового работника: {new_worker}")

    def get_boss(self, update: Update, context: CallbackContext):
        received_text = update.message.text
        ok, error = self._validate_name(received_text)
        if not ok:
            update.message.reply_text(error)
            return self.GET_BOSS
        self.tmp_storage[update.effective_user.id]["boss"] = received_text
        self.create_new_worker(update)
        del self.tmp_storage[update.effective_user.id]
        return ConversationHandler.END

    def cancel(self, update: Update, context: CallbackContext):
        logger.info(f"User {update.effective_user} cancelled the conversation")
        del self.tmp_storage[update.effective_user.id]
        return ConversationHandler.END

    def get_handler(self) -> Handler:
        return ConversationHandler(
            entry_points=[
                CommandHandler(self.command, self.start_conversation)
            ],
            states={
                self.GET_NAME: [MessageHandler(Filters.all & Filters.regex(r"^(?!\/cancel$)"), self.get_name)],
                self.GET_POSITION: [MessageHandler(Filters.all & Filters.regex(r"^(?!\/cancel$)"), self.get_position)],
                self.GET_BOSS: [MessageHandler(Filters.all & Filters.regex(r"^(?!\/cancel$)"), self.get_boss)],
                self.GET_CITY: [MessageHandler(Filters.all & Filters.regex(r"^(?!\/cancel$)"), self.get_city)],
                self.GET_TIMEDELTA: [MessageHandler(Filters.all & Filters.regex(r"^(?!\/cancel$)"),
                                                    self.get_timedelta)],
            },
            fallbacks=[
                CommandHandler('cancel', self.cancel)
            ],
            per_user=True
        )
