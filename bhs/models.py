# Standard libs:
import os
import re
import requests

# Django libs:
from django.db import models
from django.utils import timezone

# Our libs:
from WebBHS import settings

# Functions:
def preferences():
    """Return required BOINCSettings object."""

    return BOINCSettings.objects.get(name=settings.WHICH_SETTINGS)


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
        #SETTINGS = BOINCSettings.objects.get(name="default")

        # File to read data from:
        fn = "{s.full_name}.{w}.dat".format(s=self, w=what)
        fn = os.path.join(preferences().logdir, fn)

        # Arrays to put data:
        X = [] # x axis (time)
        Y = [[], [], [], []] # values for Windows, Linux, Darwin (Max) and other

        # Collect info:
        with open(fn) as f:
            for line in f:
                aline = [ int(x) for x in line.split() ]
                dt = timezone.timedelta(seconds=int(aline[0]))
                t = preferences().ref_date + dt
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

    def download(self, logger=None):
        """Download hosts.gz file."""

        # Anounce our intent:
        msg = "Will download project [ {s} ]".format(s=self)
        logger.info(msg)

        # Variables:
        #rate = BOINCSettings.objects.get(name="default").bwlimit
        rate = preferences().bwlimit
        if logger:
            msg = "Will download at a rate of {r} kb/s".format(r=rate)
            logger.info(msg)

        # Say we will download:
        if logger:
            msg = "Will download from URL: {u}".format(u=self.url)
            logger.info(msg)

        # Perform download:
        r = requests.get(self.url, stream=True)
        with open(self.hostsgz_fn, "wb") as fhandle:
            for chunk in r:
                fhandle.write(chunk)

        # Say we downloaded:
        if logger:
            msg = "Downloaded hosts.gz for project [ {s.full_name} ]".format(s=self)
            logger.info(msg)

    def distile_stats(self, logger=None, delete=True):
        """Distile the stats from a downloaded hosts.gz file.
        hosts.gz file is deleted afterwards, if 'delete' is True.
        """
        # Initialize:
        credit = 0
        os_list = ['win', 'lin', 'mac', 'oth']
        stat = {}
        for os_name in os_list:
            stat[os_name] = {"nhosts": 0, "credit": 0 }
  
        # Pre-compile pattern, for speed:
        pattern = r'total_credit>([^<]+)<';
        search_cre = re.compile(pattern).search
        
        # Say we will distile:
        if logger:
            msg = "Will gather data from hosts file: {s.hostsgz_fn}".format(s=self)
            logger.info(msg)

        # Distile file with Unix and connect to process:
        cmd = 'zcat {s.hostsgz_fn} | grep -F -e total_credit -e os_name'.format(s=self)
        with os.popen(cmd) as f:
            odd = True
            for line in f:
                if odd:
                    credit = float(search_cre(line).group(1))
                    odd = False
                else:
                    odd = True
                    if 'Windows' in line:
                        stat['win']["nhosts"] += 1
                        stat['win']["credit"] += credit
                    elif 'Linux' in line:
                        stat['lin']["nhosts"] += 1
                        stat['lin']["credit"] += credit
                    elif 'Darwin' in line:
                        stat['mac']["nhosts"] += 1
                        stat['mac']["credit"] += credit
                    else:
                        stat['oth']["nhosts"] += 1
                        stat['oth']["credit"] += credit
  
        if logger:
            msg = "Data gathered for project [ {s.full_name} ]".format(s=self)
            logger.info(msg)

        # Save log item:
        L = LogEntry()
        L.project = self
        L.date = timezone.now()
        L.nwindows = stat["win"]["nhosts"]
        L.nlinux = stat["lin"]["nhosts"]
        L.nmacos = stat["mac"]["nhosts"]
        L.nother = stat["oth"]["nhosts"]
        L.cwindows = stat["win"]["credit"]
        L.clinux = stat["lin"]["credit"]
        L.cmacos = stat["mac"]["credit"]
        L.cother = stat["oth"]["credit"]
        L.save()

        if logger:
            msg = "Data for project [ {s.full_name} ] saved in DB".format(s=self)
            logger.info(msg)

        if delete:
            if logger:
                msg = "Log file will be deleted: {s.hostsgz_fn}".format(s=self)
                logger.warning(msg)
            os.unlink(self.hostsgz_fn)


    # Public properties:
    @property
    def hostsgz_fn(self):
        """Full path to downloaded hosts.gz file."""

        #return os.path.join(BOINCSettings.objects.get(name="default").logdir, "{s.name}_hosts.gz".format(s=self))
        return os.path.join(preferences().logdir, "{s.name}_hosts.gz".format(s=self))


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
    ref_date = models.DateTimeField("Reference date", default=timezone.datetime(1970, 1, 1))

    # Public properties:
    pass

    # Special methods:
    def __unicode__(self):
        return self.__str__()

    def __str__(self):
        return self.name

class LogEntry(models.Model):
    """Log item."""

    # Attributes:
    project = models.ForeignKey(BOINCProject, on_delete=models.CASCADE, default=1)
    date = models.DateTimeField("Timestamp", default=timezone.now)
    nwindows = models.IntegerField("Windows hosts", default=0)
    nlinux = models.IntegerField("Linux hosts", default=0)
    nmacos = models.IntegerField("MacOS hosts", default=0)
    nother = models.IntegerField("Other hosts", default=0)
    cwindows = models.FloatField("Windows credits", default=0.0)
    clinux = models.FloatField("Linux credits", default=0.0)
    cmacos = models.FloatField("MacOS credits", default=0.0)
    cother = models.FloatField("Other credits", default=0.0)

    # Special methods:
    def __unicode__(self):
        return self.__str__()

    def __str__(self):
        return "{s.project} logged at {s.date}".format(s=self)

