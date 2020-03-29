from datetime import datetime, timedelta
from random import choice

from django.contrib.auth.models import User
from django.db import models
from django.db.models import ForeignKey
from django.db.models import Model, OneToOneField, PROTECT
from django.db.models.fields import CharField, BooleanField, IntegerField, DateTimeField, BigIntegerField
from django.utils import timezone

# Create your models here.
from models.model_managers import DailyCheckinManager


def generate_invite_code():
    successors = [Worker]
    length = 5

    code = "".join([choice("1234567890") for i in range(length)])
    while any([s.objects.filter(invite_code=code).exists() for s in successors]):
        code = "".join([choice("1234567890") for i in range(length)])
    return code


class TelegramUser(Model):
    full_name = CharField(max_length=50)
    company = CharField(max_length=40)
    invite_code = CharField(max_length=40, default=generate_invite_code)
    telegram_id = BigIntegerField(blank=True, null=True, unique=True)

    class Meta:
        abstract = True


class Admin(Model):
    user = OneToOneField(User, on_delete=PROTECT)
    telegram_id = BigIntegerField(blank=True, null=True)

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        if not self.user.is_superuser:
            raise Exception("None superuser cannot be admin")
        super().save(force_insert, force_update, using, update_fields)

    def __repr__(self):
        return self.user.get_full_name()

    def __str__(self):
        return self.__repr__()


class Worker(TelegramUser):
    created = DateTimeField(default=timezone.now)
    mentor = CharField(max_length=50)
    timedelta = IntegerField()
    city = CharField(max_length=40)

    def get_worker_time(self) -> datetime:
        """
        Calculates worker's local time basing on timedelta

        :return: Worker's local datetime
        """
        return datetime.now() + timedelta(hours=self.timedelta)

    def has_checked_in_today(self) -> bool:
        """
        Checks if a worker has already created a checkin today

        :return: bool
        """
        return DailyCheckin.objects.today_checkins(self).exists()

    def tg_verified(self) -> bool:
        return int(self.telegram_id or 0) > 0

    def __repr__(self):
        return f"{self.id}) {self.full_name} - сотрудник из {self.company} под менторством {self.mentor}"

    def __str__(self):
        return self.__repr__()


class DailyCheckin(Model):
    created = DateTimeField(default=timezone.now)
    worker = ForeignKey(Worker, on_delete=models.PROTECT)
    worked_today = BooleanField(default=False)
    reason_not_worked = CharField(max_length=300)
    tasks_done_today = CharField(max_length=1000)
    # проблемы с которыми столкнулся
    problems_today = CharField(max_length=500)
    will_work_tomorrow = BooleanField(default=False)
    # над чем работать завтра
    tomorrow_tasks = CharField(max_length=1000)
    # если не будет работать завтра, то через сколько начнет
    days_till_start_work = IntegerField()

    # кастомный манагер, там определен метод today_checkins, в остальном - обычный
    objects = DailyCheckinManager()

    def __repr__(self):
        return f"Дейлик от {self.worker.full_name} за {self.created.strftime('%d.%m.%Y')} " \
               f"(работал: {'да' if self.worked_today else 'нет'})"

    def __str__(self):
        return self.__repr__()
