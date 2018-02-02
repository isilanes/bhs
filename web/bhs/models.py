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

    # Public methods:
    def get_plot_data(self, what):
        """Generate plot data for 'what'."""

        # Get settings:
        SETTINGS = BOINCSettings.objects.get(name="default")

        # File to read data from:
        fn = "{s.full_name}.{w}.dat".format(s=self, w=what)
        fn = os.path.join(SETTINGS.logdir, fn)

        # Arrays to put data:
        X = [] # x axis (time)
        Y = [[], [], [], []] # values for Windows, Linux, Darwin (Max) and other

        # Collect info:
        with open(fn) as f:
            for line in f:
                aline = [ int(x) for x in line.split() ]
                dt = timezone.timedelta(seconds=int(aline[0]))
                t = SETTINGS.ref_date + dt
                X.append(t)
                for i in range(4):
                    Y[i].append(aline[i+1])

        # Plot:
        data_win = []
        for x, y in zip(X, Y[0]):
            e = { "x": x, "y": y}
            data_win.append(e)

        data_lin = []
        for x, y in zip(X, Y[1]):
            e = { "x": x, "y": y}
            data_lin.append(e)

        data_mac = []
        for x, y in zip(X, Y[2]):
            e = { "x": x, "y": y}
            data_mac.append(e)

        data_other = []
        for x, y in zip(X, Y[3]):
            e = { "x": x, "y": y}
            data_other.append(e)

        return data_win, data_lin, data_mac, data_other


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

