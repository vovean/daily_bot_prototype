# == == == == == == == == == Next line is needed to use Django ORM == == == == == == == == ==
from bot import setup_django
# == == == == == == == == == == == == == == == == == == == == == == == == == == == == == == ==
import logging
from typing import List

from telegram import Update
from telegram.ext import Updater, Dispatcher, CommandHandler, CallbackContext, JobQueue

from bot.bot_commands.base_conversation import BaseConversation
from bot.bot_commands.checkin import Checkin
from bot.bot_commands.get_me_command import GetMeCommand
from bot.bot_commands.help_command import HelpCommand
from bot.bot_commands.register_worker import RegisterWorker
from bot.bot_commands.search_driver import SearchWorker
from bot.bot_commands.unregister import UnregisterCommand
from bot.bot_commands.worker_creator import WorkerCreator
from bot.jobs.base_job import BaseJob
from bot.jobs.checkin_reminder import DailyReminder
from bot.secrets import TG_TOKEN

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


def echo(update: Update, context: CallbackContext):
    update.message.reply_text(update.message.text)


def set_handlers(commands: List[BaseConversation], dp: Dispatcher):
    for command in commands:
        dp.add_handler(command.get_handler())
    # extra
    dp.add_handler(CommandHandler('echo', echo))


def create_jobs(job_classes: List[BaseJob], jq: JobQueue):
    for job in job_classes:
        jq.run_repeating(job.run, interval=job.get_interval(), first=job.get_delay())


if __name__ in ['__main__', 'bot.main']:
    updater: Updater = Updater(token=TG_TOKEN, use_context=True)
    dispatcher: Dispatcher = updater.dispatcher
    job_queue: JobQueue = updater.job_queue

    set_handlers([
        WorkerCreator(),
        RegisterWorker(),
        Checkin(),
        SearchWorker(),
        GetMeCommand(),
        UnregisterCommand(),
        HelpCommand()
    ], dispatcher)
    create_jobs([
        DailyReminder()
    ], job_queue)

    updater.start_polling()
