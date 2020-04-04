import logging
from datetime import timedelta, datetime

from django.db.models import Q
from django.utils import timezone
from django.utils.datetime_safe import time
from telegram.ext import CallbackContext

from bot.jobs.base_job import BaseJob
from models.models import Worker, DailyCheckin
from settings import settings

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)


class DailyReminder(BaseJob):

    def __init__(self, interval=None, delay=None):
        self.delay = delay
        self.interval = interval

    @staticmethod
    def _seconds_till_next_hour():
        delta = timedelta(hours=1)
        now = datetime.now()
        next_hour = (now + delta).replace(microsecond=0, second=0, minute=0)
        return (next_hour - now).seconds

    def get_delay(self):
        if self.delay is None:
            return self._seconds_till_next_hour()
        return self.delay

    def get_interval(self):
        if self.interval is None:
            return settings.CHECKIN_CHECK_EVERY
        return self.interval

    def remind_planned_tasks(self, context):
        morning_reminder_text = "Привет, ты вчера запланировал:\n{0}"
        today = timezone.now().replace(hour=0, minute=0, second=1)
        yesterday = today - timezone.timedelta(days=1)
        yesterday_reports = DailyCheckin.objects.filter(created__lt=today,
                                                        created__gt=yesterday,
                                                        will_work_tomorrow=True)
        for report in yesterday_reports:
            if report.worker.get_worker_time().hour == settings.REMIND_PLANNED_AT:
                context.bot.send_message(chat_id=report.worker.telegram_id,
                                         text=morning_reminder_text.format(report.tomorrow_tasks))

    def remind_checkin(self, context):
        daily_prompt = "Пришло время заполнить дейли отчет. Для этого введите команду /checkin"
        workers_to_checkin = [worker for worker in Worker.objects.all()
                              if not worker.has_checked_in_today() and
                              settings.CHECKIN_SINCE < worker.get_worker_time().time() < settings.CHECKIN_TILL and
                              worker.tg_verified()]
        for tg_user in workers_to_checkin:
            last_daily: DailyCheckin = tg_user.dailycheckin_set.last()
            if last_daily.will_work_tomorrow is False and \
                    timezone.now() > last_daily.created.replace(hour=0, minute=0, second=0) + \
                    timedelta(days=last_daily.days_till_start_work + 1):
                context.bot.send_message(chat_id=tg_user.telegram_id, text=daily_prompt)

    def job(self, context: CallbackContext):
        self.remind_planned_tasks(context)
        self.remind_checkin(context)

    def run(self, context: CallbackContext):
        super().run(context)
