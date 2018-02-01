# Standard libs:
import requests
import subprocess as sp

# Django libs:
from django.http import JsonResponse
from django.shortcuts import render, redirect

# Our libs:
from bhs import core
from bhs.models import  BOINCProject, BOINCSettings

# Constants:
#SETTINGS = BOINCSettings.objects.get(name="default")

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
def project_data(request, pname):
    """Return JSON data."""

    proj = BOINCProject.objects.get(name=pname)

    data_win, data_lin, data_mac, data_other = core.make_plot(proj, "nhosts")

    data = {
        "win": data_win,
        "lin": data_lin,
        "mac": data_mac,
        "other": data_other,
    }

    return JsonResponse({"data": data})


# Action URLs:
def download(request, pname):
    """Download hosts file for project named pname."""

    # Variables:
    rate = BOINCSettings.objects.get(name="default").bwlimit
    url = BOINCProject.objects.get(name=pname).url

    # Download:
    r = requests.get(url, stream=True)
    with open("hosts.gz", "wb") as fhandle:
        for chunk in r:
            fhandle.write(chunk)

    # Return data:
    ret = {
        "status": r.status_code
    }

    return JsonResponse(ret)

