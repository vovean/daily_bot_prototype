from telegram import Update
from telegram.ext import CommandHandler, CallbackContext

from models.models import Worker


class UnregisterCommand:
    command = "unregister"

    def unregister(self, update: Update, context: CallbackContext):
        worker = Worker.objects.filter(telegram_id=update.effective_user.id)
        if not worker.exists():
            update.message.reply_text("Вы не зарегистрированы как работник")
            return
        worker = worker.first()
        worker.telegram_id = None
        worker.save()
        update.message.reply_text(f"Данный аккант больше не привязан к {worker.full_name}")

    def get_handler(self):
        return CommandHandler(self.command, self.unregister)
