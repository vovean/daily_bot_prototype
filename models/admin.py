from django.contrib import admin

# Register your models here.
from models.models import Worker, DailyCheckin, Admin

admin.site.register(Worker)
admin.site.register(Admin)
admin.site.register(DailyCheckin)
