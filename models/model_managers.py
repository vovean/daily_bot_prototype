from django.db.models import Manager
from django.utils import timezone


class DailyCheckinManager(Manager):
    def today_checkins(self, by_worker=None):
        """
        Gets checkins created today

        :param by_worker:  Filter by specified worker
        :return: Queryset
        """
        params = {
            "created__gt": (timezone.now().today() - timezone.timedelta(days=1)).replace(hour=23, minute=59, second=59),
        }
        if by_worker is not None:
            params.update({
                "worker__telegram_id": by_worker.telegram_id
            })
        return self.get_queryset().filter(**params)
