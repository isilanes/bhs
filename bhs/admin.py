# Django libs:
from django.contrib import admin

# Our libs:
from bhs.models import BOINCProject, BOINCSettings, LogEntry

# Register your models here:
admin.site.register(BOINCProject)
admin.site.register(BOINCSettings)
admin.site.register(LogEntry)
