# Standard libs:
import os

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


class BOINCSettings(models.Model):
    """Set of settings."""

    # Attributes:
    name = models.CharField("Name", default="none", max_length=50)
    bwlimit = models.IntegerField("Bandwidth limit", default=100)
    logdir = models.CharField("Log dir", 
                              default=os.path.join(os.environ['HOME'], ".LOGs", "boinc"), 
                              max_length=200)
    ref_date = models.DateField("Reference date", default=timezone.datetime(1970, 1, 1))

    # Special methods:
    def __unicode__(self):
        return self.__str__()

    def __str__(self):
        return self.name

