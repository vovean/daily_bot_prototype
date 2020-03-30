import logging

from telegram import Update, User, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery, ParseMode
from telegram.ext import Handler, CallbackContext, ConversationHandler, CommandHandler, CallbackQueryHandler, \
    MessageHandler, Filters

from bot.bot_commands.base_conversation import BaseConversation
from bot.sheets.spreadsheet import Spreadsheet
from models.models import Worker, DailyCheckin
from settings import settings

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)


class Checkin(BaseConversation):
    command = "checkin"

    yes_no_keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("Да", callback_data="Да")],
        [InlineKeyboardButton("Нет", callback_data="Нет")],
    ])

    WORKED_TODAY, REASON_NOT_WORKED, TASKS_DONE_TODAY, PROBLEMS_FACED_TODAY, \
    WORK_TOMORROW, TASKS_TOMORROW, WHEN_START, START_SOON, START_NOT_SOON, END_CHECKIN = range(10)

    def on_conversation_start(self, update: Update, context: CallbackContext):
        logger.info(f"User {update.effective_user} has requested a checkin")

    def get_worker(self, user: User) -> (bool, Worker):
        search = Worker.objects.filter(telegram_id=user.id)
        if not search.exists():
            return False, None
        return True, search.first()

    def start(self, update: Update, context: CallbackContext):
        self.on_conversation_start(update, context)
        registered, worker = self.get_worker(update.effective_user)
        if not registered:
            update.message.reply_text("Не найдено работника, привязанного к данному телеграмму")
            return ConversationHandler.END
        if not settings.CHECKIN_SINCE < worker.get_worker_time().time() < settings.CHECKIN_TILL:
            update.message.reply_html(f"В текущий момент невозможно записать отчет\n"
                                      f"Запись отчета доступна с <b>{settings.CHECKIN_SINCE.strftime('%H:%M')}</b> до "
                                      f"<b>{settings.CHECKIN_TILL.strftime('%H:%M')}</b> "
                                      f"(у вас определено {worker.get_worker_time().time().strftime('%H:%M')})")
            return ConversationHandler.END
        if worker.has_checked_in_today():
            update.message.reply_html("<b>Вы уже записывали отчет за сегодня.</b>")
            logger.info(f"User {update.effective_user} has already created a checkin before. "
                        f"Cancelling current checkin...")
            return ConversationHandler.END
        update.message.reply_html("<b>Начинаем запись отчета</b>\n<i>Чтобы прекратить введите /cancel</i>")
        self.tmp_storage[update.effective_user.id] = dict()
        self.tmp_storage[update.effective_user.id]["worker"] = worker
        update.message.reply_html("Ты работал сегодня? ", reply_markup=self.yes_no_keyboard)
        return self.WORKED_TODAY

    def get_worked_today(self, update: Update, context: CallbackContext):
        query: CallbackQuery = update.callback_query
        user_response = query.data
        query.edit_message_text(query.message.text + f"\n<b>{user_response}</b>", parse_mode=ParseMode.HTML)
        self.tmp_storage[update.effective_user.id]["worked_today"] = True if user_response == "Да" else False
        if user_response == "Нет":
            context.bot.send_message(update.effective_chat.id, "Напиши, пожалуйста, причину")
            return self.REASON_NOT_WORKED
        else:
            context.bot.send_message(update.effective_chat.id, "Какие задачи ты выполнил сегодня?")
            return self.TASKS_DONE_TODAY

    def get_reason_not_worked(self, update: Update, context: CallbackContext):
        reason_not_worked = update.message.text
        self.tmp_storage[update.effective_user.id]["reason_not_worked"] = reason_not_worked
        update.message.reply_text("Спасибо, скажи, завтра у тебя получится приступить к работе?",
                                  reply_markup=self.yes_no_keyboard)
        return self.WORK_TOMORROW

    def get_tasks_done_today(self, update: Update, context: CallbackContext):
        tasks_done_today = update.message.text
        self.tmp_storage[update.effective_user.id]["tasks_done_today"] = tasks_done_today
        update.message.reply_text("Какие задачи требуют участия руководителя для достижения результат?")
        return self.PROBLEMS_FACED_TODAY

    def get_problems_faced_today(self, update: Update, context: CallbackContext):
        problems_faced_today = update.message.text
        self.tmp_storage[update.effective_user.id]["problems_today"] = problems_faced_today
        update.message.reply_text("Спасибо, скажи, завтра у тебя получится приступить к работе?",
                                  reply_markup=self.yes_no_keyboard)
        return self.WORK_TOMORROW

    def get_work_tomorrow(self, update: Update, context: CallbackContext):
        query: CallbackQuery = update.callback_query
        user_response = query.data
        query.edit_message_text(query.message.text + f"\n<b>{user_response}</b>", parse_mode=ParseMode.HTML)
        self.tmp_storage[update.effective_user.id]["will_work_tomorrow"] = True if user_response == "Да" else False
        if user_response == "Нет":
            days_keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("2", callback_data="2")],
                [InlineKeyboardButton("3", callback_data="3")],
                [InlineKeyboardButton("4", callback_data="4")],
                [InlineKeyboardButton("5", callback_data="5")],
                [InlineKeyboardButton(">5", callback_data="100")],
            ])
            context.bot.send_message(update.effective_chat.id,
                                     "Подскажи, скажи, через сколько дней планируешь приступить к работе?",
                                     reply_markup=days_keyboard)
            return self.WHEN_START
        else:
            self.tmp_storage[update.effective_user.id]["days_till_start_work"] = 0
            context.bot.send_message(update.effective_chat.id,
                                     "Отлично, над какими задачами планируешь завтра работать?")
            return self.TASKS_TOMORROW

    def get_tasks_tomorrow(self, update: Update, context: CallbackContext):
        tomorrow_tasks = update.message.text
        self.tmp_storage[update.effective_user.id]["tomorrow_tasks"] = tomorrow_tasks
        return self.end_checkin(update, context)

    def get_when_start(self, update: Update, context: CallbackContext):
        query: CallbackQuery = update.callback_query
        user_response = query.data
        query.edit_message_text(query.message.text + f"\n<b>{user_response}</b>", parse_mode=ParseMode.HTML)
        self.tmp_storage[update.effective_user.id]["days_till_start_work"] = int(user_response)
        if user_response != ">5":
            context.bot.send_message(update.effective_chat.id,
                                     "Спасибо, я учту это")
        else:
            context.bot.send_message(update.effective_chat.id,
                                     "Спасибо, если ты не сообщил об этом своему начальнику, то свяжись с ним")
        return self.end_checkin(update, context)

    def end_checkin(self, update: Update, context: CallbackContext):
        new_checkin = DailyCheckin.objects.create(**self.tmp_storage[update.effective_user.id])
        context.bot.send_message(update.effective_chat.id,
                                 "Спасибо, ваш отчет записан")
        del self.tmp_storage[update.effective_user.id]
        Spreadsheet().write_daily_checkin(new_checkin)
        logger.info(f"User {update.effective_user} has created the new checkin id={new_checkin.id}")
        return ConversationHandler.END

    def cancel(self, update: Update, context: CallbackContext):
        logger.info(f"User {update.effective_user} cancelled the checkin")
        del self.tmp_storage[update.effective_user.id]
        update.message.reply_text("Запись отчета отменено")
        return ConversationHandler.END

    def get_handler(self) -> Handler:
        # не /cancel: ^(?!\/cancel$)
        return ConversationHandler(
            entry_points=[
                CommandHandler("checkin", self.start),
            ],
            states={
                self.WORKED_TODAY: [
                    CallbackQueryHandler(self.get_worked_today)
                ],
                self.REASON_NOT_WORKED: [
                    MessageHandler(Filters.text & Filters.regex(r"^(?!\/cancel$)"), self.get_reason_not_worked)
                ],
                self.TASKS_DONE_TODAY: [
                    MessageHandler(Filters.text & Filters.regex(r"^(?!\/cancel$)"), self.get_tasks_done_today)
                ],
                self.PROBLEMS_FACED_TODAY: [
                    MessageHandler(Filters.text & Filters.regex(r"^(?!\/cancel$)"), self.get_problems_faced_today)
                ],
                self.WORK_TOMORROW: [
                    CallbackQueryHandler(self.get_work_tomorrow)
                ],
                self.TASKS_TOMORROW: [
                    MessageHandler(Filters.text & Filters.regex(r"^(?!\/cancel$)"), self.get_tasks_tomorrow)
                ],
                self.WHEN_START: [
                    CallbackQueryHandler(self.get_when_start)
                ],
                self.END_CHECKIN: [
                    MessageHandler(Filters.text & Filters.regex(r"^(?!\/cancel$)"), self.end_checkin)
                ]
            },
            fallbacks=[
                CommandHandler("cancel", self.cancel)
            ]
        )
