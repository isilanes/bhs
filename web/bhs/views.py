# Standard libs:
import os
import subprocess as sp

# Django libs:
from django.http import JsonResponse
from django.shortcuts import render, redirect

# Our libs:
from bhs.models import  BOINCProject, BOINCSettings, LogItem

# My libs:
from logworks import logworks

# Logger:
#logfile = os.path.join(BOINCSettings.objects.get(name="default").logdir, "bhs.log")
logger = logworks.Logger(logfile="bhs.log")

# Index views:
def index(request):
    """Show index."""

    context = {
        "project_list": [p for p in BOINCProject.objects.filter(active=True)],
    }

    return render(request, 'bhs/index.html', context)

def project(request, pname):

    proj = BOINCProject.objects.get(name=pname)

    context = {
        "proj": proj,
        "project_list": [p for p in BOINCProject.objects.filter(active=True)],
    }

    return render(request, 'bhs/project.html', context)


# Data URLs:
def project_data(request, pname, what):
    """Return JSON data for project named 'pname', and item 'what' (nhosts or credit)."""

    proj = BOINCProject.objects.get(name=pname)

    data_win, data_lin, data_mac, data_other = proj.get_plot_data(what)

    data = {
        "win": data_win,
        "lin": data_lin,
        "mac": data_mac,
        "other": data_other,
    }

    return JsonResponse({"data": data})


# Action URLs:
def process_oldest(request):
    """Download and process hosts file for oldest project."""

    # Get project whose less recent log entry is oldest:
    oldest = get_less_recently_logged_project()

    # Download 'oldest' project:
    oldest.download(logger)

    # Process downloaded hosts.gz file:
    oldest.distile_stats(logger)

    # Return data:
    ret = {}

    return JsonResponse(ret)


# Helper functions:
def get_less_recently_logged_project():
    """Return project whose most recent log is the oldest."""

    dsu = []
    for proj in BOINCProject.objects.filter(active=True):
        # Get latest log entry for this project:
        latest = LogItem.objects.filter(project=proj)

        # If no log item found, then never logged. In that case, choose this project:
        if not latest:
            return proj

        latest = latest.order_by("-date")[0]
        dsu.append([latest.date, proj])

    return sorted(dsu)[0][1]

