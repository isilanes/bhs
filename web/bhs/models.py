# Django libs:
from django.db import models
from django.utils import timezone

# Classes:
class BOINCProject(models.Model):
    """Data and methods for a BOINC project."""

    # Attributes:
    name = models.CharField("Name", default="none", max_length=100)
    icon = models.CharField("Icon", default="none.png", max_length=50)
    full_name = models.CharField("Long name", default="none", max_length=100)
    url = models.CharField("URL", default="none", max_length=500)
    active = models.BooleanField("Active", default=True)

    # Public properties:
    @property
    def total_amount(self):
        """Sum of all amounts that have this TimeInstant as timestamp."""

        return sum([a.value for a in Amount.objects.filter(when=self)])

    
    # Special methods:
    def __unicode__(self):
        return self.__str__()

    def __str__(self):
        return self.full_name

