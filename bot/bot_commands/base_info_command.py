from telegram import Update
from telegram.ext import CommandHandler, CallbackContext

from models.models import Worker, Admin


class BaseInfoCommand:
    command: str = ""

    def get_info(self, update: Update) -> str:
        worker = Worker.objects.filter(telegram_id=update.effective_user.id)
        if worker.exists():
            return self.get_worker_info(worker.first())
        admin = Admin.objects.filter(telegram_id=update.effective_user.id)
        if admin.exists():
            return self.get_admin_info(admin.first())
        return self.get_guest_info()

    def get_guest_info(self) -> str:
        ...

    def get_worker_info(self, worker: Worker) -> str:
        ...

    def get_admin_info(self, admin: Admin) -> str:
        ...

    def reply_info(self, update: Update, context: CallbackContext):
        update.message.reply_text(self.get_info(update))

    def get_handler(self):
        return CommandHandler(self.command, self.reply_info)
