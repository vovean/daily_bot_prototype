from telegram import Update

from bot.bot_commands.base_info_command import BaseInfoCommand
from models.models import Worker, Admin, DailyCheckin


class GetMeCommand(BaseInfoCommand):
    command = "me"

    def get_guest_info(self):
        return "Вы не зарегистрированы в данном боте"

    def get_worker_info(self, worker: Worker) -> str:
        reply = f"ФИО: {worker.full_name}\n" \
                f"Место работы: {worker.company}\n" \
                f"Руководитель: {worker.mentor}\n" \
                f"Записано дейликов: {worker.dailycheckin_set.count()}\n" \
                f"Последний дейлик: {worker.dailycheckin_set.last().created.strftime('%d.%m.%Y') if worker.dailycheckin_set.count() > 0 else ''}\n"
        return reply

    def get_admin_info(self, admin: Admin) -> str:
        return "ADMIN"
