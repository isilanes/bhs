# Standard libs:
import os

# Django libs:
from django.core.wsgi import get_wsgi_application
from whitenoise.django import DjangoWhiteNoise

# Conf:
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "WebBHS.settings")
application = get_wsgi_application()
application = DjangoWhiteNoise(application)

