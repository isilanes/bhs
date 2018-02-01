# Django libs:
from django.contrib import admin

# Our libs:
from bhs.models import BOINCProject, BOINCSettings

# Register your models here:
admin.site.register(BOINCProject)
admin.site.register(BOINCSettings)
