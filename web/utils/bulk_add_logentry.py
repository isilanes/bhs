# Standard libs:
import os
import sys
import subprocess as sp

# Django libs:
import django
from django.utils import timezone
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "WebBHS.settings")
sys.path.append("{h}/git/GitHub/bhs/web".format(h=os.environ["HOME"])) # local
django.setup()

# Our libs:
from bhs.models import  BOINCProject, BOINCSettings, LogEntry

# My libs:
from logworks import logworks

# Logger:
logger = logworks.ConsoleLogger()

# Variables:
PNAME = sys.argv[1]
SETTINGS = BOINCSettings.objects.get(name="default")

# Functions:
def empty():
    """Return empty log entry."""

    e = {}
    for so in ["win", "lin", "mac", "other"]:
        e[so] = {}

    return e


# Code:
proj = BOINCProject.objects.get(name=PNAME)
logger.info("Will bulk-add {p}".format(p=proj))

# Harvest data:
data = {}
for what in ["nhosts", "credit"]:
    fn = "{p.full_name}.{w}.dat".format(p=proj, w=what)
    fn = os.path.join(SETTINGS.logdir, fn)
    
    logger.info("Reading {fn}...".format(fn=fn))

    with open(fn, "r") as fhandle:
        for line in fhandle:
            try:
                timestamp, win, lin, mac, other = [int(x) for x in line.split()]
                data[timestamp] = data.get(timestamp, empty())
                data[timestamp]["win"][what] = win
                data[timestamp]["lin"][what] = lin
                data[timestamp]["mac"][what] = mac
                data[timestamp]["other"][what] = other
                dt = timezone.timedelta(seconds=timestamp)
            except:
                print(line.strip())
                break

            t = SETTINGS.ref_date + dt
            logger.info("Harvesting {w} data for time {t}".format(t=t, w=what))

# Insert data into DB:
for timestamp in data:
    dt = timezone.timedelta(seconds=timestamp)
    t = SETTINGS.ref_date + dt

    # Check if already in DB:
    try:
        e = LogEntry.objects.get(date=t)
        logger.warning("{w} data for time {t} already in DB. Skipping...".format(t=t, w=what))
        continue
    except:
        pass
    
    logger.info("Inserting {w} data for time {t} into DB".format(t=t, w=what))

    L = LogEntry()
    L.project = proj
    L.date = t
    L.nwindows = data[timestamp]["win"]["nhosts"]
    L.nlinux = data[timestamp]["lin"]["nhosts"]
    L.nmacos = data[timestamp]["mac"]["nhosts"]
    L.nother = data[timestamp]["other"]["nhosts"]
    L.cwindows = data[timestamp]["win"]["credit"]
    L.clinux = data[timestamp]["lin"]["credit"]
    L.cmacos = data[timestamp]["mac"]["credit"]
    L.cother = data[timestamp]["other"]["credit"]
    L.save()
    
