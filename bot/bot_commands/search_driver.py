import logging
from copy import deepcopy

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, ParseMode
from telegram.ext import CallbackContext, Handler, ConversationHandler, CommandHandler, CallbackQueryHandler, \
    MessageHandler, Filters

from bot.bot_commands.base_conversation import BaseConversation
from models.models import Admin, Worker

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)


class SearchWorker(BaseConversation):
    command = "search_worker"
    search_params: dict = {
        "full_name__icontains": "",
        "position__icontains": "",
    }

    full_search_params_keyboard = [
        [InlineKeyboardButton("Название должности содержит", callback_data="position__icontains")],
        [InlineKeyboardButton("Имя работника содержит", callback_data="full_name__icontains")],
    ]

    callback_to_text = {
        "position__icontains": "Название должности содержит",
        "full_name__icontains": "Имя работника содержит",
    }

    SELECT_FILTER, GET_SEARCH_STRING, DO_SEARCH = range(3)

    def get_search_keyboard(self, current_search_params):
        show_params = [param for param in self.full_search_params_keyboard
                       if not current_search_params[param[0].callback_data]]
        return InlineKeyboardMarkup(show_params + [[InlineKeyboardButton("Искать", callback_data="Искать")]])

    def on_conversation_start(self, update: Update, context: CallbackContext):
        logger.info(f"User {update.effective_user} has started workers search")

    def start_conversation(self, update: Update, context: CallbackContext):
        self.on_conversation_start(update, context)
        self.tmp_storage[update.effective_user.id] = deepcopy(self.search_params)
        is_admin = Admin.objects.filter(telegram_id=update.effective_user.id).exists()
        if not is_admin:
            update.message.reply_text("Только администраторы или менеджеры могут выполнять поиск по работникам")
            return ConversationHandler.END
        update.message.reply_text("Укажите параметры поиска",
                                  reply_markup=self.get_search_keyboard(self.tmp_storage[update.effective_user.id]))
        return self.SELECT_FILTER

    def select_filter(self, update: Update, context: CallbackContext):
        query: CallbackQuery = update.callback_query
        query.edit_message_reply_markup(InlineKeyboardMarkup([[]]))
        if query.data == "Искать":
            return self.do_search(update, context)
        query.edit_message_text(f"**{self.callback_to_text[query.data]}**", parse_mode=ParseMode.MARKDOWN)
        context.user_data["filter"] = query.data
        return self.GET_SEARCH_STRING

    def get_search_string(self, update: Update, context: CallbackContext):
        search_string = update.message.text
        self.tmp_storage[update.effective_user.id][context.user_data["filter"]] = search_string
        del context.user_data["filter"]
        update.message.reply_text("Укажите параметры поиска",
                                  reply_markup=self.get_search_keyboard(self.tmp_storage[update.effective_user.id]))
        return self.SELECT_FILTER

    def do_search(self, update: Update, context: CallbackContext):
        query: CallbackQuery = update.callback_query
        workers = Worker.objects.filter(**self.tmp_storage[update.effective_user.id])
        del self.tmp_storage[update.effective_user.id]
        query.edit_message_text(f"Найдено работников: {workers.count()}")
        if workers.exists():
            context.bot.send_message(update.effective_chat.id, '\n'.join(map(str, workers)))
        return ConversationHandler.END

    def cancel(self, update: Update, context: CallbackContext):
        logger.info(f"User {update.effective_user.id} has cancelled worker search")
        del self.tmp_storage[update.effective_user.id]
        update.message.reply_text("Поиск работника отменен")
        return ConversationHandler.END

    def get_handler(self) -> Handler:
        return ConversationHandler(
            entry_points=[
                CommandHandler(self.command, self.start_conversation)
            ],
            states={
                self.SELECT_FILTER: [
                    CallbackQueryHandler(self.select_filter)
                ],
                self.GET_SEARCH_STRING: [
                    MessageHandler(Filters.all & Filters.regex(r"^(?!\/cancel$)"), self.get_search_string)
                ],
                self.DO_SEARCH: [
                    MessageHandler(Filters.all & Filters.regex(r"^(?!\/cancel$)"), self.do_search)
                ]
            },
            fallbacks=[
                CommandHandler("cancel", self.cancel)
            ]
        )
