# Standard libs:
import os
import subprocess as sp

# Django libs:
from django.http import JsonResponse
from django.shortcuts import render, redirect

# Our libs:
from bhs.models import  BOINCProject, LogEntry
from bhs.models import preferences

# My libs:
from logworks import logworks

# Logger:
logger = logworks.Logger(logfile="bhs.log")

# Index views:
def index(request):
    """Show index."""

    context = {
        "project_list": [p for p in BOINCProject.objects.filter(active=True)],
    }

    return render(request, 'bhs/index.html', context)

def project(request, pname):
    """Show plots for project named 'pname'."""

    proj = BOINCProject.objects.get(name=pname)

    context = {
        "proj": proj,
        "project_list": [p for p in BOINCProject.objects.filter(active=True)],
    }

    return render(request, 'bhs/project.html', context)


# Data URLs:
def project_data(request, pname, what):
    """Return JSON data for project named 'pname', and item 'what' (nhosts or credit)."""

    # Get project object from name 'pname':
    proj = BOINCProject.objects.get(name=pname)

    entries = LogEntry.objects.filter(project=proj).order_by("date")
    
    # Extract data to plot from DB:
    if what == "nhosts":
        data_win = [{"x": e.date, "y": e.nwindows} for e in entries]
        data_lin = [{"x": e.date, "y": e.nlinux} for e in entries]
        data_mac = [{"x": e.date, "y": e.nmacos} for e in entries]
        data_other = [{"x": e.date, "y": e.nother} for e in entries]
    elif what == "credit":
        data_win = [{"x": e.date, "y": e.cwindows} for e in entries]
        data_lin = [{"x": e.date, "y": e.clinux} for e in entries]
        data_mac = [{"x": e.date, "y": e.cmacos} for e in entries]
        data_other = [{"x": e.date, "y": e.cother} for e in entries]

    # Organize data, and return it:
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
        latest = LogEntry.objects.filter(project=proj)

        # If no log item found, then never logged. In that case, choose this project:
        if not latest:
            return proj

        latest = latest.order_by("-date")[0]
        dsu.append([latest.date, proj])

    return sorted(dsu)[0][1]

