from bot.bot_commands.base_info_command import BaseInfoCommand
from models.models import Admin, Worker


class HelpCommand(BaseInfoCommand):
    command = "help"

    def get_guest_info(self) -> str:
        reply = "Данный бот предназначен для сбора ежедневных отчетов" \
                "о выполненных задачах, проблемах и планах работников\n" \
                "Если вы работник, то напишите /register и введите инвайт-код, полученный от начальства"
        return reply

    def get_worker_info(self, worker: Worker) -> str:
        reply = "/checkin - записать отчет за день\n" \
                "/me - получить информацию об аккаунте\n" \
                "/unregister - выйти из аккаунта работника в данном боте\n" \
                "/help - вызвать эту справку еще раз\n" \
                "/cancel - отменить запущенный диалог с ботом (если начат какой-то диалог)\n"
        return reply

    def get_admin_info(self, admin: Admin) -> str:
        reply = "/create_worker - зарегистрировать работника\n" \
                "/me - получить информацию об аккаунте\n" \
                "/register - зарегистрироваться как работник\n" \
                "/unregister - выйти из аккаунта работника в данном боте\n" \
                "/search_worker - получить список зарегистрированных работников с некоторой фильтрацией\n" \
                "/help - вызвать эту справку еще раз\n" \
                "/cancel - отменить запущенный диалог с ботом (если начат какой-то диалог)\n"
        return reply
