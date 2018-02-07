# Standard libs:
import requests
import subprocess as sp

# Django libs:
from django.http import JsonResponse
from django.shortcuts import render, redirect

# Our libs:
from bhs.models import  BOINCProject, BOINCSettings

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
def download(request, pname):
    """Download hosts file for project named pname."""

    # Variables:
    rate = BOINCSettings.objects.get(name="default").bwlimit
    url = BOINCProject.objects.get(name=pname).url
    hosts_fn = BOINCSettings.objects.get(name="default").hostsgz_path

    # Download:
    r = requests.get(url, stream=True)
    with open(hosts_fn, "wb") as fhandle:
        for chunk in r:
            fhandle.write(chunk)

    # Return data:
    ret = {
        "status": r.status_code
    }

    return JsonResponse(ret)

def distile(request, pname):
    """Distile data from hosts.gz file for project named 'pname'."""

    # Variables:
    proj = BOINCProject.objects.get(name=pname)

    # Distile:
    proj.distile_stats()

    # Return data:
    ret = {}

    return JsonResponse(ret)

def get_data(request, pname):
    """download() + distile() data from hosts.gz file for project named 'pname'."""

    # Variables:
    proj = BOINCProject.objects.get(name=pname)

    # Download:
    r = requests.get(url, stream=True)
    if r.status_code == 200:
        print(r)

    # Return data:
    ret = {}

    return JsonResponse(ret)

